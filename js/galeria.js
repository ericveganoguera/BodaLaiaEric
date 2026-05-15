// ── CONFIGURACIÓ ─────────────────────────────────────────
const ALBUM_URL  = 'https://photos.app.goo.gl/wxN7cD93BrcsvdSH6';
const FOTOS_JSON = 'fotos.json';

// Patró de mides: cada posició N del grid rep una classe CSS.
// La seqüència es repeteix per crear ritme visual variat.
const SIZE_PATTERN = [
  'gran',  // 0 → 2×2
  'alt',   // 1 → 1×2
  '',      // 2 → 1×1
  '',      // 3 → 1×1
  'ample', // 4 → 2×1
  '',      // 5 → 1×1
  'alt',   // 6 → 1×2
  '',      // 7 → 1×1
  '',      // 8 → 1×1
  'ample', // 9 → 2×1
  '',      // 10 → 1×1
  '',      // 11 → 1×1
];

// ── ESTAT ────────────────────────────────────────────────
const grid = document.getElementById('galeria-grid');
let fotosVisibles = [];

// ── GALERIA ──────────────────────────────────────────────
async function carregarFotos() {
  try {
    const res = await fetch(FOTOS_JSON + '?v=' + Date.now());
    if (!res.ok) throw new Error("No s'ha pogut carregar fotos.json");
    const data = await res.json();

    if (!data.fotos || data.fotos.length === 0) {
      mostrarEstat('buit');
      return;
    }

    fotosVisibles = data.fotos;
    renderizarGaleria(fotosVisibles);
  } catch (e) {
    console.warn('Error carregant fotos.json:', e);
    mostrarEstat('error');
  }
}

function renderizarGaleria(fotos) {
  grid.innerHTML = '';

  fotos.forEach((foto, i) => {
    const sizeClass = SIZE_PATTERN[i % SIZE_PATTERN.length];

    const item = document.createElement('div');
    item.className = ['galeria-item', sizeClass].filter(Boolean).join(' ');
    item.dataset.index = i;

    const img = document.createElement('img');
    img.src     = foto.thumb || foto.url;
    img.alt     = foto.titol || `Foto ${i + 1}`;
    img.loading = 'lazy';
    img.decoding = 'async';

    img.addEventListener('load',  () => img.classList.add('loaded'));
    img.addEventListener('error', () => { img.style.display = 'none'; });

    item.addEventListener('click', () => obrirLightbox(i));
    item.appendChild(img);
    grid.appendChild(item);
  });
}

function mostrarEstat(tipus) {
  grid.innerHTML = '';

  const SVG_FOTO = `
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <circle cx="8.5" cy="8.5" r="1.5"/>
      <polyline points="21 15 16 10 5 21"/>
    </svg>`;

  const SVG_ERROR = `
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>`;

  const MISSATGES = {
    buit:  { svg: SVG_FOTO,  text: `Aviat hi hauran fotos aquí.<br>Mentrestant, pots veure l'àlbum a` },
    error: { svg: SVG_ERROR, text: `No s'han pogut carregar les fotos.<br>Pots veure l'àlbum directament a` },
  };

  const { svg, text } = MISSATGES[tipus] ?? MISSATGES.error;

  const div = document.createElement('div');
  div.className       = 'galeria-estat';
  div.style.gridColumn = '1 / -1';
  div.innerHTML = `
    ${svg}
    <p>${text}
      <a href="${ALBUM_URL}" target="_blank" rel="noopener">Google Fotos</a>.
    </p>`;

  grid.appendChild(div);
}

// ── LIGHTBOX ─────────────────────────────────────────────
const lightbox  = document.getElementById('lightbox');
const lbImg     = document.getElementById('lb-img');
const lbCounter = document.getElementById('lb-counter');
let indexActual = 0;

function obrirLightbox(index) {
  indexActual = index;
  actualitzarLightbox();
  lightbox.classList.add('actiu');
  document.body.style.overflow = 'hidden';
}

function tancarLightbox() {
  lightbox.classList.remove('actiu');
  document.body.style.overflow = '';
  lbImg.src = '';
}

function actualitzarLightbox() {
  const foto    = fotosVisibles[indexActual];
  lbImg.src     = foto.url;
  lbImg.alt     = foto.titol || `Foto ${indexActual + 1}`;
  lbCounter.textContent = `${indexActual + 1} / ${fotosVisibles.length}`;
}

function navegarLightbox(dir) {
  indexActual = (indexActual + dir + fotosVisibles.length) % fotosVisibles.length;
  actualitzarLightbox();
}

// Botons
document.getElementById('lb-tancar').addEventListener('click', tancarLightbox);
document.getElementById('lb-prev').addEventListener('click', () => navegarLightbox(-1));
document.getElementById('lb-next').addEventListener('click', () => navegarLightbox(1));

// Clic fora de la imatge
lightbox.addEventListener('click', e => {
  if (e.target === lightbox) tancarLightbox();
});

// Teclat
document.addEventListener('keydown', e => {
  if (!lightbox.classList.contains('actiu')) return;
  if (e.key === 'Escape')     tancarLightbox();
  if (e.key === 'ArrowLeft')  navegarLightbox(-1);
  if (e.key === 'ArrowRight') navegarLightbox(1);
});

// Swipe en mòbil
let touchStartX = 0;
lightbox.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
lightbox.addEventListener('touchend',   e => {
  const delta = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(delta) > 50) navegarLightbox(delta < 0 ? 1 : -1);
});

// ── INICI ────────────────────────────────────────────────
carregarFotos();
