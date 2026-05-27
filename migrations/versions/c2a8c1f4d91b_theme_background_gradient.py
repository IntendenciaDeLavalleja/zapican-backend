"""theme background gradient

Revision ID: c2a8c1f4d91b
Revises: 8f4c1b7a2c9a
Create Date: 2026-05-11 12:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2a8c1f4d91b'
down_revision = '8f4c1b7a2c9a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('theme_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('background_gradient_from', sa.String(length=20), nullable=False, server_default='#f8fbf7'))
        batch_op.add_column(sa.Column('background_gradient_to', sa.String(length=20), nullable=False, server_default='#eef5ef'))
        batch_op.add_column(sa.Column('background_gradient_angle', sa.Integer(), nullable=False, server_default='180'))

    op.execute(
        """
        UPDATE theme_settings
        SET background_gradient_from = COALESCE(background_gradient_from, '#f8fbf7'),
            background_gradient_to = COALESCE(background_gradient_to, '#eef5ef'),
            background_gradient_angle = COALESCE(background_gradient_angle, 180)
        """
    )


def downgrade():
    with op.batch_alter_table('theme_settings', schema=None) as batch_op:
        batch_op.drop_column('background_gradient_angle')
        batch_op.drop_column('background_gradient_to')
        batch_op.drop_column('background_gradient_from')