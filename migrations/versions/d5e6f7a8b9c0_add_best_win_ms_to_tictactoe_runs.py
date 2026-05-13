"""add best_win_ms to tictactoe_runs

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tictactoe_runs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('best_win_ms', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('tictactoe_runs', schema=None) as batch_op:
        batch_op.drop_column('best_win_ms')
