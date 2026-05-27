"""form submission status and notes

Revision ID: 8f4c1b7a2c9a
Revises: d0c911465268
Create Date: 2026-05-11 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f4c1b7a2c9a'
down_revision = 'd0c911465268'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('form_submissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='new'))
        batch_op.add_column(sa.Column('internal_notes', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_form_submissions_status'), ['status'], unique=False)


def downgrade():
    with op.batch_alter_table('form_submissions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_form_submissions_status'))
        batch_op.drop_column('internal_notes')
        batch_op.drop_column('status')