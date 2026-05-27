"""add applicant_address to procedure_submissions

Revision ID: a1b2c3d4e5f6
Revises: e1f2a3b4c5d6
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('procedure_submissions')]
    if 'applicant_address' not in columns:
        op.add_column(
            'procedure_submissions',
            sa.Column('applicant_address', sa.String(300), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('procedure_submissions')]
    if 'applicant_address' in columns:
        op.drop_column('procedure_submissions', 'applicant_address')
