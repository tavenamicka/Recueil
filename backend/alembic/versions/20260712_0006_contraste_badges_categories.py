"""corrige le contraste des badges Facebook et Achats/Matériel (WCAG AA)

Revision ID: 20260712_0006
Revises: 20260711_0005
Create Date: 2026-07-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260712_0006"
down_revision: Union[str, None] = "20260711_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (nom, ancienne couleur, nouvelle couleur)
COLOR_FIXES = [
    ("Réseaux sociaux - Facebook", "#1877F2", "#0D6AE4"),
    ("Achats / Matériel", "#B7791F", "#98651A"),
]

categories_table = sa.table(
    "categories",
    sa.column("nom", sa.String),
    sa.column("couleur", sa.String),
)


def upgrade() -> None:
    for nom, _old, new in COLOR_FIXES:
        op.execute(categories_table.update().where(categories_table.c.nom == nom).values(couleur=new))


def downgrade() -> None:
    for nom, old, _new in COLOR_FIXES:
        op.execute(categories_table.update().where(categories_table.c.nom == nom).values(couleur=old))
