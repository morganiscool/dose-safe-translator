"""Tests for reading the barcode in a photo of a medicine box."""
import io

import pytest

zxingcpp = pytest.importorskip("zxingcpp")
Image = pytest.importorskip("PIL.Image")


def photo_of(fmt, text, angle=0):
    """A barcode drawn on a white card, optionally turned, as JPEG bytes like a phone would send."""
    bars = zxingcpp.create_barcode(text, fmt).to_image(scale=4)
    bars = bars if isinstance(bars, Image.Image) else Image.fromarray(bars)
    card = Image.new("L", (bars.width + 240, bars.height + 240), 255)
    card.paste(bars.convert("L"), (120, 120))
    card = card.rotate(angle, expand=True, fillcolor=255)
    out = io.BytesIO()
    card.convert("RGB").save(out, "JPEG", quality=85)
    return out.getvalue()


def test_read_barcode_from_photos():
    from dose_safe.barcode import read_barcode
    assert read_barcode(photo_of(zxingcpp.BarcodeFormat.UPCA, "070038610953")) == "0070038610953"
    assert read_barcode(photo_of(zxingcpp.BarcodeFormat.UPCA, "070038610953", angle=90)) == "0070038610953"
    assert read_barcode(photo_of(zxingcpp.BarcodeFormat.DataMatrix, "(01)00070038610953(17)271231")) == \
        "00070038610953"


def test_read_barcode_without_a_barcode():
    from dose_safe.barcode import read_barcode
    blank = io.BytesIO()
    Image.new("RGB", (400, 300), "white").save(blank, "JPEG")
    assert read_barcode(blank.getvalue()) is None
    assert read_barcode(b"this is not a picture") is None
