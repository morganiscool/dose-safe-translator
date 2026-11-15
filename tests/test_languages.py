"""Tests for every language's word lists, and for the checks on scripts other than Latin."""
import re

import pytest

from dose_safe.checks import WORDS, count_negations, failed_checks, normalize
from dose_safe.languages import ENGLISH, LANGUAGES, TESTED_LANGUAGES

NLLB_CODE = re.compile(r"^[a-z]{3}_[A-Z][a-z]{3}$")
WORD_LIST_CHECKS = {"Numbers kept", "“Not” kept", "Under / over kept"}


@pytest.mark.parametrize("name", list(LANGUAGES))
def test_every_language_has_complete_word_lists(name):
    spec = LANGUAGES[name]
    assert NLLB_CODE.match(spec["code"])
    assert spec["lang"] and spec["negations"]
    assert set(spec["limits"]) == {"under/less", "over/more"} and all(spec["limits"].values())
    assert all(isinstance(value, (int, float)) for value in spec["numbers"].values())
    assert set(spec.get("ambiguous", [])) <= set(spec["numbers"])  # only number words can be ambiguous


def test_tested_languages_exist():
    assert set(TESTED_LANGUAGES) <= set(LANGUAGES)


def test_words_keep_their_vowel_signs():
    # Python's \w leaves out the vowel signs of Hindi, Bengali, Thai...: "नहीं" (not) was cut to "नह".
    assert WORDS.findall(normalize("नहीं लें")) == ["नहीं", "लें"]
    assert WORDS.findall(normalize("সেবন করবেন না")) == ["সেবন", "করবেন", "না"]


def test_a_split_dont_still_counts_as_not():
    assert count_negations("Don 't take more than six capsules", ENGLISH) == 1


def test_japanese_per_day_is_not_a_new_number():
    source = "adults: take 2 tablets 3 times daily"  # 1日3回 = 3 times a day
    assert "Numbers kept" not in failed_checks(source, "成人:1日3回、2錠を服用してください", source,
                                               LANGUAGES["Japanese"])


# Correct translations of the same instruction. The word lists were tuned on the model's own
# translations of 40 label instructions into every language; a native speaker should still check them.
DO_NOT_TAKE = {
    "Hindi": "24 घंटे में 6 से अधिक गोलियां न लें",
    "Bengali": "২৪ ঘণ্টায় ৬টির বেশি ট্যাবলেট সেবন করবেন না",
    "Thai": "ห้ามรับประทานเกิน 6 เม็ดใน 24 ชั่วโมง",
    "French": "n'utilisez pas plus de 6 comprimés en 24 heures",
    "Turkish": "24 saat içinde 6 tabletten fazla kullanmayın",
    "Japanese": "24時間以内に6錠を超えて服用しないでください",
    "Korean": "24시간 동안 6정을 초과하여 복용하지 마십시오",
    "Arabic": "لا تتناول أكثر من 6 أقراص خلال 24 ساعة",
    "Russian": "не принимайте более 6 таблеток в течение 24 часов",
    "Indonesian": "jangan minum lebih dari 6 tablet dalam 24 jam",
    "German": "nehmen Sie nicht mehr als 6 Tabletten in 24 Stunden ein",
    "Hebrew": "אין ליטול יותר מ-6 טבליות ב-24 שעות",
}


@pytest.mark.parametrize("name", list(DO_NOT_TAKE))
def test_a_correct_translation_passes_the_word_list_checks(name):
    source = "do not take more than 6 tablets in 24 hours"
    assert not WORD_LIST_CHECKS & set(failed_checks(source, DO_NOT_TAKE[name], source, LANGUAGES[name]))


@pytest.mark.parametrize("name", ["Hindi", "Thai", "Turkish", "Japanese", "Korean", "Arabic", "Indonesian"])
def test_a_translation_that_lost_the_not_is_flagged(name):
    source = "do not take more than 6 tablets in 24 hours"
    lost = {"Hindi": "24 घंटे में 6 से अधिक गोलियां लें", "Thai": "รับประทานเกิน 6 เม็ดใน 24 ชั่วโมง",
            "Turkish": "24 saat içinde 6 tabletten fazla kullanın", "Japanese": "24時間以内に6錠を超えて服用してください",
            "Korean": "24시간 동안 6정을 초과하여 복용하십시오", "Arabic": "تناول أكثر من 6 أقراص خلال 24 ساعة",
            "Indonesian": "minum lebih dari 6 tablet dalam 24 jam"}[name]
    assert "“Not” kept" in failed_checks(source, lost, source, LANGUAGES[name])
