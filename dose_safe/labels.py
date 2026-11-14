"""Turning drug-label bullets into whole instructions (from dose_safe.ipynb, section 3)."""
import re

CONTINUATIONS = ("if ", "with ", "for ", "in ", "on ", "unless ", "while ", "to ")


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
