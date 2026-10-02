"""ajoute vignette_path sur liens (miniature de l'article)

Revision ID: 20260816_0008
Revises: 20260816_0007
Create Date: 2026-08-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260816_0008"
down_revision: Union[str, None] = "20260816_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("liens", sa.Column("vignette_path", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("liens", "vignette_path")
