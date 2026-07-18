"""ajout de duree_secondes sur medias (video/audio)

Revision ID: 20260711_0005
Revises: 20260702_0004
Create Date: 2026-07-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260711_0005"
down_revision: Union[str, None] = "20260702_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("medias", sa.Column("duree_secondes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("medias", "duree_secondes")
