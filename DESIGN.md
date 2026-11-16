---
name: Dose-Safe Translator
description: Medicine directions translated, translated back and checked, set in the FDA Drug Facts label's own grammar.
colors:
  carton: "#0e4c92"
  carton-deep: "#0a3a70"
  on-carton-muted: "#d5e2f3"
  panel: "#ffffff"
  ink: "#111111"
  muted: "#4a4a4a"
  tint: "#eef1f5"
  tint-strong: "#dde5ef"
  alert: "#c8102e"
  disabled: "#6b6b6b"
typography:
  display:
    fontFamily: "Public Sans, system-ui, sans-serif"
    fontSize: "clamp(56px, 9.5vw, 150px)"
    fontWeight: 900
    lineHeight: 0.92
    letterSpacing: "-0.045em"
  headline:
    fontFamily: "Public Sans, system-ui, sans-serif"
    fontSize: "clamp(36px, 5vw, 76px)"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.035em"
  statement:
    fontFamily: "Public Sans, system-ui, sans-serif"
    fontSize: "clamp(21px, 2.3vw, 34px)"
    fontWeight: 600
    lineHeight: 1.3
  panel-title:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.02em"
  translation:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 600
    lineHeight: 1.3
  heading:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  verdict:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 800
    lineHeight: 1.25
  subhead:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 800
    lineHeight: 1.3
  body-large:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 800
    lineHeight: 1.3
  field-label:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.5
  small:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
  button:
    fontFamily: "Public Sans, Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 800
    lineHeight: 1.5
rounded:
  none: "0px"
spacing:
  rule-hair: "1px"
  rule: "2px"
  frame: "3px"
  bar: "10px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  gutter: "24px"
  pad: "32px"
  pad-phone: "18px"
  margin: "40px"
  margin-phone: "16px"
  landing-margin: "clamp(16px, 3.5vw, 56px)"
  section-pad: "clamp(96px, 11vw, 180px)"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.panel}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: "18px 20px"
    width: "100%"
  button-primary-hover:
    backgroundColor: "#000000"
  button-primary-disabled:
    backgroundColor: "{colors.disabled}"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "12px 18px"
  button-secondary-hover:
    backgroundColor: "{colors.tint}"
  example-line:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "11px 14px"
    width: "100%"
  example-line-hover:
    backgroundColor: "{colors.tint-strong}"
  input-field:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body-large}"
    rounded: "{rounded.none}"
    padding: "12px 14px"
  verdict-check:
    backgroundColor: "{colors.alert}"
    textColor: "{colors.panel}"
    typography: "{typography.verdict}"
    rounded: "{rounded.none}"
    padding: "16px 18px"
  verdict-clear:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.verdict}"
    rounded: "{rounded.none}"
    padding: "16px 18px"
  verdict-too-long:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.panel}"
    typography: "{typography.verdict}"
    rounded: "{rounded.none}"
    padding: "16px 18px"
  check-failed-state:
    textColor: "{colors.alert}"
    typography: "{typography.small}"
    rounded: "{rounded.none}"
    padding: "0 6px"
  shell-bar:
    backgroundColor: "{colors.carton}"
    textColor: "{colors.panel}"
    height: "64px"
    padding: "0 40px"
  landing-button:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.panel}"
    rounded: "{rounded.none}"
    padding: "13px 20px"
  landing-button-hover:
    backgroundColor: "{colors.carton}"
---

# Design System: Dose-Safe Translator

## Overview

**Creative North Star: "The Drug Facts Panel"**

Every surface borrows the grammar of the FDA Drug Facts label the instructions come from: a field of carton blue, white panels drawn in black, heavy section bars, thin rules, and one plain federal grotesque. The tool's answer is set as a "Translation Facts" panel, so the result reads like the label it was checked against rather than like a software card. Structure is drawn in ink, not implied with shadows or tinted cards.

The working screen is dense and literal: two columns on the blue ground, the instruction form on the left, the framed facts panel on the right, read top to bottom from verdict to translation to round trip to checks. The landing page uses the same palette and type at poster scale, one field of colour per section, and lets the sentences carry the layout.

Colour is quarantined. Carton blue owns the ground and the bar; white owns the work; ink owns every word and every line; alert red appears only where a check failed. Motion exists to give feedback and to show the round trip, never to decorate.

**Key Characteristics:**
- Carton-blue shell, white working panels, black ink structure.
- One framed panel with 10px black section bars and 2px rules, after the Drug Facts label.
- Alert red only on failed checks, struck words and the "check this" verdict plate.
- Public Sans alone, 900/800/600/400, with a Chinese fallback.
- Square corners everywhere, no shadows.
- State always given as a word plus a form, never hue alone.

## Colors

A government-label palette: one saturated carton blue, paper white, near-black ink, two cool tints, and one reserved red.

### Primary
- **Carton Blue** (carton): the shell. The top bar and the page ground on the translator; whole section fields (the hero's lower half, Watch, Try it) on the landing page; caret colour and text selection everywhere; the 3D carton and the explainer's reveal and end cards.
- **Deep Carton** (carton-deep): the darker step of the carton. Scrollbar thumb, the landing's second time-stage block, the fill of the landing's inline input.

### Tertiary
- **Alert Red** (alert): the failed-check signal. The "Ask a pharmacist or interpreter to check this translation" verdict plate, the Failed state box and the failed check's name and detail, and the strike line through English words lost on the round trip. Nowhere else.

### Neutral
- **Paper White** (panel): working panels, inputs, text on carton and on ink, the secondary button. The landing calls the same value `--paper`.
- **Label Ink** (ink): all body text, the 3px frame, 10px bars, 2px rules, 2px control borders, the primary slab, the underline on words that came back different, the "too long" verdict plate, the landing's ink fields (Results, close).
- **Muted Ink** (muted): hints, the meta line, the check's "checks the…" line, figure captions, the muted lines of the landing's stacked headline.
- **Label Tint** (tint): example-line buttons, secondary-button hover, the landing's Intro and Limits fields.
- **Tint Rule** (tint-strong): 1px dividers between check rows, example-line hover.
- **On-Carton Muted** (on-carton-muted): inactive nav links and the prototype note on the blue bar; soft text on carton and ink fields on the landing.
- **Disabled Grey** (disabled): the primary slab while it can't be pressed.

### Named Rules
**The Carton Owns the Ground Rule.** Blue is a field, never a component colour inside a panel. Inside white panels, everything is ink.

**The Quarantined Red Rule.** Alert red marks a failed check, a struck word or the "check this" verdict plate. Errors in the form, the "too long" refusal and every other state use ink and weight, not red.

**The Word and Form Rule.** Every state is named in words and drawn as a form: "Failed" in a 2px red box, struck versus underlined words with a key underneath, a verdict plate with a sentence. Colour only reinforces.

## Typography

**Display Font:** Public Sans, self-hosted variable (100–900), `font-display: swap`
**Body Font:** Public Sans, falling back to Noto Sans SC, Microsoft YaHei, PingFang SC, system-ui for Chinese
**Label/Mono Font:** none; tabular numerals (`font-variant-numeric: tabular-nums`) handle the timer and the ledger

**Character:** A US federal grotesque, plain and heavy at the top. Weight does the hierarchy work: 900 for titles, 800 for labels and headings, 600 for the patient-facing translation, 400 for running text.

### Hierarchy
- **Display** (landing only): the hero line, the stacked "377 real lines" headline. Tight negative tracking, lines nearly touching.
- **Headline** (landing only): section headings and the closing invitation.
- **Statement** (landing only): the hero subline and pinned statement.
- **Panel Title**: "Translation Facts" (28px on phones).
- **Translation**: the patient-facing translation, set largest in the panel (26px on phones). `overflow-wrap: anywhere`, `lang` set per language.
- **Heading**: the page h1 (22px on phones).
- **Verdict**: the verdict plate's sentence (18px in the empty-state sample).
- **Subhead**: panel section headings ("Checks", "Try a real label line", sample heading).
- **Body Large**: the round-trip lines, inputs and the empty-state lead (lead held to 60ch).
- **Body**: running text, check names.
- **Label**: the row keys (Translation, English, Back to English), check-group headings, the secondary button.
- **Field Label**: form labels, nav links, the safer-mode switch text.
- **Small**: hints, the meta line, the Failed/Passed state, the trip key.

### Named Rules
**The One Grotesque Rule.** Public Sans is the only face on every surface, in the HyperFrames clips and in the explainer. No second family, no mono, no serif.

**The Translation Leads Rule.** In any panel or print that carries a translation, the translation is the largest text after the panel title (30px on screen, 26pt on the printed slip).

## Layout

**Translator.** The 1600px maximum shell is laid out as 40px margins, a 440px instruction column, a 24px gutter and a fluid facts column. The facts panel stretches to the column height. At 1100px or less the form column narrows to 360px, the panel's key/value rows stack, and the checks drop to one column. At 860px or less the form and the panel stack. At 640px or less the margins go to 16px, the panel padding to 18px, and the bar wraps the wordmark, nav and prototype note onto separate lines.

Inside the facts panel, rows are a 170px key column and a fluid value column on a 16px gap, aligned on the baseline. The checks sit in two CSS columns with a 32px gap; each check is a state column (72px, wider when the site's language has a longer state word) beside its name and detail. Rhythm is mostly 8/12/16/24/32px.

**Landing (surface-specific).** Sections are full-bleed fields of a single colour (paper, tint, carton, ink) with clamp-based section padding and margins. A 12-column grid with a 24px gap places copy against media. Five type steps carry the hierarchy (display, headline, statement, body 18px, small 16px). The fixed 72px bar takes the colour and ink of the field under it. At 900px or less the split grids stack; at 640px or less the type steps switch to vw values, the nav hides, and pinned and absolutely placed figures fall back into the flow. The Limits table puts each row's name above it whenever the table itself is narrower than 520px.

**Print.** The patient slip replaces the screen: a 3pt black frame, 8pt bar, the translation at 26pt leading, the English below for the pharmacist, the verdict sentence, and a "Checked by" line.

## Elevation & Depth

Flat. No `box-shadow` anywhere in the web build. Depth comes from the label's own means: white panels on the carton ground, a 3px ink frame, 10px bars, 2px rules and 1px tint rules. The only rendered shadow in the system is the soft key-light shadow inside the Blender carton render.

### Named Rules
**The Printed Label Rule.** Surfaces are flat like printed card stock. Separate with ink lines and fields of colour, never with shadows, blur or tonal elevation.

## Shapes

Square corners throughout: `border-radius: 0` on every control, plate and panel. Borders come in fixed label weights: 3px for the facts frame and the verdict plate, 2px for inputs, the switch, the secondary button, Failed boxes and section rules, 1px tint-strong for row dividers. The 10px bar bleeds to the panel's inner edges with negative margins. The only angled shape is the landing's carton render, rotated -4°.

**The Square Corner Rule.** Nothing is rounded. Not buttons, not inputs, not the switch knob, not video frames.

## Components

### Buttons
Heavy, flat slabs.
- **Shape:** square (0px).
- **Primary:** a full-width ink slab with white 18px/800 text and 18px 20px padding. Hover deepens to pure black; pressing nudges it down 1px (80ms). Disabled turns grey with a not-allowed cursor.
- **Secondary:** a white box with a 2px ink border and 16px/800 text ("Print for patient"); hover fills with tint.
- **Focus:** a 3px ink outline offset 3px (white on the blue bar).
- **Landing button:** an ink slab with 13px 20px padding that turns carton blue on hover (300ms); it inverts to white on ink or carton fields.

### Chips (example lines)
- **Style:** full-width tint blocks of real label text, 15px, left-aligned, no border.
- **State:** hover deepens to tint-strong; clicking fills the instruction box.

### Cards / Containers
- **Corner Style:** square.
- **Instruction panel:** white, unframed on the carton ground, 28px 32px 32px padding.
- **Translation Facts panel:** white, 3px ink frame, 22px 28px 28px padding, 32px/900 title, then a 10px bar.
- **Shadow Strategy:** none (see Elevation & Depth).

### Inputs / Fields
- **Style:** 2px ink border, white fill, square, 18px text, 12px 14px padding. The select draws its own 2px chevron.
- **Focus:** a 3px ink outline offset 2px.
- **Switch (safer mode):** a 44×24 square track with a 2px ink border and a 16px square knob; when on, the track fills ink and the knob turns white and slides 20px (160ms).
- **Error:** the status line under the button goes bold; it never turns red.

### Navigation
- **Translator bar:** carton blue, 64px tall. Wordmark 20px/900 with the label-panel mark; nav links 15px/600 in on-carton-muted, white on hover; the current page is white with a 3px white bottom border. "Prototype – not medical advice" always sits on the bar, beside the website-language menu (a globe and each language's own name).
- **Landing bar:** fixed, 72px, taking the colour and ink of the field beneath it; it hides the nav under 640px but keeps the "Try the translator" button. The website-language menu sits before the button (on a phone, a globe and a short name such as "EN" or "中文"). Each part stays on one line; when they don't fit (a long translation, a narrow phone), the nav goes first, then words wrap, then the wordmark keeps only its mark.

### Verdict Plate (signature)
A 3px-framed plate holding one sentence (22px/800) and a detail line.
- **Check this:** alert red fill, white text, a stroked triangle icon. "Ask a pharmacist or interpreter to check this translation", with the count and names of the failed checks.
- **No problems found:** white with an ink frame, no icon. "No problems found by the automatic checks", and always the note that a pharmacist should still confirm it.
- **Too long:** ink fill, white text, the icon. A refusal, never a truncated result.
- **Motion:** each new result stamps in (320ms, `cubic-bezier(.16, 1, .3, 1)`, a 10px drop, scale from 1.02 and a top-down clip reveal).

### Round Trip (signature)
English over Back to English, set word against word. English words lost on the trip are struck with a 2px alert line through 54% of the x-height; words that came back different are underlined with a 2px ink line 3px below. Both lines draw left to right (280ms after a 460ms delay). A key under the rows explains strike versus underline.

### Checks list
Two columns of rows, each a state word, the check's name (600) and what it looks at (14px muted), split by 1px tint-strong rules, failed checks first. A failed state is "Failed" in 14px/800 alert red inside a 2px alert box, with the name and detail in red too; a passed state is "Passed" in ink.

### Motion assets
- **Round-trip clip** (`web/media/roundtrip.mp4`, source `video/app-clips`): the flagged example in the empty state. It is replaced by a static HTML version when its container is narrower than 760px, at phone width (640px or less) or under reduced motion.
- **Checking loop** (`web/media/checking.mp4`, source `video/checking-loop`): plays while the server works, above a live seconds timer in tabular figures. It is hidden when its container is narrower than 600px or under reduced motion; the timer text stays.
- **Word flip** (`web/media/word-flip.mp4`, source `video/word-flip`): the landing hero's slot for the flipped word.
- **Explainer** (`web/media/explainer.mp4`, source `video/explainer`, spec `video/explainer/SPEC.md`): 45 s at 1920×1080, the same palette and face scaled for video (frames 8px, bars 14–18px), with stamps and strike/underline draws as the only flourishes.
- **Blender renders** (`blender/scene.py`): the carton and caplets in Cycles, Standard view transform so the carton blue is exact, one soft key-light shadow.
- Every clip has a poster still; none carries information the page doesn't also give as text.

## Do's and Don'ts

### Do:
- **Do** set the shell on carton blue and the work on white, with all structure in ink (3px frame, 10px bars, 2px rules).
- **Do** keep alert red to failed checks, struck words and the "check this" verdict plate.
- **Do** name every state in words and draw it as a form, so it reads without colour.
- **Do** use Public Sans alone, keeping the Noto Sans SC / YaHei / PingFang fallback on any surface that shows a translation.
- **Do** keep every corner square and every surface flat.
- **Do** limit motion on the working screen to feedback (press, focus, switch, timer), the two HyperFrames clips with their still fallbacks, and the result's verdict stamp plus the strike/underline draw; turn all of it off under `prefers-reduced-motion`.
- **Do** write the positive verdict as "No problems found by the automatic checks" and carry "Prototype – not medical advice" on every surface (the translator bar, the printed slip, the landing footer, the explainer end card).

### Don't:
- **Don't** call a translation "safe" anywhere: in copy, verdicts, the slip, video or alt text (the product name and the "Safer mode" control are the only uses of the word, and neither describes a translation).
- **Don't** use red for form errors, the "too long" refusal, hover states or emphasis.
- **Don't** add shadows, rounded corners, gradients or tinted cards on grey.
- **Don't** add a second typeface beyond the Chinese fallback.
- **Don't** let a clip's text render below 14px; swap in the still instead.
- **Don't** present the illustrated flip ("ít hơn" / "less") as real model output; label it as an illustration.
