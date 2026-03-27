"""
Add package additional fields

Revision ID: add_package_fields
Revises: 
Create Date: 2025-12-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_package_fields'
down_revision = 'add_location_stocks'  # Point to the existing head
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to packages table
    op.add_column('packages', sa.Column('theme', sa.String(), nullable=True))
    op.add_column('packages', sa.Column('default_adults', sa.Integer(), nullable=True, server_default='2'))
    op.add_column('packages', sa.Column('default_children', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('packages', sa.Column('max_stay_days', sa.Integer(), nullable=True))
    op.add_column('packages', sa.Column('food_included', sa.String(), nullable=True))  # JSON string or comma-separated


def downgrade():
    # Remove columns if we need to rollback
    op.drop_column('packages', 'food_included')
    op.drop_column('packages', 'max_stay_days')
    op.drop_column('packages', 'default_children')
    op.drop_column('packages', 'default_adults')
    op.drop_column('packages', 'theme')
