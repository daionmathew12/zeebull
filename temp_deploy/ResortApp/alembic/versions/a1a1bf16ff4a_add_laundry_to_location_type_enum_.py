"""Add Laundry to location_type enum manually

Revision ID: a1a1bf16ff4a
Revises: 36eae1f7b666
Create Date: 2025-12-11 00:53:03.430860

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1a1bf16ff4a'
down_revision: Union[str, Sequence[str], None] = '36eae1f7b666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE locationtype ADD VALUE IF NOT EXISTS 'LAUNDRY'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
