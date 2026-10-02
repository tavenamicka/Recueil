#!/usr/bin/env python3
"""
Extracteur de liens WhatsApp
---------------------------
Usage:
    python3 whatsapp_link_extractor.py /chemin/vers/export.txt

Ce script :
  1. Parse un export WhatsApp (.txt)
  2. Extrait tous les liens
  3. Va chercher le vrai titre de chaque page (une seule fois par URL, mis en cache en base)
  4. Classe automatiquement par catégorie
  5. Stocke tout dans liens.db (SQLite, dédupliqué)
  6. Exporte liens_classes.xlsx à jour

Dépendances : requests, beautifulsoup4, openpyxl
Installation :
    python3 -m venv venv
    source venv/bin/activate
    pip install requests beautifulsoup4 openpyxl
"""

import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

DB_PATH = Path(__file__).parent / "liens.db"
XLSX_PATH = Path(__file__).parent / "liens_classes.xlsx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
TIMEOUT = 8

ENTRY_RE = re.compile(r"^(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}) - mickael tavenart: (.*)$")
URL_RE = re.compile(r"(https?://\S+)")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS liens (
            url TEXT PRIMARY KEY,
            date TEXT,
            heure TEXT,
            domaine TEXT,
            titre_brut TEXT,
            titre_page TEXT,
            categorie TEXT,
            date_ajout TEXT
        )
    """)
    return conn


def fetch_title(url: str) -> str:
    """Récupère le titre réel de la page (suit les redirections, ex: share.google)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        # Sans charset explicite dans l'en-tête Content-Type, requests suppose ISO-8859-1
        # (RFC 2616) alors que la page est presque toujours en UTF-8 -> titres mojibake.
        if r.encoding is None or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip()
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:
        pass
    return ""


def fetch_og_image(url: str) -> str:
    """Récupère l'URL de l'image de prévisualisation (og:image) d'une page, si présente."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"].strip()
    except Exception:
        pass
    return ""


# Domaines dont le contenu est prévisible indépendamment du titre (contrairement à
# facebook.com/youtube.com/instagram.com/linkedin.com, qui hébergent n'importe quel
# thème selon qui poste — le feed LinkedIn de l'utilisateur est très majoritairement
# tech, pas "carrière/business").
_DOMAIN_THEMES = [
    ("amazon.", "Achats / Bons plans"),
    ("korben.info", "Technologie / IA"),
    ("numerama.com", "Technologie / IA"),
    ("clubic.com", "Technologie / IA"),
    ("justgeek", "Technologie / IA"),
    ("lesnumeriques.com", "Technologie / IA"),
    ("zdnet.fr", "Technologie / IA"),
    ("01net.com", "Technologie / IA"),
    ("romhustler", "Technologie / IA"),
]

# Ordre du plus spécifique au plus générique : le premier thème dont un mot-clé
# matche l'emporte, donc les thèmes "fourre-tout" (Technologie / IA en tête) sont
# vérifiés en dernier pour ne pas voler les titres plus spécifiques.
_THEME_KEYWORDS = [
    ("Musique", ["musique", "music", "chanson", "song", "guitare", "guitar", "piano",
                 "playlist", "techno", "trance", "chord", "accord", "violão", "violao"]),
    ("Cuisine / Recettes", ["recette", "recipe", "cuisine", "cuisiner", "cooking", "ingrédients",
                             "ingredients", "farine", "boulangerie", "gourmand", "nuggets", "burger"]),
    ("Dessin / Créativité manuelle", ["dessin", "dessiner", "doodle", "origami", "manga",
                                       "artwork", "drawing", "illustration", "coloriage"]),
    ("Sport / Santé / Bien-être", ["fitness", "musculation", "exercice", "exercices", "workout",
                                    "étirement", "etirement", "stretch", "sciatique", "sciatica",
                                    "back pain", "bien-être", "bien-etre", "wellness", "gym"]),
    ("Sciences / Curiosités", ["quantique", "quantum", "espace", "cosmos", "univers", "astronomie",
                                "physique", "insolite", "phénomène", "phenomene", "mystère", "mystere"]),
    ("Bricolage / Jardinage", ["jardin", "jardinage", "garden", "gardener", "cascade", "bricolage",
                                "brico", "terrasse", "pallet", "palette", "diy", "rénovation",
                                "renovation", "construction", "carpenter", "menuiserie"]),
    ("Langues / Apprentissage", ["anglais", "english", "apprendre", "apprentissage",
                                  "learn", "learning", "learnenglish", "learnfrench"]),
    ("Humour / Divertissement", ["humour", "humor", "drôle", "drole", "comique", "blague", "meme"]),
    ("Achats / Bons plans", ["bon plan", "bons plans", "promo", "réduction", "reduction", "gadget",
                              "amazonfinds"]),
    ("Business / Marketing / Carrière", ["marketing", "entreprise", "business", "site web",
                                          "startup", "carrière", "carriere"]),
    ("Technologie / IA", ["korben", "logiciel", "claude", "ia", "intelligence artificielle",
                           "deepclaude", "windows", "linux", "docker", "jellyfin", "plex", "beszel",
                           "self-hosting", "selfhosting", "homelab", "devops", "sysadmin", "réseau",
                           "reseau", "network", "networking", "vpn", "serveur", "server", "chatgpt",
                           "opensource", "open source", "code", "coding", "vibecoding", "développeur",
                           "developpeur"]),
]


def categorize(domain: str, title: str) -> str:
    t = title.lower()
    d = domain.lower()
    for needle, theme in _DOMAIN_THEMES:
        if needle in d:
            return theme
    for theme, keywords in _THEME_KEYWORDS:
        # "s?" final : tolère les pluriels simples (quantique/quantiques, recette/recettes)
        # sans avoir à lister chaque variante.
        if any(re.search(rf"\b{re.escape(kw)}s?\b", t) for kw in keywords):
            return theme
    return "Autre"


def parse_export(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    records = []
    for line in lines:
        m = ENTRY_RE.match(line)
        if not m:
            continue
        date, time, text = m.groups()
        urls = URL_RE.findall(text)
        for url in urls:
            url_clean = url.rstrip(")")
            title_brut = text.split(url)[0].strip(" -:\u200e")
            domain = urlparse(url_clean).netloc.replace("www.", "")
            records.append({"date": date, "time": time, "domain": domain,
                             "title_brut": title_brut, "url": url_clean})
    return records


def process(export_path: Path):
    conn = init_db()
    records = parse_export(export_path)
    nouveaux = 0
    for r in records:
        exists = conn.execute("SELECT 1 FROM liens WHERE url=?", (r["url"],)).fetchone()
        if exists:
            continue
        nouveaux += 1
        titre_page = r["title_brut"] or fetch_title(r["url"])
        categorie = categorize(r["domain"], titre_page or r["title_brut"])
        conn.execute(
            "INSERT INTO liens VALUES (?,?,?,?,?,?,?,?)",
            (r["url"], r["date"], r["time"], r["domain"], r["title_brut"],
             titre_page, categorie, datetime.now().isoformat()),
        )
        print(f"  + {r['domain']:25s} {titre_page[:60]}")
    conn.commit()
    print(f"\n{nouveaux} nouveaux liens ajoutés sur {len(records)} trouvés dans l'export.")
    export_xlsx(conn)
    conn.close()


def export_xlsx(conn):
    rows = conn.execute(
        "SELECT date, heure, categorie, COALESCE(NULLIF(titre_page,''), titre_brut), domaine, url "
        "FROM liens ORDER BY date DESC, heure DESC"
    ).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tous les liens"
    headers = ["Date", "Heure", "Catégorie", "Titre", "Domaine", "Lien"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF", name="Arial")
        cell.fill = PatternFill("solid", start_color="1F4E78")
        cell.alignment = Alignment(horizontal="center")
    for row in rows:
        ws.append(list(row))
    for i, w in enumerate([12, 8, 30, 55, 20, 55], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Arial", size=10)
        if str(row[5].value).startswith("http"):
            row[5].hyperlink = row[5].value
            row[5].font = Font(name="Arial", size=10, color="0563C1", underline="single")
    ws.freeze_panes = "A2"

    from collections import Counter
    cats = Counter(r[2] for r in rows)
    ws2 = wb.create_sheet("Résumé")
    ws2.append(["Catégorie", "Nombre de liens"])
    for cell in ws2[1]:
        cell.font = Font(bold=True, color="FFFFFF", name="Arial")
        cell.fill = PatternFill("solid", start_color="1F4E78")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        ws2.append([cat, count])
    ws2.column_dimensions["A"].width = 35
    ws2.column_dimensions["B"].width = 18

    wb.save(XLSX_PATH)
    print(f"Fichier exporté : {XLSX_PATH}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 whatsapp_link_extractor.py /chemin/vers/export.txt")
        sys.exit(1)
    process(Path(sys.argv[1]))
