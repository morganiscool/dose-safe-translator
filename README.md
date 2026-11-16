---
title: Dose-Safe Translator
emoji: 💊
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
license: cc-by-nc-4.0
short_description: Translate OTC directions and flag risky translations
pinned: false
---

# 💊 Dose-Safe Translator

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/morganiscool/dose-safe-translator/blob/main/dose_safe.ipynb)

**Website:** [dose-safe.netlify.app](https://dose-safe.netlify.app) shows both pages in 13 languages. Checking a
translation needs the model, so to try that, use Google Colab (steps below).

**Track:** Languages
**Team:** _names_

> This project is a prototype and is not medical advice.

## Try it in Google Colab (judges, start here)

It runs on Google's free computers, so it doesn't depend on our team's computer being on. You only
need a Google account; there's nothing to install.

1. Click **Open in Colab** above.
2. Choose **Runtime → Change runtime type → T4 GPU → Save**.
3. Choose **Runtime → Run all**. If Colab warns that the notebook wasn't written by Google, click
   **Run anyway**.
4. Wait about 10–15 minutes. The notebook downloads the translation model (about 2.5 GB), then
   translates and checks 150 real label instructions in Spanish and Vietnamese; the results appear
   in sections 6–7 as it goes.
5. At the bottom, section 11 prints a public link ending in `.gradio.live`. Open it in a new tab or on
   a phone (the app also appears right under that cell).
6. In the app, type or pick an English instruction from a medicine label, choose the patient's
   language and click **Translate and check**. You get the translation, the translation back into
   English, and the safety checks. The **📷 Photo of the label** tab reads a label's Directions from
   a photo: pick an example photo or upload one, click **1 · Read the label**, check the text, then
   click **2 · Translate and check every line**.

If the link stops working, Colab has ended the session: run the last cell again for a new link. The
`localhost` link Colab also shows only works inside Colab. Without a free GPU it still runs, only
much slower. If Colab says you have too many active sessions, end the old ones under
**Runtime → Manage sessions**.

## The problem

Pharmacists in the US regularly hand over-the-counter medicine directions to patients who don't read
English well. Free machine translation is instant, but it makes mistakes on medical instructions. In a
UCSF study of emergency-room discharge instructions, Google Translate was 92% accurate for Spanish and
81% for Chinese, and one mistranslation ("hold the kidney medicine" became "keep taking the medication")
could have been life-threatening ([UCSF](https://universityofcalifornia.edu/news/google-translates-doctors-orders-spanish-and-chinese-few-important-caveats)).
A study in *Pediatrics* found errors in about half of Spanish prescription labels made by pharmacy
translation software ([Fierce Healthcare](https://www.fiercehealthcare.com/healthcare/up-to-half-spanish-translated-prescriptions-include-dangerous-mistakes)).

A common shortcut is to translate the result back into English and see if it still makes sense. **We
wanted to know whether that back-translation check actually catches the dangerous mistakes, and whether
targeted safety checks catch more.**

## What we built

A tool that **double-checks a translated medicine label the way a careful pharmacist would**, for a
patient who doesn't read English. It translates each instruction on the label, translates it back, and
checks that every number, "not" and age or dose limit made it through, then tells the pharmacist which
translations still need a person to check them. It covers 28 languages: Spanish, Vietnamese and
Chinese (Simplified) are tested on 150 real label instructions each; the other 25, from Arabic and Hindi
to Korean and Indonesian, work the same way, with word lists tuned on 40 label instructions each.

- **In:** an English instruction from a medicine label, e.g. *"do not take more than 6 caplets in 24 hours"*.
- **Out:** the translation, the translation turned back into English, nine safety checks, and a verdict:
  ✅ *no problems found by the automatic checks* or ⚠️ *ask a pharmacist or interpreter to check this
  translation*. The tool never says a translation is "safe".
- **Safer mode:** instead of taking the model's first answer, it looks at its top 5 translations and keeps
  the one with the fewest problems in the translation itself (then the fewest problems overall).
- **Photo input** (notebook demo, and the web app's *One label line* tab): the pharmacist can photograph
  the label's Directions section instead of typing. EasyOCR reads it and **highlights the words it wasn't sure about** (with a stricter bar for
  numbers). The pharmacist checks the text against the label before anything is translated.
- **Photo mode** (web app): photograph the barcode on a medicine box, or type its barcode or NDC number.
  The app finds the box's official label (openFDA → DailyMed), shows the product so the pharmacist can
  confirm it's the right box, then translates and checks every line of its **Purpose** (what it does),
  **Uses** (what the label says it treats), **Directions** (how much, how often, who may take it) and
  **Do not use** sections, and prints the whole label as one slip. It shows only the label's own words.
  Because the words come from the official label, not from reading the photo, there are no misread words
  to check; the pharmacist checks the product instead.
- **Boxes from other countries** (web app): the FDA's database only has medicines sold in the US. When a
  photo has no barcode, or one the database doesn't know, the app reads the box's printed directions with
  the notebook's photo reader (EasyOCR, the same rules), marks the words it wasn't sure about, and has
  the pharmacist correct every line and tick that they compared it with the box before it's translated.
- **The website in 13 languages** (web app): a language menu in the header shows the site itself in
  English, Español, Français, Português, Bahasa Indonesia, Tagalog, Tiếng Việt, 中文, 한국어, 日本語,
  Русский, العربية (right to left) or हिन्दी, so people who don't read English can use it too. The label
  lines and the round trip's English stay in English, because that is what the checks compare.

There are two ways to try it: a Gradio app at the end of the notebook, which prints a public
`….gradio.live` link that also works on a phone, and a web app built for the pharmacy counter (see
**Run the web app**). Both offer every language and read a label's printed text from a photo. The web
app's *Photo of the box* reads the barcode first and finds the whole official label, and reads the
printed text instead when the barcode has no US label.

## What we added

We started from suggested project **4.4.2 (Translation quality test)**, which lists "translate text from
a real setting, such as … medicine instructions" as one way to make it your own. Beyond the brief's steps:

- **Our own data:** about 380 real instructions taken bullet by bullet from 66 US over-the-counter drug
  labels (openFDA + DailyMed), instead of general news sentences.
- **Our own user:** a pharmacist handing directions to a patient who doesn't read English.
- **Our own question:** does back-translation catch dangerous errors? We compare a back-translation-only
  check with our targeted checks, against blind ratings from a fluent speaker on our team.
- **An improvement we measured:** safer mode (best of 5 translations, chosen by the checks).
- **A second risk we measured:** reading a photo can change a number before translation even starts,
  and then every translation check passes. We test the photo reader on made-up label photos whose true
  text we know, and count how many dangerous misreads the highlighting catches.

## How it works

**Data.** We search openFDA for over-the-counter labels of 24 common medicines (acetaminophen,
ibuprofen, loratadine, nicotine gum, …), download each label's original XML file from DailyMed, and split
its **Directions** and **Do not use** sections into single instructions. Nested bullets keep their
heading, e.g. *"adults and children 12 years and over: take 2 caplets every 6 hours"*. We tested the
instructions that contain a number, a "not", or an age or amount limit, because those are where a
mistake can hurt someone.

**Model.** [NLLB-200](https://huggingface.co/facebook/nllb-200-distilled-600M) (distilled, 600M
parameters) is a free model from Meta that translates between 200 languages, including many that
commercial apps serve poorly. We use beam search to get its top translations, and use the same model to
translate each one back into English.

**Safety checks.** A translation is flagged if any of these fail. The first four look at the translation
itself; the rest look at the back-translation.

| Check | What it looks for |
|---|---|
| Numbers kept | Every number in the English appears in the translation (as digits or words), and no new number appears |
| "Not" kept | The translation has at least as many "not / don't" words as the English |
| Under / over kept | "children *under* 12" or "no *more* than 6" keeps a word for the limit (Spanish *menores de*, Vietnamese *dưới*, Chinese *以下*, …) |
| Actually translated | The model didn't just copy the English |
| Numbers survive the round trip | Every number is still there in the back-translation |
| "Not" survives the round trip | The back-translation still says "not" (or "without") |
| Units survive the round trip | Hours stay hours, days stay days, mg stays mg |
| Under / over survives the round trip | The back-translation still says *under*, *over*, *more*, *less*… |
| Back-translation matches | The back-translation is similar to the original (chrF ≥ 40) |

These are simple word rules, so they can't understand meaning. That's why the real test is a fluent
speaker's ratings.

**Why safer mode ranks the translation-side checks first.** In our first test run, the English said
*"children 4 to **under** 12 yrs: ask a doctor"*. NLLB's Spanish was correct (*"niños de 4 a **menos de** 12
años"*), but its back-translation dropped "under", so the checks flagged it. An early version of safer
mode then picked another candidate, *"niños de 4 a 12 años"*, which really does lose "under", just because
its back-translation looked more similar. Checking the translation itself for words like *menos / menores*
and ranking those checks first fixed it.

**Photo input.** [EasyOCR](https://github.com/JaidedAI/EasyOCR) finds each word in the photo, reads it,
and gives a confidence from 0 to 1. The app joins the words into lines and the lines into instructions
(a new one starts at each ■ bullet or table row). Then it highlights words to check: numbers read with
less than 70% confidence, other words below 30%, and letters mixed into a number, like *"l2"*. We chose
those two cut-offs on photos of 60 label instructions that are not in the test set. While building it we
found two dangerous problems and fixed them:
- With EasyOCR's default settings, one-character words were silently dropped, so *"3 to 4 times daily"*
  came out as *"3 to times daily"*. We now keep small text boxes and read word by word.
- The ■ bullet was often read as a number, so *"■ do not take more than directed"* became *"2 do not take
  more than directed"*. A text box that is square and mostly ink is now treated as a bullet.

To test it, we print each test instruction like a label and make it look like a phone photo (tilted,
blurred, unevenly lit, noisy and JPEG-compressed) at four levels of blur. A **dangerous misread** changes
a number, a "not" or an under/over limit.

**More languages.** NLLB-200 translates every language here; the checks also need each language's
words for "not", for numbers and for limits. Besides the five we started with, we wrote word lists for
23 more, picked from the languages US pharmacies most often need, plus Indonesian and Malay: Arabic,
Bengali, Chinese (Traditional), French, German, Greek, Gujarati, Hebrew, Hindi, Indonesian, Italian,
Japanese, Korean, Malay, Persian, Polish, Portuguese, Punjabi, Russian, Thai, Turkish, Ukrainian and
Urdu. Then we translated 40 label instructions into every language and back, and added the words the
checks missed in correct translations (German *ab 12 Jahren* = 12 and over, Russian *до 12 лет* = under
12, Japanese *1日* = per day). Three changes made the checks work in other scripts:
- Words keep their vowel signs. Python's word pattern cut Hindi *नहीं* ("not") into pieces at each sign.
- A word can carry "not" inside it, like French *n'utilisez* or Turkish *kullanmayın* (don't use).
- Thai, Japanese and Korean are matched by their characters, because "not" is part of a longer word.

In that quick test, the checks flagged 5–20% of the translations in most languages and 28–35% in Arabic,
Persian, German, Thai, Korean, Japanese and Chinese (Traditional). The failures we read were mostly real
problems: a dropped "Do not use", Korean and Persian turning "not more than 3 to 4 times daily" into
"more than", a Japanese "every 1/2 hour" that became "every minute". Nobody who speaks these languages
has checked the lists yet. When unsure, a list leaves a word out: a missing word causes a false
alarm, a wrong word could let a dangerous translation through.

**Evaluation.** A fluent speaker of a tested language rates each translation blind (they don't know
which version made it or whether it was flagged): 2 = correct, 1 = small mistake but same meaning,
0 = dangerous. The notebook makes the rating sheet in section 8 for the language set as `TEAM_LANGUAGE`
in section 2 (Vietnamese now). From those ratings we measure how often each version is dangerous, and how many dangerous
translations each checker **misses** (false negatives) and how many **false alarms** it raises (false
positives).

## Results

**Automatic checks** (share of translations flagged, section 7). Re-run on Nov 15, 2026 with the fixed
checks (the bugs and their tests are in `tests/test_checks.py` and `tests/test_labels.py`) on the
current data snapshot: 150 label instructions per language, run on a laptop processor. The check fixes
left the totals where they were (the first run on Nov 14 also gave 11 % → 10 % and 17 % → 10 %); they
change which single translations get flagged in the edge cases the bugs were about. Splitting
symbol-font bullets (section 3) then changed one test instruction: five directions that had been read
as one became *"Do not give more than 6 doses in any 24 hours period"* alone. Its Vietnamese
translation is no longer flagged, so Vietnamese as-is went from 17 % to 16 %. Every other verdict
stayed the same.

| Language | NLLB as-is | Safer mode | Safer mode changed |
|---|---|---|---|
| Spanish | 11 % | 10 % | 3 % of translations |
| Vietnamese | 16 % | 10 % | 7 % of translations |
| Chinese (Simplified) | 31 % | 21 % | 13 % of translations |

Safer mode is chosen *by* these checks, so it will always look better here. The ratings below are the
fair test.

**Chinese (Simplified)** was run the same way on Nov 15, 2026 (the same 150 instructions, the current
checks): 46 translations flagged as NLLB wrote them, 31 in safer mode, which picked a different
translation for 20. Of the first 14 lines safer mode still flagged, we read 8 as real problems the
checks caught: the model left out a whole "Do not use…" sentence three times (chest pain, MAOI, "any
other drug containing acetaminophen"), turned *diphenhydramine* into "amines", dropped "ulcer" from "if
you have an ulcer", dropped "1 lozenge" from a dosing line, and garbled a tablet line. The other 6 were
false alarms: a correct 以下 ("under") whose back-translation lost "under" (the same false alarm as
Spanish *menos de*), "once daily" coming back as "daily", a correct line reworded on the way back, and a
label's own double negative (*"do not use no more than 7 days"*). So the checks behave sensibly in
Chinese; NLLB simply makes more real mistakes there. Nobody who reads Chinese has checked these yet.

**Reading label photos** (section 10). From our test run on Nov 15, 2026: 100 label instructions, each
printed as a made-up label photo at four levels of blur (run on a laptop CPU; Colab's numbers may differ
slightly):

| Photo | Read exactly right | Dangerous misreads | Caught by the highlight | **Missed** (false negatives) | False alarms (false positives) |
|---|---|---|---|---|---|
| Sharp | 92 % | 0 | 0 | 0 | 7 |
| Slightly blurry | 91 % | 2 | 1 | 1 | 9 |
| Blurry | 54 % | 30 | 24 | 6 | 16 |
| Very blurry | 3 % | 70 | 69 | 1 | 23 |

These numbers are rough. When we re-made the photos three times with different random tilt and noise,
blurry photos were read exactly right 54–67% of the time, and the highlight caught 80–95% of their
dangerous misreads. The notebook now gives each instruction the same made-up photo on every run, so the
table only changes when the data or the code does.

Being strict with numbers is a trade-off. Highlighting numbers read with less than 70% confidence caught
92.2% of the dangerous misreads, but also highlighted 18.5% of the photos that were read safely. A 30%
cut-off caught 89.2%, with 12.8% false alarms.

**Fluent-speaker ratings** (section 8): **not collected yet.** We don't have a fluent rater for a tested
language yet, so these numbers don't exist, and we don't estimate them. When a fluent speaker fills in
the blind rating sheet, section 8 reports how often each version (NLLB as-is, safer mode) is dangerous,
and how many dangerous translations the back-translation check alone catches and misses compared with
our full checks, with the false alarms each raises.

Until then, the automatic results above count flags, not confirmed errors. One comparison doesn't need
ratings: back-translation similarity alone (chrF below 40) would have flagged 4 of the 150 Spanish
translations, 7 of the Vietnamese and 19 of the Chinese; the full checks flagged 17, 24 and 46 (NLLB
as-is). Which of the extra flags are real errors is what the ratings will show; the Chinese lines we
read are a first look (above).

**General translation quality** (FLORES+ chrF, section 9): not run. It's optional, and it scores
general sentences, not medicine directions.

**Where it fails.** Real examples from our test runs. A fluent speaker still has to confirm them and give
the correct translations:
- **Missed by the checks:** *"laxative products should not be used for a period longer than 1 week
  unless directed by a doctor"*. The Vietnamese translation back-translates as *"**slimming** products
  should not be used…"*. Every number, "not" and limit survived, so no check fired, yet the medicine type
  may be wrong. In Chinese the same line came back as *"The use of **emulsifiers** should not exceed one
  week…"* (乳化剂), and passed every check too.
- **False alarm:** *"children 4 to under 12 yrs: ask a doctor"*. The Spanish (*"menos de 12 años"*) was
  right, but the back-translation dropped "under", so the round-trip checks flagged it.
- **Photo misreads the highlight missed:** in a slightly blurry photo, *"30 mL every 4 hrs"* was read as
  *"30 mL every hrs"*. The "4" was skipped entirely, so there was no word to highlight. In a blurry one,
  *"correct dose (17 g)"* became *"(17 9)"*, and the OCR was sure enough about the "9" that nothing was
  highlighted. The translation checks can't help after that, because they compare the translation with
  the misread English. Half of the blurry misses were the word "a" read as "8" or "0" (*"ask 0 doctor"*):
  easy for a person to spot, but still a changed number. This is why the pharmacist compares the text
  with the label.

Known limits:
- Word lists can't judge meaning. A "not" in the wrong place passes the "not" check, and a wrong word
  (like "slimming" for "laxative") passes everything.
- The word lists for each language were written without a native speaker. In testing, Tagalog *"sa
  ilalim ng 12"* ("under 12") was flagged until we added *ilalim*. The lists (notebook section 2,
  `dose_safe/languages.py`) still need a fluent speaker to check them. The 23 languages added on Nov 15
  were only tuned on 40 machine translations each.
- Number words can be ambiguous: Vietnamese *năm* means both "five" and "year", and Spanish *una* is
  also "a".
- We only tested US over-the-counter labels, a handful of languages, and one free model.
- Our label photos are made up. Real photos have glare, curved bottles, shadows and tiny print, so real
  misreads may be more common. We haven't measured photo reading on real photos yet.
- The highlight can't flag a word the OCR skipped entirely, and the instruction splitting is a simple
  rule: two lines of a table can be joined or split wrongly. That's why the pharmacist checks the text.

## What we'd do next

- Have pharmacists and more native speakers rate a larger set, especially of prescription labels.
- Use the ratings to tune which checks matter most, and let the tool point to the exact risky words.
- Test photo input on real photos of medicine boxes, with the correct text typed in by hand.
- Ask native speakers to check the word lists of the 23 new languages, starting with the ones our
  community needs most.

## Run the web app

The app (`server.py` and the pages in `web/`) uses the same translator and safety checks as the
notebook's demo, kept in `dose_safe/`, with a translator screen built for a pharmacy counter. Its front page
(`/`) explains the project, with a 45-second explainer film (`web/media/explainer.mp4`); the
translator is at `/translate`. The film and the small looping clips are HyperFrames projects in
`video/`, and the 3D carton and caplets are rendered by `blender/scene.py`. Under *One label line*,
the translator can also read lines from a photo of a label's text, with the same reader photo mode
uses (`dose_safe/ocr.py`, see **Boxes from other countries** below): pick a line it read, compare the
marked words with the label, then check it. A line from a photo gets a tenth check, *Photo read
clearly*, which fails while a word the reader wasn't sure about is still in it (until the pharmacist
corrects it or ticks that it matches the label).

**On a Windows PC, with a free public link:** double-click `run-public.bat`. The first run sets
up the Python packages (about 1.2 GB) and downloads Cloudflare's free tunnel program; the
translation model (about 2.5 GB) and the photo text reader (about 100 MB) download the first time the
app starts. After a `git pull` that changes `requirements-app.txt` (as photo mode and the text reader
did on Nov 15), the next run installs the new packages first. The window then prints
an `https://….trycloudflare.com` link anyone can open. The link works only while that window is
open and the PC is awake, and it changes each time you start it. A check takes about 10–40
seconds on a normal laptop.

**Website language.** The menu starts in the browser's language and remembers the choice. Each
language is one file in `web/i18n/`, with the English text as the key; anything missing shows in
English. After changing the site's text, run `python scripts/i18n_keys.py` and
`python -m pytest tests/test_i18n.py`, which lists the phrases still to translate. The 12 translations
were made with an AI model and haven't been checked by native speakers yet; `?i18n=pseudo` on any
page shows every translated phrase in ⟦ ⟧, to spot text that was missed.

**Just on your own computer:** `pip install -r requirements-app.txt`, then
`uvicorn server:app --port 7860` and open http://localhost:7860/translate.

**Photo mode** is the "Photo of the box" tab (or `/translate?mode=photo`). It needs an internet
connection to look the label up. On a phone, the photo button opens the camera. The photo is only used
to read the barcode (with [zxing-cpp](https://github.com/zxing-cpp/zxing-cpp)) and isn't saved. A whole
label takes longer than one line: about 100 seconds for a 10-line label in safer mode on a laptop
processor. Two limits of the data:
- Only about a third of over-the-counter labels in openFDA list their barcode (16,218 of 49,694 on
  Nov 15, 2026), so the NDC number printed on the box works too.
- Some makers fill in a placeholder barcode (012345678905 is on 134 different labels). When a barcode
  matches more than one product, the app refuses to guess and asks for the NDC number.

**Boxes from other countries.** openFDA only has medicines sold in the US, so a box made for another
country is never found: its barcode starts with something other than 0 or 1 (a real one we were sent
starts with 529), and the app says so. Photograph the box's Directions panel instead. The app reads the
printed text with EasyOCR (`dose_safe/ocr.py`, ported from the notebook's section 10 with the same
cut-offs: numbers read with less than 70% confidence, other words below 30%, letters mixed into a
number), joins it into one instruction per bullet or table row, and marks the words to check. The
pharmacist corrects the lines against the box and ticks *"I compared every line with the box"*; only
then can they be translated. Reading a photo takes about 2 seconds on a laptop processor; the reader
starts after the translation model, and its first start downloads about 100 MB. It reads English: text
that doesn't look like English gets a warning, because the safety checks compare against English.
The same limits as the notebook apply: a word the reader skips entirely can't be marked, which is why
every line is checked, not only the marked ones.

No box at hand? The tab shows a real barcode (from an acetaminophen 500 mg label) to photograph from
the screen, or to use with one click, and a made-up photo of printed directions (the real Directions
of an "Allergy Relief" diphenhydramine label, printed and roughened like a phone photo by
`scripts/make_sample_directions.py`).

**Tests:** `pip install -r requirements-dev.txt`, then `python -m pytest`.

**On Hugging Face:** the repo is set up as a Docker Space (`Dockerfile` and the settings at the
top of this file), but new Docker Spaces now need a paid PRO account.

**On Netlify (the pages only)**, like ours at https://dose-safe.netlify.app: in Netlify, choose **Add new site → Import an existing project**, pick this
repository and deploy; `netlify.toml` publishes the `web` folder as it is, with no build. Netlify can't run
the model, so that copy shows both pages in all 13 languages, but checking a translation needs `server.py`
running somewhere (or the Colab notebook). If a server is running at a fixed https address, the last line
of `web/_redirects` forwards the translator's requests to it.

## How to run the notebook

Click **Open in Colab** at the top (or upload `dose_safe.ipynb` to Colab) → **Runtime → Change runtime
type → T4 GPU** → **Run all**.
The first run downloads the model (about 2.5 GB) and takes about 10–15 minutes. Nothing needs
changing first.

The app at the end prints a public link ending in `.gradio.live`. Open it in a new tab or on a phone; it
works while the notebook is running. (The `localhost` link Colab also shows only works inside Colab.) If
Colab says you have too many active sessions, end your old ones under **Runtime → Manage sessions**.

`data/otc_directions.csv` is a snapshot of the label data downloaded on Nov 14, 2026 (378 instructions
from 66 labels). To skip the download, upload it into a `data` folder in Colab's Files panel before
running.

## Sources

- Data: [openFDA drug label API](https://open.fda.gov/apis/drug/label/) and
  [DailyMed web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm) (US National
  Library of Medicine)
- Model: [facebook/nllb-200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M)
  (Meta, CC-BY-NC 4.0, non-commercial use)
- Photo reading: [EasyOCR](https://github.com/JaidedAI/EasyOCR) (Jaided AI, Apache 2.0)
- Made-up label photos: [Pillow](https://python-pillow.org) and the DejaVu Sans font that comes with
  [Matplotlib](https://matplotlib.org)
- Test set (optional): [FLORES+](https://huggingface.co/datasets/openlanguagedata/flores_plus)
- Libraries: [Hugging Face Transformers](https://github.com/huggingface/transformers),
  [PyTorch](https://pytorch.org), [sacrebleu](https://github.com/mjpost/sacrebleu) (chrF),
  [Gradio](https://www.gradio.app), [pandas](https://pandas.pydata.org); for the web app,
  [FastAPI](https://fastapi.tiangolo.com), [zxing-cpp](https://github.com/zxing-cpp/zxing-cpp) (barcode
  reading), [Pillow](https://python-pillow.org) and [Requests](https://requests.readthedocs.io)
- Background: [UCSF on Google Translate for discharge instructions](https://universityofcalifornia.edu/news/google-translates-doctors-orders-spanish-and-chinese-few-important-caveats);
  [*Pediatrics* study on Spanish prescription labels](https://www.fiercehealthcare.com/healthcare/up-to-half-spanish-translated-prescriptions-include-dangerous-mistakes)
- Explainer film: built with [HyperFrames](https://hyperframes.heygen.com) (`video/explainer`), opening on a
  Blender render (`blender/scene.py`); music from HeyGen's music library (`video/explainer/assets/bgm/CREDITS.md`);
  CC0 sound effects from Freesound via Openverse (`video/explainer/assets/sfx/CREDITS.md`); archival pharmacy
  photographs on the landing page are public domain or CC0 (credited in its footer)
- Demo film (`web/media/demo.mp4`, 45 s): built with HyperFrames (`video/demo`, plan in `SPEC.md`) from
  captures of the running app on Nov 15, 2026 (real model output, Vietnamese) and two Blender shots
  (`blender/scene.py --shot counter` and `--shot slip`, the slip being the app's own print of a real
  label run). The box from another country in it is a made-up example photo, captioned as one: a real
  label's Directions printed beside a real non-US barcode. Same music and sound effects as the explainer.
- AI tools: Claude (Anthropic) was used as a coding assistant.
