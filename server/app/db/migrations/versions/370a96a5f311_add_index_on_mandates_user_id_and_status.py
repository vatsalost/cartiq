"""Add index on mandates user_id and status

Revision ID: 370a96a5f311
Revises: 0198d6a4c1bb
Create Date: 2026-11-03 23:37:25.318072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '370a96a5f311'
down_revision: Union[str, None] = '0198d6a4c1bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('mandates', schema=None) as batch_op:
        batch_op.create_index('ix_mandates_user_status', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('mandates', schema=None) as batch_op:
        batch_op.drop_index('ix_mandates_user_status')
