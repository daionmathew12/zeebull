"""Add rental and damage tracking to stock issue details

Revision ID: add_rental_damage_tracking
Revises: 
Create Date: 2025-12-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_rental_damage_tracking'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to stock_issue_details table
    op.add_column('stock_issue_details', sa.Column('rental_price', sa.Float(), nullable=True))
    op.add_column('stock_issue_details', sa.Column('is_damaged', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('stock_issue_details', sa.Column('damage_notes', sa.Text(), nullable=True))


def downgrade():
    # Remove columns if rolling back
    op.drop_column('stock_issue_details', 'damage_notes')
    op.drop_column('stock_issue_details', 'is_damaged')
    op.drop_column('stock_issue_details', 'rental_price')
