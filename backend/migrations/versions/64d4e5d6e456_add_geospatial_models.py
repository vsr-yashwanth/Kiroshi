"""add_geospatial_models

Revision ID: 64d4e5d6e456
Revises: 9e6815f24dd5
Create Date: 2026-09-04 11:46:11.555763

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision: str = '64d4e5d6e456'
down_revision: str | None = '9e6815f24dd5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS postgis;"))

    # 1. Create geo_zones
    op.create_table(
        'geo_zones',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('zone_type', sa.Enum('SAFE', 'RESTRICTED', 'HIGH_RISK', 'CUSTOM', name='geozonetype', native_enum=False), nullable=False),
        sa.Column('geom', Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=True),
        sa.Column('coordinates_json', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('geo_zones', schema=None) as batch_op:
        batch_op.create_index('ix_geo_zones_name', ['name'], unique=True)
        batch_op.create_index('ix_geo_zones_zone_type', ['zone_type'], unique=False)
        batch_op.create_index('ix_geo_zones_is_active', ['is_active'], unique=False)

    # 2. Create tourist_zone_states
    op.create_table(
        'tourist_zone_states',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tourist_id', sa.Uuid(), nullable=False),
        sa.Column('zone_id', sa.Uuid(), nullable=False),
        sa.Column('entered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tourist_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['geo_zones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tourist_id', 'zone_id', name='uq_tourist_zone_occupancy')
    )
    with op.batch_alter_table('tourist_zone_states', schema=None) as batch_op:
        batch_op.create_index('ix_tourist_zone_states_tourist_id', ['tourist_id'], unique=False)
        batch_op.create_index('ix_tourist_zone_states_zone_id', ['zone_id'], unique=False)

    # 3. Create location_events
    op.create_table(
        'location_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tourist_id', sa.Uuid(), nullable=False),
        sa.Column('trip_id', sa.Uuid(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('geom', Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tourist_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('location_events', schema=None) as batch_op:
        batch_op.create_index('ix_location_events_tourist_id', ['tourist_id'], unique=False)
        batch_op.create_index('ix_location_events_trip_id', ['trip_id'], unique=False)
        batch_op.create_index('ix_location_events_recorded_at', ['recorded_at'], unique=False)
        batch_op.create_index('ix_location_events_tourist_recorded', ['tourist_id', 'recorded_at'], unique=False)
        batch_op.create_index('ix_location_events_trip_recorded', ['trip_id', 'recorded_at'], unique=False)

    # 4. Create zone_events
    op.create_table(
        'zone_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tourist_id', sa.Uuid(), nullable=False),
        sa.Column('trip_id', sa.Uuid(), nullable=False),
        sa.Column('zone_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.Enum('ENTER', 'EXIT', name='zoneeventtype', native_enum=False), nullable=False),
        sa.Column('location_event_id', sa.Uuid(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tourist_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['geo_zones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_event_id'], ['location_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('zone_events', schema=None) as batch_op:
        batch_op.create_index('ix_zone_events_tourist_id', ['tourist_id'], unique=False)
        batch_op.create_index('ix_zone_events_trip_id', ['trip_id'], unique=False)
        batch_op.create_index('ix_zone_events_zone_id', ['zone_id'], unique=False)
        batch_op.create_index('ix_zone_events_event_type', ['event_type'], unique=False)
        batch_op.create_index('ix_zone_events_occurred_at', ['occurred_at'], unique=False)
        batch_op.create_index('ix_zone_events_tourist_occurred', ['tourist_id', 'occurred_at'], unique=False)
        batch_op.create_index('ix_zone_events_zone_occurred', ['zone_id', 'occurred_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('zone_events', schema=None) as batch_op:
        batch_op.drop_index('ix_zone_events_zone_occurred')
        batch_op.drop_index('ix_zone_events_tourist_occurred')
        batch_op.drop_index('ix_zone_events_occurred_at')
        batch_op.drop_index('ix_zone_events_event_type')
        batch_op.drop_index('ix_zone_events_zone_id')
        batch_op.drop_index('ix_zone_events_trip_id')
        batch_op.drop_index('ix_zone_events_tourist_id')
    op.drop_table('zone_events')

    with op.batch_alter_table('location_events', schema=None) as batch_op:
        batch_op.drop_index('ix_location_events_trip_recorded')
        batch_op.drop_index('ix_location_events_tourist_recorded')
        batch_op.drop_index('ix_location_events_recorded_at')
        batch_op.drop_index('ix_location_events_trip_id')
        batch_op.drop_index('ix_location_events_tourist_id')
    op.drop_table('location_events')

    with op.batch_alter_table('tourist_zone_states', schema=None) as batch_op:
        batch_op.drop_index('ix_tourist_zone_states_zone_id')
        batch_op.drop_index('ix_tourist_zone_states_tourist_id')
    op.drop_table('tourist_zone_states')

    with op.batch_alter_table('geo_zones', schema=None) as batch_op:
        batch_op.drop_index('ix_geo_zones_is_active')
        batch_op.drop_index('ix_geo_zones_zone_type')
        batch_op.drop_index('ix_geo_zones_name')
    op.drop_table('geo_zones')
