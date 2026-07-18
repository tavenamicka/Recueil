"""schéma initial — categories, liens, medias

Revision ID: 20260701_0001
Revises:
Create Date: 2026-07-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260701_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

media_type_enum = postgresql.ENUM("image", "video", "audio", name="media_type", create_type=False)

# Catégories par défaut (reprises du classement Excel existant, cf CONTEXT.md)
DEFAULT_CATEGORIES = [
    ("Réseaux sociaux - Facebook", "#0D6AE4"),
    ("Réseaux sociaux - Instagram", "#C13584"),
    ("Vidéos - YouTube", "#CC0000"),
    ("Pro / Tech / Carrière - LinkedIn", "#0A66C2"),
    ("Achats / Matériel", "#98651A"),
    ("Téléchargement / Jeux", "#6B21A8"),
    ("Santé / Sport", "#15803D"),
    ("Tech / Logiciels", "#1F4E78"),
    ("Maison / Bricolage", "#92400E"),
    ("Business / Marketing", "#B45309"),
    ("Sorties / Local", "#0E7490"),
    ("Autre", "#4B5563"),
    ("Images", "#BE185D"),
    ("Vidéos", "#7C2D12"),
    ("Audio", "#075985"),
]


def upgrade() -> None:
    media_type_enum.create(op.get_bind(), checkfirst=True)

    categories_table = op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("couleur", sa.String(length=7), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nom"),
    )

    op.create_table(
        "liens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("heure", sa.Time(), nullable=True),
        sa.Column("domaine", sa.String(length=255), nullable=True),
        sa.Column("titre_brut", sa.String(length=1000), nullable=True),
        sa.Column("titre_page", sa.String(length=1000), nullable=True),
        sa.Column("categorie_id", sa.Integer(), nullable=True),
        sa.Column("date_ajout", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["categorie_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(op.f("ix_liens_domaine"), "liens", ["domaine"])
    op.create_index(op.f("ix_liens_date"), "liens", ["date"])

    op.create_table(
        "medias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("type", media_type_enum, nullable=False),
        sa.Column("chemin_stockage", sa.String(length=1000), nullable=False),
        sa.Column("vignette_path", sa.String(length=1000), nullable=True),
        sa.Column("date_originale", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_upload", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("taille_octets", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.bulk_insert(
        categories_table,
        [{"nom": nom, "couleur": couleur} for nom, couleur in DEFAULT_CATEGORIES],
    )


def downgrade() -> None:
    op.drop_table("medias")
    op.drop_index(op.f("ix_liens_date"), table_name="liens")
    op.drop_index(op.f("ix_liens_domaine"), table_name="liens")
    op.drop_table("liens")
    op.drop_table("categories")
    media_type_enum.drop(op.get_bind(), checkfirst=True)
