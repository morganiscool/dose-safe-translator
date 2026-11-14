// Dose-Safe Translator landing page: section entrances and the bar's ink. Everything is visible
// without this script; it only adds motion.
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

// People who ask for less motion get the still frame of each looping clip.
if (reduceMotion) {
  document.querySelectorAll("video[autoplay]").forEach((video) => {
    video.removeAttribute("autoplay");
    video.pause();
  });
}
