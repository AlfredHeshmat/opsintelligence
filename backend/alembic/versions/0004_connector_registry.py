"""Credential-free connector metadata.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
revision='0004'
down_revision='0003'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('enterprise_connectors',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('organisation_id',sa.Integer,sa.ForeignKey('identity_organisations.id',ondelete='CASCADE'),nullable=False),
        sa.Column('display_name',sa.String(120),nullable=False),
        sa.Column('kind',sa.String(32),nullable=False),
        sa.Column('provider',sa.String(40),nullable=False),
        sa.Column('status',sa.String(24),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_enterprise_connectors_organisation_id','enterprise_connectors',['organisation_id'])

def downgrade():
    op.drop_index('ix_enterprise_connectors_organisation_id',table_name='enterprise_connectors')
    op.drop_table('enterprise_connectors')
