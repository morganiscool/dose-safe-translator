---
version: 1
slug: "web-translate-html"
primary_target: "web/translate.html"
related_targets: ["web/css/app.css","web/js/translate.js"]
---

# Surface: translator screen (/translate)

Mode: Operate. Audience: a US pharmacist at the counter (primary); hackathon judges trying it (secondary). Task: paste one English label instruction, pick the patient's language, get the translation, its trip back into English, nine checks and a verdict; print a slip for the patient. Frequent action: Translate and check. Photo mode (added Nov 15 at the user's request, "you photo the thing that needs to be translated and you get the dosage and what it does"): photograph the box's barcode (or type it, or the NDC number), confirm the product found, then translate the label's Purpose, Uses, Directions and Do not use lines, each checked. Constraints: CPU server, 10-40 s per check, model may be warming up; never say "safe"; "Prototype – not medical advice" always visible; Chinese and Vietnamese must render correctly; photo mode shows only the label's own words, never generated medical claims.

## Direction contract

THESIS: Every translation returns as a "Translation Facts" panel set in the FDA Drug Facts format the instruction came from. It refuses the category default of white cards on grey, a teal button and a soft "needs review" badge.

OWN-WORLD: Carton field #0e4c92 owns the shell: the top bar and the ground. Working surfaces are white panels framed 3px black, sections split by 10px black bars and 2px black rules. Ink #111. Alert red #c8102e is reserved for failed checks and the "check this" verdict plate, nowhere else. Public Sans (a US federal grotesque) at 900/800/600/400 is the only face, with a system CJK fallback. Corners are square. Controls are 2px black-bordered boxes, and the primary is a solid black slab.

STORY: The pharmacist pastes one bullet, picks the patient's language and presses one button. They read the verdict plate first, then the translation set large, then the round trip, where changed words are marked. Then they print the slip or call an interpreter. A judge sees the whole mechanism on one screen. In photo mode the pharmacist photographs the barcode, checks the product line (brand, active ingredient, maker) is the box in hand, presses one button, and watches the label fill in section by section in the patient's language, each line with its own state word; the whole label prints as one slip.

FIRST VIEWPORT:
- Carton-blue top bar: the wordmark on the left; "Translator", "How it works" and the prototype note on the right.
- Two columns on the blue ground.
- Left (440px): a white Instruction panel. It holds the 24px h1, a two-part mode switch ("One label line" / "Photo of the box", ink-filled when chosen), then for one line: the instruction box; for photo: a 2px-framed photo button with a barcode glyph and a typed-number field. Shared below: the "Patient reads" select, the safer-mode switch, the black slab ("Translate and check" / "Find the label") and real lines or a real barcode to try. Photo mode is two steps: "Find the label" on the left, then, once the pharmacist has checked the product line, "Translate the label into <language>" inside the facts panel; while a label is on screen, "Find the label" steps back to a 2px-framed white button so only one black slab shows.
- Right (fluid): the framed Translation Facts panel, which reads top to bottom:
  1. its title at 32px and a 10px bar;
  2. the verdict plate;
  3. the translation at 30px;
  4. a 2px rule;
  5. English over Back to English, with changed words marked;
  6. a 10px bar;
  7. the checks in two columns, failed first;
  8. a meta line and "Print for patient".
- Photo mode, same panel: the product line (brand 22px/800, active ingredient, maker, barcode, DailyMed source link), the whole-label verdict plate once done, then each label section under a Drug Facts heading and 2px rule; each line's translation at 24px leads, its English below at 16px muted, a state word box beside it (Waiting / Translating / Passed / Failed, with the failed checks named in red under the line), and a disclosure with that line's round trip and checks, open by default on a failed line. During the run the checking loop clip plays above the progress line and timer. The whole-label slip sets each translation at 16pt (the one-line slip uses 26pt) so a 10 to 20 line label fits a page or two; the translation still leads every entry, with the English under it at 9.5pt.
- Empty state: the frame and headings, with the nine check names listed as what will be checked; in photo mode, the four label sections named with what each tells the patient, then one real flagged line from the sample label (Failed box, translation, English, its round trip struck and underlined), captioned as real model output.

FORM: Drug Facts Panel, candidate 4 of 7 on my ordered list (assigned by the roll). seed:40afe95296bca757. Signature interaction: the round trip set word against word. Words lost from the English are struck in red, and words that changed on the way back are underlined. Motion: feedback (press, focus, the running timer), plus what the user asked for on Nov 14 ("add animations inside the app ... using hyperframes"): two HyperFrames clips (the empty state's round trip, the checking loop) and one result moment, the verdict stamp with the struck/underlined words drawing in. Photo mode adds no new motion: it reuses the checking loop and the verdict stamp. Nothing else enters.

Raises:
- Orienteering map: one reserved ink.
- Ticket wallet: failed checks struck and stamped in place, never hidden; the slip carries the verdict.
- Lexicon: colour quarantined to the shell and the verdict plate.
- Transit diagram: the round trip as one path.
- Emission rail: state shown as a word and a form, never hue alone.
- Design annual: one grotesque.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
