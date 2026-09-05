"""add v06 camera and cctv investigation tables

Revision ID: c63e8290f102
Revises: b52e7189c101
Create Date: 2026-09-05 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = 'c63e8290f102'
down_revision: Union[str, None] = 'b52e7189c101'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Cameras table
    op.create_table(
        'cameras',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='ACTIVE'),
        sa.Column('location', geoalchemy2.Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False),
        sa.Column('coverage_radius_meters', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('is_simulated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('stream_url', sa.String(500), nullable=True),
        sa.Column('camera_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. CCTV Investigations table
    op.create_table(
        'cctv_investigations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='REQUESTED'),
        sa.Column('search_radius_meters', sa.Float(), nullable=False, server_default='200.0'),
        sa.Column('time_window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('time_window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cameras_queried_count', sa.Float(), nullable=False, server_default='0'),
        sa.Column('cameras_queried', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('detection_results', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('investigation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_cctv_investigations_incident_id', 'cctv_investigations', ['incident_id'])
    op.create_index('ix_cctv_investigations_requested_by', 'cctv_investigations', ['requested_by'])
    op.create_index('ix_cctv_investigations_status', 'cctv_investigations', ['status'])


def downgrade() -> None:
    op.drop_index('ix_cctv_investigations_status', table_name='cctv_investigations')
    op.drop_index('ix_cctv_investigations_requested_by', table_name='cctv_investigations')
    op.drop_index('ix_cctv_investigations_incident_id', table_name='cctv_investigations')
    op.drop_table('cctv_investigations')
    op.drop_table('cameras')
