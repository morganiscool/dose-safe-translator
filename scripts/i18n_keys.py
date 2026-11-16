"""List every phrase of the website that the language menu translates, into web/i18n/source.json.

Run it after changing the website's text:  python scripts/i18n_keys.py
Then add the new phrases to each web/i18n/<lang>.json (tests/test_i18n.py says which are missing).

The English text is the key. It comes from:
- the pages' own text, except inside translate="no" (label lines and other English that stays English);
- elements marked data-i18n-html, whose inner HTML is translated as one sentence;
- the aria-label, alt, title and placeholder attributes;
- t("...") and phrase("...") in the pages' scripts.
"""
import html.parser
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = {"web/translate.html": "translator page", "web/index.html": "landing page"}
SCRIPTS = {"web/js/translate.js": "translator page, shown by its script"}
ATTRIBUTES = ("aria-label", "alt", "title", "placeholder")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def worth_translating(text):
    return bool(re.search(r"[^\W\d_]", text))  # has a letter


class PageText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, skip text inside?)
        self.found = []

    def skipping(self):
        return any(skip for _, skip in self.stack)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        skip = bool(tag in ("script", "style", "svg") or attrs.get("translate") == "no"
                    or "data-i18n-html" in attrs or (self.stack and self.stack[-1][1]))
        if not skip:
            for name in ATTRIBUTES:
                if attrs.get(name) and worth_translating(attrs[name]):
                    self.found.append(normalize(attrs[name]))
        if tag not in VOID:
            self.stack.append((tag, skip))

    def handle_endtag(self, tag):
        while self.stack:
            if self.stack.pop()[0] == tag:
                break

    def handle_data(self, data):
        text = normalize(data)
        if text and worth_translating(text) and not self.skipping():
            self.found.append(text)


def collect(repo=REPO):
    """{English phrase: where it appears}, in the order first found."""
    phrases = {}
    for path, where in PAGES.items():
        source = (repo / path).read_text(encoding="utf-8")
        parser = PageText()
        parser.feed(source)
        title = re.search(r"<title>(.*?)</title>", source, re.S)
        for text in ([normalize(title.group(1))] if title else []) + parser.found:
            phrases.setdefault(text, where)
        # Whole sentences with markup inside: the key is the element's inner HTML.
        for match in re.finditer(r"<(\w+)\b[^>]*\bdata-i18n-html\b[^>]*>(.*?)</\1>", source, re.S):
            phrases.setdefault(normalize(match.group(2)), f"{where}, a sentence with markup (keep the tags)")
    for path, where in SCRIPTS.items():
        source = (repo / path).read_text(encoding="utf-8")
        for match in re.finditer(r'\b(?:t|phrase)\(\s*"((?:[^"\\]|\\.)*)"', source):
            text = match.group(1).encode().decode("unicode_escape").encode("latin-1").decode("utf-8")
            phrases.setdefault(text, where)
    return phrases


if __name__ == "__main__":
    phrases = collect()
    out = REPO / "web" / "i18n" / "source.json"
    out.write_text(json.dumps(phrases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(phrases)} phrases written to {out.relative_to(REPO)}")
