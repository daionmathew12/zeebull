"""Add quantity to asset_mappings

Revision ID: 36eae1f7b666
Revises: add_food_timing
Create Date: 2025-12-09 19:43:14.952016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '36eae1f7b666'
down_revision: Union[str, Sequence[str], None] = 'add_food_timing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('asset_mappings', sa.Column('quantity', sa.Float(), nullable=False, server_default='1.0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('asset_mappings', 'quantity')
