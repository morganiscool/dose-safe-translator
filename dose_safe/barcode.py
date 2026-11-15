"""Reading the barcode in a photo of a medicine box (with zxing-cpp, a free barcode reader)."""
import io
import re

MAX_SIDE = 2000  # bigger photos are shrunk first; barcodes read fine at this size


def read_barcode(image_bytes):
    """The number in the first retail barcode found in the photo, or None.

    Reads the barcodes printed on US medicine boxes (UPC-A, UPC-E, EAN-13, EAN-8) and the GS1
    DataMatrix squares on some packs, from which it takes the product number (GTIN)."""
    import zxingcpp
    from PIL import Image, ImageOps

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("L")  # phone photos are often stored sideways
    except Exception:
        return None
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    formats = [zxingcpp.BarcodeFormat.UPCA, zxingcpp.BarcodeFormat.UPCE, zxingcpp.BarcodeFormat.EAN13,
               zxingcpp.BarcodeFormat.EAN8, zxingcpp.BarcodeFormat.DataMatrix]
    for found in zxingcpp.read_barcodes(image, formats=formats):
        text = found.text.strip()
        gtin = re.search(r"\(01\)(\d{14})", text) or re.match(r"^01(\d{14})", text)
        if gtin:
            return gtin[1]
        if text.isdigit() and len(text) in (8, 12, 13):
            return text
    return None
