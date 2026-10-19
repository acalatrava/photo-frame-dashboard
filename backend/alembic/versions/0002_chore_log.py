"""chore log

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-19 15:40:00
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'chore_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chore_id', sa.String(length=32), nullable=False),
        sa.Column('day', sa.String(length=10), nullable=False),
        sa.Column('person_id', sa.String(length=32), nullable=False),
        sa.Column('done_by_device', sa.String(length=32), nullable=True),
        sa.Column('done_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chore_id', 'day', 'person_id', name='uq_chore_day_person'),
    )
    op.create_index(op.f('ix_chore_log_chore_id'), 'chore_log', ['chore_id'], unique=False)
    op.create_index(op.f('ix_chore_log_day'), 'chore_log', ['day'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chore_log_day'), table_name='chore_log')
    op.drop_index(op.f('ix_chore_log_chore_id'), table_name='chore_log')
    op.drop_table('chore_log')
