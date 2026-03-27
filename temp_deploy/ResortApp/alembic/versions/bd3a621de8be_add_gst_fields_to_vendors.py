"""add_gst_fields_to_vendors

Revision ID: bd3a621de8be
Revises: 
Create Date: 2025-11-26 01:17:20.471421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bd3a621de8be'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add GST fields to vendors table."""
    # Add new GST and banking fields to vendors table
    op.add_column('vendors', sa.Column('company_name', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('gst_registration_type', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('legal_name', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('trade_name', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('qmp_scheme', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('vendors', sa.Column('msme_udyam_no', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('billing_address', sa.Text(), nullable=True))
    op.add_column('vendors', sa.Column('billing_state', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('shipping_address', sa.Text(), nullable=True))
    op.add_column('vendors', sa.Column('distance_km', sa.Float(), nullable=True))
    op.add_column('vendors', sa.Column('is_msme_registered', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('vendors', sa.Column('tds_apply', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('vendors', sa.Column('rcm_applicable', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('vendors', sa.Column('preferred_payment_method', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('account_holder_name', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('bank_name', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('account_number', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('ifsc_code', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('branch_name', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('upi_id', sa.String(), nullable=True))
    op.add_column('vendors', sa.Column('upi_mobile_number', sa.String(), nullable=True))
    
    # Add indexes
    op.create_index(op.f('ix_vendors_gst_number'), 'vendors', ['gst_number'], unique=False)
    op.create_index(op.f('ix_vendors_pan_number'), 'vendors', ['pan_number'], unique=False)
    op.create_index(op.f('ix_vendors_name'), 'vendors', ['name'], unique=False)
    
    # Set default for is_active if it doesn't have one
    op.alter_column('vendors', 'is_active',
                    existing_type=sa.Boolean(),
                    nullable=False,
                    server_default='true')


def downgrade() -> None:
    """Downgrade schema - Remove GST fields from vendors table."""
    # Drop indexes
    op.drop_index(op.f('ix_vendors_name'), table_name='vendors')
    op.drop_index(op.f('ix_vendors_pan_number'), table_name='vendors')
    op.drop_index(op.f('ix_vendors_gst_number'), table_name='vendors')
    
    # Drop columns
    op.drop_column('vendors', 'upi_mobile_number')
    op.drop_column('vendors', 'upi_id')
    op.drop_column('vendors', 'branch_name')
    op.drop_column('vendors', 'ifsc_code')
    op.drop_column('vendors', 'account_number')
    op.drop_column('vendors', 'bank_name')
    op.drop_column('vendors', 'account_holder_name')
    op.drop_column('vendors', 'preferred_payment_method')
    op.drop_column('vendors', 'rcm_applicable')
    op.drop_column('vendors', 'tds_apply')
    op.drop_column('vendors', 'is_msme_registered')
    op.drop_column('vendors', 'distance_km')
    op.drop_column('vendors', 'shipping_address')
    op.drop_column('vendors', 'billing_state')
    op.drop_column('vendors', 'billing_address')
    op.drop_column('vendors', 'msme_udyam_no')
    op.drop_column('vendors', 'qmp_scheme')
    op.drop_column('vendors', 'trade_name')
    op.drop_column('vendors', 'legal_name')
    op.drop_column('vendors', 'gst_registration_type')
    op.drop_column('vendors', 'company_name')
