"""procedures module

Revision ID: 4b7d9e3f1a2c
Revises: c2a8c1f4d91b
Create Date: 2026-05-11 14:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b7d9e3f1a2c'
down_revision = 'c2a8c1f4d91b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'procedure_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=220), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=True),
        sa.Column('description_html', sa.Text(), nullable=True),
        sa.Column('eligibility_notes', sa.Text(), nullable=True),
        sa.Column('fee_text', sa.String(length=200), nullable=True),
        sa.Column('estimated_days', sa.Integer(), nullable=True),
        sa.Column('required_documents_json', sa.JSON(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_types_is_active'), 'procedure_types', ['is_active'], unique=False)
    op.create_index(op.f('ix_procedure_types_is_featured'), 'procedure_types', ['is_featured'], unique=False)
    op.create_index(op.f('ix_procedure_types_slug'), 'procedure_types', ['slug'], unique=True)

    op.create_table(
        'procedure_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('procedure_type_id', sa.Integer(), nullable=False),
        sa.Column('applicant_name', sa.String(length=160), nullable=False),
        sa.Column('applicant_email', sa.String(length=160), nullable=False),
        sa.Column('applicant_phone', sa.String(length=60), nullable=True),
        sa.Column('document_number', sa.String(length=80), nullable=True),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('attachments_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['procedure_type_id'], ['procedure_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedure_submissions_applicant_email'), 'procedure_submissions', ['applicant_email'], unique=False)
    op.create_index(op.f('ix_procedure_submissions_procedure_type_id'), 'procedure_submissions', ['procedure_type_id'], unique=False)
    op.create_index(op.f('ix_procedure_submissions_status'), 'procedure_submissions', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_procedure_submissions_status'), table_name='procedure_submissions')
    op.drop_index(op.f('ix_procedure_submissions_procedure_type_id'), table_name='procedure_submissions')
    op.drop_index(op.f('ix_procedure_submissions_applicant_email'), table_name='procedure_submissions')
    op.drop_table('procedure_submissions')

    op.drop_index(op.f('ix_procedure_types_slug'), table_name='procedure_types')
    op.drop_index(op.f('ix_procedure_types_is_featured'), table_name='procedure_types')
    op.drop_index(op.f('ix_procedure_types_is_active'), table_name='procedure_types')
    op.drop_table('procedure_types')