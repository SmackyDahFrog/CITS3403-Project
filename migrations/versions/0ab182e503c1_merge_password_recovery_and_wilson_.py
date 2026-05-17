"""merge password recovery and wilson leaderboard heads

Revision ID: 0ab182e503c1
Revises: 4c65ba9a360f, fb1873ddf7f5
Create Date: 2026-05-17 16:43:36.517311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ab182e503c1'
down_revision = ('4c65ba9a360f', 'fb1873ddf7f5')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
