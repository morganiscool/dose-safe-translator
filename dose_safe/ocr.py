"""Reading the printed directions off a medicine box, for boxes whose label isn't in the FDA's database
(any box made for another country, and US labels that don't list their barcode).

Ported from dose_safe.ipynb, section 10 (photo input), where it is tested on made-up label photos at four
levels of blur. EasyOCR reads each word with a confidence from 0 to 1; the words are joined into whole
instructions, one per bullet or table row; and the words the pharmacist must compare with the box are
marked: numbers read with less than 70% confidence, other words below 30%, and letters mixed into a
number (like "l2"). A misread number passes every translation check, so the pharmacist checks the text
before anything is translated.
"""
import io
import math
import re

from dose_safe.labels import clean

# Words read with less confidence than this are marked. Numbers get a stricter bar, because a wrong
# number is the most dangerous misread. Both values were picked in the notebook on made-up photos of
# 60 label instructions that are not in its test set.
OCR_CONFIDENCE_MIN = 0.3
NUMBER_CONFIDENCE_MIN = 0.7
MAX_SIDE = 2000  # bigger photos are shrunk first (the page already sends at most 2000 px)
MAX_INSTRUCTIONS = 40  # a photo with more text than this isn't a Directions panel

HEADINGS = ["drug facts (continued)", "drug facts", "directions", "uses", "warnings",
            "other information", "inactive ingredients"]  # section titles, left out of the text
STARTERS = ("adults", "adult", "children", "child", "teens", "teenagers", "persons", "infants",
            "do not", "don't")  # a line that starts like this is a new instruction (a new table row)
CONNECTORS = {"and", "or", "to", "of", "than", "the", "a", "an", "every", "by", "for", "in", "with",
              "under", "over", "if", "not"}  # a line that ends like this continues on the next line
BULLET = re.compile(r"^[■□▪▫●•◦‣∙*=»]+")     # OCR often reads the ■ bullet as = or •
BORDER = re.compile(r"^[|\[\]{}_]+$")        # table borders read as characters
MIXED = re.compile(r"(?=.*\d)(?=.*[a-z])", re.I)
UNIT_SUFFIX = re.compile(r"^\d+(?:[.,/]\d+)?(?:mg|mcg|ml|g|oz|hrs?|h|th|st|nd|rd|x|yrs?)$", re.I)

# Common words of English medicine directions. Text where few words are on this list is probably in
# another language, and the safety checks only work from English.
ENGLISH_WORDS = set("""
a about after age all an and any are as ask at be before by can chew children child daily day days dissolve
do does doctor dose doses each every exceed food for from give glass hour hours if in is it keep last less
may meal meals more most mouth not of on once one or other over per pharmacist product products should
stop swallow symptoms tablet tablets take taken than that the them then this time times to twice under
until up use used using water week weeks when while with without years you your adults adult capsule
capsules caplet caplets teaspoon teaspoons ml mg directed directions warning warnings hrs
""".split())


def load_reader():
    """EasyOCR's English reader, on the CPU. The first call downloads its models (about 100 MB)."""
    import easyocr

    return easyocr.Reader(["en"], gpu=False, verbose=False)


def read_lines(reader, image_bytes):
    """Every word in the photo, as lines from top to bottom; each line is a list of (word, confidence)
    pairs from left to right. None if the bytes aren't a picture."""
    import numpy as np
    from PIL import Image, ImageOps

    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    except Exception:
        return None
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    pixels = np.asarray(image)
    # One box per word (width_ths=0), and keep small boxes (min_size=4): with EasyOCR's defaults,
    # one-character words like the "4" in "3 to 4 times" were silently dropped in the notebook's tests.
    found = reader.readtext(pixels, width_ths=0.0, min_size=4)
    return lines_from_boxes(found, pixels.mean(axis=2))


def lines_from_boxes(found, gray):
    """Group EasyOCR's word boxes [(corners, word, confidence)] into lines. `gray` is the photo as a
    2-D array of brightness, used to tell the ■ bullet from a character."""
    boxes = []
    for corners, word, confidence in found:
        xs, ys = [float(x) for x, _ in corners], [float(y) for _, y in corners]
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        word, confidence = word.strip(), float(confidence)
        # The ■ bullet is often read as "2", "4" or "E", which would add a number to the instruction.
        # A box that is roughly square and mostly ink is a bullet, not a character.
        patch = gray[int(max(top, 0)):int(bottom) + 1, int(max(left, 0)):int(right) + 1]
        if patch.size and 0.6 < (right - left) / max(1.0, bottom - top) < 1.6:
            if (patch < (float(patch.min()) + float(patch.max())) / 2).mean() > 0.5:
                word, confidence = "■", 1.0
        if word and not BORDER.match(word):
            boxes.append({"left": left, "top": top, "bottom": bottom, "word": word, "confidence": confidence})
    lines = []
    for box in sorted(boxes, key=lambda b: b["top"] + b["bottom"]):
        middle = (box["top"] + box["bottom"]) / 2
        if lines and lines[-1][-1]["top"] <= middle <= lines[-1][-1]["bottom"]:
            lines[-1].append(box)  # same row as the word before it
        else:
            lines.append([box])
    return [[(b["word"], b["confidence"]) for b in sorted(line, key=lambda b: b["left"])] for line in lines]


def photo_warning(word, confidence):
    """Why a word read from a photo should be checked against the box (None if it looks fine)."""
    has_digit = any(char.isdigit() for char in word)
    if confidence < (NUMBER_CONFIDENCE_MIN if has_digit else OCR_CONFIDENCE_MIN):
        # Rounded down, so a number read at 0.696 says "69% sure", not the "70%" it fell short of.
        return f"{math.floor(round(confidence * 100, 6))}% sure"
    for token in re.split(r"[-–/]", word.strip(",.;:()")):
        if MIXED.search(token) and not UNIT_SUFFIX.match(token):
            return "letters mixed into a number"
    return None


def instructions_from_lines(lines):
    """Join a photo's lines into whole instructions, one per bullet or table row:
    [{"text", "words": [{"text", "check"}]}], where "check" says why a word must be compared with the box."""
    chunks = []
    for line in lines:
        joined = "".join(word for word, _ in line)
        # The number printed under a barcode: 8+ digits and no letters, whatever marks the reader
        # adds (a real read came back as '5 "290665 007802'). It ends the instruction before it.
        if sum(char.isdigit() for char in joined) >= 8 and not re.search(r"[^\W\d_]", joined):
            chunks.append(None)
            continue
        previous = chunks[-1] if chunks else None
        last = previous["words"][-1][0] if previous and previous["words"] else ""
        after_colon = last.endswith(":")  # "children under 2 years:" goes on to the next line
        plain = [clean(word).lower() for word, _ in line]
        for heading in HEADINGS:  # a capitalized section title like "Directions" is left out
            size = len(heading.split())
            if not after_colon and line[0][0][:1].isupper() and plain[:size] == heading.split():
                line, previous, last = line[size:], None, ""
                chunks.append(None)  # a title also ends the instruction before it
                break
        if not line:
            continue
        first_words = clean(" ".join(word for word, _ in line[:3])).lower()
        line_starts_new = (not previous or not previous["words"] or (not after_colon and (
            last.endswith((".", ";")) or
            (first_words.startswith(STARTERS) and clean(last).lower() not in CONNECTORS))))
        for i, (word, confidence) in enumerate(line):
            bullet = BULLET.match(word)
            word = BULLET.sub("", word).strip()
            if bullet or (i == 0 and line_starts_new):
                chunks.append({"words": []})
            if word:
                chunks[-1]["words"].append((word, confidence))
    instructions = []
    for chunk in chunks:
        if not chunk or not chunk["words"]:
            continue
        text = clean(" ".join(word for word, _ in chunk["words"]))
        if len(text.split()) < 2 and not re.search(r"\d", text):
            continue  # a stray mark, not an instruction
        instructions.append({"text": text, "words": [{"text": word, "check": photo_warning(word, confidence)}
                                                     for word, confidence in chunk["words"]]})
    return instructions[:MAX_INSTRUCTIONS]


def looks_english(instructions):
    """False when few of the words read are common English direction words, None when there are too
    few words to tell."""
    words = [w for item in instructions for w in re.findall(r"[^\W\d_]{2,}", item["text"].lower())]
    if len(words) < 4:
        return None
    return sum(word in ENGLISH_WORDS for word in words) / len(words) >= 0.25


def still_in(word, text):
    """Whether a word read from the photo is still in the text after the pharmacist's corrections. The
    text was cleaned (quotes, trailing commas), so the word is looked for as read and as cleaned."""
    return any(re.search(rf"(?<!\w){re.escape(form)}(?!\w)", text) for form in {word, clean(word)} if form)
