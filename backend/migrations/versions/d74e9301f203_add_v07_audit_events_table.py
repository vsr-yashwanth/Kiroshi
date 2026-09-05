"""add v07 audit events table

Revision ID: d74e9301f203
Revises: c63e8290f102
Create Date: 2026-09-05 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd74e9301f203'
down_revision: Union[str, None] = 'c63e8290f102'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sequence_number', sa.Integer(), nullable=False, unique=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_email', sa.String(255), nullable=True),
        sa.Column('actor_role', sa.String(50), nullable=True),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('outcome', sa.String(32), nullable=False, server_default='SUCCESS'),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('previous_hash', sa.String(64), nullable=False),
        sa.Column('event_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_audit_events_sequence_number', 'audit_events', ['sequence_number'])
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])
    op.create_index('ix_audit_events_actor_id', 'audit_events', ['actor_id'])
    op.create_index('ix_audit_events_resource_type', 'audit_events', ['resource_type'])
    op.create_index('ix_audit_events_resource_id', 'audit_events', ['resource_id'])
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_audit_events_created_at', table_name='audit_events')
    op.drop_index('ix_audit_events_resource_id', table_name='audit_events')
    op.drop_index('ix_audit_events_resource_type', table_name='audit_events')
    op.drop_index('ix_audit_events_actor_id', table_name='audit_events')
    op.drop_index('ix_audit_events_event_type', table_name='audit_events')
    op.drop_index('ix_audit_events_sequence_number', table_name='audit_events')
    op.drop_table('audit_events')
