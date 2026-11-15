"""Tests for One label line's "read the lines from a photo" (/api/read-text) and the check it adds.
The reading itself (dose_safe/ocr.py) is tested in test_ocr.py; here a fake EasyOCR answers."""
import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from dose_safe.ocr import read_lines, still_in
from dose_safe.translator import FakeTranslator
from server import PHOTO_CHECK, create_app


def box(left, top, width, height=20):
    return [[left, top], [left + width, top], [left + width, top + height], [left, top + height]]


class FakeEasyOCR:
    """Answers readtext() with fixed (box, word, confidence) results, like EasyOCR does."""

    def __init__(self, results):
        self.results = results

    def readtext(self, pixels, **_):
        return self.results


# A Directions panel: a heading, a bulleted instruction that runs onto a second line, and a table
# row. The reader was only 55% sure of the "24".
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
    """A PNG of a white label with a black ■ where the reader found the bullet."""
    image = Image.new("RGB", (400, 160), "white")
    ImageDraw.Draw(image).rectangle([12, 52, 28, 68], fill="black")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


SPANISH = {
    ("do not take more than 6 tablets in 24 hours", "spa_Latn"): ["no tome más de 6 tabletas en 24 horas"],
    ("no tome más de 6 tabletas en 24 horas", "eng_Latn"): ["do not take more than 6 tablets in 24 hours"],
}


def make_client(reader=True):
    # The same kind of reader the real app loads: photo bytes in, lines of (word, confidence) out.
    load = (lambda: (lambda image_bytes: read_lines(FakeEasyOCR(LABEL), image_bytes))) if reader else None
    return TestClient(create_app(lambda: FakeTranslator(SPANISH), load_in_background=False,
                                 find_label=lambda code: None, load_photo_reader=load))


def test_read_text_marks_the_words_to_compare_with_the_label():
    with make_client() as client:
        assert client.get("/api/status").json()["photo_reader"] == "ready"
        body = client.post("/api/read-text", content=label_photo(),
                           headers={"Content-Type": "image/png"}).json()
    assert [item["text"] for item in body["instructions"]] == [
        "do not take more than 6 tablets in 24 hours",
        "children under 12 years: ask a doctor",
    ]
    first = body["instructions"][0]
    assert first["unsure"] == [{"word": "24", "warning": "“24” (55% sure)"}]
    assert [w["text"] for w in first["words"] if w["warning"]] == ["24"]
    assert body["instructions"][1]["unsure"] == []


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


def test_a_corrected_word_no_longer_counts():
    assert still_in("24", "do not take more than 6 tablets in 24 hours")
    assert not still_in("24", "do not take more than 6 tablets in 12 hours")
    assert not still_in("2", "take 12 tablets")  # a whole word, not part of another number


def test_read_text_is_off_without_a_reader():
    with make_client(reader=False) as client:
        assert client.get("/api/status").json()["photo_reader"] == "off"
        assert client.post("/api/read-text", content=label_photo()).status_code == 503


def test_bad_photos():
    with make_client() as client:
        assert client.post("/api/read-text", content=b"").status_code == 422
        assert client.post("/api/read-text", content=b"not an image").status_code == 415
