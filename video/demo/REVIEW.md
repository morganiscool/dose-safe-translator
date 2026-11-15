# Demo film: review and delivery note (Nov 15, 2026)

**Creative calls.** The person's direction was a film "just in general about how the app works and how it
affects people", so it follows the patient and the pharmacist (the English-only label, the risk of a free
translator, the app's three ways in, the slip the patient can read) instead of the three feature-led
storylines in `STORYLINES.md`, which were not built. Real screens come from the running app (2x captures,
real model output); the two 3D shots are rendered by `blender/scene.py` (`--shot counter`, `--shot slip`).
The slip on the counter is the app's own print of a real label run. The box from another country is a
made-up example photo (a real label's Directions beside a real non-US barcode) and is captioned
"Example photo" on screen.

**Time is compressed.** On screen a check lands about 1.4 s after the click; the real line took 8.5 s and
the 10-line label 171 s on a laptop processor. The captured panels still show the real times ("Took 8.5 s",
"10 lines took 171 s").

**Measured.** `hyperframes check`: no errors or warnings (the remaining info notes are the screen captures
being larger than the frame, which is how the camera moves over them). `snapshot --review`: beats, all 7
seams and the phone sheet looked at. Fixed from the review:
- 0-4.5 s: the titles ran onto the white Drug Facts panel as the camera pushed in; they now sit in the
  carton-blue band, one line at a time, like the other scenes.
- 13.0 s and 27.5 s: the opening close-ups showed the empty results panel's illustration of a red
  "Ask a pharmacist" verdict, which could read as the result; both now frame the form alone.
- 30.8 s: the "Example photo" tag covered the photo's heading; moved to its empty corner.
- 4.5-10 s: the source line was on screen under its reading time; shortened and shown earlier.

**Sound, measured.** The first render was -22.4 LUFS, too quiet; every level was doubled in `index.html`
(the music bed to 1.0) and the delivered render measures -16.4 LUFS integrated, true peak -1.2 dBTP, no
clipping, with its hits on the cut at 4.5 s, the checks and verdict at 15.5-16.5 s, the stamp at 22.7 s, the
cut at 27.5 s and the printer at 35.2 s.

**Not checked by anyone.** The sound was measured with `hyperframes audio`, not heard. At phone width
(360 px) the titles read, but the app's small print inside the screen scenes does not; the film is made for
1080p (submission and landing page).

**Weakest shot.** The risk beat (4.5-10 s) is type only, with no picture of the harm; with more time it
would show the two instructions as printed slips. Second: the barcode scene's pan to the flagged line moves
over a long panel quickly; a slower pan or a cut would read better.
