"""Add last_login to User model and expand password_hash field

Revision ID: 54a08cfb9337
Revises: 
Create Date: 2026-01-07 16:15:40.255083

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError


# revision identifiers, used by Alembic.
revision = '54a08cfb9337'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Expand password_hash field to accommodate scrypt hashes (170+ chars)
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
                   existing_type=sa.String(128),
                   type_=sa.String(255),
                   existing_nullable=False)
    
    # Add last_login column if it doesn't exist
    # Safe handling for case where column already exists from db.create_all()
    try:
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
    except ProgrammingError as e:
        # If column already exists, just skip
        if 'already exists' in str(e) or 'duplicate' in str(e).lower():
            pass
        else:
            raise


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Downgrade password_hash back to 128
        batch_op.alter_column('password_hash',
                   existing_type=sa.String(255),
                   type_=sa.String(128),
                   existing_nullable=False)
        
        # Drop last_login column if exists
        try:
            batch_op.drop_column('last_login')
        except ProgrammingError:
            pass  # Column might not exist
