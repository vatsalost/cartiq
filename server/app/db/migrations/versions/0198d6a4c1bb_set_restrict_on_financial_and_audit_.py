"""Set RESTRICT on financial and audit foreign keys

Revision ID: 0198d6a4c1bb
Revises: 775b38b12bc4
Create Date: 2026-11-03 23:29:43.996667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0198d6a4c1bb'
down_revision: Union[str, None] = '775b38b12bc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint('audit_events_user_id_fkey', 'audit_events', type_='foreignkey')
        op.create_foreign_key('fk_audit_events_user_id', 'audit_events', 'users', ['user_id'], ['id'], ondelete='RESTRICT')
        op.drop_constraint('orders_user_id_fkey', 'orders', type_='foreignkey')
        op.create_foreign_key('fk_orders_user_id', 'orders', 'users', ['user_id'], ['id'], ondelete='RESTRICT')
        op.drop_constraint('refunds_order_id_fkey', 'refunds', type_='foreignkey')
        op.create_foreign_key('fk_refunds_order_id', 'refunds', 'orders', ['order_id'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint('fk_refunds_order_id', 'refunds', type_='foreignkey')
        op.create_foreign_key('refunds_order_id_fkey', 'refunds', 'orders', ['order_id'], ['id'], ondelete='CASCADE')
        op.drop_constraint('fk_orders_user_id', 'orders', type_='foreignkey')
        op.create_foreign_key('orders_user_id_fkey', 'orders', 'users', ['user_id'], ['id'], ondelete='CASCADE')
        op.drop_constraint('fk_audit_events_user_id', 'audit_events', type_='foreignkey')
        op.create_foreign_key('audit_events_user_id_fkey', 'audit_events', 'users', ['user_id'], ['id'], ondelete='CASCADE')
