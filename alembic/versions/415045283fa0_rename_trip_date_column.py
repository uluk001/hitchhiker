"""rename_trip_date_column

Revision ID: 415045283fa0
Revises: 5bedfe44690b
Create Date: 2025-06-04 10:19:30.417805

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '415045283fa0'
down_revision: Union[str, None] = '5bedfe44690b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename old ``trip_date`` column to ``departure_date`` if present."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='trips' AND column_name='trip_date'
            ) THEN
                ALTER TABLE trips RENAME COLUMN trip_date TO departure_date;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    """Revert column rename."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='trips' AND column_name='departure_date'
            ) THEN
                ALTER TABLE trips RENAME COLUMN departure_date TO trip_date;
            END IF;
        END$$;
        """
    )
