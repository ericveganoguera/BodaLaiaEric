#!/usr/bin/env python3
"""
fetch-photos.py
Obté les URLs de les fotos d'un àlbum compartit de Google Fotos
i genera el fitxer fotos.json que llegeix la galeria web.

Ús:
    python scripts/fetch-photos.py           # normal
    python scripts/fetch-photos.py --debug   # desa el HTML per inspecció
"""

import re
import json
import sys
import time
import requests

# ── CONFIGURACIÓ ──────────────────────────────────────────────────────────────
ALBUM_URL  = "https://photos.app.goo.gl/wxN7cD93BrcsvdSH6"
OUTPUT     = "fotos.json"
DEBUG_HTML = "debug_album.html"   # només es crea amb --debug

MIDA_GRAN  = "=w1920-h1440"
MIDA_THUMB = "=w600-h450"
# ─────────────────────────────────────────────────────────────────────────────

DEBUG = "--debug" in sys.argv

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ca,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Tots els patrons coneguts de Google Fotos, del més específic al més general
PATRONS = [
    # Fotos personals d'usuari (format més comú en àlbums compartits)
    r'"(https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_\-]+)',
    # Sense cometes inicials
    r'(https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_\-]+)',
    # Format alternatiu sense /pw/
    r'"(https://lh3\.googleusercontent\.com/[A-Za-z0-9_\-]{60,})',
    # Format amb path addicional
    r'(https://lh3\.googleusercontent\.com/[A-Za-z0-9/_\-]{60,})',
]


def fetch_html(url: str, retries: int = 3) -> tuple[str, str]:
    """Retorna (html, url_final) seguint redireccions."""
    session = requests.Session()
    session.headers.update(HEADERS)

    for intent in range(retries):
        try:
            resp = session.get(url, allow_redirects=True, timeout=30)
            resp.raise_for_status()
            return resp.text, resp.url
        except requests.RequestException as e:
            print(f"  Intent {intent + 1}/{retries} fallat: {e}")
            if intent < retries - 1:
                time.sleep(3)

    raise RuntimeError(f"No s'ha pogut descarregar: {url}")


def extract_photo_urls(html: str) -> list[dict]:
    """Prova cada patró fins trobar URLs de fotos."""
    for i, patro in enumerate(PATRONS):
        matches = re.findall(patro, html)
        print(f"  Patró {i+1}: {len(matches)} coincidències")

        if not matches:
            continue

        # Netejar i deduplicar
        vists = set()
        fotos = []
        for url_base in matches:
            # Treure paràmetres de mida existents
            url_neta = re.sub(r'=[sw][^"&\s,\]]*', '', url_base).rstrip('=')
            # Filtrar URLs massa curtes (probablement icones o avatars)
            if len(url_neta) < 60:
                continue
            if url_neta in vists:
                continue
            vists.add(url_neta)
            fotos.append({
                "url":   url_neta + MIDA_GRAN,
                "thumb": url_neta + MIDA_THUMB,
            })

        if fotos:
            print(f"  → Usant patró {i+1}: {len(fotos)} fotos úniques trobades.")
            return fotos

    return []


def debug_info(html: str) -> None:
    """Imprimeix informació de diagnòstic i desa el HTML."""
    print("\n── DEBUG ────────────────────────────────────────────")
    print(f"  Longitud HTML: {len(html):,} caràcters")

    # Cercar qualsevol menció de lh3.googleusercontent.com
    mencions = re.findall(r'lh3\.googleusercontent\.com[^\s"\'<]{0,80}', html)
    print(f"  Mencions de lh3.googleusercontent.com: {len(mencions)}")
    for m in mencions[:5]:
        print(f"    {m[:100]}")

    # Cercar AF_initDataCallback
    callbacks = re.findall(r'AF_initDataCallback\(\{key:\s*[\'"]([^\'"]+)', html)
    print(f"  AF_initDataCallback keys: {callbacks[:10]}")

    # Guardar HTML per inspecció manual
    with open(DEBUG_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML desat a: {DEBUG_HTML}")
    print("─────────────────────────────────────────────────────\n")


def save_json(fotos: list[dict], path: str) -> None:
    data = {
        "album": ALBUM_URL,
        "total": len(fotos),
        "fotos": fotos,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Desat a {path} ({len(fotos)} fotos)")


def main() -> int:
    print(f"Obtenint fotos de: {ALBUM_URL}")

    try:
        html, url_final = fetch_html(ALBUM_URL)
        print(f"  URL final: {url_final}")
        print(f"  HTML rebut: {len(html):,} caràcters")
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if DEBUG:
        debug_info(html)

    print("Extraient URLs de fotos...")
    fotos = extract_photo_urls(html)

    if not fotos:
        print("\nAVÍS: No s'han trobat fotos.", file=sys.stderr)
        print("Executa amb --debug per inspeccionar el HTML:", file=sys.stderr)
        print("  python scripts/fetch-photos.py --debug", file=sys.stderr)

        # Imprimir fragment del HTML per diagnòstic ràpid
        print("\n── Primer fragment del HTML (500 chars) ──")
        print(html[:500])
        print("\n── Fragment amb 'lh3' (si n'hi ha) ──")
        idx = html.find('lh3')
        if idx >= 0:
            print(html[max(0, idx-50):idx+200])
        else:
            print("  'lh3' no trobat al HTML")

        save_json([], OUTPUT)
        return 0

    print(f"Trobades {len(fotos)} fotos.")
    save_json(fotos, OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
