"""Tests for the safety checks. Run with:  python -m pytest"""
import pytest

from dose_safe.checks import FORWARD_CHECKS, failed_checks
from dose_safe.languages import LANGUAGES

ES = LANGUAGES["Spanish"]
VI = LANGUAGES["Vietnamese"]
TL = LANGUAGES["Tagalog"]
HT = LANGUAGES["Haitian Creole"]
ZH = LANGUAGES["Chinese (Simplified)"]
CAPLETS = "do not take more than 6 caplets in 24 hours"


# The notebook's own self-tests (section 4). These must keep passing.

@pytest.mark.parametrize("translation, back", [
    ("no tome más de 6 cápsulas en 24 horas", "do not take more than 6 capsules in 24 hours"),
    ("no tome más de seis cápsulas en veinticuatro horas",
     "do not take more than six capsules in twenty-four hours"),
])
def test_correct_spanish_passes(translation, back):
    assert failed_checks(CAPLETS, translation, back, ES) == []


@pytest.mark.parametrize("translation, back", [
    ("tome más de 6 cápsulas en 24 horas", "take more than 6 capsules in 24 hours"),          # lost the "not"
    ("no tome más de 8 cápsulas en 24 horas", "do not take more than 8 capsules in 24 hours"),  # wrong number
    ("no tome más de 6 cápsulas en 24 días", "do not take more than 6 capsules in 24 days"),    # hours -> days
])
def test_broken_spanish_is_flagged(translation, back):
    assert failed_checks(CAPLETS, translation, back, ES)


def test_under_kept_and_dropped():
    src = "children under 12 years: ask a doctor"
    assert failed_checks(src, "niños menores de 12 años: consulte a un médico",
                         "children under 12 years: see a doctor", ES) == []
    assert "Under / over kept" in failed_checks(src, "niños de 12 años: consulte a un médico",
                                                "children 12 years old: see a doctor", ES)


def test_readme_menos_de_example_passes_the_translation_checks():
    # From the README: the Spanish was right, only its back-translation dropped "under".
    failed = failed_checks("children 4 to under 12 yrs: ask a doctor",
                           "niños de 4 a menos de 12 años: pregunte a un médico",
                           "children 4 to 12 years: ask a doctor", ES)
    assert not set(failed) & set(FORWARD_CHECKS)


# Bugs found in the code review. Each one let a dangerous translation through.

def test_vietnamese_less_than_does_not_count_as_more_than():
    # "do not take LESS than 6 caplets": the limit flipped. ít hơn (less than) contains hơn (more).
    assert "Under / over kept" in failed_checks(CAPLETS, "không uống ít hơn 6 viên trong 24 giờ", CAPLETS, VI)


def test_vietnamese_more_than_still_passes():
    for translation in ["không uống quá 6 viên trong 24 giờ", "không uống nhiều hơn 6 viên trong 24 giờ"]:
        assert "Under / over kept" not in failed_checks(CAPLETS, translation, CAPLETS, VI)


def test_chinese_not_inside_under_word_is_not_a_negation():
    # "可给不满12岁的儿童" = "MAY give to children under 12". Its only 不 belongs to 不满 (under).
    src = "do not give to children under 12 years"
    assert "“Not” kept" in failed_checks(src, "可给不满12岁的儿童", src, ZH)


def test_chinese_not_inside_discomfort_is_not_a_negation():
    # "如果您有胃部不适，请使用" = "if you have stomach discomfort, please use". 不适 = discomfort.
    src = "do not use if you have stomach pain"
    assert "“Not” kept" in failed_checks(src, "如果您有胃部不适，请使用", src, ZH)


def test_chinese_real_negations_still_count():
    src = "do not give to children under 12 years"
    assert "“Not” kept" not in failed_checks(src, "不要给不满12岁的儿童服用", src, ZH)
    assert "“Not” kept" not in failed_checks(CAPLETS, "24小时内不超过6粒", CAPLETS, ZH)


def test_tagalog_hindi_pa_age_limit_is_not_a_negation():
    # "ibigay sa mga batang hindi pa 12 taong gulang" = "GIVE to children not yet 12 years old".
    src = "do not give to children under 12 years"
    assert "“Not” kept" in failed_checks(src, "ibigay sa mga batang hindi pa 12 taong gulang", src, TL)


def test_new_number_written_as_a_word_is_flagged():
    # "take 2 tablets" became "take two tablets SIX times a day".
    failed = failed_checks("take 2 tablets", "tome dos tabletas seis veces al día",
                           "take two tablets six times a day", ES)
    assert "Numbers kept" in failed
    assert "Numbers survive the round trip" in failed


def test_articles_that_look_like_numbers_are_not_new_numbers():
    # "un vaso" = "a glass", and "a" is not a new 1.
    failed = failed_checks("take 2 tablets with water", "tome 2 tabletas con un vaso de agua",
                           "take 2 tablets with a glass of water", ES)
    assert "Numbers kept" not in failed


def test_haitian_yon_counts_as_one():
    failed = failed_checks("take 1 tablet every 4 hours", "pran yon grenn chak 4 èdtan",
                           "take one tablet every 4 hours", HT)
    assert "Numbers kept" not in failed
