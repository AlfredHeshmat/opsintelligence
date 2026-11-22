"""Versioned, tenant-owned optimisation results; records are snapshots, not commands."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ProjectOptimisationRun(Base):
    __tablename__ = 'project_optimisation_runs'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('identity_projects.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('identity_users.id', ondelete='SET NULL'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    dataset_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    solver_message: Mapped[str] = mapped_column(String(300), nullable=False)
    handling_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    defer_penalty_aud_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pending_orders: Mapped[int] = mapped_column(Integer, nullable=False)
    baseline_cost_aud: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    objective_cost_aud: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    decisions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
