"""titre_brut/titre_page en texte non borné (og:title peut dépasser 1000 caractères)

Revision ID: 20260702_0002
Revises: 20260701_0001
Create Date: 2026-07-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260702_0002"
down_revision: Union[str, None] = "20260701_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("liens", "titre_brut", type_=sa.Text(), existing_type=sa.String(length=1000))
    op.alter_column("liens", "titre_page", type_=sa.Text(), existing_type=sa.String(length=1000))


def downgrade() -> None:
    op.alter_column(
        "liens",
        "titre_page",
        type_=sa.String(length=1000),
        existing_type=sa.Text(),
        postgresql_using="substring(titre_page for 1000)",
    )
    op.alter_column(
        "liens",
        "titre_brut",
        type_=sa.String(length=1000),
        existing_type=sa.Text(),
        postgresql_using="substring(titre_brut for 1000)",
    )
