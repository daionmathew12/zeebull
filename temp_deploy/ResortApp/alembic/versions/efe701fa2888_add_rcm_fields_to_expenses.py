"""add_rcm_fields_to_expenses

Revision ID: efe701fa2888
Revises: add_rcm_expenses
Create Date: 2025-11-29 03:01:35.003781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efe701fa2888'
down_revision: Union[str, Sequence[str], None] = 'bd3a621de8be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add RCM fields to expenses table."""
    # Add RCM (Reverse Charge Mechanism) fields to expenses table
    op.add_column('expenses', sa.Column('rcm_applicable', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('expenses', sa.Column('rcm_tax_rate', sa.Float(), nullable=True))
    op.add_column('expenses', sa.Column('nature_of_supply', sa.String(), nullable=True))
    op.add_column('expenses', sa.Column('original_bill_no', sa.String(), nullable=True))
    op.add_column('expenses', sa.Column('self_invoice_number', sa.String(), nullable=True))
    op.add_column('expenses', sa.Column('vendor_id', sa.Integer(), nullable=True))
    op.add_column('expenses', sa.Column('rcm_liability_date', sa.Date(), nullable=True))
    op.add_column('expenses', sa.Column('itc_eligible', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add foreign key constraint for vendor_id
    op.create_foreign_key(
        'fk_expenses_vendor_id',
        'expenses', 'vendors',
        ['vendor_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add index on self_invoice_number for uniqueness and performance
    op.create_index(op.f('ix_expenses_self_invoice_number'), 'expenses', ['self_invoice_number'], unique=True)


def downgrade() -> None:
    """Downgrade schema - Remove RCM fields from expenses table."""
    # Drop index
    op.drop_index(op.f('ix_expenses_self_invoice_number'), table_name='expenses')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_expenses_vendor_id', 'expenses', type_='foreignkey')
    
    # Drop columns
    op.drop_column('expenses', 'itc_eligible')
    op.drop_column('expenses', 'rcm_liability_date')
    op.drop_column('expenses', 'vendor_id')
    op.drop_column('expenses', 'self_invoice_number')
    op.drop_column('expenses', 'original_bill_no')
    op.drop_column('expenses', 'nature_of_supply')
    op.drop_column('expenses', 'rcm_tax_rate')
    op.drop_column('expenses', 'rcm_applicable')
