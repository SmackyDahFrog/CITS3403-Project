"""add scores table

Revision ID: 9db630ec8356
Revises: 63df55c41a65
Create Date: 2026-05-08 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9db630ec8356'
down_revision = '63df55c41a65'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('game', sa.String(length=20), nullable=False),
    sa.Column('value', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('scores', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_scores_game'), ['game'], unique=False)


def downgrade():
    with op.batch_alter_table('scores', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_scores_game'))

    op.drop_table('scores')
