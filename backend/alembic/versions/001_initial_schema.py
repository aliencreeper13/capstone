"""Initial schema creation - v1

Revision ID: 001
Revises: 
Create Date: 2024-01-01

This migration creates all base tables for game persistence:
- Users and authentication
- Games and access control
- Empire and City entities
- Buildings, Units, Effects
- Job assignments and game events
"""

from alembic import op
import sqlalchemy as sa

# Alembic revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('auth_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create games table
    op.create_table(
        'games',
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('game_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('current_tick', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('schema_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_modified_at', sa.DateTime(), nullable=False),
        sa.Column('worldmap_size', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('game_id'),
    )
    op.create_index('idx_game_owner_id', 'games', ['owner_user_id'])
    op.create_index('idx_game_created_at', 'games', ['created_at'])
    
    # Create game_participants table
    op.create_table(
        'game_participants',
        sa.Column('participant_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_level', sa.String(50), nullable=False, server_default='editor'),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('participant_id'),
    )
    op.create_index('idx_participant_game_user', 'game_participants', ['game_id', 'user_id'])
    
    # Create empires table
    op.create_table(
        'empires',
        sa.Column('empire_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('knowledge', sa.Float(), nullable=False, server_default='0'),
        sa.Column('autonomy', sa.Float(), nullable=False, server_default='50'),
        sa.Column('ideology_type', sa.String(255), nullable=False, server_default='neutral'),
        sa.Column('total_resources', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_modified_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id']),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('empire_id'),
    )
    op.create_index('idx_empire_game_id', 'empires', ['game_id'])
    op.create_index('idx_empire_owner_id', 'empires', ['owner_user_id'])
    
    # Create cities table
    op.create_table(
        'cities',
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('empire_id', sa.Integer(), nullable=False),
        sa.Column('coord_x', sa.Integer(), nullable=False),
        sa.Column('coord_y', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_capital', sa.Boolean(), nullable=False, server_default='False'),
        sa.Column('resources', sa.JSON(), nullable=False),
        sa.Column('resource_capacities', sa.JSON(), nullable=False),
        sa.Column('total_population', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('employable_population', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('employed_population', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('morale', sa.Float(), nullable=False, server_default='100'),
        sa.Column('defense', sa.Float(), nullable=False, server_default='100'),
        sa.Column('hitpoints', sa.Float(), nullable=False, server_default='100'),
        sa.Column('max_hitpoints', sa.Float(), nullable=False, server_default='100'),
        sa.Column('space_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('space_total', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_modified_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['empire_id'], ['empires.empire_id']),
        sa.PrimaryKeyConstraint('city_id'),
    )
    op.create_index('idx_city_empire_id', 'cities', ['empire_id'])
    op.create_index('idx_city_coords', 'cities', ['coord_x', 'coord_y'])
    
    # Create building_instances table
    op.create_table(
        'building_instances',
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('building_id', sa.String(255), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_state', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_modified_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.city_id']),
        sa.PrimaryKeyConstraint('instance_id'),
    )
    op.create_index('idx_building_city_id', 'building_instances', ['city_id'])
    op.create_index('idx_building_id', 'building_instances', ['building_id'])
    
    # Create unit_instances table
    op.create_table(
        'unit_instances',
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('unit_type_id', sa.String(255), nullable=False),
        sa.Column('position', sa.JSON(), nullable=False),
        sa.Column('health', sa.Float(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='idle'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_modified_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.city_id']),
        sa.PrimaryKeyConstraint('unit_id'),
    )
    op.create_index('idx_unit_city_id', 'unit_instances', ['city_id'])
    op.create_index('idx_unit_type_id', 'unit_instances', ['unit_type_id'])
    
    # Create active_effects table
    op.create_table(
        'active_effects',
        sa.Column('effect_id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('effect_type', sa.String(255), nullable=False),
        sa.Column('effect_data', sa.JSON(), nullable=False),
        sa.Column('ticks_remaining', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.city_id']),
        sa.PrimaryKeyConstraint('effect_id'),
    )
    op.create_index('idx_effect_city_id', 'active_effects', ['city_id'])
    op.create_index('idx_effect_expires', 'active_effects', ['ticks_remaining'])
    
    # Create job_assignments table
    op.create_table(
        'job_assignments',
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(255), nullable=False),
        sa.Column('job_data', sa.JSON(), nullable=False),
        sa.Column('citizen_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['city_id'], ['cities.city_id']),
        sa.PrimaryKeyConstraint('assignment_id'),
    )
    op.create_index('idx_job_city_id', 'job_assignments', ['city_id'])
    op.create_index('idx_job_type', 'job_assignments', ['job_type'])
    
    # Create game_events table
    op.create_table(
        'game_events',
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(255), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id']),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('event_id'),
    )
    op.create_index('idx_event_game_id', 'game_events', ['game_id'])
    op.create_index('idx_event_timestamp', 'game_events', ['timestamp'])
    op.create_index('idx_event_type', 'game_events', ['event_type'])
    
    # Create action_logs table
    op.create_table(
        'action_logs',
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(255), nullable=False),
        sa.Column('action_data', sa.JSON(), nullable=False),
        sa.Column('applied_to_db', sa.Boolean(), nullable=False, server_default='False'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('action_id'),
    )
    op.create_index('idx_action_game_id', 'action_logs', ['game_id'])
    op.create_index('idx_action_user_id', 'action_logs', ['user_id'])
    op.create_index('idx_action_timestamp', 'action_logs', ['timestamp'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_action_timestamp', table_name='action_logs')
    op.drop_index('idx_action_user_id', table_name='action_logs')
    op.drop_index('idx_action_game_id', table_name='action_logs')
    op.drop_table('action_logs')
    
    op.drop_index('idx_event_type', table_name='game_events')
    op.drop_index('idx_event_timestamp', table_name='game_events')
    op.drop_index('idx_event_game_id', table_name='game_events')
    op.drop_table('game_events')
    
    op.drop_index('idx_job_type', table_name='job_assignments')
    op.drop_index('idx_job_city_id', table_name='job_assignments')
    op.drop_table('job_assignments')
    
    op.drop_index('idx_effect_expires', table_name='active_effects')
    op.drop_index('idx_effect_city_id', table_name='active_effects')
    op.drop_table('active_effects')
    
    op.drop_index('idx_unit_type_id', table_name='unit_instances')
    op.drop_index('idx_unit_city_id', table_name='unit_instances')
    op.drop_table('unit_instances')
    
    op.drop_index('idx_building_id', table_name='building_instances')
    op.drop_index('idx_building_city_id', table_name='building_instances')
    op.drop_table('building_instances')
    
    op.drop_index('idx_city_coords', table_name='cities')
    op.drop_index('idx_city_empire_id', table_name='cities')
    op.drop_table('cities')
    
    op.drop_index('idx_empire_owner_id', table_name='empires')
    op.drop_index('idx_empire_game_id', table_name='empires')
    op.drop_table('empires')
    
    op.drop_index('idx_participant_game_user', table_name='game_participants')
    op.drop_table('game_participants')
    
    op.drop_index('idx_game_created_at', table_name='games')
    op.drop_index('idx_game_owner_id', table_name='games')
    op.drop_table('games')
    
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')