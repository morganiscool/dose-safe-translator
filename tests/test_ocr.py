"""Tests for reading the printed directions off a box (dose_safe/ocr.py)."""
import io
from pathlib import Path

import pytest

from dose_safe.ocr import instructions_from_lines, lines_from_boxes, looks_english, photo_warning

np = pytest.importorskip("numpy")


def box(left, top, word, confidence=0.99, width=None, height=20):
    width = width or 12 * len(word)
    corners = [(left, top), (left + width, top), (left + width, top + height), (left, top + height)]
    return corners, word, confidence


def test_words_are_grouped_into_lines_left_to_right():
    white = np.full((200, 600), 250.0)
    found = [box(120, 12, "more"), box(10, 10, "do"), box(50, 11, "not"), box(10, 60, "children")]
    assert lines_from_boxes(found, white) == [[("do", 0.99), ("not", 0.99), ("more", 0.99)],
                                              [("children", 0.99)]]


def test_a_square_of_ink_is_the_bullet_not_a_number():
    # The ■ bullet is often read as "2", which would put a new number into the instruction.
    gray = np.full((100, 400), 250.0)
    gray[10:30, 10:30] = 20.0  # a solid square
    found = [box(10, 10, "2", 0.9, width=20), box(40, 10, "shake"), box(110, 10, "well")]
    assert lines_from_boxes(found, gray)[0][0] == ("■", 1.0)


def test_lines_are_joined_into_instructions_one_per_bullet_or_row():
    lines = [[("Directions", 0.99)],
             [("■", 1.0), ("do", 0.99), ("not", 0.99), ("take", 0.99), ("more", 0.99), ("than", 0.99)],
             [("6", 0.99), ("caplets", 0.99), ("in", 0.99), ("24", 0.99), ("hours", 0.99)],
             [("children", 0.99), ("under", 0.99), ("12", 0.99), ("years:", 0.99)],
             [("ask", 0.99), ("a", 0.99), ("doctor", 0.99)],
             [("0", 0.99), ("70038", 0.99), ("61095", 0.99), ("3", 0.99)]]  # the digits under a barcode
    texts = [item["text"] for item in instructions_from_lines(lines)]
    assert texts == ["do not take more than 6 caplets in 24 hours",  # "than" carries on to the next line
                     "children under 12 years: ask a doctor"]      # a colon carries on too


def test_barcode_digits_with_a_stray_mark_are_still_left_out():
    # A real read of a box with its barcode beside the Directions: the digits came back as
    # '5 "290665 007802', and the quote mark let them join the last instruction ("... do not use 5
    # "290665 007802"), adding numbers that aren't on the label.
    lines = [[("■", 1.0), ("children", 0.99), ("under", 0.99), ("6", 0.99), ("years:", 0.99), ("do", 0.99),
              ("not", 0.99), ("use", 0.99)],
             [("5", 0.91), ('"290665', 0.62), ("007802", 0.88)]]
    assert [item["text"] for item in instructions_from_lines(lines)] == ["children under 6 years: do not use"]


def test_unsure_words_are_marked_with_the_reason():
    lines = [[("take", 0.99), ("2", 0.45), ("tablets", 0.99), ("every", 0.2), ("l2", 0.99), ("hours", 0.99),
              ("500mg", 0.99)]]
    words = instructions_from_lines(lines)[0]["words"]
    checks = {w["text"]: w["check"] for w in words}
    assert checks["2"] == "45% sure"          # numbers need 70%
    assert checks["every"] == "20% sure"      # other words need 30%
    assert checks["l2"] == "letters mixed into a number"
    assert checks["500mg"] is None and checks["take"] is None
    assert photo_warning("4", 0.69) and not photo_warning("4", 0.7)
    assert photo_warning("24", 0.696) == "69% sure"  # never "70% sure" for a word under the 70% bar
    assert photo_warning("6", 0.57) == "57% sure"


@pytest.mark.parametrize("text, english", [
    ("adults and children 12 years and over: take 2 tablets every 6 hours", True),
    ("tomar 2 comprimidos cada 6 horas con un vaso de agua", False),
    ("Παιδιά κάτω των 12 ετών: συμβουλευτείτε γιατρό", False),
    ("take 2", None),  # too few words to tell
])
def test_text_in_another_language_is_noticed(text, english):
    assert looks_english([{"text": text}]) is english


MODELS = Path.home() / ".EasyOCR" / "model"


@pytest.mark.skipif(not (MODELS / "craft_mlt_25k.pth").exists(), reason="EasyOCR's models aren't downloaded")
def test_easyocr_reads_a_printed_directions_panel():
    from PIL import Image, ImageDraw, ImageFont

    from dose_safe.ocr import load_reader, read_lines

    panel = ["Directions", "■ do not take more than directed",
             "■ adults and children 12 years and over: take 2 caplets every 6 hours",
             "■ children under 12 years: ask a doctor"]
    image = Image.new("RGB", (1200, 280), (248, 248, 244))
    draw = ImageDraw.Draw(image)
    for i, text in enumerate(panel):
        draw.text((30, 24 + 60 * i), text, fill=(20, 20, 20), font=ImageFont.load_default(size=30 if i else 34))
    photo = io.BytesIO()
    image.save(photo, "JPEG", quality=90)
    found = instructions_from_lines(read_lines(load_reader(), photo.getvalue()))
    assert [item["text"] for item in found] == [s.removeprefix("■ ") for s in panel[1:]]
