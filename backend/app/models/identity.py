"""Organisation security boundary. Demo warehouse tables remain shared synthetic data."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = 'identity_users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    failed_logins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Organisation(Base):
    __tablename__ = 'identity_organisations'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membership(Base):
    __tablename__ = 'identity_memberships'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('identity_users.id', ondelete='CASCADE'), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    __table_args__ = (UniqueConstraint('organisation_id', 'user_id'),)


class SessionToken(Base):
    __tablename__ = 'identity_sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('identity_users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrganisationProject(Base):
    __tablename__ = 'identity_projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    industry_id: Mapped[str] = mapped_column(String(70), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityAudit(Base):
    __tablename__ = 'identity_audit_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey('identity_users.id', ondelete='SET NULL'))
    organisation_id: Mapped[int | None] = mapped_column(ForeignKey('identity_organisations.id', ondelete='CASCADE'), index=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(45), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
