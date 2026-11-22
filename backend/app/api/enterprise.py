"""Phase 4B.1: credentialless bootstrap CLI, opaque sessions, tenant-scoped workspace APIs.

NOT A PRODUCTION IDENTITY PROVIDER. Only synthetic demo data is public elsewhere.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re
import secrets
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.operations import get_db
from app.models.identity import Membership, Organisation, OrganisationProject, SecurityAudit, SessionToken, User
from app.security.passwords import hash_password, verify_password
from app.core.config import get_settings
from app.services.industry_registry import get_industry

router = APIRouter(prefix='/api/v1/enterprise', tags=['enterprise-security'])
DB = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)
SESSION_HOURS = 8
ROLES = {'viewer': 0, 'analyst': 1, 'admin': 2, 'owner': 3}


def now():
    return datetime.now(timezone.utc)


def audit(db: Session, user_id: int | None, org_id: int | None, action: str,
          resource_type: str, resource_id: int | None = None):
    db.add(SecurityAudit(actor_id=user_id, organisation_id=org_id,
                         action=action, resource_type=resource_type, resource_id=resource_id))


def principal(db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})
    digest = sha256(credentials.credentials.encode()).hexdigest()
    session = db.scalar(select(SessionToken).where(SessionToken.token_digest == digest))
    if session is None or session.revoked_at is not None or session.expires_at.replace(tzinfo=timezone.utc) <= now():
        raise HTTPException(401, 'Session expired or invalid', headers={'WWW-Authenticate': 'Bearer'})
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, 'Session invalid')
    return (user, session)

Principal = Annotated[tuple[User, SessionToken], Depends(principal)]


def access(db: Session, user: User, org_id: int, required: str = 'viewer') -> Membership:
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.organisation_id == org_id))
    # 404 for both nonmember and nonexistent org to avoid enumeration.
    if membership is None:
        raise HTTPException(404, 'Workspace not found')
    if ROLES[membership.role] < ROLES[required]:
        raise HTTPException(403, 'Insufficient workspace permissions')
    return membership


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class CompanyRegistration(BaseModel):
    organisation_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=256)


@router.post('/auth/register-company', status_code=201)
def register_company(payload: CompanyRegistration, db: DB):
    """LOCAL DEMO ONLY: creates a new organisation and its first owner atomically.

    Disable this endpoint for internet-facing deployments until verification,
    abuse controls, and onboarding approval are implemented.
    """
    if not get_settings().ops_enable_local_signup:
        raise HTTPException(403, 'Self-service registration is disabled')
    email = payload.email.strip().lower()
    name = payload.organisation_name.strip()
    if len(name) < 2 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise HTTPException(422, 'Valid organisation name and email are required')
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(409, 'Account already exists; sign in or ask an administrator')
    # Hash outside the transaction: the DB never stores plaintext passwords.
    hashed = hash_password(payload.password)
    user = User(email=email, password_hash=hashed, failed_logins=0)
    org = Organisation(name=name)
    try:
        db.add_all([user, org])
        db.flush()
        db.add(Membership(user_id=user.id, organisation_id=org.id, role='owner'))
        audit(db, user.id, org.id, 'organisation.registered', 'organisation', org.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Registration could not be completed') from None
    return {'message': 'Company account created. Sign in to continue.', 'organisation_id': org.id}


class ProjectRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industry_id: str = Field(min_length=2, max_length=70)


class MemberRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    role: Literal['viewer', 'analyst', 'admin']


class MemberRoleChange(BaseModel):
    role: Literal['viewer', 'analyst', 'admin']


def org_view(org: Organisation, role: str) -> dict:
    return {'id': org.id, 'name': org.name, 'role': role}


@router.post('/auth/login')
def login(payload: LoginRequest, db: DB):
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    # Use a comparable KDF for unknown users to reduce timing-based account enumeration.
    if user is None:
        from app.security.passwords import hash_password
        verify_password(payload.password, hash_password('invalid-login-placeholder'))
        raise HTTPException(401, 'Invalid credentials')
    if user.locked_until and user.locked_until.replace(tzinfo=timezone.utc) > now():
        raise HTTPException(429, 'Too many attempts. Try again later.')
    if not verify_password(payload.password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= 5:
            user.locked_until = now() + timedelta(minutes=15)
            user.failed_logins = 0
        db.commit()
        raise HTTPException(401, 'Invalid credentials')
    user.failed_logins = 0
    user.locked_until = None
    raw = secrets.token_urlsafe(48)
    expiration = now() + timedelta(hours=SESSION_HOURS)
    db.add(SessionToken(user_id=user.id, token_digest=sha256(raw.encode()).hexdigest(), expires_at=expiration))
    audit(db, user.id, None, 'auth.login', 'session')
    db.commit()
    return {'access_token': raw, 'token_type': 'bearer', 'expires_at': expiration.isoformat()}


@router.get('/auth/me')
def me(auth: Principal, db: DB):
    user, _ = auth
    memberships = db.execute(select(Membership, Organisation).join(Organisation, Membership.organisation_id == Organisation.id).where(Membership.user_id == user.id)).all()
    return {'user': {'id': user.id, 'email': user.email}, 'organisations': [org_view(org, m.role) for m, org in memberships]}


@router.post('/auth/logout', status_code=204)
def logout(auth: Principal, db: DB):
    user, session = auth
    session.revoked_at = now()
    audit(db, user.id, None, 'auth.logout', 'session', session.id)
    db.commit()


@router.get('/auth/sessions')
def my_sessions(auth: Principal, db: DB):
    """Expose only session metadata, never bearer tokens or token digests."""
    user, current = auth
    sessions = db.scalars(select(SessionToken).where(
        SessionToken.user_id == user.id,
        SessionToken.revoked_at.is_(None),
        SessionToken.expires_at > now(),
    ).order_by(SessionToken.id.desc())).all()
    return [{'id': s.id, 'current': s.id == current.id,
             'created_at': s.created_at.isoformat(),
             'expires_at': s.expires_at.isoformat()} for s in sessions]


@router.post('/auth/logout-all', status_code=204)
def logout_all(auth: Principal, db: DB):
    """Revoke every session for this identity, including the calling session."""
    user, _ = auth
    active_sessions = db.scalars(select(SessionToken).where(
        SessionToken.user_id == user.id, SessionToken.revoked_at.is_(None)
    )).all()
    timestamp = now()
    for session in active_sessions:
        session.revoked_at = timestamp
    audit(db, user.id, None, 'auth.logout_all', 'session')
    db.commit()


@router.get('/organisations/{org_id}/projects')
def projects(org_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id)
    result = db.scalars(select(OrganisationProject).where(OrganisationProject.organisation_id == org_id).order_by(OrganisationProject.id)).all()
    return [{'id': p.id, 'name': p.name, 'industry_id': p.industry_id, 'organisation_id': p.organisation_id} for p in result]


@router.post('/organisations/{org_id}/projects', status_code=201)
def create_project(org_id: int, payload: ProjectRequest, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'analyst')
    if get_industry(payload.industry_id) is None:
        raise HTTPException(422, 'Unsupported industry identifier')
    p = OrganisationProject(organisation_id=org_id, name=payload.name.strip(), industry_id=payload.industry_id)
    db.add(p)
    db.flush()
    audit(db, user.id, org_id, 'project.created', 'project', p.id)
    db.commit()
    return {'id': p.id, 'organisation_id': org_id, 'name': p.name, 'industry_id': p.industry_id}


@router.get('/organisations/{org_id}/members')
def members(org_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'admin')
    rows = db.execute(select(Membership, User).join(User, Membership.user_id == User.id).where(Membership.organisation_id == org_id)).all()
    return [{'user_id': u.id, 'email': u.email, 'role': m.role} for m, u in rows]


@router.post('/organisations/{org_id}/members', status_code=201)
def add_member(org_id: int, payload: MemberRequest, auth: Principal, db: DB):
    user, _ = auth
    actor_membership = access(db, user, org_id, 'admin')
    if payload.role == 'admin' and actor_membership.role != 'owner':
        raise HTTPException(403, 'Only organisation owners may grant administrator permissions')
    target = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if target is None:
        raise HTTPException(404, 'Existing user not found; create accounts using the local CLI')
    if db.scalar(select(Membership).where(Membership.organisation_id == org_id, Membership.user_id == target.id)):
        raise HTTPException(409, 'User already belongs to this organisation')
    m = Membership(organisation_id=org_id, user_id=target.id, role=payload.role)
    db.add(m)
    audit(db, user.id, org_id, 'member.added', 'user', target.id)
    db.commit()
    return {'user_id': target.id, 'role': m.role}


def _managed_membership(db: Session, actor: User, org_id: int, target_id: int) -> Membership:
    """Enforce tenant boundary and privilege separation, including on direct API calls."""
    actor_membership = access(db, actor, org_id, 'admin')
    target = db.scalar(select(Membership).where(
        Membership.organisation_id == org_id,
        Membership.user_id == target_id,
    ).with_for_update())
    if target is None:
        raise HTTPException(404, 'Organisation member not found')
    if target.user_id == actor.id:
        raise HTTPException(403, 'You cannot change or remove your own membership')
    if target.role == 'owner':
        raise HTTPException(403, 'Owner membership cannot be changed here')
    if target.role == 'admin' and actor_membership.role != 'owner':
        raise HTTPException(403, 'Only owners can manage administrators')
    return target


@router.patch('/organisations/{org_id}/members/{member_user_id}')
def change_member_role(org_id: int, member_user_id: int, payload: MemberRoleChange,
                       auth: Principal, db: DB):
    user, _ = auth
    target = _managed_membership(db, user, org_id, member_user_id)
    if payload.role == 'admin' and access(db, user, org_id).role != 'owner':
        raise HTTPException(403, 'Only owners may grant administrator permissions')
    if target.role == payload.role:
        raise HTTPException(409, 'Member already has this role')
    target.role = payload.role
    audit(db, user.id, org_id, 'member.role_changed', 'user', target.user_id)
    db.commit()
    return {'user_id': target.user_id, 'role': target.role}


@router.delete('/organisations/{org_id}/members/{member_user_id}', status_code=204)
def remove_member(org_id: int, member_user_id: int, auth: Principal, db: DB):
    user, _ = auth
    target = _managed_membership(db, user, org_id, member_user_id)
    db.delete(target)
    audit(db, user.id, org_id, 'member.removed', 'user', member_user_id)
    db.commit()


@router.get('/organisations/{org_id}/audit')
def audit_events(org_id: int, auth: Principal, db: DB):
    user, _ = auth
    access(db, user, org_id, 'admin')
    events = db.scalars(select(SecurityAudit).where(SecurityAudit.organisation_id == org_id).order_by(SecurityAudit.id.desc()).limit(100)).all()
    return [{'id': x.id, 'action': x.action, 'resource_type': x.resource_type,
             'resource_id': x.resource_id, 'created_at': x.created_at.isoformat()} for x in events]
