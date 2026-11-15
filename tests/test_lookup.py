"""Tests for finding a label from a barcode, with a stand-in for the internet (no real requests)."""
from pathlib import Path

import pytest

from dose_safe.lookup import (LabelNotFound, LabelSourceDown, fetch_label_xml, find_label, search_terms,
                              upce_to_upca)

FIXTURES = Path(__file__).parent / "fixtures"
SET_ID = "0005aafa-08f8-4990-a54d-cc097195708f"


class Response:
    def __init__(self, status_code, body=None, content=b""):
        self.status_code, self._body, self.content = status_code, body, content

    def json(self):
        return self._body


class FakeHttp:
    """Answers each .get() with the next response (or raises it, if it's an exception)."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        answer = self.responses.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def label(set_id, effective_time, brand, upc="0070038610953"):
    return {"set_id": set_id, "effective_time": effective_time,
            "openfda": {"brand_name": [brand], "generic_name": ["ACETAMINOPHEN"], "upc": [upc],
                        "manufacturer_name": ["Valu Merchandisers Company"], "product_ndc": ["63941-519"]}}


@pytest.mark.parametrize("typed, field, forms", [
    ("070038610953", "openfda.upc", ["0070038610953", "070038610953"]),        # UPC-A, as printed
    ("0070038610953", "openfda.upc", ["0070038610953", "070038610953"]),       # read as EAN-13
    ("0 70038 61095 3", "openfda.upc", ["0070038610953", "070038610953"]),     # typed with spaces
    ("00070038610953", "openfda.upc", ["0070038610953", "070038610953"]),      # GTIN-14 (DataMatrix)
    ("8907460005526", "openfda.upc", ["8907460005526"]),                       # a foreign EAN-13
    ("NDC 63941-519-62", "openfda.product_ndc", ["63941-519"]),                # NDC from the box
    ("50580-0472-01", "openfda.product_ndc", ["50580-0472", "50580-472"]),     # 11-digit NDC
])
def test_search_terms(typed, field, forms):
    assert search_terms(typed) == (field, forms)


def test_short_upc_e_barcodes_are_written_out_in_full():
    assert upce_to_upca("01234565") == "012345000065"
    assert search_terms("01234565") == ("openfda.upc", ["0012345000065", "012345000065"])


@pytest.mark.parametrize("typed", ["", "aspirin", "12345", "0000000000000"])
def test_things_that_are_not_barcodes_are_refused_with_a_message(typed):
    with pytest.raises(ValueError, match="."):
        search_terms(typed)


def test_find_label_searches_both_spellings_and_keeps_the_newest_label():
    http = FakeHttp(Response(200, {"meta": {"results": {"total": 2}},
                                   "results": [label("old-id", "20200101", "Pain Reliever Extra Strength"),
                                               label(SET_ID, "20260102", "Pain Reliever Extra Strength")]}))
    product = find_label("070038610953", http)
    assert product["set_id"] == SET_ID
    assert product["brand"] == "Pain Reliever Extra Strength"
    assert product["matches"] == 2
    assert product["dailymed_url"].endswith(SET_ID)
    assert http.calls[0][1]["params"]["search"] == 'openfda.upc:("0070038610953" "070038610953")'


def test_a_barcode_shared_by_different_products_is_refused_not_guessed():
    # Real case: the placeholder UPC 012345678905 is on 134 labels (nicotine gum, a deodorant, ...).
    http = FakeHttp(Response(200, {"meta": {"results": {"total": 134}},
                                   "results": [label("a", "20261101", "Equate Nicotine", "0012345678905"),
                                               label("b", "20250218", "Sure Antiperspirant", "0012345678905")]}))
    with pytest.raises(LabelNotFound, match="134 different medicine labels.*NDC"):
        find_label("012345678905", http)


def test_a_barcode_openfda_doesnt_know_suggests_the_ndc_number():
    with pytest.raises(LabelNotFound, match="NDC"):
        find_label("070038610953", FakeHttp(Response(404, {"error": {"code": "NOT_FOUND"}})))


def test_openfda_being_down_is_its_own_error():
    with pytest.raises(LabelSourceDown):
        find_label("070038610953", FakeHttp(ConnectionError("no network")))
    with pytest.raises(LabelSourceDown):
        find_label("070038610953", FakeHttp(Response(500, {})))


def test_fetch_label_xml_retries_then_reads_the_label(monkeypatch):
    monkeypatch.setattr("dose_safe.lookup.time.sleep", lambda _: None)
    xml = (FIXTURES / "acetaminophen_label.xml").read_bytes()
    http = FakeHttp(TimeoutError("slow"), Response(200, content=b"<broken"), Response(200, content=xml))
    root = fetch_label_xml(SET_ID, http)
    assert root.tag == "{urn:hl7-org:v3}document"
    assert len(http.calls) == 3


def test_fetch_label_xml_gives_up_after_three_tries(monkeypatch):
    monkeypatch.setattr("dose_safe.lookup.time.sleep", lambda _: None)
    with pytest.raises(LabelSourceDown):
        fetch_label_xml(SET_ID, FakeHttp(*[Response(503)] * 3))
    with pytest.raises(LabelNotFound):
        fetch_label_xml("../../etc/passwd", FakeHttp())

