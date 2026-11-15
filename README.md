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

**Track:** Languages
**Team:** _names_

> This project is a prototype and is not medical advice.

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

A tool for a **pharmacist at the counter** whose patient reads only Vietnamese, Tagalog, Haitian Creole,
Chinese or Spanish.

- **In:** an English instruction from a medicine label, e.g. *"do not take more than 6 caplets in 24 hours"*.
- **Out:** the translation, the translation turned back into English, nine safety checks, and a verdict:
  ✅ *no problems found by the automatic checks* or ⚠️ *ask a pharmacist or interpreter to check this
  translation*. The tool never says a translation is "safe".
- **Safer mode:** instead of taking the model's first answer, it looks at its top 5 translations and keeps
  the one with the fewest problems in the translation itself (then the fewest problems overall).
- **Photo input:** the pharmacist can photograph the label's Directions section instead of typing.
  EasyOCR reads it and **highlights the words it wasn't sure about** (with a stricter bar for numbers).
  The pharmacist checks the text against the label before anything is translated.

The demo is a Gradio app at the end of the notebook. It prints a public `….gradio.live` link that also
works on a phone. Photo input is only in this notebook demo so far, not in the web app.

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

**Evaluation.** A teammate who reads _TEAM_LANGUAGE_ fluently rates each translation blind (they don't know
which version made it or whether it was flagged): 2 = correct, 1 = small mistake but same meaning,
0 = dangerous. From those ratings we measure how often each version is dangerous, and how many dangerous
translations each checker **misses** (false negatives) and how many **false alarms** it raises (false
positives).

## Results

_Fill these in from the notebook output (sections 7 and 8). Report what you actually got, including
weak results._

**Automatic checks** (share of translations flagged, section 7). From our test run on Nov 14, 2026
(150 label instructions per language, Colab T4 GPU). These numbers come from before the fixes to the
checks (the bugs and their tests are in `tests/test_checks.py` and `tests/test_labels.py`), so re-run
the notebook and update them:

| Language | NLLB as-is | Safer mode | Safer mode changed |
|---|---|---|---|
| Spanish | 11 % | 10 % | 2 % of translations |
| Vietnamese | 17 % | 10 % | 7 % of translations |

Safer mode is chosen *by* these checks, so it will always look better here. The ratings below are the
fair test.

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

**Fluent-speaker ratings** (_TEAM_LANGUAGE_, section 8):

| | NLLB as-is | Safer mode |
|---|---|---|
| Dangerous translations | __ % | __ % |

| Checker | Dangerous caught | Dangerous **missed** (false negatives) | False alarms (false positives) |
|---|---|---|---|
| Back-translation only | __ | __ | __ |
| Our full safety checks | __ | __ | __ |

**General translation quality** (optional, FLORES+ chrF, section 9): Spanish __, _TEAM_LANGUAGE_ __.

**Where it fails.** _Show at least one real example side by side: the English, the model's translation,
the correct translation from your teammate, and why you think it went wrong (and whether the checks
caught it)._

Two real examples from our test run, to check with your fluent speaker:
- **Missed by the checks:** *"laxative products should not be used for a period longer than 1 week
  unless directed by a doctor"*. The Vietnamese translation back-translates as *"**slimming** products
  should not be used…"*. Every number, "not" and limit survived, so no check fired, yet the medicine type
  may be wrong.
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
  ilalim ng 12"* ("under 12") was flagged until we added *ilalim*. Have your speaker check the lists in
  section 2.
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

## Run the web app

The app (`server.py` and the pages in `web/`) is the same tool as the notebook's demo, with the
safety checks in `dose_safe/` and a translator screen built for a pharmacy counter. Its front page
(`/`) explains the project, with a 45-second explainer film (`web/media/explainer.mp4`); the
translator is at `/translate`. The film and the small looping clips are HyperFrames projects in
`video/`, and the 3D carton and caplets are rendered by `blender/scene.py`.

**On a Windows PC, with a free public link:** double-click `run-public.bat`. The first run sets
up the Python packages (about 1 GB) and downloads Cloudflare's free tunnel program; the
translation model (about 2.5 GB) downloads the first time the app starts. The window then prints
an `https://….trycloudflare.com` link anyone can open. The link works only while that window is
open and the PC is awake, and it changes each time you start it. A check takes about 10–40
seconds on a normal laptop.

**Just on your own computer:** `pip install -r requirements-app.txt`, then
`uvicorn server:app --port 7860` and open http://localhost:7860/translate.

**Tests:** `pip install -r requirements-dev.txt`, then `python -m pytest`.

**On Hugging Face:** the repo is set up as a Docker Space (`Dockerfile` and the settings at the
top of this file), but new Docker Spaces now need a paid PRO account.

## How to run the notebook

Click **Open in Colab** at the top (or upload `dose_safe.ipynb` to Colab) → **Runtime → Change runtime
type → T4 GPU** → **Run all**.
The first run downloads the model (about 2.5 GB) and takes about 10–15 minutes. Set `TEAM_LANGUAGE` in
section 2 first.

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
  [Gradio](https://www.gradio.app), [pandas](https://pandas.pydata.org)
- Background: [UCSF on Google Translate for discharge instructions](https://universityofcalifornia.edu/news/google-translates-doctors-orders-spanish-and-chinese-few-important-caveats);
  [*Pediatrics* study on Spanish prescription labels](https://www.fiercehealthcare.com/healthcare/up-to-half-spanish-translated-prescriptions-include-dangerous-mistakes)
- Explainer film: built with [HyperFrames](https://hyperframes.heygen.com) (`video/explainer`), opening on a
  Blender render (`blender/scene.py`); music from HeyGen's music library (`video/explainer/assets/bgm/CREDITS.md`);
  CC0 sound effects from Freesound via Openverse (`video/explainer/assets/sfx/CREDITS.md`); archival pharmacy
  photographs on the landing page are public domain or CC0 (credited in its footer)
- AI tools: Claude (Anthropic) was used as a coding assistant. _Everyone on the team should be able to
  explain every section before submitting._
