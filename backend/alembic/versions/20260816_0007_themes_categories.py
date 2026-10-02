"""remplace les catégories par plateforme d'origine par des catégories thématiques

Revision ID: 20260816_0007
Revises: 20260712_0006
Create Date: 2026-08-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260816_0007"
down_revision: Union[str, None] = "20260712_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 11 thèmes de contenu (remplacent les catégories par plateforme d'origine — Facebook/
# Instagram/YouTube ne disent rien du sujet traité). "Autre" existe déjà
# et n'a pas besoin d'être réinséré. "Images"/"Vidéos"/"Audio" sont des pseudo-catégories
# utilisées par le frontend (useCatalog.js/MEDIA_CATEGORY_TYPE) pour les onglets médias
# par type — elles ne classent aucun lien et restent inchangées ici.
NEW_THEMES = [
    ("Technologie / IA", "#1F4E78"),
    ("Cuisine / Recettes", "#C2410C"),
    ("Bricolage / Jardinage", "#92400E"),
    ("Dessin / Créativité manuelle", "#A21CAF"),
    ("Sport / Santé / Bien-être", "#15803D"),
    ("Musique", "#6D28D9"),
    ("Sciences / Curiosités", "#0E7490"),
    ("Achats / Bons plans", "#98651A"),
    ("Business / Marketing / Carrière", "#0A66C2"),
    ("Langues / Apprentissage", "#4338CA"),
    ("Humour / Divertissement", "#BE123C"),
]

# Anciennes catégories par plateforme : jamais utilisées par les médias (categorie_id
# n'existe pas sur `medias`), donc sans risque une fois tous les liens repointés.
OLD_PLATFORM_CATEGORIES = [
    "Réseaux sociaux - Facebook",
    "Réseaux sociaux - Instagram",
    "Vidéos - YouTube",
    "Pro / Tech / Carrière - LinkedIn",
    "Achats / Matériel",
    "Téléchargement / Jeux",
    "Santé / Sport",
    "Tech / Logiciels",
    "Maison / Bricolage",
    "Business / Marketing",
    "Sorties / Local",
]

categories_table = sa.table(
    "categories",
    sa.column("id", sa.Integer),
    sa.column("nom", sa.String),
    sa.column("couleur", sa.String),
)
liens_table = sa.table(
    "liens",
    sa.column("id", sa.Integer),
    sa.column("domaine", sa.String),
    sa.column("titre_page", sa.String),
    sa.column("titre_brut", sa.String),
    sa.column("categorie_id", sa.Integer),
)


def upgrade() -> None:
    # Import différé : le module applicatif n'est disponible qu'une fois `app` sur le path
    # (déjà le cas ici, cf. alembic/env.py), et on veut la même logique que l'app en prod,
    # pas une copie qui pourrait diverger.
    from app.services.whatsapp_link_extractor import categorize

    bind = op.get_bind()

    existing = {
        row.nom: row.id for row in bind.execute(sa.select(categories_table.c.nom, categories_table.c.id))
    }
    for nom, couleur in NEW_THEMES:
        if nom not in existing:
            new_id = bind.execute(
                categories_table.insert().values(nom=nom, couleur=couleur).returning(categories_table.c.id)
            ).scalar_one()
            existing[nom] = new_id

    # Recatégorise chaque lien existant avec la nouvelle logique thématique, plutôt que de
    # renommer les anciennes lignes en bloc : "Réseaux sociaux - Facebook" mélangeait des
    # dizaines de thèmes différents (cuisine, bricolage, sport...), il faut réanalyser
    # titre par titre.
    rows = bind.execute(
        sa.select(liens_table.c.id, liens_table.c.domaine, liens_table.c.titre_page, liens_table.c.titre_brut)
    ).fetchall()
    for lien_id, domaine, titre_page, titre_brut in rows:
        nom = categorize(domaine or "", titre_page or titre_brut or "")
        categorie_id = existing.get(nom)
        if categorie_id is None:
            categorie_id = bind.execute(
                categories_table.insert().values(nom=nom, couleur="#4B5563").returning(categories_table.c.id)
            ).scalar_one()
            existing[nom] = categorie_id
        bind.execute(liens_table.update().where(liens_table.c.id == lien_id).values(categorie_id=categorie_id))

    bind.execute(
        categories_table.delete().where(
            categories_table.c.nom.in_(OLD_PLATFORM_CATEGORIES),
            ~sa.exists().where(liens_table.c.categorie_id == categories_table.c.id),
        )
    )


def downgrade() -> None:
    # Best-effort : recrée les catégories par plateforme si absentes, mais l'affectation
    # d'origine par lien est perdue (les liens gardent leur thème, ils ne sont pas
    # re-répartis par plateforme) — cette migration n'est pas destinée à être annulée
    # une fois en production.
    bind = op.get_bind()
    old_colors = {
        "Réseaux sociaux - Facebook": "#0D6AE4",
        "Réseaux sociaux - Instagram": "#C13584",
        "Vidéos - YouTube": "#CC0000",
        "Pro / Tech / Carrière - LinkedIn": "#0A66C2",
        "Achats / Matériel": "#98651A",
        "Téléchargement / Jeux": "#6B21A8",
        "Santé / Sport": "#15803D",
        "Tech / Logiciels": "#1F4E78",
        "Maison / Bricolage": "#92400E",
        "Business / Marketing": "#B45309",
        "Sorties / Local": "#0E7490",
    }
    existing_noms = {row.nom for row in bind.execute(sa.select(categories_table.c.nom))}
    for nom, couleur in old_colors.items():
        if nom not in existing_noms:
            bind.execute(categories_table.insert().values(nom=nom, couleur=couleur))

    bind.execute(
        categories_table.delete().where(
            categories_table.c.nom.in_([nom for nom, _ in NEW_THEMES]),
            ~sa.exists().where(liens_table.c.categorie_id == categories_table.c.id),
        )
    )
