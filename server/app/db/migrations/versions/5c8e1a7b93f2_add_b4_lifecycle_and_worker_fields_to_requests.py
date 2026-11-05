"""Add B4 lifecycle, worker lease and retry fields to requests

Revision ID: 5c8e1a7b93f2
Revises: 370a96a5f311
Create Date: 2026-11-04 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c8e1a7b93f2'
down_revision: Union[str, None] = '370a96a5f311'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'))
        batch_op.add_column(sa.Column('locked_by', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('error_details', sa.JSON(), nullable=True))
        batch_op.create_index('ix_requests_status_locked', ['status', 'locked_until'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('requests', schema=None) as batch_op:
        batch_op.drop_index('ix_requests_status_locked')
        batch_op.drop_column('error_details')
        batch_op.drop_column('locked_until')
        batch_op.drop_column('locked_by')
        batch_op.drop_column('max_retries')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('processing_started_at')
