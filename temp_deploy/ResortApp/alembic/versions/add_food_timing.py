"""Add food_timing to packages

Revision ID: add_food_timing
Revises: add_package_fields
Create Date: 2025-12-09 14:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_food_timing'
down_revision = 'add_package_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add food_timing column as JSON
    # We use String for SQLite compatibility if needed, but JSON/JSONB is better for Postgres
    # Let's use String to be safe and simple: '{"Breakfast": "08:00", "Lunch": "13:00"}'
    op.add_column('packages', sa.Column('food_timing', sa.String(), nullable=True))

def downgrade():
    op.drop_column('packages', 'food_timing')
