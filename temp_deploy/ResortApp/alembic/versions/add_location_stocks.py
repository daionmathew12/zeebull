"""Add location_stocks table

Revision ID: add_location_stocks
Revises: add_food_waste_support
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_location_stocks'
down_revision = 'add_food_waste_support'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('location_stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_stocks_id'), 'location_stocks', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_location_stocks_id'), table_name='location_stocks')
    op.drop_table('location_stocks')
