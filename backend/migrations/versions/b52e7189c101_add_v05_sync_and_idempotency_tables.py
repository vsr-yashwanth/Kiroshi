"""add_v05_sync_and_idempotency_tables

Revision ID: b52e7189c101
Revises: a41d9230e71b
Create Date: 2026-09-05 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b52e7189c101'
down_revision: str | None = 'a41d9230e71b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'sync_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column(
            'event_type',
            sa.Enum(
                'SOS_EVENT',
                'LOCATION_EVENT',
                'TRIP_UPDATE',
                'INCIDENT_ACTION',
                name='synceventtype',
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.Uuid(), nullable=True),
        sa.Column(
            'status',
            sa.Enum(
                'SYNCED',
                'DUPLICATE',
                'REJECTED',
                'CONFLICT',
                'ERROR',
                name='synceventstatus',
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('sync_records', schema=None) as batch_op:
        batch_op.create_index('ix_sync_records_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_sync_records_idempotency_key', ['idempotency_key'], unique=True)
        batch_op.create_index('ix_sync_records_event_type', ['event_type'], unique=False)
        batch_op.create_index('ix_sync_records_status', ['status'], unique=False)
        batch_op.create_index('ix_sync_records_user_created', ['user_id', 'created_at'], unique=False)
        batch_op.create_index('ix_sync_records_user_idempotency', ['user_id', 'idempotency_key'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('sync_records', schema=None) as batch_op:
        batch_op.drop_index('ix_sync_records_user_idempotency')
        batch_op.drop_index('ix_sync_records_user_created')
        batch_op.drop_index('ix_sync_records_status')
        batch_op.drop_index('ix_sync_records_event_type')
        batch_op.drop_index('ix_sync_records_idempotency_key')
        batch_op.drop_index('ix_sync_records_user_id')

    op.drop_table('sync_records')
