#!/usr/bin/env python3
"""
fetch-photos.py
Obté les URLs de les fotos d'un àlbum compartit de Google Fotos
i genera el fitxer fotos.json que llegeix la galeria web.

Ús:
    python scripts/fetch-photos.py

Requeriments:
    pip install requests
"""

import re
import json
import sys
import time
import requests

# ── CONFIGURACIÓ ──────────────────────────────────────────────────────────────
ALBUM_URL  = "https://photos.app.goo.gl/wxN7cD93BrcsvdSH6"
OUTPUT     = "fotos.json"

# Mides de les URLs que es generaran
# Google Fotos accepta paràmetres com =w1920 (ample), =h1080 (alt), =w800-h600-c (crop)
MIDA_GRAN  = "=w1920-h1440"   # URL per al lightbox (alta resolució)
MIDA_THUMB = "=w600-h450"     # URL per a la miniatura de la grid
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ca,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_html(url: str, retries: int = 3) -> str:
    """Descarrega el contingut HTML d'una URL, seguint redireccions."""
    session = requests.Session()
    session.headers.update(HEADERS)

    for intent in range(retries):
        try:
            resp = session.get(url, allow_redirects=True, timeout=30)
            resp.raise_for_status()
            print(f"  URL final: {resp.url}")
            return resp.text
        except requests.RequestException as e:
            print(f"  Intent {intent + 1}/{retries} fallat: {e}")
            if intent < retries - 1:
                time.sleep(3)

    raise RuntimeError(f"No s'ha pogut descarregar: {url}")


def extract_photo_urls(html: str) -> list[dict]:
    """
    Extreu les URLs de fotos del codi HTML de l'àlbum de Google Fotos.

    Google Fotos incrusta les dades de les fotos en blocs de JavaScript
    com arrays amb URLs del tipus lh3.googleusercontent.com/pw/...
    
    El patró extreu la URL base sense paràmetres de mida,
    i després afegim els paràmetres que volem.
    """
    # Patró principal: URLs de fotos d'usuari a Google Fotos
    # Exemple: https://lh3.googleusercontent.com/pw/AP1GczN...
    PATRO_FOTO = re.compile(
        r'"(https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_\-]+)"'
    )

    # Patró alternatiu per si canvia el format
    PATRO_ALT = re.compile(
        r'(https://lh3\.googleusercontent\.com/pw/[A-Za-z0-9_\-]+)'
    )

    matches = PATRO_FOTO.findall(html)

    if not matches:
        print("  Patró principal sense resultats, provant patró alternatiu...")
        matches = PATRO_ALT.findall(html)

    # Eliminar duplicats mantenint l'ordre
    vists = set()
    fotos = []

    for url_base in matches:
        # Eliminar qualsevol paràmetre de mida existent (=w... o =s...)
        url_neta = re.sub(r'=[sw][^"&\s]*', '', url_base).rstrip('=')

        if url_neta in vists:
            continue
        vists.add(url_neta)

        fotos.append({
            "url":   url_neta + MIDA_GRAN,
            "thumb": url_neta + MIDA_THUMB,
        })

    return fotos


def save_json(fotos: list[dict], path: str) -> None:
    """Desa el llistat de fotos com a fitxer JSON."""
    data = {
        "album":  ALBUM_URL,
        "total":  len(fotos),
        "fotos":  fotos,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Desat a {path} ({len(fotos)} fotos)")


def main() -> int:
    print(f"Obtenint fotos de: {ALBUM_URL}")

    try:
        html = fetch_html(ALBUM_URL)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("Extraient URLs de fotos...")
    fotos = extract_photo_urls(html)

    if not fotos:
        print(
            "AVÍS: No s'han trobat fotos.\n"
            "  Pot ser que Google hagi canviat l'estructura del HTML.\n"
            "  Comprova manualment la pàgina de l'àlbum i actualitza el patró PATRO_FOTO.",
            file=sys.stderr,
        )
        # Desa un JSON buit per evitar errors a la web
        save_json([], OUTPUT)
        return 0

    print(f"Trobades {len(fotos)} fotos.")
    save_json(fotos, OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
