"""Word lists for each language the translator supports (from dose_safe.ipynb, section 2).

For each language: the model's language code, words that mean "not / don't", number words
(so the checks know "dos" means 2), and words for "under / less" and "over / more" limits.
"ambiguous" lists number words that are also everyday words ("una" = a, "năm" = year), so a
new one is not reported as a new number. "not_negations" (Chinese) lists words that contain a
negation character without meaning "not" (不适 = discomfort).
To add a language, copy an entry and fill it in (ask a fluent speaker to check the words).
"flores" is the code used by the FLORES+ test set in the notebook's section 9 (optional).
"""

LANGUAGES = {
    "Spanish": {
        "code": "spa_Latn", "flores": ["spa_Latn"],
        "negations": ["no", "nunca", "jamás", "ni", "tampoco"],
        "numbers": {"cero": 0, "uno": 1, "una": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4,
                    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
                    "once": 11, "doce": 12, "quince": 15, "veinte": 20, "veinticuatro": 24,
                    "treinta": 30, "media": 0.5, "medio": 0.5},
        "ambiguous": ["uno", "una", "un", "media", "medio"],
        "limits": {"under/less": ["menos", "menor", "menores", "bajo", "inferior", "inferiores"],
                   "over/more": ["más", "mayor", "mayores", "exceder", "exceda", "excede",
                                 "superior", "superiores", "máximo", "máxima"]},
    },
    "Vietnamese": {
        "code": "vie_Latn", "flores": ["vie_Latn"],
        "negations": ["không", "đừng", "chớ", "cấm"],
        "numbers": {"một": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "sáu": 6, "bảy": 7,
                    "tám": 8, "chín": 9, "mười": 10, "mười một": 11, "mười hai": 12,
                    "mười lăm": 15, "hai mươi": 20, "hai mươi bốn": 24, "hai mươi tư": 24,
                    "ba mươi": 30, "nửa": 0.5},
        "ambiguous": ["một", "năm", "tư"],
        "limits": {"under/less": ["dưới", "ít hơn", "nhỏ hơn", "chưa đủ", "chưa tới"],
                   "over/more": ["trên", "quá", "hơn", "tối đa", "vượt", "trở lên"]},
    },
    "Tagalog": {
        "code": "tgl_Latn", "flores": ["fil_Latn", "tgl_Latn"],
        "negations": ["huwag", "hindi", "wag", "di"],
        "numbers": {"isa": 1, "isang": 1, "dalawa": 2, "dalawang": 2, "tatlo": 3, "tatlong": 3,
                    "apat": 4, "lima": 5, "limang": 5, "anim": 6, "pito": 7, "pitong": 7,
                    "walo": 8, "walong": 8, "siyam": 9, "sampu": 10, "sampung": 10,
                    "labing-isa": 11, "labindalawa": 12, "labindalawang": 12, "labinlima": 15,
                    "dalawampu": 20, "dalawampu't apat": 24, "kalahati": 0.5},
        "ambiguous": ["isa", "isang"],
        "limits": {"under/less": ["ilalim", "ibaba", "wala pang", "pababa", "mas bata", "kulang",
                                  "mababa", "hindi pa"],
                   "over/more": ["higit", "mahigit", "pataas", "lampas", "lumampas", "sobra",
                                 "mas matanda", "pinakamarami", "hanggang"]},
    },
    "Haitian Creole": {
        "code": "hat_Latn", "flores": ["hat_Latn"],
        "negations": ["pa", "pinga", "jamè", "okenn"],
        # "yon" (a / one) was missing, so "pran yon grenn" (take one tablet) was flagged.
        # A native speaker should confirm "yon", "en" and "de" here.
        "numbers": {"youn": 1, "yon": 1, "en": 1, "de": 2, "twa": 3, "kat": 4, "senk": 5, "sis": 6,
                    "sèt": 7, "uit": 8, "nèf": 9, "dis": 10, "onz": 11, "douz": 12, "kenz": 15,
                    "ven": 20, "vennkat": 24, "trant": 30, "mwatye": 0.5, "demi": 0.5},
        "ambiguous": ["youn", "yon", "en", "de"],
        "limits": {"under/less": ["anba", "mwens", "pi piti", "pi jèn", "poko"],
                   "over/more": ["plis", "depase", "pi gran", "anwo", "maksimòm", "pase"]},
    },
    "Chinese (Simplified)": {
        "code": "zho_Hans", "flores": ["cmn_Hans", "zho_Hans"], "cjk": True,
        "negations": ["不", "勿", "别", "没", "禁"],
        "not_negations": ["不适", "不良", "不舒服", "不同"],  # discomfort, adverse, unwell, different
        "numbers": {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8,
                    "九": 9, "十": 10, "十一": 11, "十二": 12, "十五": 15, "二十": 20,
                    "二十四": 24, "三十": 30, "半": 0.5},
        "ambiguous": ["一"],  # also in 一些 (some), 一起 (together), 一般 (usually)
        "limits": {"under/less": ["以下", "不满", "未满", "少于", "低于", "小于", "不到"],
                   "over/more": ["以上", "超过", "多于", "高于", "大于", "最多", "超出"]},
    },
}

ENGLISH = {
    "code": "eng_Latn",
    "negations": ["not", "never", "no", "nor", "cannot", "don't", "dont", "doesn't"],
    "numbers": {"zero": 0, "one": 1, "once": 1, "two": 2, "twice": 2, "three": 3, "four": 4,
                "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                "twelve": 12, "fifteen": 15, "twenty": 20, "twenty-four": 24, "twenty four": 24,
                "thirty": 30, "half": 0.5},
    "ambiguous": ["one", "once"],
    "limits": {"under/less": ["under", "below", "younger", "less", "fewer", "lower"],
               "over/more": ["over", "above", "older", "more", "exceed", "exceeds", "exceeding",
                             "maximum", "most", "longer"]},
}

# Languages we have run on real label instructions (notebook sections 6-7). The others work,
# but nobody has looked at their results yet, so the app says so.
TESTED_LANGUAGES = ["Spanish", "Vietnamese"]
