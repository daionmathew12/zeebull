"""Add food waste support

Revision ID: add_food_waste_support
Revises: add_purchase_location
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_food_waste_support'
down_revision = 'add_purchase_location'
branch_labels = None
depends_on = None


def upgrade():
    # Add food_item_id and is_food_item columns
    op.add_column('waste_logs', 
        sa.Column('food_item_id', sa.Integer(), nullable=True)
    )
    op.add_column('waste_logs', 
        sa.Column('is_food_item', sa.Boolean(), server_default='false', nullable=False)
    )
    
    # Make item_id nullable (since we can have either item_id OR food_item_id)
    op.alter_column('waste_logs', 'item_id', nullable=True)
    
    # Add foreign key for food_item_id
    op.create_foreign_key(
        'fk_waste_logs_food_item_id',
        'waste_logs', 'food_items',
        ['food_item_id'], ['id']
    )


def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_waste_logs_food_item_id', 'waste_logs', type_='foreignkey')
    
    # Drop columns
    op.drop_column('waste_logs', 'is_food_item')
    op.drop_column('waste_logs', 'food_item_id')
    
    # Make item_id required again
    op.alter_column('waste_logs', 'item_id', nullable=False)
