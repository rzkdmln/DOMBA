"""normalize_dinas_naming

Revision ID: afb58329a3e2
Revises: f6e9f25b26bc
Create Date: 2026-03-17 09:26:15.811560

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afb58329a3e2'
down_revision = 'f6e9f25b26bc'
branch_labels = None
depends_on = None


def upgrade():
    # Normalize 'Gudang Dinas (Pusat)' to 'Dinas'
    op.execute(
        "UPDATE kecamatan SET nama_kecamatan = 'Dinas' WHERE nama_kecamatan = 'Gudang Dinas (Pusat)'"
    )


def downgrade():
    # Revert 'Dinas' back to 'Gudang Dinas (Pusat)'
    # Note: This might overwrite other 'Dinas' entries if they didn't come from 'Gudang Dinas (Pusat)'
    # but based on the code logic, 'Dinas' is the intended name.
    op.execute(
        "UPDATE kecamatan SET nama_kecamatan = 'Gudang Dinas (Pusat)' WHERE nama_kecamatan = 'Dinas'"
    )
