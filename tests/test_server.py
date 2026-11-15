"""Tests for the web API, using FakeTranslator instead of the 2.5 GB model."""
import base64
import io
import threading

import pytest
from fastapi.testclient import TestClient

from dose_safe.translator import FakeTranslator
from server import create_app

CAPLETS = "do not take more than 6 caplets in 24 hours"
LOST_NOT = "tome más de 6 cápsulas en 24 horas"
CORRECT = "no tome más de 6 cápsulas en 24 horas"
TABLE = {
    (CAPLETS, "spa_Latn"): [LOST_NOT, CORRECT],  # the model's first choice lost the "not"
    (LOST_NOT, "eng_Latn"): ["take more than 6 capsules in 24 hours"],
    (CORRECT, "eng_Latn"): ["do not take more than 6 capsules in 24 hours"],
}


def make_client(loader=lambda: FakeTranslator(TABLE), background=False):
    return TestClient(create_app(loader, load_in_background=background))


def test_status_lists_languages_and_which_were_tested():
    with make_client() as client:
        body = client.get("/api/status").json()
    assert body["status"] == "ready"
    tested = {lang["name"]: lang["tested"] for lang in body["languages"]}
    assert tested["Spanish"] and tested["Vietnamese"] and not tested["Tagalog"]


def test_safer_mode_picks_the_translation_that_keeps_the_not():
    with make_client() as client:
        body = client.post("/api/check", json={"english": CAPLETS, "language": "Spanish"}).json()
    assert body["verdict"] == "no_problems_found"
    assert body["translation"] == CORRECT
    assert body["changed"] is True
    assert all(check["ok"] for check in body["checks"])


def test_first_choice_mode_flags_the_lost_not_and_lists_failures_first():
    with make_client() as client:
        body = client.post("/api/check", json={"english": CAPLETS, "language": "Spanish", "safer": False}).json()
    assert body["verdict"] == "check"
    assert body["translation"] == LOST_NOT
    oks = [check["ok"] for check in body["checks"]]
    assert oks == sorted(oks)  # every failed check comes before every passed one
    assert body["checks"][0]["name"] == "“Not” kept"
    assert body["checks"][0]["detail"]


def test_too_long_input_is_refused_instead_of_cut_off():
    with make_client() as client:
        body = client.post("/api/check", json={"english": "take 1 tablet " * 100, "language": "Spanish"}).json()
    assert body["verdict"] == "too_long"
    assert "translation" not in body


def test_untested_language_is_marked():
    with make_client() as client:
        body = client.post("/api/check", json={"english": CAPLETS, "language": "Tagalog"}).json()
    assert body["language_tested"] is False


def test_bad_requests():
    with make_client() as client:
        assert client.post("/api/check", json={"english": CAPLETS, "language": "Klingon"}).status_code == 400
        assert client.post("/api/check", json={"english": "   ", "language": "Spanish"}).status_code == 422


def test_check_waits_politely_while_the_model_loads():
    release = threading.Event()

    def slow_loader():
        release.wait(5)
        return FakeTranslator(TABLE)

    with make_client(slow_loader, background=True) as client:
        assert client.get("/api/status").json()["status"] == "warming_up"
        response = client.post("/api/check", json={"english": CAPLETS, "language": "Spanish"})
        assert response.status_code == 503
        release.set()


def test_model_load_failure_is_reported():
    def broken_loader():
        raise RuntimeError("no disk space")

    with make_client(broken_loader) as client:
        assert client.get("/api/status").json()["status"] == "error"
        assert client.post("/api/check", json={"english": CAPLETS, "language": "Spanish"}).status_code == 503


# ---- Photo mode -----------------------------------------------------------------------------------

def test_check_lines_answers_every_line_in_order():
    lines = [CAPLETS, "take 1 tablet " * 100]
    with make_client() as client:
        body = client.post("/api/check-lines", json={"lines": lines, "language": "Spanish"}).json()
    first, second = body["results"]
    assert first["english"] == CAPLETS and first["translation"] == CORRECT
    assert first["verdict"] == "no_problems_found"
    assert second["verdict"] == "too_long" and "translation" not in second
    assert body["language_tested"] is True


def test_check_lines_refuses_empty_or_too_many_lines():
    with make_client() as client:
        assert client.post("/api/check-lines", json={"lines": [], "language": "Spanish"}).status_code == 422
        assert client.post("/api/check-lines", json={"lines": ["  "], "language": "Spanish"}).status_code == 422
        assert client.post("/api/check-lines", json={"lines": [CAPLETS] * 21, "language": "Spanish"}).status_code == 422
        assert client.post("/api/check-lines", json={"lines": [CAPLETS], "language": "Klingon"}).status_code == 400


LABEL = {"product": {"set_id": "0005aafa-08f8-4990-a54d-cc097195708f", "brand": "Pain Reliever Extra Strength"},
         "active_ingredients": ["Acetaminophen 500 mg"],
         "sections": [{"name": "Directions", "lines": [CAPLETS]}]}


def label_client(find_label):
    return TestClient(create_app(lambda: FakeTranslator(TABLE), load_in_background=False, find_label=find_label))


def test_label_by_typed_barcode_is_looked_up_once():
    asked = []

    def find_label(code):
        asked.append(code)
        return LABEL

    with label_client(find_label) as client:
        for _ in range(2):
            body = client.post("/api/label", json={"code": " 070038610953 "}).json()
    assert body["barcode"] == "070038610953"
    assert body["sections"] == LABEL["sections"]
    assert asked == ["070038610953"]  # the second time came from memory


def test_label_from_a_photo_reads_the_barcode():
    zxingcpp = pytest.importorskip("zxingcpp")
    from test_barcode import photo_of  # pytest puts tests/ on the import path

    photo = "data:image/jpeg;base64," + base64.b64encode(photo_of(zxingcpp.BarcodeFormat.UPCA, "070038610953")).decode()
    with label_client(lambda code: LABEL) as client:
        assert client.post("/api/label", json={"image": photo}).json()["barcode"] == "0070038610953"


def test_label_errors_say_what_to_do_next():
    from dose_safe.lookup import LabelNotFound, LabelSourceDown

    def not_found(code):
        raise LabelNotFound("No medicine label with this barcode is in the FDA's database.")

    def down(code):
        raise LabelSourceDown("Couldn't reach the FDA's label database.")

    blank = io.BytesIO()
    pytest.importorskip("PIL.Image").new("RGB", (300, 200), "white").save(blank, "JPEG")
    no_barcode = "data:image/jpeg;base64," + base64.b64encode(blank.getvalue()).decode()
    with label_client(not_found) as client:
        assert client.post("/api/label", json={"code": "070038610953"}).status_code == 404
        assert client.post("/api/label", json={"code": "aspirin"}).status_code == 422  # not a number
        assert client.post("/api/label", json={}).status_code == 422
        assert client.post("/api/label", json={"image": "data:image/jpeg;base64,@@@"}).status_code == 422
        response = client.post("/api/label", json={"image": no_barcode})
        assert response.status_code == 422 and "barcode" in response.json()["detail"]
    with label_client(down) as client:
        assert client.post("/api/label", json={"code": "070038610953"}).status_code == 502
