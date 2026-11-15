"""Reading US drug labels (DailyMed SPL XML) into whole instructions.

The parsing functions come from dose_safe.ipynb, section 3, where they build the test data. Photo
mode uses them too: `label_sections` pulls out what a pharmacist needs to tell a patient.
"""
import re
import unicodedata

HL7 = "{urn:hl7-org:v3}"  # the XML namespace of every SPL label
CONTINUATIONS = ("if ", "with ", "for ", "in ", "on ", "unless ", "while ", "to ")

# Label section codes (LOINC) and the headings printed on the Drug Facts panel.
ACTIVE_INGREDIENT = "55106-9"
PHOTO_SECTIONS = {  # in the order photo mode shows them
    "55105-1": "Purpose",
    "34067-9": "Uses",
    "34068-7": "Directions",
    "50570-1": "Do not use",
}
UNTITLED_PART = "42229-5"  # "SPL unclassified section": a sub-part with no heading of its own
# Bullet marks. Some labels use a symbol-font bullet stored as a private-use character (like U+F06E).
BULLETS = r"[•●▪■◦-]"


def clean(text):
    text = unicodedata.normalize("NFKC", text).replace("⁄", "/")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(BULLETS, " ", text)
    return " ".join(text.split()).strip(" ;,-–—:")


def element_text(element, skip_lists=False):
    """All the text inside an XML element (optionally leaving out nested lists and tables)."""
    parts = [element.text or ""]
    for child in element:
        if not (skip_lists and child.tag in (f"{HL7}list", f"{HL7}table")):
            parts.append(element_text(child, skip_lists))
        parts.append(child.tail or "")
    return " ".join(" ".join(parts).split())


def child_lists(element):
    """Lists directly inside this element (not lists nested deeper inside those lists)."""
    found = []
    for child in element:
        if child.tag == f"{HL7}list":
            found.append(child)
        elif child.tag != f"{HL7}table":
            found.extend(child_lists(child))
    return found


def list_units(xml_list, prefix=""):
    """Turn a bulleted list into sentences, e.g. 'adults: take 2 caplets every 6 hours'."""
    units = []
    for item in xml_list.findall(f"{HL7}item"):
        own_text = clean(element_text(item, skip_lists=True))
        label = f"{prefix}: {own_text}" if prefix and own_text else (prefix or own_text)
        nested = child_lists(item)
        if nested:
            for sub_list in nested:
                units += list_units(sub_list, label)
        elif label:
            units.append(label)
    return units


def table_units(table):
    """Dosing tables: 'children 6-11 years: take 1 tablet every 4 hours'."""
    units = []
    for row in table.iter(f"{HL7}tr"):
        if any(cell.tag == f"{HL7}th" for cell in row):
            continue  # header row
        cells = [clean(element_text(cell)) for cell in row if cell.tag == f"{HL7}td"]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            units.append(f"{cells[0]}: {'; '.join(cells[1:])}")
        elif cells:
            units.append(cells[0])
    return units


def full_warning(unit):
    """Turn a "Do not use" bullet like "if you have an ulcer" into "Do not use if you have an ulcer".

    Only the bullet's first sentence decides whether it already says "not". A later sentence such as
    "If you are not sure, ask a doctor" must not stop the "Do not use" from being added, or
    "with any other drug containing acetaminophen" would read as permission."""
    first_sentence = re.split(r"(?<=[.!?])\s+", unit.strip(), maxsplit=1)[0].lower()
    if re.search(r"\b(not|never)\b|n't\b", first_sentence):
        return unit
    if unit[:1].islower() or unit.lower().startswith(CONTINUATIONS):
        return f"Do not use {unit}"
    return unit


def section_units(section, heading):
    """One label section as a list of whole instructions."""
    units = []
    # A line like "Do not use if you have:" introduces the bullets after it, so we keep it as a lead-in.
    title = section.find(f"{HL7}title")
    title_text = clean(element_text(title)) if title is not None else ""
    lead = title_text if heading == "Do not use" and len(title_text.split()) > 3 else ""
    text_element = section.find(f"{HL7}text")
    if text_element is not None:
        for child in text_element:
            if child.tag == f"{HL7}list":
                units += list_units(child, lead)
            elif child.tag == f"{HL7}table":
                units += table_units(child)
            elif child.tag == f"{HL7}paragraph":
                own_text = element_text(child, skip_lists=True)
                inner_lists = child_lists(child)
                if inner_lists:  # "Do not use if you have <bullets>" in one paragraph
                    paragraph_lead = clean(own_text)
                    if paragraph_lead.lower() in ("", "directions", "do not use"):
                        paragraph_lead = lead
                    for xml_list in inner_lists:
                        units += list_units(xml_list, paragraph_lead)
                elif own_text.rstrip().endswith(":"):
                    lead = clean(own_text)
                else:
                    units += [clean(piece) for piece in re.split(BULLETS, own_text)]
                for table in child.iter(f"{HL7}table"):
                    units += table_units(table)
    for sub_section in section.findall(f"{HL7}component/{HL7}section"):
        code = sub_section.find(f"{HL7}code")
        if code is None or code.get("code") in (None, UNTITLED_PART):  # only untitled sub-parts
            units += section_units(sub_section, heading)
    if heading == "Do not use":  # turn bullets like "if you have an ulcer" into full warnings
        units = [full_warning(u) for u in units if u]
    # drop lead-ins that lost their bullets, like "Do not use if you have"
    return [u for u in units if not re.search(r"(if you (have|are)|the following)$", u.lower())]


# ---- Photo mode ---------------------------------------------------------------------------------

def _tidy(line, heading):
    """Small fixes for showing a line on its own: dot leaders ("Acetaminophen 500 mg.....Pain
    reliever") become a colon, and a heading repeated inside the text ("Uses: ...") is dropped."""
    line = clean(re.sub(r"\s*(?:\.{3,}|…+|_{3,})\s*", ": ", line))
    if heading != "Do not use":  # there the heading is part of the warning itself
        line = re.sub(rf"^{re.escape(heading)}\s*:\s*", "", line, flags=re.IGNORECASE)
    return clean(line)


def group_short_items(units, max_words=4):
    """'relieves pain due to: headache', 'relieves pain due to: toothache' -> one line,
    'relieves pain due to: headache, toothache'. Only short items are joined, so the list of
    conditions in "Uses" reads as one sentence instead of a dozen."""
    grouped = []  # [prefix, [items]] or [None, line]
    for unit in units:
        prefix, sep, item = unit.rpartition(": ")
        if sep and prefix and len(item.split()) <= max_words:
            if grouped and grouped[-1][0] == prefix:
                grouped[-1][1].append(item)
            else:
                grouped.append([prefix, [item]])
        else:
            grouped.append([None, unit])
    return [line if prefix is None else f"{prefix}: {', '.join(line)}" for prefix, line in grouped]


def section_code(section):
    code = section.find(f"{HL7}code")
    return code.get("code") if code is not None else None


def label_sections(root):
    """The parts of a label a patient needs explained, as
    [{"name": "Purpose" | "Uses" | "Directions" | "Do not use", "lines": [...]}], in that order.
    Sections the label doesn't have are left out. Lines are the label's own words."""
    found = {heading: [] for heading in PHOTO_SECTIONS.values()}
    for section in root.iter(f"{HL7}section"):
        heading = PHOTO_SECTIONS.get(section_code(section))
        if heading:
            lines = [_tidy(u, heading) for u in section_units(section, heading)]
            if heading == "Uses":
                lines = group_short_items(lines)
            found[heading] += lines
    sections = []
    for heading, lines in found.items():
        seen, kept = set(), []
        for line in lines:
            if re.search(r"[^\W\d_]{2}", line) and line.lower() not in seen and line.lower() != heading.lower():
                seen.add(line.lower())
                kept.append(line)
        if kept:
            sections.append({"name": heading, "lines": kept})
    return sections


def active_ingredients(root):
    """'Acetaminophen 500 mg' and the like, from the Active ingredient section (shown, not translated)."""
    lines = []
    for section in root.iter(f"{HL7}section"):
        if section_code(section) == ACTIVE_INGREDIENT:
            for unit in section_units(section, "Active ingredient"):
                line = _tidy(_tidy(unit, "Active ingredients"), "Active ingredient")
                if line and line.lower() not in (l.lower() for l in lines):
                    lines.append(line)
    return lines
