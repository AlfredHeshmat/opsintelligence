"""Organisation authentication, access control and audit schema.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('identity_users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('password_hash', sa.String(300), nullable=False),
        sa.Column('failed_logins', sa.Integer, nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('email'))
    op.create_index('ix_identity_users_email','identity_users',['email'])
    op.create_table('identity_organisations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table('identity_memberships',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('organisation_id',sa.Integer,sa.ForeignKey('identity_organisations.id',ondelete='CASCADE'),nullable=False),
        sa.Column('user_id',sa.Integer,sa.ForeignKey('identity_users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('role',sa.String(16),nullable=False),
        sa.UniqueConstraint('organisation_id','user_id'))
    op.create_index('ix_identity_memberships_organisation_id','identity_memberships',['organisation_id'])
    op.create_index('ix_identity_memberships_user_id','identity_memberships',['user_id'])
    op.create_table('identity_sessions',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('user_id',sa.Integer,sa.ForeignKey('identity_users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('token_digest',sa.String(64),nullable=False,unique=True),
        sa.Column('expires_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('revoked_at',sa.DateTime(timezone=True)),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_identity_sessions_user_id','identity_sessions',['user_id'])
    op.create_table('identity_projects',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('organisation_id',sa.Integer,sa.ForeignKey('identity_organisations.id',ondelete='CASCADE'),nullable=False),
        sa.Column('name',sa.String(120),nullable=False),
        sa.Column('industry_id',sa.String(70),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_identity_projects_organisation_id','identity_projects',['organisation_id'])
    op.create_table('identity_audit_events',
        sa.Column('id',sa.Integer,primary_key=True),
        sa.Column('actor_id',sa.Integer,sa.ForeignKey('identity_users.id',ondelete='SET NULL')),
        sa.Column('organisation_id',sa.Integer,sa.ForeignKey('identity_organisations.id',ondelete='CASCADE')),
        sa.Column('action',sa.String(60),nullable=False),
        sa.Column('resource_type',sa.String(45),nullable=False),
        sa.Column('resource_id',sa.Integer),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index('ix_identity_audit_events_organisation_id','identity_audit_events',['organisation_id'])


def downgrade():
    for table in ('identity_audit_events','identity_projects','identity_sessions','identity_memberships','identity_organisations','identity_users'):
        op.drop_table(table)
