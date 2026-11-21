# OpsIntelligence Phase 4B.1 — Authenticated workspaces

## Security scope

- Backend-managed identity, PBKDF2-SHA256 password hashes (600,000 rounds with per-user random salt), opaque random bearer sessions, SHA-256 token digests stored in PostgreSQL, 8-hour expiration and explicit server-side revocation.
- Per-account failed-password lockout after 5 attempts for 15 minutes; **not** a full distributed rate-limiting solution. There is no password reset, MFA, SSO, email verification, SCIM, or session/device management in this phase.
- Organisation-level membership and access roles: viewer can read projects; analyst can create projects; admin/owner can read membership/audit and add existing users. Nonmembers receive 404 to avoid organisation enumeration.
- Organisation/project identifiers are always checked through the authenticated user membership before querying tenant-scoped resources. Security events record action/resource metadata without storing tokens or passwords.
- No public signup or first-run bootstrap HTTP endpoint. Local CLI only creates the first owner, and refuses to rerun if any users exist. Subsequent users are provisioned by local server operator; org admins add these identities as members.
- Frontend token is **memory-only** (no browser storage). Reopening/refreshing requires login; browsers with XSS can still steal in-memory tokens. Further CSP and security testing required.
- The pre-existing `/api/v1/data/seed`, `/api/v1/orders`, `/api/v1/optimization/*`, `/api/v1/workspace/*` and `/api/v1/intelligence/*` endpoints are explicitly **public synthetic demonstration routes**. Their data is *NOT* tenant-isolated. **Never connect confidential company data to them.**
- API-key/MCP/database external connectors remain disabled. Do not insert secrets in this project until the subsequent security implementation passes independent review.
- This is a locally running security prototype, **not an audited production authentication system**. Bind FastAPI to loopback; use HTTPS and mature identity infrastructure before public deployment.

## Local installation

1. PostgreSQL: `docker compose up -d db` from repository root. Keep existing database volumes.
2. Backend (from `backend`): `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`
3. Database migration (from `backend`): `.\.venv\Scripts\python.exe -m alembic upgrade head`
4. First-time provisioning **only once** (from `backend`): `.\.venv\Scripts\python.exe -m scripts.bootstrap_identity`. Prompts for email, organisation and password; never paste these into chat or command arguments.
5. Further user (optional): `.\.venv\Scripts\python.exe -m scripts.create_user` and assign membership using the admin UI.
6. Start backend: `.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000`
7. Start frontend: `npm run dev` from `frontend`. Open Organisation security section; log in with the locally bootstrapped identity.
8. Run `python -m pytest -q` from `backend`, `npm run build` from `frontend`.

## API contract

- `POST /api/v1/enterprise/auth/login` with `email` and `password`, returns short-lived opaque token (never logged or persisted in JS storage).
- `GET /api/v1/enterprise/auth/me`, `POST /api/v1/enterprise/auth/logout` require bearer authentication.
- `GET|POST /api/v1/enterprise/organisations/{id}/projects` (viewer read; analyst+ create).
- `GET|POST /api/v1/enterprise/organisations/{id}/members` (admin+).
- `GET /api/v1/enterprise/organisations/{id}/audit` (admin+).

## Release blockers before any real company data

Tenant-scope all future operational records, rework existing demo routes to require explicit synthetic dataset boundaries, use managed identity or external security review, resilient rate limiting, robust secret management, HTTPS and security headers, backup/restore exercises, least-privilege outbound connection allowlists, SSRF and MCP tool safeguards, external penetration testing and enterprise access controls.
