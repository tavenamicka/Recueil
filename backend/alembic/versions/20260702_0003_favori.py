"""ajout de favori (bool) sur liens et medias

Revision ID: 20260702_0003
Revises: 20260702_0002
Create Date: 2026-07-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260702_0003"
down_revision: Union[str, None] = "20260702_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "liens", sa.Column("favori", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column(
        "medias", sa.Column("favori", sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    op.drop_column("medias", "favori")
    op.drop_column("liens", "favori")
