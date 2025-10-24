"""initial migration

Revision ID: initial_001
Revises: 
Create Date: 2023-10-24 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'initial_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create table with all columns including registration_number
    op.create_table('bhakts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_number', sa.String(10), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('mobile_number', sa.String(15), nullable=False),
        sa.Column('email_address', sa.String(100), nullable=True),
        sa.Column('abhishek_types', sa.String(255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('validity_months', sa.Integer(), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mobile_number'),
        sa.UniqueConstraint('registration_number')
    )

def downgrade():
    op.drop_table('bhakts')