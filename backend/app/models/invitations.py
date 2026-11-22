"""One-time, hashed invitations scoped to a single organisation and email."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class OrganisationInvitation(Base):
    __tablename__ = 'identity_invitations'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    code_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('identity_users.id', ondelete='SET NULL'))
    accepted_by: Mapped[int | None] = mapped_column(ForeignKey('identity_users.id', ondelete='SET NULL'))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('organisation_id', 'email', name='uq_identity_invite_org_email'),)
