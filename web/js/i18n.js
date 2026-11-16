// Dose-Safe Translator: the language of the website itself (not the patient's language).
// The English text is the key: web/i18n/<lang>.json maps each English phrase to its translation, and
// anything missing stays in English. The page's own text is translated where it stands; text that must
// stay English (label lines, the English side of a round trip) is marked translate="no". Translation
// files are written by the team and served with the site, so data-i18n-html may hold simple markup.

window.I18N = (() => {
  // The website's languages, each in its own name. Arabic is written right to left.
  const LANGUAGES = [
    ["en", "English"], ["es", "Español"], ["fr", "Français"], ["pt", "Português"],
    ["id", "Bahasa Indonesia"], ["tl", "Tagalog"], ["vi", "Tiếng Việt"], ["zh-Hans", "中文（简体）"],
    ["ko", "한국어"], ["ja", "日本語"], ["ru", "Русский"], ["ar", "العربية"], ["hi", "हिन्दी"],
  ];
  const RIGHT_TO_LEFT = new Set(["ar"]);
  // The menu's short name, where a page shows one (the landing page on a phone).
  const SHORT = { "zh-Hans": "中文", ko: "한국어", ja: "日本語", ar: "عربي", hi: "हिन्दी" };
  const STORE = "dose-safe-site-language";
  const codes = LANGUAGES.map(([code]) => code);

  // The saved choice, else the first of the browser's languages the site has, else English.
  function choose() {
    let saved = null;
    try { saved = localStorage.getItem(STORE); } catch { /* private window: no saved choice */ }
    if (codes.includes(saved)) return saved;
    for (const wanted of navigator.languages || [navigator.language || "en"]) {
      const tag = String(wanted).toLowerCase();
      if (/^zh-(hant|tw|hk|mo)/.test(tag)) continue;  // Traditional Chinese readers: not Simplified
      if (tag.startsWith("zh")) return "zh-Hans";
      if (tag.startsWith("fil")) return "tl";
      const primary = tag.split("-")[0];
      if (codes.includes(primary)) return primary;
    }
    return "en";
  }

  const lang = choose();
  let table = {};
  // ?i18n=pseudo (for checking the site): every translated phrase shows in ⟦ ⟧, so any English
  // without them was missed.
  const pseudo = /[?&]i18n=pseudo\b/.test(location.search);
  const normalize = (text) => text.replace(/\s+/g, " ").trim();

  // The translation of an English phrase, with {name} filled in from `values`.
  function t(key, values) {
    let text = Object.prototype.hasOwnProperty.call(table, key) ? table[key] : key;
    if (values) text = text.replace(/\{(\w+)\}/g, (all, name) => (name in values ? String(values[name]) : all));
    return pseudo ? `⟦${text}⟧` : text;
  }
  const has = (key) => pseudo || Object.prototype.hasOwnProperty.call(table, key);
  const look = (key) => (pseudo ? `⟦${key}⟧` : table[key]);

  // A patient language's name in the website's language ("Spanish" → "Spanyol"), from the browser.
  function languageName(englishName, tag) {
    if (lang === "en" || !tag) return englishName;
    try {
      return new Intl.DisplayNames([lang], { type: "language" }).of(tag) || englishName;
    } catch {
      return englishName;
    }
  }

  // Translate the page where it stands: text, a few attributes, and whole sentences with markup.
  const originalText = new WeakMap();
  const originalAttrs = new WeakMap();
  const ATTRIBUTES = ["aria-label", "alt", "title", "placeholder"];
  function apply(root = document.body) {
    const skip = "script, style, svg, [translate='no'], [data-i18n-html]";
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => (!node.nodeValue.trim() || !node.parentElement || node.parentElement.closest(skip)
        ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (!originalText.has(node)) originalText.set(node, node.nodeValue);
      const original = originalText.get(node);
      const key = normalize(original);
      if (has(key)) node.nodeValue = original.match(/^\s*/)[0] + look(key) + original.match(/\s*$/)[0];
    }
    for (const element of root.querySelectorAll(ATTRIBUTES.map((a) => `[${a}]`).join(","))) {
      if (element.closest("[translate='no']")) continue;
      const originals = originalAttrs.get(element) || {};
      for (const name of ATTRIBUTES) {
        if (!element.hasAttribute(name)) continue;
        if (!(name in originals)) originals[name] = element.getAttribute(name);
        const key = normalize(originals[name]);
        if (has(key)) element.setAttribute(name, look(key));
      }
      originalAttrs.set(element, originals);
    }
    for (const element of root.querySelectorAll("[data-i18n-html]")) {
      if (!element.dataset.i18nKey) element.dataset.i18nKey = normalize(element.innerHTML);
      if (has(element.dataset.i18nKey)) element.innerHTML = look(element.dataset.i18nKey);
    }
    if (!document.documentElement.dataset.titleKey) document.documentElement.dataset.titleKey = document.title;
    document.title = t(document.documentElement.dataset.titleKey);
  }

  // The language menu in the page header.
  function mountMenu() {
    const menu = document.getElementById("site-language");
    if (!menu) return;
    for (const [code, name] of LANGUAGES) menu.append(new Option(name, code));
    menu.value = lang;
    for (const short of document.querySelectorAll(".site-language-short")) short.textContent = SHORT[lang] || lang.toUpperCase();
    menu.addEventListener("change", () => {
      try { localStorage.setItem(STORE, menu.value); } catch { /* the choice lasts for this page only */ }
      location.reload();
    });
  }

  const ready = (async () => {
    document.documentElement.lang = lang;
    document.documentElement.dir = RIGHT_TO_LEFT.has(lang) ? "rtl" : "ltr";
    if (lang !== "en" || pseudo) {
      try {
        const response = lang === "en" ? null : await fetch(`/static/i18n/${lang}.json`);
        if (response && response.ok) table = await response.json();
      } catch { /* no translation file: the page stays in English */ }
      apply();
    }
    mountMenu();
    document.documentElement.classList.remove("i18n-pending");
  })();

  // Marks a phrase for translation where it's defined but translated later, with t(), when shown.
  const phrase = (key) => key;

  return { lang, t, phrase, languageName, apply, ready, rightToLeft: RIGHT_TO_LEFT.has(lang) };
})();
