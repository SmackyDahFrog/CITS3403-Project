"""add kai_runs table

Revision ID: a47c1f8e2d10
Revises: 0ab182e503c1
Create Date: 2026-05-09 09:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a47c1f8e2d10'
down_revision = '0ab182e503c1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('kai_runs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('time_ms', sa.Integer(), nullable=False),
    sa.Column('avg_eat_ms', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('eat_count', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('kai_runs')
