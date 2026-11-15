---
version: 1
slug: "web-translate-html"
primary_target: "web/translate.html"
related_targets: ["web/css/app.css","web/js/translate.js"]
---

# Surface: translator screen (/translate)

Mode: Operate. Audience: a US pharmacist at the counter (primary); hackathon judges trying it (secondary). Task: paste one English label instruction, pick the patient's language, get the translation, its trip back into English, nine checks and a verdict; print a slip for the patient. Frequent action: Translate and check. Constraints: CPU server, 10-40 s per check, model may be warming up; never say "safe"; "Prototype – not medical advice" always visible; Chinese and Vietnamese must render correctly.

## Direction contract

THESIS: Every translation returns as a "Translation Facts" panel set in the FDA Drug Facts format the instruction came from. It refuses the category default of white cards on grey, a teal button and a soft "needs review" badge.

OWN-WORLD: Carton field #0e4c92 owns the shell: the top bar and the ground. Working surfaces are white panels framed 3px black, sections split by 10px black bars and 2px black rules. Ink #111. Alert red #c8102e is reserved for failed checks and the "check this" verdict plate, nowhere else. Public Sans (a US federal grotesque) at 900/800/600/400 is the only face, with a system CJK fallback. Corners are square. Controls are 2px black-bordered boxes, and the primary is a solid black slab.

STORY: The pharmacist pastes one bullet, picks the patient's language and presses one button. They read the verdict plate first, then the translation set large, then the round trip, where changed words are marked. Then they print the slip or call an interpreter. A judge sees the whole mechanism on one screen.

FIRST VIEWPORT:
- Carton-blue top bar: the wordmark on the left; "Translator", "How it works" and the prototype note on the right.
- Two columns on the blue ground.
- Left (440px): a white Instruction panel. It holds the 24px h1, the instruction box, the "Patient reads" select, the safer-mode switch, the black "Translate and check" slab and real label lines to try.
- Right (fluid): the framed Translation Facts panel, which reads top to bottom:
  1. its title at 32px and a 10px bar;
  2. the verdict plate;
  3. the translation at 30px;
  4. a 2px rule;
  5. English over Back to English, with changed words marked;
  6. a 10px bar;
  7. the checks in two columns, failed first;
  8. a meta line and "Print for patient".
- Empty state: the frame and headings, with the nine check names listed as what will be checked.

FORM: Drug Facts Panel, candidate 4 of 7 on my ordered list (assigned by the roll). seed:40afe95296bca757. Signature interaction: the round trip set word against word. Words lost from the English are struck in red, and words that changed on the way back are underlined. Motion: feedback (press, focus, the running timer), plus what the user asked for on Nov 14 ("add animations inside the app ... using hyperframes"): two HyperFrames clips (the empty state's round trip, the checking loop) and one result moment, the verdict stamp with the struck/underlined words drawing in. Nothing else enters.

Raises:
- Orienteering map: one reserved ink.
- Ticket wallet: failed checks struck and stamped in place, never hidden; the slip carries the verdict.
- Lexicon: colour quarantined to the shell and the verdict plate.
- Transit diagram: the round trip as one path.
- Emission rail: state shown as a word and a form, never hue alone.
- Design annual: one grotesque.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
