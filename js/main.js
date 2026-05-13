const root = document.documentElement;
const maxScroll = 180;
const maxOpacity = 0.75;
const maxBlur = 6;

function updateNavOpacity() {
  const progress = Math.min(window.scrollY / maxScroll, 1);

  root.style.setProperty("--nav-bg-opacity", (progress * maxOpacity).toFixed(2));
  root.style.setProperty("--nav-blur", `${(progress * maxBlur).toFixed(1)}px`);
}

updateNavOpacity();
window.addEventListener("scroll", updateNavOpacity, { passive: true });