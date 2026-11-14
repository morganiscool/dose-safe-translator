"""Tests for the web API, using FakeTranslator instead of the 2.5 GB model."""
import threading

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
