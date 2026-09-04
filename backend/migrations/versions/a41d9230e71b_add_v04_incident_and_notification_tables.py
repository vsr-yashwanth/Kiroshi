"""add_v04_incident_and_notification_tables

Revision ID: a41d9230e71b
Revises: f2ae5b201aa7
Create Date: 2026-09-04 16:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a41d9230e71b'
down_revision: str | None = 'f2ae5b201aa7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Incidents table
    op.create_table(
        'incidents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('source', sa.Enum('SOS', 'RISK_ENGINE', 'AUTHORITY', 'SYSTEM', name='incidentsource', native_enum=False), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='incidentseverity', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('DETECTED', 'VERIFYING', 'VERIFIED', 'ESCALATED', 'ASSIGNED', 'RESPONDING', 'RESOLVED', 'CLOSED', 'DISMISSED', name='incidentstatus', native_enum=False), nullable=False),
        sa.Column('tourist_id', sa.Uuid(), nullable=False),
        sa.Column('trip_id', sa.Uuid(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('location_freshness', sa.Enum('LIVE', 'RECENT', 'STALE', 'UNKNOWN', name='locationfreshness', native_enum=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('risk_assessment_id', sa.Uuid(), nullable=True),
        sa.Column('assigned_responder_id', sa.Uuid(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tourist_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['risk_assessment_id'], ['risk_assessments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_responder_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.create_index('ix_incidents_source', ['source'], unique=False)
        batch_op.create_index('ix_incidents_severity', ['severity'], unique=False)
        batch_op.create_index('ix_incidents_status', ['status'], unique=False)
        batch_op.create_index('ix_incidents_tourist_id', ['tourist_id'], unique=False)
        batch_op.create_index('ix_incidents_trip_id', ['trip_id'], unique=False)
        batch_op.create_index('ix_incidents_assigned_responder_id', ['assigned_responder_id'], unique=False)
        batch_op.create_index('ix_incidents_idempotency_key', ['idempotency_key'], unique=True)
        batch_op.create_index('ix_incidents_status_created', ['status', 'created_at'], unique=False)
        batch_op.create_index('ix_incidents_tourist_created', ['tourist_id', 'created_at'], unique=False)
        batch_op.create_index('ix_incidents_assigned_status', ['assigned_responder_id', 'status'], unique=False)

    # 2. Incident Events table
    op.create_table(
        'incident_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('actor_role', sa.String(length=50), nullable=True),
        sa.Column('event_type', sa.Enum('INCIDENT_CREATED', 'STATUS_CHANGED', 'INCIDENT_VERIFIED', 'INCIDENT_ESCALATED', 'INCIDENT_ASSIGNED', 'RESPONSE_STARTED', 'INCIDENT_RESOLVED', 'INCIDENT_CLOSED', 'INCIDENT_DISMISSED', name='incidenteventtype', native_enum=False), nullable=False),
        sa.Column('from_status', sa.Enum('DETECTED', 'VERIFYING', 'VERIFIED', 'ESCALATED', 'ASSIGNED', 'RESPONDING', 'RESOLVED', 'CLOSED', 'DISMISSED', name='incidentstatus', native_enum=False), nullable=True),
        sa.Column('to_status', sa.Enum('DETECTED', 'VERIFYING', 'VERIFIED', 'ESCALATED', 'ASSIGNED', 'RESPONDING', 'RESOLVED', 'CLOSED', 'DISMISSED', name='incidentstatus', native_enum=False), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('incident_events', schema=None) as batch_op:
        batch_op.create_index('ix_incident_events_incident_id', ['incident_id'], unique=False)
        batch_op.create_index('ix_incident_events_event_type', ['event_type'], unique=False)
        batch_op.create_index('ix_incident_events_incident_created', ['incident_id', 'created_at'], unique=False)

    # 3. Incident Assignments table
    op.create_table(
        'incident_assignments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=False),
        sa.Column('responder_id', sa.Uuid(), nullable=False),
        sa.Column('assigned_by_id', sa.Uuid(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('unassigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'REASSIGNED', 'CANCELLED', name='assignmentstatus', native_enum=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responder_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('incident_assignments', schema=None) as batch_op:
        batch_op.create_index('ix_incident_assignments_incident_id', ['incident_id'], unique=False)
        batch_op.create_index('ix_incident_assignments_responder_id', ['responder_id'], unique=False)
        batch_op.create_index('ix_incident_assignments_status', ['status'], unique=False)
        batch_op.create_index('ix_incident_assignments_responder_status', ['responder_id', 'status'], unique=False)
        batch_op.create_index('ix_incident_assignments_incident_assigned', ['incident_id', 'assigned_at'], unique=False)

    # 4. Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('recipient_id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channel', sa.Enum('IN_APP', 'PUSH', 'SMS', 'EMAIL', name='notificationchannel', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'RETRYING', name='notificationdeliverystatus', native_enum=False), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index('ix_notifications_recipient_id', ['recipient_id'], unique=False)
        batch_op.create_index('ix_notifications_channel', ['channel'], unique=False)
        batch_op.create_index('ix_notifications_status', ['status'], unique=False)
        batch_op.create_index('ix_notifications_is_read', ['is_read'], unique=False)
        batch_op.create_index('ix_notifications_idempotency_key', ['idempotency_key'], unique=True)
        batch_op.create_index('ix_notifications_recipient_status', ['recipient_id', 'status'], unique=False)
        batch_op.create_index('ix_notifications_recipient_created', ['recipient_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('incident_assignments')
    op.drop_table('incident_events')
    op.drop_table('incidents')
