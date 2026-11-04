"""Add client_request_id to requests for submission idempotency

Revision ID: e14a87c9b012
Revises: 5c8e1a7b93f2
Create Date: 2026-11-04 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e14a87c9b012'
down_revision: Union[str, None] = '5c8e1a7b93f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_request_id', sa.String(length=64), nullable=True))
        batch_op.create_index('ix_requests_user_client_id', ['user_id', 'client_request_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('requests', schema=None) as batch_op:
        batch_op.drop_index('ix_requests_user_client_id')
        batch_op.drop_column('client_request_id')
