"""create transparency_requests table

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-05-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision = 'f1a2b3c4d5e6'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'transparency_requests' not in existing_tables:
        op.create_table(
            'transparency_requests',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('reference_number', sa.String(length=20), nullable=False),
            sa.Column('requester_type', sa.String(length=60), nullable=False),
            sa.Column('full_name', sa.String(length=220), nullable=False),
            sa.Column('identifier', sa.String(length=100), nullable=False),
            sa.Column('address', sa.String(length=300), nullable=False),
            sa.Column('email', sa.String(length=160), nullable=False),
            sa.Column('phone', sa.String(length=60), nullable=True),
            sa.Column('preferred_response_channel', sa.String(length=80), nullable=False),
            sa.Column('requested_information', sa.Text(), nullable=False),
            sa.Column('additional_location_data', sa.Text(), nullable=True),
            sa.Column('preferred_format', sa.String(length=80), nullable=True),
            sa.Column('municipality', sa.String(length=160), nullable=False),
            sa.Column('accepted_terms', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
            sa.Column('internal_notes', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('reference_number'),
        )
        op.create_index('ix_transparency_requests_reference_number', 'transparency_requests', ['reference_number'], unique=True)
        op.create_index('ix_transparency_requests_status', 'transparency_requests', ['status'], unique=False)
        op.create_index('ix_transparency_requests_is_read', 'transparency_requests', ['is_read'], unique=False)


def downgrade():
    op.drop_index('ix_transparency_requests_is_read', table_name='transparency_requests')
    op.drop_index('ix_transparency_requests_status', table_name='transparency_requests')
    op.drop_index('ix_transparency_requests_reference_number', table_name='transparency_requests')
    op.drop_table('transparency_requests')
