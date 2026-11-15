GOAL:    The viewer understands that a free translator can flip a medicine limit, and that Dose-Safe's round trip and checks show a pharmacist exactly which translations to double-check.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    45.3 s x 30 = 1359 frames. Music bed around 90 BPM (20 frames a beat); a new layout every 2-4 s.
LOOK:    The Drug Facts label as a medium.
         - Paper: flat #ffffff, no texture.
         - Ink: #111111, for every word and every structural bar (bars 14-18 px, the label's own weight).
         - Carton: #0e4c92, owning whole fields (the reveal card, the end card) and the 3D carton.
         - Alert: #c8102e, only on a failed check, a struck word and the verdict plate (one focus per frame).
         - Type: Public Sans. Display 900 at 96-140 px, tracking -0.03em. Titles 800 at 56 px. Running lines 600 at 44-64 px. Small notes 500 at 30 px.
         - Medium: the Blender carton (assets/carton.png, transparent, rendered key light upper left) and flat printed panels.
         - No shadows except the carton's own render. No grain, no vignette.
OBJECTS:
         - The carton: 3D render with its Drug Facts side panel readable.
         - The Drug Facts panel: white, framed 8 px black, 18 px section bars, "Directions" bullets.
         - The label line: "do not take more than 6 caplets in 24 hours".
         - The Vietnamese line: "không uống ít hơn 6 viên trong 24 giờ" (illustrated flip, marked as such).
         - The back-translation: "do not take less than 6 tablets in 24 hours".
         - Nine check squares (48 px, 6 px border) that fill.
         - Failed stamps (red 5 px border).
         - The red verdict plate.
         - The patient slip: white paper 4:5 with the real model output "không dùng nhiều hơn 6 viên trong 24 giờ" and "Checked by: ____".
MOTION:  - Enter: expo.out over 10-14 frames.
         - Move: power2.inOut over 18 frames.
         - Exit: power3.in over 6-8 frames.
         - Camera push: power2.inOut over 60 frames.
         - Stamp: scale 1.35 to 1, expo.out, 6 frames.
         - Words per word: blur 6 px to 0 over 4 frames, 2 frames apart.
         - Strike or underline draws: scaleX 0 to 1, power3.out, 9 frames.
         - No springs on text. A landed title is dead still.
SHOTS:
  1. 0-6 s, label. Push from the full carton into its Drug Facts panel (scale 1 to 1.9, 60 frames). Cut at 2.0 s to the flat panel; the red underline draws under "do not take more than 6 caplets in 24 hours" at 2.4 s. Title "One line from a real medicine label" lands 3.0 s and holds. Sound: soft card-slide, click on the underline. Hands off: the line lifts out of the panel.
  2. 6-13 s, flip. Giant "hold the kidney medicine" (UCSF example), struck in red at 8.0 s; "keep taking the medication" prints over it at 8.6 s. Source line: "UCSF study of Google Translate on emergency discharge instructions". Title: "A free translator can flip the meaning". Sound: stamp on the strike.
  3. 13-17 s, reveal. A carton-blue field wipes up (power2.inOut, 18 frames) with "Dose-Safe Translator" 140 px white, then "translates the label line, then checks it" at 44 px. Sound: low hit.
  4. 17-33 s, round trip.
     - English on line 1 at 17.5 s.
     - "Translate" and the Vietnamese at 19.5 s.
     - "Translate back" and the back-translation at 22.0 s.
     - "Compare word by word": "more" struck red at 24.5 s, "less" underlined at 24.8 s.
     - Nine squares fill, 3 frames apart, at 26.5 s. "Under / over kept" and "Under / over survives the round trip" stamp Failed at 28.5 s and 29.0 s; "The other 7 checks passed" at 29.6 s.
     - "Illustrated example" note, 30 px, bottom left.
     - Sound: a click per step and a stamp per Failed.
  5. 33-40 s, verdict and slip. The red plate stamps in at 33.3 s, "Ask a pharmacist or interpreter to check this translation". At 36 s the patient slip slides up from below (24 frames) with the real translation and "Checked by: ____". Title "A pharmacist checks it, then prints it". Sound: stamp, printer.
  6. 40-46 s, claim and end. "It never says a translation is safe." / "It shows what to check." on white, then the carton-blue end card: "Dose-Safe Translator" typed in, "Prototype – not medical advice", "Veritas AI High School Hackathon 2026 · AI + Languages". Holds 2.5 s. Sound: music resolves.
BANNED:  every default in spec.md; plus
         - green ticks or "safe" anywhere;
         - red outside the failed check, struck word and verdict;
         - any translation presented as a real model output when it is the illustrated flip;
         - fades on every element;
         - centred everything (titles sit left on a 120 px margin).
QA:
         - 1.0 s: the carton fills 70% of the height.
         - 2.6 s: the underline is under the right line.
         - 9.0 s: the strike and replacement are readable.
         - 15.0 s: the reveal card.
         - 25.0 s: "more" struck and "less" underlined on the same frame.
         - 29.8 s: two Failed stamps and the pass line.
         - 34.0 s: the verdict plate.
         - 38.0 s: the slip, readable.
         - 44.5 s: the end card, every line readable.
