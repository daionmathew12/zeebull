"""Add payment_method to purchase_masters table

This migration adds a payment_method column to track how purchases are paid
(Cash, Bank Transfer, UPI, Cheque, etc.)
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add payment_method column to purchase_masters table
    op.add_column('purchase_masters', 
        sa.Column('payment_method', sa.String(), nullable=True)
    )


def downgrade():
    # Remove payment_method column
    op.drop_column('purchase_masters', 'payment_method')
