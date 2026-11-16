"""Tests for the website's own languages: web/i18n/<lang>.json against the site's English text."""
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
I18N = REPO / "web" / "i18n"
spec = importlib.util.spec_from_file_location("i18n_keys", REPO / "scripts" / "i18n_keys.py")
i18n_keys = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n_keys)

SOURCE = json.loads((I18N / "source.json").read_text(encoding="utf-8"))
# The menu's languages, as listed in web/js/i18n.js
SITE_LANGUAGES = re.findall(r'\["([\w-]+)", "[^"]+"\]', (REPO / "web" / "js" / "i18n.js").read_text(encoding="utf-8"))
TRANSLATED = [code for code in SITE_LANGUAGES if code != "en"]


def test_the_phrase_list_matches_the_site():
    # If this fails, run: python scripts/i18n_keys.py, then translate the new phrases.
    assert set(i18n_keys.collect()) == set(SOURCE)


def test_the_menu_lists_english_and_twelve_languages():
    assert SITE_LANGUAGES[0] == "en" and len(TRANSLATED) == 12


@pytest.mark.parametrize("code", TRANSLATED)
def test_every_phrase_is_translated_with_its_placeholders_and_tags(code):
    table = json.loads((I18N / f"{code}.json").read_text(encoding="utf-8"))
    assert set(table) == set(SOURCE), "missing or extra phrases"
    for key, text in table.items():
        assert isinstance(text, str) and text.strip(), key
        assert set(re.findall(r"\{(\w+)\}", text)) == set(re.findall(r"\{(\w+)\}", key)), (key, text)
        assert Counter(re.findall(r"<[^>]+>", text)) == Counter(re.findall(r"<[^>]+>", key)), (key, text)


@pytest.mark.parametrize("code", TRANSLATED)
def test_names_and_codes_stay_as_they_are(code):
    table = json.loads((I18N / f"{code}.json").read_text(encoding="utf-8"))
    for key, text in table.items():
        for kept in ("NLLB-200", "openFDA", "DailyMed", "12345-678-90", "0 70038 61095 3"):
            if kept in key:
                assert kept in text, (kept, key, text)
