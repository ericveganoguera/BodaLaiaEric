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
import time

ALBUM_URL  = "https://photos.app.goo.gl/wxN7cD93BrcsvdSH6"
OUTPUT     = "fotos.json"
MIDA_GRAN  = "=w1920-h1440"
MIDA_THUMB = "=w600-h450"

# Màxim de scrolls per carregar totes les fotos (cada scroll ~2s)
MAX_SCROLLS = 30


def netejar_url(url: str) -> str | None:
    """Treu els paràmetres de mida d'una URL de Google Fotos."""
    # Treure tot a partir de = seguida de w, s, h o p (paràmetres de mida/crop)
    base = re.sub(r'=[wshpc][^"&\s,\]]*', '', url).rstrip('=')
    # Filtrar URLs massa curtes (icones, avatars...)
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

        # Esperar que apareguin les primeres fotos
        try:
            page.wait_for_selector(
                'img[src*="lh3.googleusercontent.com"]',
                timeout=20_000,
            )
        except PWTimeout:
            print("  AVÍS: No han aparegut imatges en 20s. Provant igualment...")

        # Scroll per carregar totes les fotos (lazy loading)
        print("  Fent scroll per carregar totes les fotos...")
        prev_count = 0
        for i in range(MAX_SCROLLS):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1_800)

            count = page.evaluate("""
                () => document.querySelectorAll('img[src*="lh3.googleusercontent.com"]').length
            """)
            print(f"    Scroll {i+1}: {count} imatges trobades")

            if count > 0 and count == prev_count:
                # Dos scrolls consecutius sense canvis → hem carregat tot
                if i > 0:
                    break
            prev_count = count

        # Extreure totes les URLs
        srcs = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('img[src*="lh3.googleusercontent.com"]')
            ).map(img => img.src)
        """)

        print(f"  URLs brutes trobades: {len(srcs)}")

        # Netejar i deduplicar
        vistes = set()
        for src in srcs:
            base = netejar_url(src)
            if base and base not in vistes:
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
