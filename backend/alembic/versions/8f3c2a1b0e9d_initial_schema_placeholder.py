"""initial schema placeholder

Revision ID: 8f3c2a1b0e9d
Revises:
Create Date: 2024-07-22 00:00:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "8f3c2a1b0e9d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the initial migration."""
    pass


def downgrade() -> None:
    """Revert the initial migration."""
    pass
