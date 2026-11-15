"""Tests for reading the text of a label in a photo, using a fake reader instead of EasyOCR's models."""
import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from dose_safe.photo import photo_to_instructions, photo_warning, still_in
from dose_safe.translator import FakeTranslator
from server import PHOTO_CHECK, create_app


def box(left, top, width, height=20):
    return [[left, top], [left + width, top], [left + width, top + height], [left, top + height]]


class FakeReader:
    """Answers readtext() with fixed (box, word, confidence) results, like EasyOCR does."""

    def __init__(self, results):
        self.results = results

    def readtext(self, pixels, **_):
        return self.results


# A Directions panel: a heading, two bulleted instructions (the second runs onto a second line)
# and a table row. The reader was only 55% sure of the "24".
LABEL = [
    (box(10, 10, 120), "Directions", 0.99),
    (box(10, 50, 20), "■", 0.40),
    (box(40, 50, 30), "do", 0.99), (box(80, 50, 30), "not", 0.98), (box(120, 50, 50), "take", 0.97),
    (box(180, 50, 50), "more", 0.99), (box(240, 50, 40), "than", 0.99), (box(290, 50, 14), "6", 0.93),
    (box(10, 80, 60), "tablets", 0.96), (box(80, 80, 20), "in", 0.99), (box(110, 80, 24), "24", 0.55),
    (box(140, 80, 60), "hours", 0.99),
    (box(10, 110, 70), "children", 0.98), (box(90, 110, 50), "under", 0.97), (box(150, 110, 24), "12", 0.95),
    (box(180, 110, 60), "years:", 0.94), (box(250, 110, 30), "ask", 0.99), (box(290, 110, 14), "a", 0.90),
    (box(310, 110, 60), "doctor", 0.99),
]


def label_photo():
    """A white photo with a black ■ where the reader found the bullet."""
    image = Image.new("RGB", (400, 160), "white")
    ImageDraw.Draw(image).rectangle([12, 52, 28, 68], fill="black")
    return image


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def test_photo_is_read_into_whole_instructions_with_the_unsure_number_flagged():
    found = photo_to_instructions(FakeReader(LABEL), label_photo())
    assert [item["text"] for item in found] == [
        "do not take more than 6 tablets in 24 hours",
        "children under 12 years: ask a doctor",
    ]
    assert found[0]["unsure"] == [("24", "“24” (55% sure)")]
    assert found[1]["unsure"] == []


def test_the_bullet_square_is_not_read_as_a_number():
    # The reader called the bullet "2", which would have added a number to the instruction.
    misread = [(box(10, 50, 20), "2", 0.80)] + LABEL[2:8]
    found = photo_to_instructions(FakeReader(misread), label_photo())
    assert found[0]["text"] == "do not take more than 6"


def test_photo_warnings():
    assert photo_warning("24", 0.69) == "“24” (69% sure)"      # numbers need 70%
    assert photo_warning("tablets", 0.35) is None                 # other words need 30%
    assert photo_warning("l2", 0.99) == "“l2” (letters mixed into a number)"
    assert photo_warning("200mg", 0.99) is None                   # a unit, not a misread


def test_a_corrected_word_no_longer_counts():
    assert still_in("24", "do not take more than 6 tablets in 24 hours")
    assert not still_in("24", "do not take more than 6 tablets in 12 hours")
    assert not still_in("2", "take 12 tablets")  # a whole word, not part of another number


SPANISH = {
    ("do not take more than 6 tablets in 24 hours", "spa_Latn"): ["no tome más de 6 tabletas en 24 horas"],
    ("no tome más de 6 tabletas en 24 horas", "eng_Latn"): ["do not take more than 6 tablets in 24 hours"],
}


def make_client(reader=FakeReader(LABEL)):
    return TestClient(create_app(lambda: FakeTranslator(SPANISH), load_in_background=False,
                                 load_text_reader=(lambda: reader) if reader else None))


def test_read_text_endpoint():
    with make_client() as client:
        assert client.get("/api/status").json()["text_reader"] == "ready"
        body = client.post("/api/read-text", content=png(label_photo()),
                           headers={"Content-Type": "image/png"}).json()
    first = body["instructions"][0]
    assert first["text"] == "do not take more than 6 tablets in 24 hours"
    assert first["unsure"] == [{"word": "24", "warning": "“24” (55% sure)"}]
    assert [w["text"] for w in first["words"] if w["warning"]] == ["24"]


def test_a_line_from_the_photo_is_flagged_until_the_unsure_word_is_checked():
    request = {"english": "do not take more than 6 tablets in 24 hours", "language": "Spanish",
               "safer": False, "photo_unsure": [{"word": "24", "warning": "“24” (55% sure)"}]}
    with make_client() as client:
        body = client.post("/api/check", json=request).json()
        assert body["verdict"] == "check"
        assert body["from_photo"] is True
        assert body["checks"][0] == {"name": PHOTO_CHECK, "ok": False, "looks_at": "photo",
                                     "detail": "hard to read: “24” (55% sure)"}
        # The same line typed in, without photo words: every check passes.
        typed = client.post("/api/check", json={**request, "photo_unsure": None}).json()
        assert typed["verdict"] == "no_problems_found"
        assert all(c["name"] != PHOTO_CHECK for c in typed["checks"])
        # The pharmacist compared the marked word with the label: the page sends no unsure words.
        confirmed = client.post("/api/check", json={**request, "photo_unsure": []}).json()
        assert confirmed["verdict"] == "no_problems_found"
        assert {"name": PHOTO_CHECK, "ok": True, "detail": "", "looks_at": "photo"} in confirmed["checks"]


def test_text_reader_off_without_a_reader():
    with make_client(reader=None) as client:
        assert client.get("/api/status").json()["text_reader"] == "off"
        response = client.post("/api/read-text", content=png(label_photo()))
        assert response.status_code == 503


def test_a_text_reader_that_is_not_installed_turns_it_off():
    def missing():
        raise ImportError("No module named 'easyocr'")

    app = create_app(lambda: FakeTranslator(SPANISH), load_in_background=False, load_text_reader=missing)
    with TestClient(app) as client:
        body = client.get("/api/status").json()
    assert body["status"] == "ready" and body["text_reader"] == "off"


def test_bad_photos():
    with make_client() as client:
        assert client.post("/api/read-text", content=b"").status_code == 422
        assert client.post("/api/read-text", content=b"not an image").status_code == 415
