"""Bounded organisation-scoped project CSV import.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('project_datasets',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('organisation_id', sa.Integer, sa.ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('identity_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_filename', sa.String(180), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('row_count', sa.Integer, nullable=False),
        sa.Column('imported_by', sa.Integer, sa.ForeignKey('identity_users.id', ondelete='SET NULL')),
        sa.Column('imported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id'),
    )
    op.create_index('ix_project_datasets_organisation_id','project_datasets',['organisation_id'])
    op.create_index('ix_project_datasets_project_id','project_datasets',['project_id'])
    op.create_table('project_orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('organisation_id', sa.Integer, sa.ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('identity_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', sa.String(64), nullable=False),
        sa.Column('order_date', sa.Date, nullable=False),
        sa.Column('warehouse_id', sa.String(40), nullable=False),
        sa.Column('sku', sa.String(64), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('promised_date', sa.Date, nullable=False),
        sa.Column('shipped_date', sa.Date),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('unit_price_aud', sa.Numeric(12,2), nullable=False),
        sa.Column('unit_cost_aud', sa.Numeric(12,2), nullable=False),
        sa.Column('shipping_cost_aud', sa.Numeric(12,2), nullable=False),
        sa.Column('destination_region', sa.String(30), nullable=False),
        sa.UniqueConstraint('project_id','order_id'),
    )
    op.create_index('ix_project_orders_organisation_id','project_orders',['organisation_id'])
    op.create_index('ix_project_orders_project_id','project_orders',['project_id'])


def downgrade():
    op.drop_index('ix_project_orders_project_id',table_name='project_orders')
    op.drop_index('ix_project_orders_organisation_id',table_name='project_orders')
    op.drop_table('project_orders')
    op.drop_index('ix_project_datasets_project_id',table_name='project_datasets')
    op.drop_index('ix_project_datasets_organisation_id',table_name='project_datasets')
    op.drop_table('project_datasets')
