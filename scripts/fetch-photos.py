#!/usr/bin/env python3
"""
fetch-photos.py
Usa Playwright (Chromium headless) per obtenir les fotos d'un àlbum
compartit de Google Fotos i genera fotos.json per a la galeria web.

Com troba les fotos (es combinen les dues fonts):
  1. Dades inicials: l'HTML de l'àlbum ja porta la llista de fotos
     (URLs lh3.googleusercontent.com/pw/...). És la font principal.
  2. Scroll: Google Fotos només manté al DOM les miniatures visibles
     (llista virtualitzada), així que es recullen les URLs a CADA pas
     del scroll, no només al final. Serveix per a àlbums molt grans
     que no porten totes les fotos a les dades inicials.

Si alguna cosa falla o no es troba cap foto, NO es sobreescriu
fotos.json: la galeria continua mostrant les fotos que ja tenia.

Requeriments:
    pip install playwright
    playwright install chromium
    playwright install-deps chromium
"""

import json
import os
import re
import sys

ALBUM_URL = "https://photos.google.com/share/AF1QipMulBwGDXxbVg5fkktqWZR8Jxb7vN4mgmU8hFFlSLTmRorDDzyouQIb_mum5tb17A?key=TnNQaGtvU3hZTTFIZWp5ZURPaEhMT09QMURzeTlR"

OUTPUT     = "fotos.json"
MIDA_GRAN  = "=w1920-h1440"
MIDA_THUMB = "=w600-h450"
MAX_SCROLLS = 150          # límit de seguretat
SCROLLS_SENSE_NOVES = 4    # passos seguits sense fotos noves per donar-ho per acabat

# URL base d'una foto d'àlbum compartit (sense paràmetres de mida)
RE_FOTO = re.compile(r"https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_\-]{20,}")


def netejar_url(url: str) -> str | None:
    m = RE_FOTO.match(url.replace("\\/", "/"))
    return m.group(0) if m else None


def urls_del_dom(page) -> list[str]:
    """URLs de fotos presents ara mateix al DOM (img, data-latest-bg, style)."""
    return page.evaluate(r"""
        () => {
            const urls = [];
            document.querySelectorAll('img[src*="lh3.googleusercontent.com/pw/"]')
                .forEach(img => urls.push(img.src));
            document.querySelectorAll('[data-latest-bg*="lh3.googleusercontent.com/pw/"]')
                .forEach(el => urls.push(el.dataset.latestBg));
            document.querySelectorAll('[style*="lh3.googleusercontent.com/pw/"]')
                .forEach(el => {
                    const m = el.getAttribute('style').match(/https:\/\/lh3\.googleusercontent\.com\/pw\/[^"')\s]+/);
                    if (m) urls.push(m[0]);
                });
            return urls;
        }
    """)


def fetch_photos_playwright() -> list[str]:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    ordre: dict[str, None] = {}   # dict = conjunt que conserva l'ordre de l'àlbum

    def afegir(urls) -> int:
        noves = 0
        for u in urls:
            base = netejar_url(u)
            if base and base not in ordre:
                ordre[base] = None
                noves += 1
        return noves

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ca-ES",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print(f"  Obrint: {ALBUM_URL}")
        page.goto(ALBUM_URL, wait_until="domcontentloaded", timeout=60_000)
        print(f"  URL final: {page.url}")

        try:
            page.wait_for_selector(
                '[data-latest-bg*="lh3.googleusercontent.com/pw/"], '
                'img[src*="lh3.googleusercontent.com/pw/"], '
                '[style*="lh3.googleusercontent.com/pw/"]',
                timeout=30_000,
            )
            print("  Contingut de l'àlbum detectat.")
        except PWTimeout:
            print("  AVÍS: no s'han vist miniatures; es continua amb les dades inicials.")

        # 1) Dades inicials de la pàgina
        inicials = afegir(RE_FOTO.findall(page.content().replace("\\/", "/")))
        print(f"  Fotos a les dades inicials: {inicials}")

        # 2) Scroll recollint a cada pas. La roda del ratolí fa scroll del
        #    contenidor que hi ha sota el cursor (Google Fotos no fa scroll
        #    de la finestra, sinó d'un contenidor intern).
        page.mouse.move(640, 500)
        sense_noves = 0
        for i in range(MAX_SCROLLS):
            noves = afegir(urls_del_dom(page))
            page.mouse.wheel(0, 1500)
            page.keyboard.press("PageDown")
            page.wait_for_timeout(1_200)
            noves += afegir(urls_del_dom(page))
            print(f"    Scroll {i + 1}: +{noves} (total {len(ordre)})")
            sense_noves = 0 if noves else sense_noves + 1
            if sense_noves >= SCROLLS_SENSE_NOVES:
                print("  Sense fotos noves en diversos passos: àlbum complet.")
                break

        # Per si l'àlbum en té més que les dades inicials, tornar a llegir l'HTML
        afegir(RE_FOTO.findall(page.content().replace("\\/", "/")))
        browser.close()

    print(f"  Fotos úniques trobades: {len(ordre)}")
    return list(ordre)


def total_actual() -> int:
    try:
        with open(OUTPUT, encoding="utf-8") as f:
            return int(json.load(f).get("total", 0))
    except (OSError, ValueError):
        return 0


def save_json(bases: list[str]) -> None:
    fotos = [{"url": b + MIDA_GRAN, "thumb": b + MIDA_THUMB} for b in bases]
    data = {"album": ALBUM_URL, "total": len(fotos), "fotos": fotos}
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Desat {OUTPUT} amb {len(fotos)} fotos.")


def main() -> int:
    print(f"Obtenint fotos de: {ALBUM_URL}")
    abans = total_actual()
    try:
        bases = fetch_photos_playwright()
    except Exception as e:
        print(f"ERROR: {e}. No es modifica {OUTPUT} ({abans} fotos).", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 1

    if not bases:
        print(f"AVÍS: no s'ha trobat cap foto. No es modifica {OUTPUT} ({abans} fotos).", file=sys.stderr)
        return 1

    if abans and len(bases) < abans * 0.5 and not os.environ.get("FORCAR"):
        print(f"AVÍS: s'han trobat {len(bases)} fotos i abans n'hi havia {abans}. "
              f"Sembla un error de lectura; no es modifica {OUTPUT}. "
              f"(Executa amb FORCAR=1 si l'àlbum s'ha reduït de debò.)", file=sys.stderr)
        return 1

    save_json(bases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
