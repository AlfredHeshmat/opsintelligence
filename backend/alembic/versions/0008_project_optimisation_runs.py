"""Immutable project optimisation history, scoped by organisation and project.

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('project_optimisation_runs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('organisation_id', sa.Integer, sa.ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('identity_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('identity_users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('dataset_sha256', sa.String(64), nullable=False),
        sa.Column('model_version', sa.String(40), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('solver_message', sa.String(300), nullable=False),
        sa.Column('handling_capacity', sa.Integer, nullable=False),
        sa.Column('defer_penalty_aud_per_unit', sa.Numeric(10,2), nullable=False),
        sa.Column('pending_orders', sa.Integer, nullable=False),
        sa.Column('baseline_cost_aud', sa.Numeric(16,2)),
        sa.Column('objective_cost_aud', sa.Numeric(16,2)),
        sa.Column('decisions', sa.JSON, nullable=False),
    )
    op.create_index('ix_project_optimisation_runs_organisation_id','project_optimisation_runs',['organisation_id'])
    op.create_index('ix_project_optimisation_runs_project_id','project_optimisation_runs',['project_id'])


def downgrade():
    op.drop_index('ix_project_optimisation_runs_project_id', table_name='project_optimisation_runs')
    op.drop_index('ix_project_optimisation_runs_organisation_id', table_name='project_optimisation_runs')
    op.drop_table('project_optimisation_runs')
