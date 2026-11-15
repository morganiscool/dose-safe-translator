"""Finding a medicine's official label from the barcode or NDC number on its box.

openFDA (the FDA's drug label database) turns the barcode into the label's DailyMed id ("set id"),
and DailyMed (US National Library of Medicine) has the label itself as XML. Both are free and need
no account. Only about a third of over-the-counter labels in openFDA list a barcode, so the NDC
number printed on the box ("NDC 12345-678-90") works too.
"""
import re
import time
import xml.etree.ElementTree as ET

OPENFDA_LABELS = "https://api.fda.gov/drug/label.json"
DAILYMED_SPL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{}.xml"
DAILYMED_PAGE = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={}"
HEADERS = {"User-Agent": "dose-safe-translator"}
TIMEOUT = 20
NDC = re.compile(r"^(\d{4,5})-(\d{3,4})(?:-(\d{1,2}))?$")


class LabelNotFound(Exception):
    """No label matches this barcode or NDC number. The message can be shown to the user."""


class LabelSourceDown(Exception):
    """openFDA or DailyMed didn't answer. The message can be shown to the user."""


def upce_to_upca(code):
    """The short 8-digit UPC-E barcode on small boxes, written out as the full 12-digit UPC-A."""
    system, d, check = code[0], code[1:7], code[7]
    if d[5] in "012":
        body = d[0:2] + d[5] + "0000" + d[2:5]
    elif d[5] == "3":
        body = d[0:3] + "00000" + d[3:5]
    elif d[5] == "4":
        body = d[0:4] + "00000" + d[4]
    else:
        body = d[0:5] + "0000" + d[5]
    return system + body + check


def search_terms(code):
    """What to ask openFDA for, from what a barcode reader or a person gave us.

    openFDA stores barcodes as 13 digits ("0070038610953" for the UPC 070038610953), so both
    spellings are searched. Raises ValueError with a message for the user when it isn't a barcode."""
    text = code.strip()
    text = re.sub(r"^ndc\s*", "", text, flags=re.IGNORECASE)
    ndc = NDC.match(text)
    if ndc:  # openFDA writes it with 10 digits (4-4, 5-3 or 5-4); boxes sometimes pad it to 11 (5-4)
        labeler, product = ndc[1], ndc[2]
        forms = [f"{labeler}-{product}"]
        if len(labeler) == 5 and labeler.startswith("0") and len(product) == 4:
            forms.append(f"{labeler[1:]}-{product}")
        if len(labeler) == 5 and len(product) == 4 and product.startswith("0"):
            forms.append(f"{labeler}-{product[1:]}")
        return "openfda.product_ndc", forms
    digits = re.sub(r"[\s-]", "", text)
    if not digits.isdigit():
        raise ValueError("That isn't a barcode number. Type the digits under the barcode, or the NDC "
                         "number printed on the box (it looks like 12345-678-90).")
    if len(digits) == 8:
        digits = upce_to_upca(digits)
    if len(digits) == 14:  # GTIN-14 from a GS1 DataMatrix: drop the packaging-level digit
        digits = digits[1:]
    if len(digits) == 12:
        forms = ["0" + digits, digits]
    elif len(digits) == 13:
        forms = [digits] + ([digits[1:]] if digits.startswith("0") else [])
    else:
        raise ValueError("A barcode on a medicine box has 8, 12 or 13 digits. Check the number, or type "
                         "the NDC number printed on the box (it looks like 12345-678-90).")
    if not digits.strip("0"):
        raise ValueError("That barcode is all zeros, which some labels use as a blank. Type the NDC "
                         "number printed on the box instead.")
    return "openfda.upc", forms


def find_label(code, http):
    """The newest openFDA label for a barcode or NDC number:
    {"set_id", "brand", "generic", "manufacturer", "upc", "ndc", "matches"}.
    `http` is the requests module (or a stand-in with the same .get, for tests)."""
    field, forms = search_terms(code)
    query = f"{field}:(" + " ".join(f'"{form}"' for form in forms) + ")"
    try:
        response = http.get(OPENFDA_LABELS, params={"search": query, "limit": 10},
                            headers=HEADERS, timeout=TIMEOUT)
    except Exception as error:  # connection refused, timeout, DNS...
        raise LabelSourceDown("Couldn't reach the FDA's label database. Check the internet "
                              "connection and try again.") from error
    if response.status_code == 404:
        what = "NDC number" if field == "openfda.product_ndc" else "barcode"
        hint = ("" if field == "openfda.product_ndc" else
                " Not every label lists its barcode there; try the NDC number printed on the box "
                "(it looks like 12345-678-90).")
        raise LabelNotFound(f"No medicine label with this {what} is in the FDA's database.{hint}")
    if response.status_code != 200:
        raise LabelSourceDown("The FDA's label database didn't answer properly. Try again in a minute.")
    body = response.json()
    results = [r for r in body.get("results", []) if r.get("set_id")]
    if not results:
        raise LabelNotFound("No medicine label with this barcode is in the FDA's database.")
    total = body.get("meta", {}).get("results", {}).get("total", len(results))

    def first(label, key):
        return (label.get("openfda", {}).get(key) or [""])[0]

    # Some makers fill in a placeholder barcode (012345678905 is on 134 different labels), so a barcode
    # shared by different products can't say which medicine this is. Guessing could show the wrong
    # directions, so ask for the NDC number, which names the maker and the product.
    products = {(first(r, "brand_name").lower().strip(), first(r, "manufacturer_name").lower().strip())
                for r in results}
    if field == "openfda.upc" and len(products) > 1:
        raise LabelNotFound(f"This barcode is listed on {total} different medicine labels in the FDA's "
                            "database, so it can't tell which one this box is. Type the NDC number printed "
                            "on the box instead (it looks like 12345-678-90).")
    newest = max(results, key=lambda r: r.get("effective_time", ""))
    return {"set_id": newest["set_id"],
            "brand": first(newest, "brand_name"),
            "generic": first(newest, "generic_name"),
            "manufacturer": first(newest, "manufacturer_name"),
            "upc": first(newest, "upc"),
            "ndc": first(newest, "product_ndc"),
            "matches": total,
            "dailymed_url": DAILYMED_PAGE.format(newest["set_id"])}


def fetch_label_xml(set_id, http, tries=3):
    """One label's original XML file from DailyMed, as an ElementTree root."""
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", set_id):
        raise LabelNotFound("That isn't a DailyMed label id.")
    for attempt in range(tries):
        try:
            response = http.get(DAILYMED_SPL.format(set_id), headers=HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                return ET.fromstring(response.content)
            if response.status_code == 404:
                raise LabelNotFound("DailyMed doesn't have this label any more.")
        except LabelNotFound:
            raise
        except Exception:  # connection trouble or a broken download: try again
            pass
        if attempt + 1 < tries:
            time.sleep(1 + attempt)
    raise LabelSourceDown("Couldn't download the label from DailyMed. Try again in a minute.")
