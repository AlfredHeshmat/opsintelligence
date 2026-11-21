"""Organisation-scoped connector descriptions ONLY; no secret or network access."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ConnectorRegistration(Base):
    __tablename__ = 'enterprise_connectors'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default='not_configured')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    purpose: Mapped[str] = mapped_column(String(300), nullable=False, default='Existing demonstration connector')
    data_classification: Mapped[str] = mapped_column(String(20), nullable=False, default='internal')
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey('identity_users.id', ondelete='SET NULL'))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
