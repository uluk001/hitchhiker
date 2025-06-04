"""add_time_column_to_trips

Revision ID: 5bedfe44690b
Revises: c6e500703796
Create Date: 2025-06-04 15:37:09.449621

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5bedfe44690b'
down_revision: Union[str, None] = 'c6e500703796'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('trips', sa.Column('time', sa.Time(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trips', 'time')
