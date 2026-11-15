// Dose-Safe Translator: the translator screen. Talks to server.py's /api/status, /api/check,
// /api/label and /api/check-lines. Everything the model, the label or the user wrote is put on the
// page with textContent, never as HTML.

const LANG_CODES = { "Spanish": "es", "Vietnamese": "vi", "Tagalog": "tl", "Haitian Creole": "ht",
                     "Chinese (Simplified)": "zh-Hans" };
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
    submit.textContent = busyWith === "line" ? "Checking…" : "Translate and check";
    submit.disabled = busy || !ready;
  } else {
    submit.textContent = busyWith === "find" ? "Finding the label…" : "Find the label";
    submit.disabled = busy;  // finding a label doesn't need the translation model
  }
  // Once a label is on screen, "Translate the label" is the one black slab; finding another steps back.
  submit.classList.toggle("quiet", mode === "photo" && label !== null);
  const fromPhoto = label !== null && label.source === "photo_text";
  const checking = fromPhoto && !$("read-check").hidden;
  labelGo.disabled = busy || !ready || (checking && !$("read-confirm").checked);
  $("read-edit").disabled = busy;
  labelGo.textContent = !ready ? "Translating turns on when the model is ready"
    : fromPhoto ? `Translate these lines into ${language.value}`
    : `Translate the label into ${language.value}`;
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
      if (statusLine.dataset.kind === "waiting") setStatus("");
      updateButtons();
      return;
    }
    if (body.status === "error") {
      setStatus("The translation model failed to start. Reload the page in a minute; if it keeps " +
                "happening, the server needs a restart.", "error");
      return;
    }
    setStatus("The translation model is starting up. After the app has been asleep this takes a " +
              "minute or two; translating turns on when it's ready.", "waiting");
  } catch {
    setStatus("Can't reach the translator. Check your connection; this page will keep trying.", "error");
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
    setStatus("Type or paste one instruction from the label first.", "error");
    english.focus();
    return;
  }
  setBusy(true, "line");
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
  renderChecks($("checks"), body.checks);

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
  $("slip-date").textContent = today();
  $("slip-verdict").textContent = body.verdict === "check"
    ? "Not yet confirmed: the automatic checks found problems."
    : "The automatic checks found no problems.";

  $("verdict").focus();
}

function today() {
  return new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

$("print").addEventListener("click", () => {
  document.body.dataset.print = "line";
  window.print();
});

for (const button of document.querySelectorAll("[data-example]")) {
  button.addEventListener("click", () => {
    english.value = button.dataset.example;
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
    setStatus("This photo can't be opened here. Take it with the camera, or use a JPEG or PNG picture.", "error");
    return;
  }
  const preview = $("photo-preview");
  const thumbnail = new Image();
  thumbnail.alt = "Your photo";
  thumbnail.src = dataUrl;
  preview.querySelector("img")?.remove();
  preview.prepend(thumbnail);
  preview.hidden = false;
  $("photo-preview-text").textContent = "Reading the photo…";
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
      setStatus("Couldn't load the sample photo. Check the connection and try again.", "error");
    }
  });
}

async function findLabel(request) {
  if (busy) return;
  if ("code" in request && !request.code.trim()) {
    setStatus("Take a photo of the barcode, or type its number first.", "error");
    barcodeInput.focus();
    return;
  }
  setBusy(true, "find");
  setStatus(request.image ? "Reading the photo: the barcode first, then the printed text if the barcode " +
                            "has no US label. Printed text takes a few seconds." : "Finding the label…", "working");
  try {
    const response = await fetch("/api/label", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      setStatus(typeof body.detail === "string" ? body.detail : "That didn't work. Try again.", "error");
      if (request.image) $("photo-preview-text").textContent = "Nothing usable was found in this photo.";
      return;
    }
    setStatus("");
    if (body.source === "photo_text") {
      if (request.image) {
        $("photo-preview-text").textContent = body.barcode
          ? `Read the barcode ${body.barcode}; it has no US label, so the printed text was read.`
          : "Read the printed text.";
      }
      showReadText(body);
      return;
    }
    if (request.image) $("photo-preview-text").textContent = `Read the barcode ${body.barcode}.`;
    barcodeInput.value = body.barcode;
    showLabel(body);
  } catch {
    setStatus("Couldn't reach the server. Check the connection and try again.", "error");
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
  $("label-untested").hidden = true;
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
  brand.textContent = product.brand || titleCase(product.generic) || "Medicine label";
  brand.tabIndex = -1;
  $("product-active").textContent = body.active_ingredients.join("; ") || titleCase(product.generic);
  const meta = $("product-meta");
  meta.replaceChildren();
  const facts = [product.manufacturer, `barcode ${body.barcode}`].filter(Boolean).join(" · ");
  meta.append(facts ? `${facts} · ` : "");
  if (/^https:\/\/dailymed\.nlm\.nih\.gov\//.test(product.dailymed_url || "")) {
    const link = document.createElement("a");
    link.href = product.dailymed_url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "the full label on DailyMed";
    meta.append(link);
  }
  if (product.matches > 1) meta.append(` · ${product.matches} versions of this label list the barcode; this is the newest.`);

  renderSections(body.sections);
  if (!body.sections.length) {
    labelGo.hidden = true;
    setLabelProgress("This label has no Purpose, Uses, Directions or Do not use section that could be read. " +
                     "Open the full label on DailyMed, or check its lines one at a time.", "error");
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
  brand.textContent = "Directions read from your photo";
  brand.tabIndex = -1;
  const count = body.instructions.length;
  $("product-active").textContent = `${count} ${count === 1 ? "line" : "lines"} of printed text`;
  $("product-meta").textContent = body.barcode_note
    ? `${body.barcode_note} So the printed text in the photo was read instead.`
    : "There was no barcode in the photo, so its printed text was read.";
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
    name.textContent = `Line ${n}`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "text-button";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove line ${n}`);
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
    row.append(head, box);
    const unsure = item.words.filter((w) => w.check);
    if (unsure.length) {
      row.dataset.unsure = "true";
      const note = document.createElement("p");
      note.className = "read-note";
      note.id = `read-line-${n}-note`;
      box.setAttribute("aria-describedby", note.id);
      note.append("Hard to read in the photo: ");
      unsure.forEach((w, k) => {
        const word = document.createElement("span");
        word.className = "unsure";
        word.textContent = w.text;
        note.append(word, ` ${w.check}${k < unsure.length - 1 ? ", " : "."}`);
      });
      note.append(" Compare with the box.");
      row.append(note);
      flagged.push({ n, unsure });
    }
    list.append(row);
  });
  const total = flagged.reduce((sum, f) => sum + f.unsure.length, 0);
  $("read-summary").dataset.unsure = total ? "true" : "false";
  $("read-summary-title").textContent = !readItems.length ? "No lines left"
    : total ? `${total} ${total === 1 ? "word was" : "words were"} hard to read`
    : "Every word was read clearly";
  $("read-summary-detail").textContent = total
    ? `Compare ${total === 1 ? "it" : "them"}, and every other line, with the box and fix any mistake. A misread ` +
      "number would pass every translation check."
    : "Still compare every line with the box: a word the reader skipped entirely can't be marked.";
  const links = $("read-summary-list");
  links.replaceChildren();
  for (const f of flagged) {
    const entry = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#read-line-${f.n}`;
    link.textContent = `Line ${f.n}: ${f.unsure.map((w) => `“${w.text}”`).join(", ")}`;
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
    setLabelProgress("There's no text to translate. Add a line, or take another photo.", "error");
    return false;
  }
  if (!$("read-confirm").checked) return false;
  label.sections = [{ name: "Directions (read from the photo)", lines: texts }];
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
  $("label-untested").hidden = true;
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
    heading.textContent = section.name;
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

const STATE_WORDS = { waiting: "Waiting", working: "Translating", passed: "Passed", failed: "Failed",
                      too_long: "Too long" };

function setLineState(line, state) {
  line.item.dataset.state = state;
  line.state.textContent = STATE_WORDS[state];
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
  $("label-untested").hidden = true;
  $("label-print").hidden = true;
  $("label-meta").textContent = "";
  lines.forEach(clearLine);
  labelGo.hidden = true;
  showLabelChecking(true);

  const started = Date.now();
  const seconds = () => `${Math.round((Date.now() - started) / 1000)} s`;
  let doing = "";
  const tick = () => { $("label-seconds").textContent = seconds(); };
  const timer = setInterval(tick, 1000);
  const answers = new Map();
  let tested = true;
  let stopped = "";
  try {
    sections: for (const [s, section] of label.sections.entries()) {
      const sectionLines = lines.filter((line) => line.section === s);
      for (let start = 0; start < sectionLines.length; start += MAX_LINES) {
        const chunk = sectionLines.slice(start, start + MAX_LINES);
        chunk.forEach((line) => setLineState(line, "working"));
        doing = `Translating ${section.name} (part ${s + 1} of ${label.sections.length}) into ${targetLanguage}, ` +
          "translating it back and running 9 checks on each line.";
        setLabelProgress(doing, "", seconds());
        const response = await fetch("/api/check-lines", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lines: chunk.map((line) => line.english), language: targetLanguage, safer: saferOn }),
        });
        if (response.status === 503) {
          ready = false;
          pollStatus();
          stopped = "The translation model is starting up again. Press the button once it's ready.";
          break sections;
        }
        const body = await response.json().catch(() => ({}));
        if (!response.ok) {
          stopped = typeof body.detail === "string" ? body.detail : "That didn't work. Try again.";
          break sections;
        }
        tested = body.language_tested;
        body.results.forEach((answer, k) => {
          showLine(chunk[k], answer, targetLanguage);
          answers.set(chunk[k], answer);
        });
      }
    }
  } catch {
    stopped = "The translation didn't finish: the connection dropped. Try again.";
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
  labelRun = { language: targetLanguage, safer: saferOn, answers, tested, seconds: Math.round((Date.now() - started) / 1000) };
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
    note.textContent = "Too long to check in one go, so it's left in English. Split it and check each part " +
      "under One label line.";
    line.content.append(note);
    line.extra.push(note);
    return;
  }
  const failed = answer.checks.filter((c) => !c.ok);
  line.translation.textContent = answer.translation;
  line.translation.lang = LANG_CODES[targetLanguage] || "";
  setLineState(line, failed.length ? "failed" : "passed");
  const parts = [];
  if (failed.length) {
    const names = document.createElement("p");
    names.className = "line-failed";
    names.textContent = `${failed.length} of ${answer.checks.length} checks failed: ${failed.map((c) => c.name).join(", ")}`;
    parts.push(names);
  }
  const details = document.createElement("details");
  details.className = "line-details";
  const summary = document.createElement("summary");
  summary.textContent = "Round trip and checks";
  const rows = [["English", answer.english, answer.back_translation, "lost"],
                ["Back to English", answer.back_translation, answer.english, "changed"]].map(([name, text, other, mark]) => {
    const row = document.createElement("div");
    row.className = "row";
    const k = document.createElement("p");
    k.className = "k";
    k.textContent = name;
    const trip = document.createElement("p");
    trip.className = "trip";
    markRoundTrip(trip, text, other, mark);
    row.append(k, trip);
    return row;
  });
  const tripKey = document.createElement("p");
  tripKey.className = "trip-key";
  const struck = document.createElement("span");
  struck.className = "lost";
  struck.textContent = "Struck";
  const underlined = document.createElement("span");
  underlined.className = "changed";
  underlined.textContent = "underlined";
  tripKey.append(struck, " words didn't make the round trip; ", underlined, " words came back different.");
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
  const longNote = long ? ` ${long === 1 ? "1 line was" : `${long} lines were`} too long to check and ` +
    `${long === 1 ? "is" : "are"} left in English.` : "";
  if (failed) {
    box.dataset.verdict = "check";
    $("label-verdict-title").textContent = "Ask a pharmacist or interpreter to check this translation";
    $("label-verdict-detail").textContent = `${failed} of ${total} lines failed at least one check; ` +
      `they're marked Failed below.${longNote}`;
  } else if (long) {
    box.dataset.verdict = "too_long";
    $("label-verdict-title").textContent = "Part of this label wasn't translated";
    $("label-verdict-detail").textContent = `${longNote.trim()} The other lines passed every check; a ` +
      "pharmacist should still confirm them.";
  } else {
    box.dataset.verdict = "no_problems_found";
    $("label-verdict-title").textContent = "No problems found by the automatic checks";
    $("label-verdict-detail").textContent = `All ${total} lines passed all 9 checks. These checks can't ` +
      "understand meaning. A pharmacist should still confirm the translation before it goes to the patient.";
  }
  const verdict = $("label-verdict");
  verdict.hidden = false;
  void box.offsetWidth;
  box.classList.add("animate");
  $("label-untested").hidden = labelRun.tested;
  $("label-untested-language").textContent = labelRun.language;
  $("label-meta").textContent = (label.source === "photo_text"
    ? "The English was read from your photo and corrected by you. " : "") + (labelRun.safer
    ? "Safer mode tried 5 translations of each line and kept the one with the fewest problems."
    : "The model's first choice for each line.") + ` ${total} lines took ${labelRun.seconds} s.`;
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
  const lang = LANG_CODES[labelRun.language] || "";
  $("lslip-language").textContent = labelRun.language;
  const fromPhoto = label.source === "photo_text";
  $("lslip-product").textContent = fromPhoto ? "Directions printed on the box"
    : [$("product-brand").textContent, $("product-active").textContent].filter(Boolean).join(" · ");
  $("lslip-source").textContent = fromPhoto ? "Read from a photo of the box and checked by the pharmacist"
    : "Label from DailyMed";
  const host = $("lslip-sections");
  host.replaceChildren();
  label.sections.forEach((section, s) => {
    const part = document.createElement("div");
    part.className = "lslip-section";
    const heading = document.createElement("p");
    heading.className = "lslip-heading";
    heading.textContent = section.name;
    part.append(heading);
    for (const line of lines.filter((l) => l.section === s)) {
      const answer = labelRun.answers.get(line);
      const entry = document.createElement("div");
      entry.className = "lslip-line";
      const translated = document.createElement("p");
      translated.className = "lslip-translation";
      const englishText = document.createElement("p");
      englishText.className = "lslip-english";
      englishText.textContent = line.english;
      if (answer.verdict === "too_long") {
        translated.textContent = line.english;
        entry.append(translated);
      } else {
        translated.textContent = answer.translation;
        translated.lang = lang;
        entry.append(translated, englishText);
      }
      if (answer.verdict !== "no_problems_found") {
        const flag = document.createElement("span");
        flag.className = "lslip-flag";
        flag.textContent = answer.verdict === "too_long" ? "Not translated: too long" : "Check this line";
        entry.append(flag);
      }
      part.append(entry);
    }
    host.append(part);
  });
  const failed = [...labelRun.answers.values()].filter((a) => a.verdict !== "no_problems_found").length;
  $("lslip-verdict").textContent = failed
    ? `Not yet confirmed: the automatic checks found problems in ${failed} of ${labelRun.answers.size} lines, ` +
      "marked for the pharmacist."
    : "The automatic checks found no problems.";
  $("lslip-date").textContent = today();
}

$("label-print").addEventListener("click", () => {
  document.body.dataset.print = "label";
  window.print();
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
updateButtons();
pollStatus();
