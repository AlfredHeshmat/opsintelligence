"""Organisation connector governance, non-executable metadata only.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('enterprise_connectors', sa.Column('purpose', sa.String(300), nullable=False, server_default='Existing demonstration connector'))
    op.add_column('enterprise_connectors', sa.Column('data_classification', sa.String(20), nullable=False, server_default='internal'))
    op.add_column('enterprise_connectors', sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('identity_users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('enterprise_connectors', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('enterprise_connectors', 'reviewed_at')
    op.drop_column('enterprise_connectors', 'reviewed_by')
    op.drop_column('enterprise_connectors', 'data_classification')
    op.drop_column('enterprise_connectors', 'purpose')
