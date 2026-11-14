"""Tests for turning label bullets into whole instructions, and for the saved label data."""
import csv
from pathlib import Path

import pytest

from dose_safe.labels import CONTINUATIONS, full_warning

DATA_FILE = Path(__file__).parent.parent / "data" / "otc_directions.csv"


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
