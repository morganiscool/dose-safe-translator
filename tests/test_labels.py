"""Tests for turning label bullets into whole instructions, and for the saved label data."""
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from dose_safe.labels import (CONTINUATIONS, active_ingredients, full_warning, group_short_items,
                              label_sections)

DATA_FILE = Path(__file__).parent.parent / "data" / "otc_directions.csv"
FIXTURES = Path(__file__).parent / "fixtures"
HL7_DOC = '<document xmlns="urn:hl7-org:v3"><component><structuredBody>{}</structuredBody></component></document>'


def section_xml(code, title, body):
    return (f'<component><section><code code="{code}"/><title>{title}</title>'
            f'<text>{body}</text></section></component>')


@pytest.mark.parametrize("bullet", [
    "if you have an ulcer",
    # Real bullets from the saved data. Each has a "not" in its SECOND sentence, which used to stop
    # the "Do not use" from being added, so the instruction read as permission.
    "with any other drug containing acetaminophen (prescription or nonprescription). If you are not "
    "sure whether a drug contains acetaminophen, ask a doctor or pharmacist.",
    "if you are now taking a prescription monoamine oxidase inhibitor (MAOI) (certain drugs for "
    "depression, psychiatric, or emotional conditions, or Parkinson's disease), or for 2 weeks after "
    "stopping the MAOI drug. If you do not know if your prescription drug contains an MAOI, ask a "
    "doctor or pharmacist before taking this product.",
    "in a child who is taking a prescription monoamine oxidase inhibitor (MAOI). If you do not know "
    "if your child's prescription drug contains an MAOI, ask a doctor or pharmacist.",
])
def test_do_not_use_bullets_get_their_do_not_use(bullet):
    assert full_warning(bullet).startswith("Do not use ")


@pytest.mark.parametrize("bullet", [
    "Do not use if you have ever had an allergic reaction to this product or any of its ingredients",
    "laxative products should not be used for a period longer than 1 week unless directed by a doctor.",
    "if you are not sure whether a drug contains acetaminophen, ask a doctor or pharmacist",
])
def test_bullets_that_already_say_not_are_left_alone(bullet):
    assert full_warning(bullet) == bullet


def test_saved_do_not_use_rows_are_whole_warnings():
    with DATA_FILE.open(encoding="utf-8") as f:
        fragments = [row["instruction_id"] for row in csv.DictReader(f)
                     if row["section"] == "Do not use" and row["instruction"].lower().startswith(CONTINUATIONS)]
    assert fragments == []


# ---- Photo mode: reading a whole label ------------------------------------------------------------

def test_a_real_label_comes_out_in_the_photo_mode_sections():
    root = ET.parse(FIXTURES / "acetaminophen_label.xml").getroot()
    assert label_sections(root) == [
        {"name": "Purpose", "lines": ["Pain reliever/fever reducer"]},
        {"name": "Uses", "lines": [
            "temporarily relieves minor aches and pains due to: headache, the common cold, backache, "
            "minor pain of arthritis, toothache, muscular aches, premenstrual and menstrual cramps",
            "temporarily reduces fever"]},
        {"name": "Directions", "lines": [
            "do not take more than directed",
            "adults and children 12 years and over: take 2 gelcaps every 6 hours while symptoms last",
            "adults and children 12 years and over: do not take more than 6 gelcaps in 24 hours, unless "
            "directed by a doctor",
            "adults and children 12 years and over: do not take for more than 10 days unless directed by a doctor",
            "children under 12 years: ask a doctor"]},
        {"name": "Do not use", "lines": [
            "Do not use if you are allergic to acetaminophen or any of the inactive ingredients in this product",
            "Do not use with any other drug containing acetaminophen (prescription or nonprescription). "
            "If you are not sure whether a drug contains acetaminophen, ask a doctor or pharmacist."]},
    ]
    assert active_ingredients(root) == ["Acetaminophen 500 mg"]


def test_dosing_lines_are_never_joined_only_short_lists_of_uses():
    # Directions keep one line per bullet even when the bullets are short: each is checked on its own.
    root = ET.fromstring(HL7_DOC.format(section_xml(
        "34068-7", "Directions",
        "<list><item>adults<list><item>take 2 tablets</item><item>do not exceed 8</item></list></item></list>")))
    assert label_sections(root) == [
        {"name": "Directions", "lines": ["adults: take 2 tablets", "adults: do not exceed 8"]}]
    # A long item stays on its own line, and the short ones after it start a new group.
    assert group_short_items(["helps: a cough", "helps: a cough due to minor throat irritation",
                              "helps: sneezing", "helps: runny nose"]) == \
        ["helps: a cough", "helps: a cough due to minor throat irritation", "helps: sneezing, runny nose"]


def test_symbol_font_bullets_split_a_paragraph():
    # From the Rompe Pechito DM label: its bullets are U+F06E (a symbol-font square), so the whole
    # paragraph used to come out as one instruction with the dose limit buried in it.
    root = ET.fromstring(HL7_DOC.format(section_xml(
        "34068-7", "Directions",
        "<paragraph> Do not give more than 6 doses in any 24 hours period  shake well before use"
        "</paragraph>")))
    assert label_sections(root) == [
        {"name": "Directions", "lines": ["Do not give more than 6 doses in any 24 hours period",
                                         "shake well before use"]}]


def test_dot_leaders_repeated_headings_and_missing_sections():
    root = ET.fromstring(HL7_DOC.format(
        section_xml("55106-9", "Active ingredients (in each tablet)",
                    "<paragraph>Chlorpheniramine maleate 4 mg..........Antihistamine</paragraph>")
        + section_xml("55105-1", "", "<paragraph>Purpose</paragraph><paragraph>Antihistamine</paragraph>")
        + section_xml("34067-9", "", "<paragraph>Uses: temporarily relieves sneezing and runny nose</paragraph>")))
    assert active_ingredients(root) == ["Chlorpheniramine maleate 4 mg: Antihistamine"]
    assert label_sections(root) == [
        {"name": "Purpose", "lines": ["Antihistamine"]},
        {"name": "Uses", "lines": ["temporarily relieves sneezing and runny nose"]},
    ]
