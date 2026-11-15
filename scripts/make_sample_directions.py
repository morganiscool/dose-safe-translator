"""Make web/media/sample-directions.jpg: a made-up phone photo of a box's printed Directions panel.

The text is the real Directions section of the DailyMed label "Allergy Relief" (diphenhydramine),
set id 00f89eee-0edc-40dc-9297-8645afb91004, printed with the app's font (Public Sans) and spoiled
like a quick phone photo (tilt, soft focus, uneven light, noise, JPEG), the way dose_safe.ipynb
section 10 makes its test photos. The 6 in the second line is printed slightly worn, like a scuffed
box (it still reads correctly; the 24 after it is the word marked as hard to read).
python scripts/make_sample_directions.py . --worn
"""
import io
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

repo = sys.argv[1]
worn = "--worn" in sys.argv
FONT = f"{repo}/web/fonts/PublicSans-Variable.ttf"
LINES = [
    "take every 4 to 6 hours, or as directed by a doctor",
    "do not take more than 6 times in 24 hours",
    "adults and children 12 years and over: 1 to 2 tablets",
    "children 6 to under 12 years: 1 tablet",
    "children under 6 years: do not use",
]


def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(weight)
    return f


W, H = 1500, 760
card = Image.new("RGB", (W, H), (250, 248, 242))
draw = ImageDraw.Draw(card)
draw.rectangle([18, 18, W - 19, H - 19], outline=(25, 25, 25), width=5)
draw.text((52, 40), "Directions", fill=(18, 18, 18), font=font(52, "Black"))
draw.rectangle([52, 118, W - 52, 124], fill=(25, 25, 25))
body = font(40, "Regular")
y = 160
worn_box = None
for text in LINES:
    draw.rectangle([56, y + 16, 75, y + 35], fill=(18, 18, 18))  # the ■ bullet (Public Sans has no ■)
    draw.text((100, y), text, fill=(18, 18, 18), font=body)
    if worn and text.startswith("do not take more than 6"):
        x0 = 100 + body.getlength("do not take more than ")
        worn_box = (int(x0) - 4, y + 2, int(x0 + body.getlength("6")) + 6, y + 52)
    y += 108

if worn_box:  # a scuffed digit: lighter, broken ink, as on a worn box
    patch = card.crop(worn_box)
    a = np.asarray(patch, dtype=np.float32)
    rng = np.random.default_rng(7)
    a = 255 - (255 - a) * 0.70  # faded ink
    a += rng.normal(0, 18, a.shape)
    patch = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
    card.paste(patch, worn_box[:2])

# The box on a counter, photographed a little crooked.
photo = Image.new("RGB", (W + 160, H + 160), (196, 188, 176))
photo.paste(card, (80, 70))
photo = photo.rotate(-2.2, resample=Image.BICUBIC, expand=False, fillcolor=(196, 188, 176))
photo = photo.filter(ImageFilter.GaussianBlur(0.9))
a = np.asarray(photo, dtype=np.float32)
light = np.linspace(0.84, 1.03, a.shape[1])[None, :, None] * np.linspace(1.0, 0.92, a.shape[0])[:, None, None]
rng = np.random.default_rng(15)
a = a * light + rng.normal(0, 5, a.shape)
out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
out.thumbnail((1400, 1400))
out.save(f"{repo}/web/media/sample-directions.jpg", "JPEG", quality=82, optimize=True)
print("saved", out.size)
