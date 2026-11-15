"""Reading a photo of a drug label's Directions section (from dose_safe.ipynb, section 10).

EasyOCR finds each word in the photo, reads it, and gives a confidence from 0 to 1. The words are
joined into lines and the lines into instructions (a new one starts at each ■ bullet or table row).
Words to check against the label are flagged: numbers read with less than 70% confidence, other
words below 30%, and letters mixed into a number, like "l2". The notebook chose these cut-offs on
made-up label photos and measured how many dangerous misreads they catch (README, "Reading label
photos"). The reader can still skip a word entirely, so a person must compare the text with the label.
"""
import re
import unicodedata

import numpy as np

OCR_CONFIDENCE_MIN = 0.3
NUMBER_CONFIDENCE_MIN = 0.7
MAX_SIDE = 2000  # longer photos are shrunk first: much faster, and label print stays readable
BULLETS = r"[•●▪■◦-]"  # bullet marks, including symbol-font ones like U+F06E
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


def clean(text):
    text = unicodedata.normalize("NFKC", text).replace("⁄", "/")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(BULLETS, " ", text)
    return " ".join(text.split()).strip(" ;,-–—:")


def load_reader(gpu=False):
    """EasyOCR's English reader. It downloads about 100 MB of models the first time."""
    import easyocr
    return easyocr.Reader(["en"], gpu=gpu, verbose=False)


def prepare(image):
    """The photo upright (phones store the rotation separately), in color, and not too big."""
    from PIL import ImageOps
    image = ImageOps.exif_transpose(image).convert("RGB")
    if max(image.size) > MAX_SIDE:
        image.thumbnail((MAX_SIDE, MAX_SIDE))
    return image


def read_photo(reader, image):
    """Read every word in a photo. Returns its lines from top to bottom; each line is a list of
    (word, confidence) pairs from left to right."""
    pixels = np.asarray(image.convert("RGB"))
    gray = pixels.mean(axis=2)
    # One box per word (width_ths=0), and keep small boxes (min_size=4): with EasyOCR's defaults,
    # one-character words like the "4" in "3 to 4 times" were silently dropped in our tests.
    found = reader.readtext(pixels, width_ths=0.0, min_size=4)
    boxes = []
    for corners, word, confidence in found:
        xs, ys = [float(x) for x, _ in corners], [float(y) for _, y in corners]
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        word, confidence = word.strip(), float(confidence)
        # The ■ bullet is often read as "2", "4" or "E", which would add a number to the
        # instruction. A box that is roughly square and mostly ink is a bullet, not a character.
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
    return [[(b["word"], b["confidence"]) for b in sorted(line, key=lambda b: b["left"])]
            for line in lines]


def photo_warning(word, confidence, number_min=None):
    """Why a word read from a photo should be checked against the label (None if it looks fine)."""
    has_digit = any(char.isdigit() for char in word)
    minimum = (NUMBER_CONFIDENCE_MIN if number_min is None else number_min) if has_digit else OCR_CONFIDENCE_MIN
    if confidence < minimum:
        return f"“{word}” ({confidence:.0%} sure)"
    for token in re.split(r"[-–/]", word.strip(",.;:()")):
        if MIXED.search(token) and not UNIT_SUFFIX.match(token):
            return f"“{word}” (letters mixed into a number)"
    return None


def photo_to_instructions(reader, image):
    """Read a label photo and join its lines into whole instructions, one per bullet or table row.
    Each instruction keeps the words it was read from and the ones to check."""
    chunks = []
    for line in read_photo(reader, image):
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
        unsure = [(word, warning) for word, confidence in chunk["words"]
                  if (warning := photo_warning(word, confidence))]
        instructions.append({"text": text, "words": chunk["words"], "unsure": unsure})
    return instructions


def still_in(word, text):
    """Whether a word read from the photo is still in the (possibly corrected) text. The text was
    cleaned (quotes, trailing commas), so the word is looked for as read and as cleaned."""
    return any(re.search(rf"(?<!\w){re.escape(form)}(?!\w)", text)
               for form in {word, clean(word)} if form)
