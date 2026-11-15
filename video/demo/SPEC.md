# Dose-Safe Translator demo film: how it works, and who it helps

The person's direction (Nov 15, 2026): "The demo video should be just in general about how the app works
and how it affects people", with a Blender opening, made after the photo features were added. It replaced
three proposed storylines (`STORYLINES.md`).

GOAL:    a stranger understands that a pharmacist can hand a patient medicine directions in the patient's
         language, that every line is checked, and that the tool flags rather than promises.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    45.3 s x 30 = 1359 frames (the music bed is 45.3 s with its own fades)
LOOK:    the app's own world. Ground carton blue #0e4c92 (title band and UI ground) or white #ffffff
         (the risk and end-card lines); ink #111111; alert red #c8102e only where the app itself shows it
         (a struck word, a failed check, the "check this" verdict). Public Sans only: titles 56-64 px / 800,
         big lines 96 px / 900 at -0.035em, source lines 30 px / 500.
         Medium: real product screens (2x captures of the running app, Nov 15, 2026) and two Blender
         shots (Cycles, 64 samples, denoised): a mid-grey counter (0.40 albedo), the carton, three
         caplets, a carton-deep wall (#0a3a70) out of focus at f/2.8.
OBJECTS: the acetaminophen carton with its real Drug Facts panel (blender/textures); the app's panels as
         captured; the patient's printed slip (the app's own print of a real label run, as a texture).
MOTION:  titles land word by word (opacity + 6 px blur, 0.13 s each, 0.067 s stagger, power2.out), then
         hold still. Camera over the product: 0.5 s moves on power2.inOut, then hold while the UI acts.
         Cursor 64 px, enters from off-screen on power2.out over 0.7 s; its click changes the screen on
         the same frame. Scene changes: colour wipes (0.6 s power2.inOut) or hard cuts on a click.
SHOTS:
  0.0-4.5   counter (Blender): push in on the carton's Drug Facts panel. "The label is in English." /
            "The patient reads Vietnamese." White on the dark wall. Sound: the bed starts.
  4.5-10.0  risk: white. "A free translator turned" / "hold the kidney medicine" / "into" /
            "keep taking the medication"; "hold" struck red, "keep taking" underlined (the app's own
            marks). Source line. Pencil on the strike.
  10.0-13.0 reveal: the carton colour wipes up; "Dose-Safe Translator" / "It translates, then checks the
            translation". Whoosh.
  13.0-20.5 one line (real UI): the cursor presses Translate and check; the facts panel works, then the
            verdict lands; push in on the Vietnamese and the round trip; pan to the nine checks.
  20.5-27.5 barcode (real UI): the official label found from the sample barcode; Translate the label;
            the red verdict; pan to the flagged Directions line and its round trip.
  27.5-34.5 another country (real UI): the "isn't from a US box" reason; the example photo's printed
            lines with "24" marked; pick a line; its check. The photo is captioned "Example photo".
  34.5-39.5 slip (Blender): the printed slip on the counter. "A slip the patient can read" /
            "checked by the pharmacist". Printer sound.
  39.5-45.3 end card: "The tool flags the risk." / "A person decides." then the carton field carries
            the name, "Prototype – not medical advice" and the hackathon line.
BANNED:  a dark void; glow, particles, gradients, glass cards; three cards in a row; a title over a
         dimmed screenshot; the logo docked in a corner; numbered "01 / 02" labels; text moving while
         it is read; any number or claim not in the app, the README or PRODUCT.md; drawn UI standing in
         for the app.
QA:      frames at 2.0, 7.5, 11.5, 16.5, 18.5, 24.0, 26.0, 30.0, 33.5, 37.0, 43.0: every title readable
         (>= 28 px after any push), the real screen's text legible at its punch-in, nothing cut at the
         title-safe edge, the Vietnamese with its diacritics intact.
