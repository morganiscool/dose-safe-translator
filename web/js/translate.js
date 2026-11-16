// Dose-Safe Translator: the translator screen. Talks to server.py's /api/status, /api/check,
// /api/label, /api/check-lines and /api/read-text. Everything the model, the label, the photo reader
// or the user wrote is put on the page with textContent, never as HTML. The website's own words go
// through t() (i18n.js), so they show in the language chosen in the header.

const LANG_CODES = { "Spanish": "es", "Vietnamese": "vi", "Tagalog": "tl", "Haitian Creole": "ht",
                     "Chinese (Simplified)": "zh-Hans" };
const LANGS = {};  // name → {lang, rtl} for every language, from /api/status
const { t, phrase } = I18N;
const MAX_LINES = 20;  // lines per /api/check-lines request (the server's limit)
const $ = (id) => document.getElementById(id);
const work = document.querySelector(".work");
const form = $("check-form");
const english = $("english");
const language = $("language");
const safer = $("safer");
const submit = $("submit");
const statusLine = $("status");
const result = $("result");
const barcodeInput = $("barcode");
const labelGo = $("label-translate");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let ready = false;
let busy = false;
let busyWith = "";  // "line", "find" or "label": what the server is working on
let mode = "line";
let fromPhoto = null;  // {text, unsure} while the box holds a line read from a photo of the label

function setStatus(text, kind = "") {
  statusLine.textContent = text;
  statusLine.dataset.kind = kind;
}

function setBusy(on, what = "") {
  busy = on;
  busyWith = on ? what : "";
  form.setAttribute("aria-busy", on ? "true" : "false");
  updateButtons();
}

function updateButtons() {
  if (mode === "line") {
    submit.textContent = busyWith === "line" ? t("Checking…") : t("Translate and check");
    submit.disabled = busy || !ready;
  } else {
    submit.textContent = busyWith === "find" ? t("Finding the label…") : t("Find the label");
    submit.disabled = busy;  // finding a label doesn't need the translation model
  }
  // Once a label is on screen, "Translate the label" is the one black slab; finding another steps back.
  submit.classList.toggle("quiet", mode === "photo" && label !== null);
  const fromPhoto = label !== null && label.source === "photo_text";
  const checking = fromPhoto && !$("read-check").hidden;
  labelGo.disabled = busy || !ready || (checking && !$("read-confirm").checked);
  $("read-edit").disabled = busy;
  labelGo.textContent = !ready ? t("Translating turns on when the model is ready")
    : fromPhoto ? t("Translate these lines into {language}", { language: langName(language.value) })
    : t("Translate the label into {language}", { language: langName(language.value) });
}

// The language tag and writing direction for text in a language.
function langOf(name) {
  const info = LANGS[name] || {};
  return { lang: info.lang || LANG_CODES[name] || "", dir: info.rtl ? "rtl" : "ltr" };
}

// A patient language's name in the website's language.
function langName(name) {
  const info = LANGS[name] || {};
  return I18N.languageName(name, info.lang || LANG_CODES[name]);
}

// Every language, in alphabetical order of its name in the website's language.
function fillLanguages(list) {
  for (const lang of list) LANGS[lang.name] = lang;
  const named = list.map((lang) => [langName(lang.name), lang.name]);
  named.sort((a, b) => a[0].localeCompare(b[0], I18N.lang));
  for (const [shown, name] of named) language.append(new Option(shown, name));
  language.value = "Vietnamese";
}

// ---- Text from the server, shown in the website's language ---------------------------------
// The server answers in English. Fixed messages are translated as they are; a message with a number
// or a barcode in it is matched against a template first. Anything unknown stays in English.
const CHECK_NAMES = [phrase("Numbers kept"), phrase("“Not” kept"), phrase("Under / over kept"),
  phrase("Actually translated"), phrase("Numbers survive the round trip"), phrase("“Not” survives the round trip"),
  phrase("Units survive the round trip"), phrase("Under / over survives the round trip"),
  phrase("Back-translation matches"), phrase("Photo read clearly")];
const SECTION_NAMES = [phrase("Purpose"), phrase("Uses"), phrase("Directions"), phrase("Do not use"),
  phrase("Directions (read from the photo)")];
const DETAIL_WORDS = [phrase("under/less"), phrase("over/more"), phrase("hours"), phrase("days"), phrase("weeks"),
  phrase("months"), phrase("minutes"), phrase("teaspoons"), phrase("tablespoons"), phrase("letters mixed into a number")];
const SERVER_MESSAGES = [
  phrase("That photo didn't upload properly. Try taking it again."), phrase("Unknown language"),
  phrase("Type a medicine instruction in English first"), phrase("One of the lines is empty"),
  phrase("No barcode found in the photo. Hold the box closer so the barcode fills about half the picture, with no glare on it, or type the number under the barcode."),
  phrase("No barcode found in the photo."),
  phrase("That photo couldn't be opened. Take it again, or use a JPEG or PNG picture."),
  phrase("No barcode or printed directions could be read in this photo. Photograph the barcode, or the Directions panel up close, flat and in focus, with no glare."),
  phrase("Take a photo of the barcode, or type its number."), phrase("Choose a photo first"),
  phrase("That file isn't a photo the app can open. Use a JPEG or PNG."),
  phrase("That photo is too big. Try one under 15 MB."),
  phrase("Couldn't download the label from DailyMed. Try again in a minute."),
  phrase("That isn't a barcode number. Type the digits under the barcode, or the NDC number printed on the box (it looks like 12345-678-90)."),
  phrase("That barcode is all zeros, which some labels use as a blank. Type the NDC number printed on the box instead."),
  phrase("The FDA's label database didn't answer properly. Try again in a minute."),
  phrase("That isn't a DailyMed label id."),
  phrase("A barcode on a medicine box has 8, 12 or 13 digits. Check the number, or type the NDC number printed on the box (it looks like 12345-678-90)."),
  phrase("Couldn't reach the FDA's label database. Check the internet connection and try again."),
  phrase("DailyMed doesn't have this label any more."),
  phrase("No medicine label with this NDC number is in the FDA's database."),
];
const MESSAGE_TEMPLATES = [
  phrase("No medicine label with the barcode {code} is in the FDA's database. Not every US label lists its barcode there; try the NDC number printed on the box (it looks like 12345-678-90)."),
  phrase("The barcode {code} isn't from a US box: US and Canadian barcodes start with 0 or 1, and this one starts with {prefix}, so the box was made for another country. The FDA's database only has medicines sold in the US."),
  phrase("This barcode is listed on {count} different medicine labels in the FDA's database, so it can't tell which one this box is. Type the NDC number printed on the box instead (it looks like 12345-678-90)."),
];
const MESSAGE_ENDINGS = [
  phrase("The reader for printed text is still starting; try this photo again in a minute."),
  phrase("To use this box anyway, photograph its Directions panel: the printed text is read, and you check it before it's translated."),
];
const DETAIL_TEMPLATES = [phrase("missing {numbers}"), phrase("new {numbers}"),
  phrase("English has {english}, translation has {other}"), phrase("English has {english}, back-translation has {other}"),
  phrase("no word for {names}"), phrase("lost {names}"), phrase("{score}/100 identical to English"),
  phrase("similarity {score}/100")];

// The values in `text` for each {name} in an English template, or null if it doesn't fit.
function matchTemplate(text, template) {
  const names = [];
  const source = template.split(/\{(\w+)\}/).map((part, i) => {
    if (i % 2) { names.push(part); return "(.+?)"; }
    return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }).join("");
  const match = new RegExp(`^${source}$`).exec(text);
  return match ? Object.fromEntries(names.map((name, i) => [name, match[i + 1]])) : null;
}

function serverText(message) {
  if (typeof message !== "string" || I18N.lang === "en") return message;
  if (t(message) !== message) return t(message);
  for (const template of MESSAGE_TEMPLATES) {
    const values = matchTemplate(message, template);
    if (values) return t(template, values);
  }
  for (const ending of MESSAGE_ENDINGS) {
    if (message.endsWith(` ${ending}`)) return `${serverText(message.slice(0, -ending.length - 1))} ${t(ending)}`;
  }
  return message;
}

// "52% sure" or "letters mixed into a number": why a word read from a photo should be checked.
function photoReason(reason) {
  const sure = /^(\d+)% sure$/.exec(reason);
  return sure ? t("{percent}% sure", { percent: sure[1] }) : t(reason);
}

// "“12” (52% sure)": a word read from a photo, and why to check it.
function photoWarning(warning) {
  const match = /^“(.*)” \((.*)\)$/.exec(warning);
  return match ? `“${match[1]}” (${photoReason(match[2])})` : warning;
}

// A check's detail ("missing 6; new 9", "lost hours, mg", "hard to read: …").
function checkDetail(detail) {
  if (!detail || I18N.lang === "en") return detail;
  if (detail.startsWith("hard to read: ")) {
    return t("hard to read: {words}", { words: detail.slice(14).split("; ").map(photoWarning).join("; ") });
  }
  return detail.split("; ").map((part) => {
    for (const template of DETAIL_TEMPLATES) {
      const values = matchTemplate(part, template);
      if (!values) continue;
      if ("names" in values) values.names = values.names.split(", ").map((name) => t(name)).join(", ");
      return t(template, values);
    }
    return part;
  }).join("; ");
}

// ---- Status: are the model and the photo text reader loaded yet? ---------------------------
async function pollStatus() {
  try {
    const response = await fetch("/api/status");
    const body = await response.json();
    if (!language.options.length) fillLanguages(body.languages);
    showTextReader(body.photo_reader);
    if (body.status === "ready") {
      ready = true;
      if (statusLine.dataset.kind === "waiting") setStatus("");
      updateButtons();
      if (body.photo_reader === "warming_up") setTimeout(pollStatus, 5000);  // the photo reader loads next
      return;
    }
    if (body.status === "error") {
      setStatus(t("The translation model failed to start. Reload the page in a minute; if it keeps happening, the server needs a restart."), "error");
      return;
    }
    setStatus(t("The translation model is starting up. After the app has been asleep this takes a minute or two; translating turns on when it's ready."), "waiting");
  } catch {
    setStatus(t("Can't reach the translator. Check your connection; this page will keep trying."), "error");
  }
  setTimeout(pollStatus, 5000);
}

// ---- Two modes: one label line, or a photo of the box ---------------------------------------
const tabs = { line: $("tab-line"), photo: $("tab-photo") };

function setMode(next, { focusTab = false } = {}) {
  mode = next;
  work.dataset.mode = next;
  for (const [name, tab] of Object.entries(tabs)) {
    const on = name === next;
    tab.setAttribute("aria-selected", on ? "true" : "false");
    tab.tabIndex = on ? 0 : -1;
    $(tab.getAttribute("aria-controls")).hidden = !on;
  }
  $("line-examples").hidden = next !== "line";
  $("photo-examples").hidden = next !== "photo";
  $("ocr").hidden = next !== "line";
  if (focusTab) tabs[next].focus();
  const sample = document.querySelector(".sample-video");
  if (next === "photo") sample.pause();
  else sample.play().catch(() => {});
  if (statusLine.dataset.kind !== "waiting") setStatus("");
  history.replaceState(null, "", next === "photo" ? "?mode=photo" : location.pathname);
  updateButtons();
}

for (const [name, tab] of Object.entries(tabs)) {
  tab.addEventListener("click", () => setMode(name));
  tab.addEventListener("keydown", (event) => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const other = name === "line" ? "photo" : "line";
      const target = event.key === "Home" ? "line" : event.key === "End" ? "photo" : other;
      setMode(target, { focusTab: true });
    }
  });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (mode === "line") checkLine();
  else findLabel({ code: barcodeInput.value });
});

// ---- Checking one instruction -------------------------------------------------------------
async function checkLine() {
  if (busy || !ready) return;
  const text = english.value.trim();
  if (!text) {
    setStatus(t("Type or paste one instruction from the label first."), "error");
    english.focus();
    return;
  }
  setBusy(true, "line");
  const hadResult = !result.hidden;
  let shown = false;
  showChecking(true);
  const started = Date.now();
  const tries = safer.checked ? t("5 translations") : t("1 translation");
  // Said once (and announced once); only the seconds count changes.
  setStatus("");
  $("checking-text").textContent = t("Translating into {language} ({tries}), translating back into English and running {count} checks. Usually 10–40 seconds.",
    { language: langName(language.value), tries, count: fromPhoto ? 10 : 9 });
  const tick = () => { $("checking-seconds").textContent = t("{seconds} s", { seconds: Math.round((Date.now() - started) / 1000) }); };
  tick();
  const timer = setInterval(tick, 1000);
  try {
    const response = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ english: text, language: language.value, safer: safer.checked,
                             // Ticking "I compared the marked words" clears them: the pharmacist checked.
                             photo_unsure: fromPhoto ? ($("ocr-confirm").checked ? [] : fromPhoto.unsure)
                                                     : undefined }),
    });
    if (response.status === 503) {
      ready = false;
      pollStatus();
      return;
    }
    const body = await response.json();
    if (!response.ok) {
      setStatus(typeof body.detail === "string" ? serverText(body.detail) : t("That didn't work. Check the instruction and try again."), "error");
      return;
    }
    setStatus("");
    showChecking(false);
    show(body);
    shown = true;
  } catch {
    setStatus(t("The check didn't finish: the connection dropped. Try again."), "error");
  } finally {
    clearInterval(timer);
    setBusy(false);
    if (!shown) {
      showChecking(false);
      if (hadResult) result.hidden = false;
      else $("empty").hidden = false;
    }
  }
}

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

function renderChecks(list, checks) {
  list.replaceChildren();
  for (const check of checks) {
    const item = document.createElement("li");
    item.dataset.ok = check.ok;
    const state = document.createElement("span");
    state.className = "state";
    state.textContent = check.ok ? t("Passed") : t("Failed");
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = t(check.name);
    const where = document.createElement("span");
    where.className = "where";
    const looksAt = { translation: phrase("checks the translation"), "back-translation": phrase("checks the back-translation"),
                      photo: phrase("checks the photo") }[check.looks_at] || `checks the ${check.looks_at}`;
    where.textContent = check.ok ? t(looksAt) : `${checkDetail(check.detail)} · ${t(looksAt)}`;
    item.append(state, name, where);
    list.append(item);
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
  const { lang, dir } = langOf(body.language);
  $("translation-label").textContent = langName(body.language);

  if (body.verdict === "too_long") {
    $("verdict-title").textContent = t("Too long to check in one go");
    $("verdict-detail").textContent = t("The model would cut off the end of this text without telling you. Split it into separate instructions (one bullet from the label at a time) and check each.");
    $("facts").hidden = true;
    $("print").hidden = true;
    $("verdict").focus();
    return;
  }
  $("facts").hidden = false;
  $("print").hidden = false;

  const failed = body.checks.filter((c) => !c.ok);
  if (body.verdict === "check") {
    $("verdict-title").textContent = t("Ask a pharmacist or interpreter to check this translation");
    $("verdict-detail").textContent = t("{failed} of {total} checks failed: {names}.",
      { failed: failed.length, total: body.checks.length, names: failed.map((c) => t(c.name)).join(", ") });
  } else {
    $("verdict-title").textContent = t("No problems found by the automatic checks");
    $("verdict-detail").textContent = t("These checks can't understand meaning. A pharmacist should still confirm the translation before it goes to the patient.");
  }

  const translation = $("translation");
  translation.textContent = body.translation;
  translation.lang = lang;
  translation.dir = dir;
  markRoundTrip($("english-line"), body.english, body.back_translation, "lost");
  markRoundTrip($("back-line"), body.back_translation, body.english, "changed");
  renderChecks($("checks"), body.checks);

  $("meta").textContent = (body.candidates_tried > 1
    ? (body.changed ? t("Safer mode tried {count} translations and picked one that isn't the model's first choice.", { count: body.candidates_tried })
                    : t("Safer mode tried {count} translations; the model's first choice had the fewest problems.", { count: body.candidates_tried }))
    : t("The model's first choice.")) + " " + t("Took {seconds} s.", { seconds: body.seconds });

  // The printed slip for the patient.
  $("slip-language").textContent = langName(body.language);
  const slipText = $("slip-translation");
  slipText.textContent = body.translation;
  slipText.lang = lang;
  slipText.dir = dir;
  $("slip-english").textContent = body.english;
  $("slip-date").textContent = today();
  $("slip-verdict").textContent = body.verdict === "check"
    ? t("Not yet confirmed: the automatic checks found problems.")
    : t("The automatic checks found no problems.");

  $("verdict").focus();
}

function today() {
  return new Date().toLocaleDateString(I18N.lang, { year: "numeric", month: "long", day: "numeric" });
}

$("print").addEventListener("click", () => {
  document.body.dataset.print = "line";
  window.print();
});

for (const button of document.querySelectorAll("[data-example]")) {
  button.addEventListener("click", () => {
    english.value = button.dataset.example;
    clearOcrLine();
    english.focus();
  });
}

// ---- Photo mode: find the label from the barcode --------------------------------------------
let label = null;     // what /api/label sent: barcode, product, active_ingredients, sections
let lines = [];       // one entry per label line: its English, section and page elements
let labelRun = null;  // the last finished translation of the whole label

// Phone photos are big; the barcode reads just as well at 2000 px, and the upload is far smaller.
async function photoToDataUrl(file) {
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, 2000 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    if (bitmap.close) bitmap.close();
    return canvas.toDataURL("image/jpeg", 0.9);
  } catch {
    return null;
  }
}

async function usePhoto(file) {
  if (!file || busy) return;
  const dataUrl = await photoToDataUrl(file);
  if (!dataUrl) {
    setStatus(t("This photo can't be opened here. Take it with the camera, or use a JPEG or PNG picture."), "error");
    return;
  }
  const preview = $("photo-preview");
  const thumbnail = new Image();
  thumbnail.alt = t("Your photo");
  thumbnail.src = dataUrl;
  preview.querySelector("img")?.remove();
  preview.prepend(thumbnail);
  preview.hidden = false;
  $("photo-preview-text").textContent = t("Reading the photo…");
  findLabel({ image: dataUrl });
}

$("photo").addEventListener("change", (event) => {
  const input = event.target;
  const file = input.files && input.files[0];
  usePhoto(file);
  input.value = "";  // so choosing the same photo again still counts as a change
});

for (const button of document.querySelectorAll("[data-barcode]")) {
  button.addEventListener("click", () => {
    barcodeInput.value = button.dataset.barcode;
    findLabel({ code: button.dataset.barcode });
  });
}

// The sample "printed directions" photo goes through exactly the path a camera photo takes.
for (const button of document.querySelectorAll("[data-sample-photo]")) {
  button.addEventListener("click", async () => {
    try {
      const response = await fetch(button.dataset.samplePhoto);
      usePhoto(await response.blob());
    } catch {
      setStatus(t("Couldn't load the sample photo. Check the connection and try again."), "error");
    }
  });
}

async function findLabel(request) {
  if (busy) return;
  if ("code" in request && !request.code.trim()) {
    setStatus(t("Take a photo of the barcode, or type its number first."), "error");
    barcodeInput.focus();
    return;
  }
  setBusy(true, "find");
  setStatus(request.image ? t("Reading the photo: the barcode first, then the printed text if the barcode has no US label. Printed text takes a few seconds.")
    : t("Finding the label…"), "working");
  try {
    const response = await fetch("/api/label", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      setStatus(typeof body.detail === "string" ? serverText(body.detail) : t("That didn't work. Try again."), "error");
      if (request.image) $("photo-preview-text").textContent = t("Nothing usable was found in this photo.");
      return;
    }
    setStatus("");
    if (body.source === "photo_text") {
      if (request.image) {
        $("photo-preview-text").textContent = body.barcode
          ? t("Read the barcode {code}; it has no US label, so the printed text was read.", { code: body.barcode })
          : t("Read the printed text.");
      }
      showReadText(body);
      return;
    }
    if (request.image) $("photo-preview-text").textContent = t("Read the barcode {code}.", { code: body.barcode });
    barcodeInput.value = body.barcode;
    showLabel(body);
  } catch {
    setStatus(t("Couldn't reach the server. Check the connection and try again."), "error");
  } finally {
    setBusy(false);
  }
}

// Clears what the last label or photo left on screen, before showing a new one.
function resetLabelPanel() {
  labelRun = null;
  const box = $("label");
  $("photo-empty").hidden = true;
  box.hidden = false;
  delete box.dataset.verdict;
  box.classList.remove("animate");
  $("label-verdict").hidden = true;
  $("label-meta").textContent = "";
  $("label-print").hidden = true;
  $("read-check").hidden = true;
  $("read-edit").hidden = true;
  $("product-confirm").hidden = false;
  setLabelProgress("");
}

function showLabel(body) {
  label = body;
  resetLabelPanel();
  const box = $("label");

  const product = body.product;
  const brand = $("product-brand");
  brand.textContent = product.brand || titleCase(product.generic) || t("Medicine label");
  brand.tabIndex = -1;
  $("product-active").textContent = body.active_ingredients.join("; ") || titleCase(product.generic);
  const meta = $("product-meta");
  meta.replaceChildren();
  const facts = [product.manufacturer, t("barcode {code}", { code: body.barcode })].filter(Boolean).join(" · ");
  meta.append(facts ? `${facts} · ` : "");
  if (/^https:\/\/dailymed\.nlm\.nih\.gov\//.test(product.dailymed_url || "")) {
    const link = document.createElement("a");
    link.href = product.dailymed_url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = t("the full label on DailyMed");
    meta.append(link);
  }
  if (product.matches > 1) meta.append(" · " + t("{count} versions of this label list the barcode; this is the newest.", { count: product.matches }));

  renderSections(body.sections);
  if (!body.sections.length) {
    labelGo.hidden = true;
    setLabelProgress(t("This label has no Purpose, Uses, Directions or Do not use section that could be read. Open the full label on DailyMed, or check its lines one at a time."), "error");
  } else {
    labelGo.hidden = false;
  }
  updateButtons();
  if (window.matchMedia("(max-width: 860px)").matches) {
    box.scrollIntoView({ block: "start", behavior: reducedMotion.matches ? "auto" : "smooth" });
  }
  brand.focus({ preventScroll: true });
}

function titleCase(text) {
  return (text || "").toLowerCase().replace(/\b\p{L}/gu, (c) => c.toUpperCase());
}

// ---- Photo mode: a box with no US label, read from its printed text --------------------------
// A misread number passes every translation check, so the pharmacist corrects the text against the
// box, and ticks that they did, before anything is translated.
let readItems = [];  // [{ text, words: [{ text, check }] }]: the lines as read, then as corrected

function showReadText(body) {
  label = { source: "photo_text", barcode: body.barcode, sections: [] };
  resetLabelPanel();
  renderSections([]);
  const brand = $("product-brand");
  brand.textContent = t("Directions read from your photo");
  brand.tabIndex = -1;
  const count = body.instructions.length;
  $("product-active").textContent = count === 1 ? t("1 line of printed text") : t("{count} lines of printed text", { count });
  $("product-meta").textContent = body.barcode_note
    ? `${serverText(body.barcode_note)} ${t("So the printed text in the photo was read instead.")}`
    : t("There was no barcode in the photo, so its printed text was read.");
  $("product-confirm").hidden = true;
  $("read-not-english").hidden = body.looks_english !== false;
  readItems = body.instructions.map((item) => ({ text: item.text, words: item.words }));
  renderReadLines();
  $("read-confirm").checked = false;
  $("read-check").hidden = false;
  labelGo.hidden = false;
  updateButtons();
  if (window.matchMedia("(max-width: 860px)").matches) {
    $("label").scrollIntoView({ block: "start", behavior: reducedMotion.matches ? "auto" : "smooth" });
  }
  $("read-summary").focus({ preventScroll: true });
}

function syncReadItems() {
  document.querySelectorAll("#read-lines textarea").forEach((box, i) => { readItems[i].text = box.value; });
}

function renderReadLines() {
  const list = $("read-lines");
  list.replaceChildren();
  const flagged = [];
  readItems.forEach((item, i) => {
    const n = i + 1;
    const row = document.createElement("li");
    const head = document.createElement("div");
    head.className = "read-line-head";
    const name = document.createElement("label");
    name.htmlFor = `read-line-${n}`;
    name.textContent = t("Line {number}", { number: n });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "text-button";
    remove.textContent = t("Remove");
    remove.setAttribute("aria-label", t("Remove line {number}", { number: n }));
    remove.addEventListener("click", () => {
      syncReadItems();
      readItems.splice(i, 1);
      renderReadLines();
      const next = $(`read-line-${Math.min(n, readItems.length)}`) || $("read-add");
      next.focus();
    });
    head.append(name, remove);
    const box = document.createElement("textarea");
    box.id = `read-line-${n}`;
    box.rows = 2;
    box.maxLength = 2000;
    box.value = item.text;
    box.spellcheck = false;
    box.dir = "ltr";  // English, whatever the website's language
    row.append(head, box);
    const unsure = item.words.filter((w) => w.check);
    if (unsure.length) {
      row.dataset.unsure = "true";
      const note = document.createElement("p");
      note.className = "read-note";
      note.id = `read-line-${n}-note`;
      box.setAttribute("aria-describedby", note.id);
      note.append(t("Hard to read in the photo:") + " ");
      unsure.forEach((w, k) => {
        const word = document.createElement("span");
        word.className = "unsure";
        word.textContent = w.text;
        note.append(word, ` ${photoReason(w.check)}${k < unsure.length - 1 ? ", " : "."}`);
      });
      note.append(" " + t("Compare with the box."));
      row.append(note);
      flagged.push({ n, unsure });
    }
    list.append(row);
  });
  const total = flagged.reduce((sum, f) => sum + f.unsure.length, 0);
  $("read-summary").dataset.unsure = total ? "true" : "false";
  $("read-summary-title").textContent = !readItems.length ? t("No lines left")
    : total === 1 ? t("1 word was hard to read") : total ? t("{count} words were hard to read", { count: total })
    : t("Every word was read clearly");
  $("read-summary-detail").textContent = total === 1
    ? t("Compare it, and every other line, with the box and fix any mistake. A misread number would pass every translation check.")
    : total ? t("Compare them, and every other line, with the box and fix any mistake. A misread number would pass every translation check.")
    : t("Still compare every line with the box: a word the reader skipped entirely can't be marked.");
  const links = $("read-summary-list");
  links.replaceChildren();
  for (const f of flagged) {
    const entry = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#read-line-${f.n}`;
    link.textContent = `${t("Line {number}", { number: f.n })}: ${f.unsure.map((w) => `“${w.text}”`).join(", ")}`;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      $(`read-line-${f.n}`).focus();
    });
    entry.append(link);
    links.append(entry);
  }
}

$("read-add").addEventListener("click", () => {
  syncReadItems();
  readItems.push({ text: "", words: [] });
  renderReadLines();
  $(`read-line-${readItems.length}`).focus();
});

$("read-confirm").addEventListener("change", updateButtons);

// "Translate these lines": the corrected text becomes the label's one section.
function applyReadText() {
  syncReadItems();
  const texts = readItems.map((item) => item.text.replace(/\s+/g, " ").trim()).filter(Boolean);
  if (!texts.length) {
    setLabelProgress(t("There's no text to translate. Add a line, or take another photo."), "error");
    return false;
  }
  if (!$("read-confirm").checked) return false;
  label.sections = [{ name: phrase("Directions (read from the photo)"), lines: texts }];
  renderSections(label.sections);
  $("read-check").hidden = true;
  $("read-edit").hidden = false;
  return true;
}

$("read-edit").addEventListener("click", () => {
  if (busy) return;
  const box = $("label");
  labelRun = null;
  delete box.dataset.verdict;
  box.classList.remove("animate");
  $("label-verdict").hidden = true;
  $("label-meta").textContent = "";
  $("label-print").hidden = true;
  setLabelProgress("");
  label.sections = [];
  renderSections([]);
  $("read-edit").hidden = true;
  $("read-check").hidden = false;
  $("read-confirm").checked = false;
  labelGo.hidden = false;
  updateButtons();
  $("read-line-1")?.focus();
});

function renderSections(sections) {
  const host = $("label-sections");
  host.replaceChildren();
  lines = [];
  sections.forEach((section, s) => {
    const wrap = document.createElement("section");
    wrap.className = "label-section";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.setAttribute("aria-hidden", "true");
    const heading = document.createElement("h3");
    heading.className = "label-heading";
    heading.textContent = t(section.name);
    const list = document.createElement("ul");
    list.className = "label-lines";
    for (const text of section.lines) {
      const item = document.createElement("li");
      const state = document.createElement("span");
      state.className = "state";
      const content = document.createElement("div");
      content.className = "line-body";
      const translation = document.createElement("p");
      translation.className = "line-translation";
      const englishText = document.createElement("p");
      englishText.className = "line-english";
      englishText.textContent = text;
      englishText.dir = "ltr";
      content.append(translation, englishText);
      item.append(state, content);
      list.append(item);
      const line = { section: s, english: text, item, state, content, translation, englishText, extra: [] };
      setLineState(line, "waiting");
      lines.push(line);
    }
    wrap.append(bar, heading, list);
    host.append(wrap);
  });
}

const STATE_WORDS = { waiting: phrase("Waiting"), working: phrase("Translating"), passed: phrase("Passed"),
                      failed: phrase("Failed"), too_long: phrase("Too long") };

// Some languages have a state word longer than the English column ("Menerjemahkan" in Indonesian).
// Measure the longest one, so the column fits it and a state never runs into the text beside it.
function fitStateColumns() {
  const probe = document.createElement("div");
  probe.setAttribute("aria-hidden", "true");
  probe.style.cssText = "position: absolute; visibility: hidden; top: 0; left: 0;";
  const columns = [
    { list: "label-lines", data: "state", words: STATE_WORDS, width: "--line-state-width" },
    { list: "checks", data: "ok", words: { true: phrase("Passed"), false: phrase("Failed") }, width: "--check-state-width" },
  ];
  for (const column of columns) {
    column.element = document.createElement("ul");
    column.element.className = column.list;
    for (const [value, key] of Object.entries(column.words)) {
      const item = document.createElement("li");
      item.dataset[column.data] = value;
      const state = document.createElement("span");
      state.className = "state";
      state.style.width = "min-content";  // the longest word, with the box's padding and border
      state.textContent = t(key);
      item.append(state);
      column.element.append(item);
    }
    probe.append(column.element);
  }
  document.body.append(probe);
  for (const column of columns) {
    const widths = [...column.element.querySelectorAll(".state")].map((state) => state.getBoundingClientRect().width);
    document.documentElement.style.setProperty(column.width, `${Math.ceil(Math.max(...widths))}px`);
  }
  probe.remove();
}

function setLineState(line, state) {
  line.item.dataset.state = state;
  line.state.textContent = t(STATE_WORDS[state]);
}

function clearLine(line) {
  for (const element of line.extra) element.remove();
  line.extra = [];
  line.translation.textContent = "";
  line.translation.removeAttribute("lang");
  setLineState(line, "waiting");
}

function setLabelProgress(text, kind = "", seconds = "") {
  const progress = $("label-progress");
  progress.hidden = !text;
  progress.dataset.kind = kind;
  $("label-progress-text").textContent = text;
  $("label-seconds").textContent = seconds;
}

// ---- Photo mode: translate the label, one section at a time ---------------------------------
labelGo.addEventListener("click", translateLabel);

async function translateLabel() {
  if (busy || !ready || !label) return;
  if (label.source === "photo_text" && !$("read-check").hidden && !applyReadText()) return;
  if (!lines.length) return;
  const targetLanguage = language.value;
  const saferOn = safer.checked;
  const box = $("label");
  setBusy(true, "label");
  delete box.dataset.verdict;
  box.classList.remove("animate");
  $("label-verdict").hidden = true;
  $("label-print").hidden = true;
  $("label-meta").textContent = "";
  lines.forEach(clearLine);
  labelGo.hidden = true;
  showLabelChecking(true);

  const started = Date.now();
  const seconds = () => t("{seconds} s", { seconds: Math.round((Date.now() - started) / 1000) });
  let doing = "";
  const tick = () => { $("label-seconds").textContent = seconds(); };
  const timer = setInterval(tick, 1000);
  const answers = new Map();
  let stopped = "";
  try {
    sections: for (const [s, section] of label.sections.entries()) {
      const sectionLines = lines.filter((line) => line.section === s);
      for (let start = 0; start < sectionLines.length; start += MAX_LINES) {
        const chunk = sectionLines.slice(start, start + MAX_LINES);
        chunk.forEach((line) => setLineState(line, "working"));
        doing = t("Translating {section} (part {part} of {parts}) into {language}, translating it back and running 9 checks on each line.",
          { section: t(section.name), part: s + 1, parts: label.sections.length, language: langName(targetLanguage) });
        setLabelProgress(doing, "", seconds());
        const response = await fetch("/api/check-lines", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lines: chunk.map((line) => line.english), language: targetLanguage, safer: saferOn }),
        });
        if (response.status === 503) {
          ready = false;
          pollStatus();
          stopped = t("The translation model is starting up again. Press the button once it's ready.");
          break sections;
        }
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
          stopped = typeof body.detail === "string" ? serverText(body.detail) : t("That didn't work. Try again.");
          break sections;
        }
        body.results.forEach((answer, k) => {
          showLine(chunk[k], answer, targetLanguage);
          answers.set(chunk[k], answer);
        });
      }
    }
  } catch {
    stopped = t("The translation didn't finish: the connection dropped. Try again.");
  } finally {
    clearInterval(timer);
    showLabelChecking(false);
    setBusy(false);
  }
  if (stopped) {
    for (const line of lines) if (!answers.has(line)) setLineState(line, "waiting");
    labelGo.hidden = false;
    setLabelProgress(stopped, "error");
    return;
  }
  setLabelProgress("");
  labelRun = { language: targetLanguage, safer: saferOn, answers, seconds: Math.round((Date.now() - started) / 1000) };
  showLabelVerdict();
}

// The same HyperFrames "checking" loop as one-line mode plays above the progress line during the run.
function showLabelChecking(on) {
  const video = $("label-checking-video");
  $("label-checking").hidden = !on;
  if (on) {
    video.currentTime = 0;
    video.play().catch(() => {});
  } else {
    video.pause();
  }
}

function showLine(line, answer, targetLanguage) {
  clearLine(line);
  if (answer.verdict === "too_long") {
    setLineState(line, "too_long");
    const note = document.createElement("p");
    note.className = "hint line-note";
    note.textContent = t("Too long to check in one go, so it's left in English. Split it and check each part under One label line.");
    line.content.append(note);
    line.extra.push(note);
    return;
  }
  const failed = answer.checks.filter((c) => !c.ok);
  line.translation.textContent = answer.translation;
  Object.assign(line.translation, langOf(targetLanguage));
  setLineState(line, failed.length ? "failed" : "passed");
  const parts = [];
  if (failed.length) {
    const names = document.createElement("p");
    names.className = "line-failed";
    names.textContent = t("{failed} of {total} checks failed: {names}",
      { failed: failed.length, total: answer.checks.length, names: failed.map((c) => t(c.name)).join(", ") });
    parts.push(names);
  }
  const details = document.createElement("details");
  details.className = "line-details";
  const summary = document.createElement("summary");
  summary.textContent = t("Round trip and checks");
  const rows = [[phrase("English"), answer.english, answer.back_translation, "lost"],
                [phrase("Back to English"), answer.back_translation, answer.english, "changed"]].map(([name, text, other, mark]) => {
    const row = document.createElement("div");
    row.className = "row";
    const k = document.createElement("p");
    k.className = "k";
    k.textContent = t(name);
    const trip = document.createElement("p");
    trip.className = "trip";
    trip.dir = "ltr";
    markRoundTrip(trip, text, other, mark);
    row.append(k, trip);
    return row;
  });
  // The same sentence as on the page, in the website's language (from the team's translation files).
  const tripKey = document.querySelector(".result .trip-key, #facts .trip-key").cloneNode(true);
  const checks = document.createElement("ul");
  checks.className = "checks";
  renderChecks(checks, answer.checks);
  details.append(summary, ...rows, tripKey, checks);
  details.open = failed.length > 0;  // a failed line shows its struck and underlined words without a click
  parts.push(details);
  line.content.append(...parts);
  line.extra.push(...parts);
}

function showLabelVerdict() {
  const box = $("label");
  const answers = [...labelRun.answers.values()];
  const total = answers.length;
  const failed = answers.filter((a) => a.verdict === "check").length;
  const long = answers.filter((a) => a.verdict === "too_long").length;
  const longNote = !long ? "" : " " + (long === 1 ? t("1 line was too long to check and is left in English.")
    : t("{count} lines were too long to check and are left in English.", { count: long }));
  if (failed) {
    box.dataset.verdict = "check";
    $("label-verdict-title").textContent = t("Ask a pharmacist or interpreter to check this translation");
    $("label-verdict-detail").textContent = t("{failed} of {total} lines failed at least one check; they're marked Failed below.",
      { failed, total }) + longNote;
  } else if (long) {
    box.dataset.verdict = "too_long";
    $("label-verdict-title").textContent = t("Part of this label wasn't translated");
    $("label-verdict-detail").textContent = `${longNote.trim()} ${t("The other lines passed every check; a pharmacist should still confirm them.")}`;
  } else {
    box.dataset.verdict = "no_problems_found";
    $("label-verdict-title").textContent = t("No problems found by the automatic checks");
    $("label-verdict-detail").textContent = t("All {total} lines passed all 9 checks. These checks can't understand meaning. A pharmacist should still confirm the translation before it goes to the patient.", { total });
  }
  const verdict = $("label-verdict");
  verdict.hidden = false;
  void box.offsetWidth;
  box.classList.add("animate");
  $("label-meta").textContent = (label.source === "photo_text"
    ? t("The English was read from your photo and corrected by you.") + " " : "") + (labelRun.safer
    ? t("Safer mode tried 5 translations of each line and kept the one with the fewest problems.")
    : t("The model's first choice for each line.")) + " " + t("{count} lines took {seconds} s.", { count: total, seconds: labelRun.seconds });
  $("label-print").hidden = false;
  fillLabelSlip();
  verdict.focus();
}

// Changing the language or safer mode after a run offers to translate the label again.
for (const control of [language, safer]) {
  control.addEventListener("change", () => {
    updateButtons();
    if (label && labelRun && !busy && label.sections.length &&
        (labelRun.language !== language.value || labelRun.safer !== safer.checked)) {
      labelGo.hidden = false;
    }
  });
}

// The printed slip for the whole label: each line in the patient's language, the English small under it.
function fillLabelSlip() {
  const { lang, dir } = langOf(labelRun.language);
  $("lslip-language").textContent = langName(labelRun.language);
  const fromPhoto = label.source === "photo_text";
  $("lslip-product").textContent = fromPhoto ? t("Directions printed on the box")
    : [$("product-brand").textContent, $("product-active").textContent].filter(Boolean).join(" · ");
  $("lslip-source").textContent = fromPhoto ? t("Read from a photo of the box and checked by the pharmacist")
    : t("Label from DailyMed");
  const host = $("lslip-sections");
  host.replaceChildren();
  label.sections.forEach((section, s) => {
    const part = document.createElement("div");
    part.className = "lslip-section";
    const heading = document.createElement("p");
    heading.className = "lslip-heading";
    heading.textContent = t(section.name);
    part.append(heading);
    for (const line of lines.filter((l) => l.section === s)) {
      const answer = labelRun.answers.get(line);
      const entry = document.createElement("div");
      entry.className = "lslip-line";
      const translated = document.createElement("p");
      translated.className = "lslip-translation";
      const englishText = document.createElement("p");
      englishText.className = "lslip-english";
      englishText.dir = "ltr";
      englishText.textContent = line.english;
      if (answer.verdict === "too_long") {
        translated.textContent = line.english;
        entry.append(translated);
      } else {
        translated.textContent = answer.translation;
        translated.lang = lang;
        translated.dir = dir;
        entry.append(translated, englishText);
      }
      if (answer.verdict !== "no_problems_found") {
        const flag = document.createElement("span");
        flag.className = "lslip-flag";
        flag.textContent = answer.verdict === "too_long" ? t("Not translated: too long") : t("Check this line");
        entry.append(flag);
      }
      part.append(entry);
    }
    host.append(part);
  });
  const failed = [...labelRun.answers.values()].filter((a) => a.verdict !== "no_problems_found").length;
  $("lslip-verdict").textContent = failed
    ? t("Not yet confirmed: the automatic checks found problems in {failed} of {total} lines, marked for the pharmacist.",
      { failed, total: labelRun.answers.size })
    : t("The automatic checks found no problems.");
  $("lslip-date").textContent = today();
}

$("label-print").addEventListener("click", () => {
  document.body.dataset.print = "label";
  window.print();
});

// ---- One label line: read the lines from a photo of the label's text ------------------------
const ocrButton = $("ocr-button");
const ocrExample = $("ocr-example");
const ocrFile = $("ocr-file");
const ocrStatus = $("ocr-status");
let ocrReady = false;
let ocrBusy = false;

function setOcrStatus(text, kind = "") {
  ocrStatus.textContent = text;
  ocrStatus.dataset.kind = kind;
}

function setOcrBusy(on) {
  ocrBusy = on;
  ocrButton.disabled = ocrExample.disabled = on || !ocrReady;
  ocrButton.textContent = on ? t("Reading the photo…") : t("Take or choose a photo");
}

function showTextReader(state) {
  ocrReady = state === "ready";
  if (!ocrBusy) setOcrBusy(false);
  ocrButton.hidden = ocrExample.hidden = state === "off";
  if (state === "off") {
    setOcrStatus(t("Reading photos of the label's text is off on this copy of the app (the reader isn't installed). Typing still works."));
  } else if (state === "error") {
    setOcrStatus(t("The photo reader failed to start. Typing still works."), "error");
  } else if (state === "warming_up") {
    setOcrStatus(t("The photo reader is starting up; its buttons turn on when it's ready."), "waiting");
  } else if (!ocrBusy && (ocrStatus.dataset.kind === "waiting" || !ocrStatus.dataset.kind)) {
    setOcrStatus("");
  }
}

// Phones take 12-megapixel photos. 2000 pixels on the long side is plenty to read a label, and
// much quicker to send and read. Small JPEG or PNG files go as they are.
async function shrink(file) {
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, 2000 / Math.max(bitmap.width, bitmap.height));
    if (scale === 1 && /^image\/(jpeg|png)$/.test(file.type) && file.size < 3e6) return file;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    return blob || file;
  } catch {
    return file;  // this browser can't open it (e.g. an iPhone HEIC photo on Windows): let the server try
  }
}

let ocrPreviewUrl = "";
// `reading` says what is being read, e.g. "Reading your photo… usually 5–30 seconds."
async function readTextPhoto(file, reading) {
  if (!ocrReady || ocrBusy) return;
  setOcrBusy(true);
  setOcrStatus(t(reading), "waiting");
  if (ocrPreviewUrl) URL.revokeObjectURL(ocrPreviewUrl);
  ocrPreviewUrl = URL.createObjectURL(file);
  $("ocr-preview").src = ocrPreviewUrl;
  try {
    const upload = await shrink(file);
    const response = await fetch("/api/read-text", {
      method: "POST",
      headers: { "Content-Type": upload.type || "application/octet-stream" },
      body: upload,
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      setOcrStatus(response.status !== 503 && typeof body.detail === "string" ? serverText(body.detail)
        : t("The photo reader isn't available right now. Typing still works."), "error");
      return;
    }
    showOcrLines(body.instructions);
  } catch {
    setOcrStatus(t("The photo didn't finish uploading: the connection dropped. Try again."), "error");
  } finally {
    setOcrBusy(false);
  }
}

function showOcrLines(instructions) {
  const list = $("ocr-lines");
  list.replaceChildren();
  clearOcrLine();
  $("ocr-result").hidden = false;
  if (!instructions.length) {
    $("ocr-summary").textContent = "";
    setOcrStatus(t("No text found. Try a closer, sharper photo of the Directions, held flat."), "error");
    return;
  }
  setOcrStatus("");
  const unsure = instructions.reduce((n, item) => n + item.unsure.length, 0);
  $("ocr-summary").textContent = [
    instructions.length === 1 ? t("Read 1 line.") : t("Read {count} lines.", { count: instructions.length }),
    unsure === 1 ? t("1 word was hard to read (in red).") : unsure ? t("{count} words were hard to read (in red).", { count: unsure })
      : t("No word was hard to read, but still compare each line with the label."),
    t("Pick a line to put it in the box above."),
  ].join(" ");
  instructions.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ocr-line";
    button.dir = "ltr";
    button.setAttribute("aria-pressed", "false");
    item.words.forEach((word, i) => {
      if (i) button.append(" ");
      if (word.warning) {
        const mark = document.createElement("mark");
        mark.textContent = word.text;
        mark.title = photoWarning(word.warning);
        button.append(mark);
      } else {
        button.append(word.text);
      }
    });
    if (item.unsure.length) {
      const note = document.createElement("span");
      note.className = "ocr-line-note";
      note.textContent = `${t("Check:")} ${item.unsure.map((u) => photoWarning(u.warning)).join(", ")}`;
      button.append(note);
    }
    button.addEventListener("click", () => useOcrLine(item, button, index));
    const row = document.createElement("li");
    row.append(button);
    list.append(row);
  });
}

function useOcrLine(item, button, index) {
  english.value = item.text;
  fromPhoto = { text: item.text, unsure: item.unsure };
  $("ocr-confirm").checked = false;
  $("ocr-confirm-row").hidden = !item.unsure.length;
  for (const other of document.querySelectorAll(".ocr-line")) {
    other.setAttribute("aria-pressed", String(other === button));
  }
  const toCheck = item.unsure.map((u) => u.warning.split(" (")[0]).join(", ");
  setStatus(t("Line {number} from the photo is in the box.", { number: index + 1 }) + " " + (item.unsure.length
    ? t("Compare {words} with the label and fix it if needed, then check it.", { words: toCheck })
    : t("Compare it with the label, then check it.")));
  english.focus();
  english.scrollIntoView({ block: "center", behavior: reducedMotion.matches ? "auto" : "smooth" });
}

function clearOcrLine() {
  fromPhoto = null;
  $("ocr-confirm").checked = false;
  $("ocr-confirm-row").hidden = true;
  for (const button of document.querySelectorAll(".ocr-line")) button.setAttribute("aria-pressed", "false");
}

// How much of one text's words are in the other (0 to 1).
function overlap(a, b) {
  const first = new Set(words(a));
  const second = new Set(words(b));
  if (!first.size || !second.size) return 0;
  let same = 0;
  for (const word of first) if (second.has(word)) same += 1;
  return same / Math.max(first.size, second.size);
}

// Fixing a word keeps the photo line (and its check); typing a different instruction drops it.
english.addEventListener("input", () => {
  if (fromPhoto && overlap(english.value, fromPhoto.text) < 0.5) clearOcrLine();
});

ocrButton.addEventListener("click", () => ocrFile.click());
ocrFile.addEventListener("change", () => {
  const file = ocrFile.files[0];
  ocrFile.value = "";
  if (file) readTextPhoto(file, phrase("Reading your photo… usually 5–30 seconds."));
});
ocrExample.addEventListener("click", async () => {
  try {
    const response = await fetch("/static/media/example-label.jpg", { cache: "no-cache" });
    if (!response.ok) throw new Error("missing");
    readTextPhoto(await response.blob(), phrase("Reading the example photo… usually 5–30 seconds."));
  } catch {
    setOcrStatus(t("The example photo didn't load. Try your own photo instead."), "error");
  }
});
// In One label line, a photo pasted anywhere on the page (Ctrl + V) is read too.
document.addEventListener("paste", (event) => {
  const file = [...(event.clipboardData?.files || [])].find((f) => f.type.startsWith("image/"));
  if (mode === "line" && file && ocrReady && !ocrBusy) {
    event.preventDefault();
    readTextPhoto(file, phrase("Reading the pasted photo… usually 5–30 seconds."));
  }
});

// ---- Start ----------------------------------------------------------------------------------
const params = new URLSearchParams(location.search);
// A line sent from the landing page ("Paste a label line and check it") arrives as ?q=.
const sent = params.get("q");
if (sent && sent.trim()) {
  english.value = sent.trim().slice(0, 2000);
  english.focus();
}
if (params.get("mode") === "photo") setMode("photo");
I18N.ready.then(() => {
  fitStateColumns();
  updateButtons();
  pollStatus();
});
