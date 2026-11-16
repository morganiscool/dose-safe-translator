// Dose-Safe Translator landing page: section entrances, the bar's ink, and fitting the bar's parts.
// Everything is visible without this script; it only adds motion and the fit.
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Each section's parts arrive once, in reading order, 80 ms apart.
for (const section of document.querySelectorAll("main > section, footer")) {
  section.querySelectorAll(".reveal").forEach((el, i) => el.style.setProperty("--i", i));
}
const reveal = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      entry.target.classList.add("in");
      reveal.unobserve(entry.target);
    }
  }
}, { rootMargin: "0px 0px -12% 0px" });
document.querySelectorAll(".reveal").forEach((el) => reveal.observe(el));

// The bar takes the ink of the field underneath it.
const bar = document.getElementById("site-bar");
const fields = [...document.querySelectorAll("[data-ink]")].filter((el) => el !== bar);
function updateInk() {
  const probe = 36; // the middle of the bar
  for (const field of fields) {
    const box = field.getBoundingClientRect();
    if (box.top <= probe && box.bottom > probe) {
      // The hero is two fields: paper above its middle, carton blue below.
      const overBlue = field.classList.contains("hero") && probe > box.top + box.height / 2;
      bar.dataset.ink = overBlue ? "light" : field.dataset.ink;
      const ground = field.classList.contains("hero")
        ? field.querySelector(overBlue ? ".field-bottom" : ".field-top")
        : field;
      bar.style.setProperty("--bar-bg", getComputedStyle(ground).backgroundColor);
      return;
    }
  }
}
window.addEventListener("scroll", updateInk, { passive: true });
updateInk();

// The bar's parts each stay on one line. When they don't fit (a long translation, a narrow phone),
// the section links go first, then words may wrap, then the wordmark keeps only its mark.
function fitBar() {
  const steps = ["crowded", "cramped", "squeezed"];
  bar.classList.remove(...steps);
  // Every part inside the bar's padding (either side, so right-to-left too) and no taller than the bar.
  const fits = () => {
    const box = bar.getBoundingClientRect();
    const style = getComputedStyle(bar);
    const start = box.left + parseFloat(style.paddingLeft) - 1;
    const end = box.right - parseFloat(style.paddingRight) + 1;
    return [...bar.children].every((part) => {
      const r = part.getBoundingClientRect();
      return !r.width || (r.left >= start && r.right <= end && r.height <= bar.clientHeight);
    });
  };
  for (const step of steps) {
    if (fits()) return;
    bar.classList.add(step);
  }
}
new ResizeObserver(fitBar).observe(bar);
I18N.ready.then(fitBar);
if (document.fonts) document.fonts.ready.then(fitBar);

// People who ask for less motion get the still frame of each looping clip.
if (reduceMotion) {
  document.querySelectorAll("video[autoplay]").forEach((video) => {
    video.removeAttribute("autoplay");
    video.pause();
  });
}
