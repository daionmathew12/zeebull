"""Add destination_location_id to purchase_masters

Revision ID: add_purchase_location
Revises: efe701fa2888
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_purchase_location'
down_revision = 'efe701fa2888'
branch_labels = None
depends_on = None


def upgrade():
    # Add destination_location_id column to purchase_masters table
    op.add_column('purchase_masters', 
        sa.Column('destination_location_id', sa.Integer(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_purchase_masters_destination_location_id',
        'purchase_masters', 'locations',
        ['destination_location_id'], ['id']
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint(
        'fk_purchase_masters_destination_location_id',
        'purchase_masters',
        type_='foreignkey'
    )
    
    # Drop column
    op.drop_column('purchase_masters', 'destination_location_id')
