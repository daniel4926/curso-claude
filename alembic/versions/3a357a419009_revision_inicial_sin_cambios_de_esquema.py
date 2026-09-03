"""revision inicial sin cambios de esquema

Revision ID: 3a357a419009
Revises: 
Create Date: 2026-09-02 21:01:29.295551

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '3a357a419009'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
