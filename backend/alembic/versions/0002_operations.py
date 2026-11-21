"""Warehouse operational entities and optimisation audit records."""
from alembic import op
import sqlalchemy as sa
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('orders',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('sku',sa.String(40),nullable=False),
        sa.Column('quantity',sa.Integer(),nullable=False),
        sa.Column('priority',sa.Integer(),nullable=False),
        sa.Column('promised_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('revenue',sa.Numeric(12,2),nullable=False),
        sa.Column('status',sa.String(24),nullable=False),
        sa.Column('actual_delivered_at',sa.DateTime(timezone=True),nullable=True))
    op.create_index('ix_orders_sku','orders',['sku'])
    op.create_index('ix_orders_created_at','orders',['created_at'])
    op.create_index('ix_orders_status','orders',['status'])
    op.create_table('inventory',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('sku',sa.String(40),nullable=False,unique=True),sa.Column('available_quantity',sa.Integer(),nullable=False),sa.Column('reserved_quantity',sa.Integer(),nullable=False))
    op.create_table('capacity',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('date',sa.Date(),nullable=False,unique=True),sa.Column('labour_hours',sa.Integer(),nullable=False),sa.Column('handling_units',sa.Integer(),nullable=False))
    op.create_table('shipping_options',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('name',sa.String(40),nullable=False,unique=True),sa.Column('transit_days',sa.Integer(),nullable=False),sa.Column('cost_per_order',sa.Numeric(12,2),nullable=False))
    op.create_table('optimization_runs',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('objective_value',sa.Numeric(14,2)),sa.Column('baseline_cost',sa.Numeric(14,2)),sa.Column('handling_capacity',sa.Integer(),nullable=False),sa.Column('labour_capacity_hours',sa.Integer(),nullable=False),sa.Column('solver_message',sa.String(400),nullable=False))
    op.create_table('optimization_decisions',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('run_id',sa.Integer(),sa.ForeignKey('optimization_runs.id',ondelete='CASCADE'),nullable=False),sa.Column('order_id',sa.Integer(),sa.ForeignKey('orders.id'),nullable=False),sa.Column('action',sa.String(16),nullable=False),sa.Column('shipping_option',sa.String(40)),sa.Column('estimated_cost',sa.Numeric(12,2),nullable=False),sa.UniqueConstraint('run_id','order_id'))

def downgrade():
    for table in ['optimization_decisions','optimization_runs','shipping_options','capacity','inventory','orders']:
        op.drop_table(table)
