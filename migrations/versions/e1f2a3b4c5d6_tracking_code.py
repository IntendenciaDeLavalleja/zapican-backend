"""add tracking_code to procedure_submissions

Revision ID: e1f2a3b4c5d6
Revises: 4b7d9e3f1a2c
Create Date: 2026-05-15 12:00:00.000000

"""
import secrets
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect, text

revision = 'e1f2a3b4c5d6'
down_revision = 'ab3182555235'
branch_labels = None
depends_on = None

_TRACKING_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _gen_code() -> str:
    p1 = "".join(secrets.choice(_TRACKING_CHARS) for _ in range(4))
    p2 = "".join(secrets.choice(_TRACKING_CHARS) for _ in range(4))
    return f"TRM-{p1}-{p2}"


def upgrade():
    conn = op.get_bind()
    inspector = sa_inspect(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('procedure_submissions')]

    if 'tracking_code' not in existing_cols:
        op.add_column(
            'procedure_submissions',
            sa.Column('tracking_code', sa.String(length=20), nullable=True),
        )

    # Back-fill any rows that still lack a code (DB-agnostic, Python-side)
    rows = conn.execute(text("SELECT id FROM procedure_submissions WHERE tracking_code IS NULL")).fetchall()
    used: set[str] = set()
    for row in rows:
        code = _gen_code()
        while code in used:
            code = _gen_code()
        used.add(code)
        conn.execute(
            text("UPDATE procedure_submissions SET tracking_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    op.alter_column('procedure_submissions', 'tracking_code',
                    existing_type=sa.String(length=20), nullable=False)

    existing_indexes = [i['name'] for i in inspector.get_indexes('procedure_submissions')]
    if 'ix_procedure_submissions_tracking_code' not in existing_indexes:
        op.create_index(
            op.f('ix_procedure_submissions_tracking_code'),
            'procedure_submissions', ['tracking_code'], unique=True,
        )


def downgrade():
    op.drop_index(
        op.f('ix_procedure_submissions_tracking_code'),
        table_name='procedure_submissions',
    )
    op.drop_column('procedure_submissions', 'tracking_code')
