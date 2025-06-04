"""rename_date_to_departure_date_in_trips

Revision ID: c6e500703796
Revises: 
Create Date: 2025-06-04 15:34:52.936642

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c6e500703796'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trips', sa.Column('departure_date', sa.Date(), nullable=False))


def downgrade() -> None:
    op.drop_column('trips', 'departure_date')
