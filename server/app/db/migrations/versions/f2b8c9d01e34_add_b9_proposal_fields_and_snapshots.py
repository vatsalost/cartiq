"""Add B9 proposal fields, monetary totals, and immutable snapshots

Revision ID: f2b8c9d01e34
Revises: e14a87c9b012
Create Date: 2026-11-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b8c9d01e34'
down_revision: Union[str, None] = 'e14a87c9b012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('proposals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mandate_version', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('shipping_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        batch_op.add_column(sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        batch_op.add_column(sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        batch_op.add_column(sa.Column('product_snapshot', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('offer_snapshot', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('verification_status', sa.String(length=32), nullable=False, server_default='unverified'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index('ix_proposals_request_status', ['request_id', 'status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('proposals', schema=None) as batch_op:
        batch_op.drop_index('ix_proposals_request_status')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('verification_status')
        batch_op.drop_column('offer_snapshot')
        batch_op.drop_column('product_snapshot')
        batch_op.drop_column('total_amount')
        batch_op.drop_column('tax_amount')
        batch_op.drop_column('shipping_amount')
        batch_op.drop_column('mandate_version')
