// Dose-Safe Translator: the translator screen. Talks to server.py's /api/status and /api/check.
// Everything the model or the user wrote is put on the page with textContent, never as HTML.

const LANG_CODES = { "Spanish": "es", "Vietnamese": "vi", "Tagalog": "tl", "Haitian Creole": "ht",
                     "Chinese (Simplified)": "zh-Hans" };
const $ = (id) => document.getElementById(id);
const form = $("check-form");
const english = $("english");
const language = $("language");
const safer = $("safer");
const submit = $("submit");
const statusLine = $("status");
const result = $("result");
let ready = false;
let busy = false;

function setStatus(text, kind = "") {
  statusLine.textContent = text;
  statusLine.dataset.kind = kind;
}

function setBusy(on) {
  busy = on;
  submit.disabled = on || !ready;
  submit.textContent = on ? "Checking…" : "Translate and check";
  form.setAttribute("aria-busy", on ? "true" : "false");
}

// ---- Status: is the model loaded yet? ------------------------------------------------------
async function pollStatus() {
  try {
    const response = await fetch("/api/status");
    const body = await response.json();
    if (!language.options.length) {
      for (const lang of body.languages) {
        const option = new Option(lang.tested ? lang.name : `${lang.name} (not tested yet)`, lang.name);
        language.add(option);
      }
      language.value = "Vietnamese";
    }
    if (body.status === "ready") {
      ready = true;
      setStatus("");
      setBusy(false);
      return;
    }
    if (body.status === "error") {
      setStatus("The translation model failed to start. Reload the page in a minute; if it keeps " +
                "happening, the server needs a restart.", "error");
      return;
    }
    setStatus("The translation model is starting up. After the app has been asleep this takes a " +
              "minute or two; the button turns on when it's ready.", "waiting");
  } catch {
    setStatus("Can't reach the translator. Check your connection; this page will keep trying.", "error");
  }
  setTimeout(pollStatus, 5000);
}

// ---- Checking one instruction -------------------------------------------------------------
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !ready) return;
  const text = english.value.trim();
  if (!text) {
    setStatus("Type or paste one instruction from the label first.", "error");
    english.focus();
    return;
  }
  setBusy(true);
  const hadResult = !result.hidden;
  let shown = false;
  showChecking(true);
  const started = Date.now();
  const tries = safer.checked ? "5 translations" : "1 translation";
  // Said once (and announced once); only the seconds count changes.
  setStatus("");
  $("checking-text").textContent = `Translating into ${language.value} (${tries}), translating back into ` +
    "English and running 9 checks. Usually 10–40 seconds.";
  const tick = () => { $("checking-seconds").textContent = `${Math.round((Date.now() - started) / 1000)} s`; };
  tick();
  const timer = setInterval(tick, 1000);
  try {
    const response = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ english: text, language: language.value, safer: safer.checked }),
    });
    if (response.status === 503) {
      ready = false;
      pollStatus();
      return;
    }
    const body = await response.json();
    if (!response.ok) {
      setStatus(typeof body.detail === "string" ? body.detail : "That didn't work. Check the instruction and try again.", "error");
      return;
    }
    setStatus("");
    showChecking(false);
    show(body);
    shown = true;
  } catch {
    setStatus("The check didn't finish: the connection dropped. Try again.", "error");
  } finally {
    clearInterval(timer);
    setBusy(false);
    if (!shown) {
      showChecking(false);
      if (hadResult) result.hidden = false;
      else $("empty").hidden = false;
    }
  }
});

// The HyperFrames "checking" loop plays in the Facts panel while the server works.
function showChecking(on) {
  const box = $("checking");
  const video = $("checking-video");
  box.hidden = !on;
  if (on) {
    $("empty").hidden = true;
    result.hidden = true;
    video.currentTime = 0;
    video.play().catch(() => {});
  } else {
    video.pause();
  }
}

english.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) form.requestSubmit();
});

// ---- Showing a result ---------------------------------------------------------------------
const NUMBER_WORDS = { zero: "0", one: "1", once: "1", two: "2", twice: "2", three: "3", four: "4",
  five: "5", six: "6", seven: "7", eight: "8", nine: "9", ten: "10", eleven: "11", twelve: "12",
  fifteen: "15", twenty: "20", thirty: "30", half: "0.5" };
const NEGATIONS = new Set(["not", "no", "never", "nor", "cannot", "without"]);
const MINOR = new Set(["a", "an", "the", "do", "does", "to", "of", "in", "on", "at", "for", "and", "or",
  "by", "with", "your", "you", "if", "is", "are", "be", "this", "that", "it", "as", "per"]);

function words(text) {
  return (text.toLowerCase().match(/[\p{L}\p{N}'’]+/gu) || []);
}

// One spelling per meaning, so "six" matches "6", "no" matches "not" and "hours" matches "hour".
function key(word) {
  if (NEGATIONS.has(word) || /n['’]t$/.test(word)) return "¬";
  if (NUMBER_WORDS[word]) return NUMBER_WORDS[word];
  return word.length > 3 && word.endsWith("s") ? word.slice(0, -1) : word;
}

// Set the English and the back-translation word by word, marking words that don't make the round trip.
function markRoundTrip(target, text, other, className) {
  target.replaceChildren();
  const keep = new Set(words(other).map(key));
  for (const piece of text.split(/(\s+)/)) {
    const bare = words(piece).filter((w) => !MINOR.has(w)).map(key);
    if (bare.length && bare.some((w) => !keep.has(w))) {
      const mark = document.createElement("span");
      mark.className = className;
      mark.textContent = piece;
      target.append(mark);
    } else {
      target.append(piece);
    }
  }
}

function show(body) {
  $("empty").hidden = true;
  result.hidden = false;
  result.dataset.verdict = body.verdict;
  // Replay the entrance for every new result.
  result.classList.remove("animate");
  void result.offsetWidth;
  result.classList.add("animate");
  const lang = LANG_CODES[body.language] || "";
  $("translation-label").textContent = body.language;
  $("untested").hidden = body.language_tested;
  $("untested-language").textContent = body.language;

  if (body.verdict === "too_long") {
    $("verdict-title").textContent = "Too long to check in one go";
    $("verdict-detail").textContent = "The model would cut off the end of this text without telling " +
      "you. Split it into separate instructions (one bullet from the label at a time) and check each.";
    $("facts").hidden = true;
    $("print").hidden = true;
    $("verdict").focus();
    return;
  }
  $("facts").hidden = false;
  $("print").hidden = false;

  const failed = body.checks.filter((c) => !c.ok);
  if (body.verdict === "check") {
    $("verdict-title").textContent = "Ask a pharmacist or interpreter to check this translation";
    $("verdict-detail").textContent = `${failed.length} of ${body.checks.length} checks failed: ` +
      failed.map((c) => c.name).join(", ") + ".";
  } else {
    $("verdict-title").textContent = "No problems found by the automatic checks";
    $("verdict-detail").textContent = "These checks can't understand meaning. A pharmacist should " +
      "still confirm the translation before it goes to the patient.";
  }

  const translation = $("translation");
  translation.textContent = body.translation;
  translation.lang = lang;
  markRoundTrip($("english-line"), body.english, body.back_translation, "lost");
  markRoundTrip($("back-line"), body.back_translation, body.english, "changed");

  const list = $("checks");
  list.replaceChildren();
  for (const [index, check] of body.checks.entries()) {
    const item = document.createElement("li");
    item.dataset.ok = check.ok;
    item.style.setProperty("--i", index);
    const state = document.createElement("span");
    state.className = "state";
    state.textContent = check.ok ? "Passed" : "Failed";
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = check.name;
    const where = document.createElement("span");
    where.className = "where";
    where.textContent = check.ok ? `checks the ${check.looks_at}` : `${check.detail} · checks the ${check.looks_at}`;
    item.append(state, name, where);
    list.append(item);
  }

  $("meta").textContent = (body.candidates_tried > 1
    ? (body.changed ? `Safer mode tried ${body.candidates_tried} translations and picked one that ` +
                      `isn't the model's first choice.`
                    : `Safer mode tried ${body.candidates_tried} translations; the model's first choice had the fewest problems.`)
    : "The model's first choice.") + ` Took ${body.seconds} s.`;

  // The printed slip for the patient.
  $("slip-language").textContent = body.language;
  const slipText = $("slip-translation");
  slipText.textContent = body.translation;
  slipText.lang = lang;
  $("slip-english").textContent = body.english;
  $("slip-date").textContent = new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
  $("slip-verdict").textContent = body.verdict === "check"
    ? "Not yet confirmed: the automatic checks found problems."
    : "The automatic checks found no problems.";

  $("verdict").focus();
}

$("print").addEventListener("click", () => window.print());

for (const button of document.querySelectorAll("[data-example]")) {
  button.addEventListener("click", () => {
    english.value = button.dataset.example;
    english.focus();
  });
}

// A line sent from the landing page ("Paste a label line and check it") arrives as ?q=.
const sent = new URLSearchParams(location.search).get("q");
if (sent && sent.trim()) {
  english.value = sent.trim().slice(0, 2000);
  english.focus();
}

pollStatus();
