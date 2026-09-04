"""add_risk_assessment_model

Revision ID: f2ae5b201aa7
Revises: 64d4e5d6e456
Create Date: 2026-09-04 12:26:35.946800

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f2ae5b201aa7'
down_revision: str | None = '64d4e5d6e456'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tourist_id', sa.Uuid(), nullable=False),
        sa.Column('trip_id', sa.Uuid(), nullable=False),
        sa.Column('location_event_id', sa.Uuid(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.Enum('SAFE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel', native_enum=False), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('contributing_signals', sa.JSON(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('recommended_action', sa.Enum('MONITOR', 'REVIEW', 'CONTACT_TOURIST', 'ESCALATE_FOR_HUMAN_REVIEW', name='recommendedaction', native_enum=False), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tourist_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_event_id'], ['location_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('risk_assessments', schema=None) as batch_op:
        batch_op.create_index('ix_risk_assessments_tourist_id', ['tourist_id'], unique=False)
        batch_op.create_index('ix_risk_assessments_trip_id', ['trip_id'], unique=False)
        batch_op.create_index('ix_risk_assessments_location_event_id', ['location_event_id'], unique=False)
        batch_op.create_index('ix_risk_assessments_risk_score', ['risk_score'], unique=False)
        batch_op.create_index('ix_risk_assessments_risk_level', ['risk_level'], unique=False)
        batch_op.create_index('ix_risk_assessments_created_at', ['created_at'], unique=False)
        batch_op.create_index('idx_risk_assessments_tourist_created', ['tourist_id', 'created_at'], unique=False)
        batch_op.create_index('idx_risk_assessments_trip_created', ['trip_id', 'created_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('risk_assessments', schema=None) as batch_op:
        batch_op.drop_index('idx_risk_assessments_trip_created')
        batch_op.drop_index('idx_risk_assessments_tourist_created')
        batch_op.drop_index('ix_risk_assessments_created_at')
        batch_op.drop_index('ix_risk_assessments_risk_level')
        batch_op.drop_index('ix_risk_assessments_risk_score')
        batch_op.drop_index('ix_risk_assessments_location_event_id')
        batch_op.drop_index('ix_risk_assessments_trip_id')
        batch_op.drop_index('ix_risk_assessments_tourist_id')

    op.drop_table('risk_assessments')
