"""Organisation-scoped, project-owned imported operational records.

This is a bounded CSV pilot. Do not persist raw uploaded files or credentials.
"""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ProjectDataset(Base):
    __tablename__ = 'project_datasets'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('identity_projects.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    source_filename: Mapped[str] = mapped_column(String(180), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_by: Mapped[int | None] = mapped_column(ForeignKey('identity_users.id', ondelete='SET NULL'))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectOrder(Base):
    __tablename__ = 'project_orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('identity_projects.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String(40), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    promised_date: Mapped[date] = mapped_column(Date, nullable=False)
    shipped_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price_aud: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost_aud: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shipping_cost_aud: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    destination_region: Mapped[str] = mapped_column(String(30), nullable=False)
    __table_args__ = (UniqueConstraint('project_id', 'order_id'),)
