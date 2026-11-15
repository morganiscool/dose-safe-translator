# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML/CSS/JS pages served by a small Python FastAPI server (`server.py`), which runs the NLLB-200 model and the safety checks (`dose_safe/`). Hosted as a Docker Space on Hugging Face (free CPU tier). The user approved this in the build plan (stack choice delegated to Claude, then confirmed).

## Users

- **Primary: a US pharmacist at the counter.** They are handing over-the-counter medicine directions to a patient who reads only Vietnamese, Tagalog, Haitian Creole, Chinese or Spanish. They need a translation and a quick, honest signal of whether a person should double-check it before it reaches the patient.
- **Secondary: hackathon judges** (Veritas AI International High School Hackathon 2026, AI + Languages track). They read the landing page, watch the explainer video and try the translator.

## Product Purpose

Free machine translation is instant but makes dangerous mistakes on medical instructions. The research example is UCSF's "hold the kidney medicine" becoming "keep taking the medication". The tool translates one English label instruction, translates it back, runs nine targeted safety checks, and gives a verdict: "no problems found by the automatic checks" or "ask a pharmacist or interpreter to check this translation". The project's research question: does the common back-translation check catch dangerous errors, and do targeted checks catch more? Success means pharmacists catch dangerous translations before patients see them.

## Positioning

It doesn't claim translations are correct. It flags the specific kinds of mistake that hurt people: a lost "not", a changed number, a flipped "under/over" limit, changed units. Safer mode picks the best of the model's top five translations using those checks. It is built and tested on about 380 real instructions from 66 US over-the-counter drug labels (openFDA + DailyMed).

## Operating Context

- A pharmacy counter: quick, one instruction at a time, often with a patient waiting. The result may be printed and handed to the patient.
- Instructions come from the "Directions" and "Do not use" sections of US Drug Facts labels, e.g. "do not take more than 6 caplets in 24 hours", "children under 12 years: ask a doctor".
- The model runs on a free CPU server. A safer-mode check takes roughly 10–40 seconds, and the server sleeps after about 48 hours without visitors, then takes minutes to wake.

## Capabilities and Constraints

- Languages: Spanish, Vietnamese, Tagalog, Haitian Creole, Chinese (Simplified). Only Spanish and Vietnamese have been run on real label instructions. No language's word lists have been checked by a native speaker yet.
- Nine checks. Four look at the translation: numbers kept, "not" kept, under/over kept, actually translated. Five look at the back-translation: numbers, "not", units and under/over survive the round trip, and the back-translation matches (chrF ≥ 40).
- Inputs longer than 256 model tokens are refused, not cut off.
- Photo mode (added Nov 15, 2026): a photo of the box's barcode, or a typed barcode or NDC number, finds the official label (openFDA → DailyMed). The pharmacist confirms the product, then every line of its Purpose, Uses, Directions and Do not use sections is translated and checked, and the whole label prints as one slip. It shows only the label's own words, never generated claims; "Uses" lists symptoms and conditions, not viruses. A barcode shared by different products is refused rather than guessed. A 10-line label takes about 100 s in safer mode on a laptop CPU.
- Boxes from other countries (added Nov 15, 2026, at the user's request: "medicines from all over the world"): openFDA only has US medicines, so when a photo has no barcode, or one with no US label, the box's printed directions are read with EasyOCR (the notebook's reader and cut-offs). Hard-to-read words are marked; the pharmacist corrects every line and ticks "I compared every line with the box" before anything is translated. English text only: other languages get a warning, because the checks compare against English.
- Model: facebook/nllb-200-distilled-600M, CC-BY-NC 4.0, so non-commercial use only.
- The checks are word rules. They can't understand meaning: a wrong word like "slimming" for "laxative" passes everything.

## Brand Commitments

- Name: **Dose-Safe Translator**.
- Never call a translation "safe". The positive verdict is always "no problems found by the automatic checks", and a pharmacist should still confirm.
- Always say "Prototype – not medical advice."
- Say it is a Veritas AI International High School Hackathon 2026 project, AI + Languages track.
- Team names: none for now. Leave them off; the team may add them before submitting.

## Evidence on Hand

- `data/otc_directions.csv`: 378 instructions from 66 labels, 24 ingredients (snapshot from Nov 14, 2026, with symbol-font bullets split).
- Automatic-check results, re-run on Nov 15, 2026 with the fixed checks on that snapshot (150 instructions per language, laptop CPU). Spanish: 11% flagged as-is, 10% in safer mode, which changed 3% of translations. Vietnamese: 16% → 10%, safer mode changed 7%.
- Fluent-speaker ratings: **not collected yet.** Never invent rating results, catch rates, testimonials, users or press.
- Real examples:
  - Missed by the checks: "laxative products should not be used…" came back from Vietnamese as "slimming products…".
  - False alarm: "children 4 to under 12 yrs" in correct Spanish was flagged because the back-translation dropped "under".
- Research sources: UCSF on Google Translate for discharge instructions (92% accurate for Spanish, 81% for Chinese); the *Pediatrics* study finding errors in about half of Spanish prescription labels.

## Product Principles

1. Honest uncertainty over reassurance: the tool flags; a person decides.
2. The patient-facing text is the product. The translation must be legible, large and correctly rendered in every supported script.
3. Speed and clarity at the counter beat decoration on the working screen.
4. Show the evidence, including weak results and known failures.

## Accessibility & Inclusion

- The translation must render correctly in Vietnamese (stacked diacritics), Chinese (Simplified Han), Tagalog, Haitian Creole and Spanish.
- The printed slip is read by patients who may have limited literacy in English. The translation leads, set large.
- Keyboard-operable, visible focus, WCAG AA contrast, and works at phone width.
