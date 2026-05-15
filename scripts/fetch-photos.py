#!/usr/bin/env python3
"""
fetch-photos.py
Usa Playwright (Chromium headless) per obtenir les fotos d'un àlbum
compartit de Google Fotos i genera fotos.json per a la galeria web.

Requeriments:
    pip install playwright
    playwright install chromium
    playwright install-deps chromium
"""

import re
import json
import sys

# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  CANVIA AQUESTA URL per la URL real de l'àlbum (photos.google.com/share/...)
#    Com obtenir-la:
#      1. Obre https://photos.app.goo.gl/wxN7cD93BrcsvdSH6 al teu navegador
#      2. Quan carregui l'àlbum, copia la URL de la barra d'adreces
#      3. Enganxa-la aquí (ha de començar per https://photos.google.com/share/)
# ─────────────────────────────────────────────────────────────────────────────
ALBUM_URL = "https://photos.google.com/u/1/share/AF1QipMulBwGDXxbVg5fkktqWZR8Jxb7vN4mgmU8hFFlSLTmRorDDzyouQIb_mum5tb17A?key=TnNQaGtvU3hZTTFIZWp5ZURPaEhMT09QMURzeTlR"

OUTPUT     = "fotos.json"
MIDA_GRAN  = "=w1920-h1440"
MIDA_THUMB = "=w600-h450"
MAX_SCROLLS = 40


def netejar_url(url: str) -> str | None:
    base = re.sub(r'=[wshpc][^"&\s,\]]*', '', url).rstrip('=')
    return base if len(base) > 60 else None


def fetch_photos_playwright() -> list[dict]:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    fotos = []

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
        page.goto(ALBUM_URL, wait_until="domcontentloaded", timeout=45_000)
        print(f"  URL final: {page.url}")

        # Esperar que apareguin les miniatures de les fotos de l'àlbum.
        # Google Fotos usa l'atribut aria-label a les fotos de l'àlbum.
        try:
            page.wait_for_selector(
                'div[data-latest-bg*="lh3.googleusercontent"], '
                'img[src*="lh3.googleusercontent.com/pw"], '
                '[style*="lh3.googleusercontent"]',
                timeout=20_000,
            )
            print("  Contingut de l'àlbum detectat.")
        except PWTimeout:
            print("  AVÍS: Selector principal no trobat, continuant igualment...")

        # Scroll per activar el lazy loading de totes les fotos
        print("  Fent scroll per carregar totes les fotos...")
        prev_count = 0
        scrolls_sense_canvi = 0

        for i in range(MAX_SCROLLS):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2_000)

            # Comptar elements que contenen URLs de fotos (incl. backgrounds CSS)
            count = page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img[src*="lh3.googleusercontent.com"]');
                    const divs = document.querySelectorAll('[data-latest-bg*="lh3.googleusercontent"]');
                    return imgs.length + divs.length;
                }
            """)
            print(f"    Scroll {i+1}: {count} elements trobats")

            if count == prev_count:
                scrolls_sense_canvi += 1
                if scrolls_sense_canvi >= 2:
                    print("  Dues pàgines sense canvis — àlbum complet carregat.")
                    break
            else:
                scrolls_sense_canvi = 0

            prev_count = count

        # Extreure URLs: tant de <img src="..."> com de style="background-url(...)"
        srcs = page.evaluate("""
            () => {
                const urls = new Set();

                // Imatges directes
                document.querySelectorAll('img[src*="lh3.googleusercontent.com"]')
                    .forEach(img => urls.add(img.src));

                // Backgrounds amb data-latest-bg
                document.querySelectorAll('[data-latest-bg*="lh3.googleusercontent"]')
                    .forEach(el => urls.add(el.dataset.latestBg));

                // Backgrounds en atribut style
                document.querySelectorAll('[style*="lh3.googleusercontent"]')
                    .forEach(el => {
                        const m = el.getAttribute('style').match(/url\\(["']?(https:\\/\\/lh3\\.googleusercontent\\.com[^"')]+)/);
                        if (m) urls.add(m[1]);
                    });

                return [...urls];
            }
        """)

        print(f"  URLs brutes trobades: {len(srcs)}")

        # Netejar i deduplicar
        vistes = set()
        for src in srcs:
            base = netejar_url(src)
            if base and base not in vistes:
                # Filtrar avatar/foto de perfil (path /a/ en comptes de /pw/)
                if "/a/ACg8" in base or "/a/ACg" in base:
                    continue
                vistes.add(base)
                fotos.append({
                    "url":   base + MIDA_GRAN,
                    "thumb": base + MIDA_THUMB,
                })

        browser.close()

    return fotos


def save_json(fotos: list[dict]) -> None:
    data = {"album": ALBUM_URL, "total": len(fotos), "fotos": fotos}
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Desat {OUTPUT} amb {len(fotos)} fotos.")


def main() -> int:
    if "POSA_AQUI_LA_URL_REAL" in ALBUM_URL:
        print("ERROR: Actualitza la variable ALBUM_URL amb la URL real de l'àlbum.", file=sys.stderr)
        print("  Llegeix les instruccions al principi del fitxer.", file=sys.stderr)
        return 1

    print(f"Obtenint fotos de: {ALBUM_URL}")
    try:
        fotos = fetch_photos_playwright()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        save_json([])
        return 1

    if not fotos:
        print("AVÍS: No s'han trobat fotos.", file=sys.stderr)
        save_json([])
        return 0

    print(f"Total fotos úniques: {len(fotos)}")
    save_json(fotos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
