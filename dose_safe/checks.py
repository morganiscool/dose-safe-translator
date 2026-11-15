"""Safety checks: how we spot a dangerous translation (from dose_safe.ipynb, section 4).

A translation is flagged ("ask a pharmacist to check") if any check fails. The first four look at
the translation itself; the rest look at the back-translation (the translation turned back into
English). These are simple word rules, so they can't understand meaning.
"""
import re
import unicodedata
from collections import Counter

import sacrebleu

from .languages import ENGLISH

BACK_SIMILARITY_MIN = 40  # back-translation similarity (0-100) below this is flagged
DIGITS = re.compile(r"\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?")
# A word is letters plus the combining marks many scripts write vowels with (Hindi नहीं, Thai ไม่).
# Python's \w leaves those marks out, which cut such words into pieces at every vowel sign.
MARKS = "".join(chr(c) for c in range(0x300, 0x10000) if unicodedata.category(chr(c)).startswith("M"))
LETTER = rf"(?:[^\W\d_]|[{MARKS}])"
WORDS = re.compile(rf"{LETTER}+(?:['’-]{LETTER}+)*")
UNITS = {  # ages ("12 years") are already protected by the numbers check
    "hours": ["hour", "hours", "hr", "hrs", "hourly"],
    "days": ["day", "days", "daily"],
    "weeks": ["week", "weeks", "weekly"],
    "months": ["month", "months", "monthly"],
    "minutes": ["minute", "minutes", "min", "mins"],
    "mg": ["mg", "milligram", "milligrams"],
    "mL": ["ml", "milliliter", "milliliters", "millilitre", "millilitres"],
    "teaspoons": ["teaspoon", "teaspoons", "tsp"],
    "tablespoons": ["tablespoon", "tablespoons", "tbsp"],
}
FORWARD_CHECKS = ["Numbers kept", "“Not” kept", "Under / over kept", "Actually translated"]
ROUND_TRIP_CHECKS = ["Numbers survive the round trip", "“Not” survives the round trip",
                     "Units survive the round trip", "Under / over survives the round trip",
                     "Back-translation matches"]
CHECK_NAMES = FORWARD_CHECKS + ROUND_TRIP_CHECKS

def normalize(text):
    # Turkish "İ" lowercases to "i" plus a combining dot; drop the dot so "İlaç" matches "ilaç".
    text = unicodedata.normalize("NFKC", text).replace("⁄", "/").lower().replace("i̇", "i")
    # The model sometimes writes "don 't" with a space; join it so the "not" still counts.
    return re.sub(r"(\w)\s+(['’]t)\b", r"\1\2", text)


def match_phrases(text, phrases, cjk=False):
    """Find phrases in a normalized text, trying the longest phrase first at each position, so each
    word belongs to one phrase only ("ít hơn" = less than is not also read as "hơn" = more).

    `phrases` maps each phrase to a label. Returns (the labels found, in order; what is left of the
    text: a string for Chinese, a list of words otherwise)."""
    found = []
    if cjk:  # no spaces between words (Chinese, Japanese, Thai): match characters
        table = {}
        for phrase, label in phrases.items():  # normalized like the text (Thai ำ changes)
            table.setdefault(normalize(phrase), label)
        keys = sorted((k for k in table if k), key=len, reverse=True)
        rest, i = list(text), 0
        while i < len(text):
            match = next((k for k in keys if text.startswith(k, i)), None)
            if match:
                found.append(table[match])
                rest[i:i + len(match)] = " " * len(match)
                i += len(match)
            else:
                i += 1
        return found, "".join(rest)
    table = {tuple(WORDS.findall(normalize(p))): label for p, label in phrases.items()}
    table.pop((), None)
    tokens, rest, i = WORDS.findall(text), [], 0
    longest = max((len(k) for k in table), default=1)
    while i < len(tokens):
        for size in range(min(longest, len(tokens) - i), 0, -1):
            key = tuple(tokens[i:i + size])
            if key in table:
                found.append(table[key])
                i += size
                break
        else:
            rest.append(tokens[i])
            i += 1
    return found, rest


def digit_numbers(text):
    """Numbers written as digits, e.g. "2", "7.5", "1/2" (= 0.5)."""
    digits = []
    for token in DIGITS.findall(normalize(text)):
        token = token.replace(" ", "")
        try:
            if "/" in token:
                top, bottom = token.split("/")
                digits.append(round(float(top.replace(",", ".")) / float(bottom), 3))
            else:
                digits.append(round(float(token.replace(",", ".")), 3))
        except (ValueError, ZeroDivisionError):
            pass
    return digits


def word_numbers(text, spec):
    """Numbers written as words, as (word, value) pairs, e.g. [("dos", 2)]."""
    words, _ = match_phrases(normalize(text), {w: (w, v) for w, v in spec["numbers"].items()},
                             spec.get("cjk"))
    return words


def number_parts(text, spec):
    """Numbers written as digits, and numbers written as words, in a text."""
    return digit_numbers(text), [float(v) for _, v in word_numbers(text, spec)]


def count_negations(text, spec):
    """How many "not / don't" words a text has. Words that only contain a negation (Chinese 不满 =
    under, 不适 = discomfort; Tagalog "hindi pa" = not yet, as in an age limit) don't count.
    Some languages say "not" inside a longer word: "negation_starts" and "negation_ends" say how
    such words start or end (French n'utilisez, Turkish kullanmayın = don't use)."""
    skip = [p for phrases in spec["limits"].values() for p in phrases] + spec.get("not_negations", [])
    _, rest = match_phrases(normalize(text), dict.fromkeys(skip), spec.get("cjk"))
    if spec.get("cjk"):
        return sum(rest.count(normalize(word)) for word in spec["negations"])
    negations = {normalize(word) for word in spec["negations"]}
    starts = tuple(normalize(word) for word in spec.get("negation_starts", []))
    ends = ("n't", "n’t") + tuple(normalize(word) for word in spec.get("negation_ends", []))
    return sum(1 for t in rest if t in negations or t.endswith(ends) or t.startswith(starts))


def word_groups(text, groups):
    tokens = set(WORDS.findall(normalize(text)))
    return {name for name, words in groups.items() if tokens & set(words)}


def limit_groups(text, spec):
    """Which kinds of limit ("under/less", "over/more") a text mentions, in its own language."""
    phrases = {p: name for name, words in spec["limits"].items() for p in words}
    found, _ = match_phrases(normalize(text), phrases, spec.get("cjk"))
    return set(found)


def _show(values):
    return ", ".join(str(int(v)) if float(v).is_integer() else str(v) for v in sorted(values))


def compare_numbers(source, text, spec):
    src_digits, src_words = number_parts(source, ENGLISH)
    needed = Counter(src_digits + src_words)
    digits, word_hits = digit_numbers(text), word_numbers(text, spec)
    missing = needed - Counter(digits + [float(v) for _, v in word_hits])
    # A number that appears out of nowhere is a problem, written as digits or as a word. Words that
    # are also ordinary words ("una" = a, "năm" = year) can't be trusted as new numbers, and nor can
    # digits in set phrases ("ambiguous_digits": Japanese 1日 = per day, as in 1日3回 = 3 times a day).
    ambiguous = set(spec.get("ambiguous", []))
    firm_words = [float(v) for w, v in word_hits if w not in ambiguous]
    set_phrases = Counter()
    for phrase in spec.get("ambiguous_digits", []):
        set_phrases.update(digit_numbers(phrase) * normalize(text).count(normalize(phrase)))
    firm_digits = list((Counter(digits) - set_phrases).elements())
    new = Counter(firm_digits + firm_words) - needed
    problems = []
    if missing:
        problems.append("missing " + _show(missing.elements()))
    if new:
        problems.append("new " + _show(new.elements()))
    return not problems, "; ".join(problems)


def safety_checks(source, translation, back, spec, back_similarity_min=BACK_SIMILARITY_MIN):
    """Run every check. Returns {check name: {"ok": True/False, "detail": "..."}}."""
    results = {}
    n_not = count_negations(source, ENGLISH)
    source_limits = limit_groups(source, ENGLISH)

    # Checks on the translation itself
    ok, detail = compare_numbers(source, translation, spec)
    results["Numbers kept"] = {"ok": ok, "detail": detail}
    n = count_negations(translation, spec)
    results["“Not” kept"] = {"ok": n >= n_not, "detail": f"English has {n_not}, translation has {n}"}
    lost = source_limits - limit_groups(translation, spec)
    results["Under / over kept"] = {"ok": not lost, "detail": "no word for " + ", ".join(sorted(lost))}
    copied = sacrebleu.sentence_chrf(translation, [source]).score
    results["Actually translated"] = {"ok": copied < 75, "detail": f"{copied:.0f}/100 identical to English"}

    # Checks on the back-translation (the translation turned back into English)
    ok, detail = compare_numbers(source, back, ENGLISH)
    results["Numbers survive the round trip"] = {"ok": ok, "detail": detail}
    n = count_negations(back, ENGLISH) + len(re.findall(r"\bwithout\b", normalize(back)))
    results["“Not” survives the round trip"] = {"ok": n >= n_not,
                                                "detail": f"English has {n_not}, back-translation has {n}"}
    lost = word_groups(source, UNITS) - word_groups(back, UNITS)
    results["Units survive the round trip"] = {"ok": not lost, "detail": "lost " + ", ".join(sorted(lost))}
    lost = source_limits - limit_groups(back, ENGLISH)
    results["Under / over survives the round trip"] = {"ok": not lost,
                                                       "detail": "lost " + ", ".join(sorted(lost))}
    similarity = sacrebleu.sentence_chrf(back, [source]).score
    results["Back-translation matches"] = {"ok": similarity >= back_similarity_min,
                                           "detail": f"similarity {similarity:.0f}/100"}
    return results


def failed_checks(source, translation, back, spec):
    return [name for name, c in safety_checks(source, translation, back, spec).items() if not c["ok"]]
