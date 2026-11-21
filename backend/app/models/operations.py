from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import DateTime, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    promised_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(24), default='pending', index=True)
    actual_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Inventory(Base):
    __tablename__ = 'inventory'
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True)
    available_quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)

class Capacity(Base):
    __tablename__ = 'capacity'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True)
    labour_hours: Mapped[int] = mapped_column(Integer)
    handling_units: Mapped[int] = mapped_column(Integer)

class ShippingOption(Base):
    __tablename__ = 'shipping_options'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    transit_days: Mapped[int] = mapped_column(Integer)
    cost_per_order: Mapped[Decimal] = mapped_column(Numeric(12, 2))

class OptimizationRun(Base):
    __tablename__ = 'optimization_runs'
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(30))
    objective_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    baseline_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    handling_capacity: Mapped[int] = mapped_column(Integer)
    labour_capacity_hours: Mapped[int] = mapped_column(Integer)
    solver_message: Mapped[str] = mapped_column(String(400))
    decisions: Mapped[list['OptimizationDecision']] = relationship(back_populates='run', cascade='all, delete-orphan')

class OptimizationDecision(Base):
    __tablename__ = 'optimization_decisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey('optimization_runs.id', ondelete='CASCADE'))
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    action: Mapped[str] = mapped_column(String(16))
    shipping_option: Mapped[str | None] = mapped_column(String(40), nullable=True)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    run: Mapped[OptimizationRun] = relationship(back_populates='decisions')
    __table_args__ = (UniqueConstraint('run_id','order_id'),)
