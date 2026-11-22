"""Organisation employee invitations (hashed one-time codes).

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('identity_invitations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('organisation_id', sa.Integer, sa.ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('code_digest', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('identity_users.id', ondelete='SET NULL')),
        sa.Column('accepted_by', sa.Integer, sa.ForeignKey('identity_users.id', ondelete='SET NULL')),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('organisation_id', 'email', name='uq_identity_invite_org_email'),
    )
    op.create_index('ix_identity_invitations_organisation_id', 'identity_invitations', ['organisation_id'])


def downgrade():
    op.drop_index('ix_identity_invitations_organisation_id', table_name='identity_invitations')
    op.drop_table('identity_invitations')
