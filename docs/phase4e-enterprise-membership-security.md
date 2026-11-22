# Phase 4E — Organisation membership and session controls (increment 1)

## What is implemented

- Individual local accounts, salted password hashes and organisation-scoped memberships are **pre-existing** foundations.
- New owner/admin-controlled membership role updates and removals, each checked by FastAPI against **current** database membership.
- Owner accounts cannot be edited or deleted through these APIs. Users cannot edit or remove their own membership. Only owners can grant/manage administrator membership; administrators may manage analysts and viewers.
- Member removal takes effect on the next organisation API request even if the removed user still has a globally valid identity session. Sessions are account-level and may still be needed for memberships in other organisations.
- Role changes and removals append organisation-scoped audit events (`member.role_changed`, `member.removed`) without storing password or bearer token material.
- Authenticated users can list their own session **metadata** (never token/digest) and revoke all active sessions. Normal sign-out revokes only the current session.
- Organisation workspace UI includes member role selection, removal confirmation and `Sign out all devices`.
- Cross-origin support includes PATCH for the authenticated role-change endpoint.

## Permission policy

| Actor | Viewer/analyst membership | Admin membership | Owner membership | Own membership |
|---|---|---|---|---|
| Owner | Add / change / remove | Add / change / remove | No API mutation | No API mutation |
| Admin | Add / change / remove | Not permitted | Not permitted | No API mutation |
| Analyst / Viewer | No | No | No | No |

Membership removal is not user-account deletion; an identity may belong to multiple organisations.

## API endpoints

- `PATCH /api/v1/enterprise/organisations/{org_id}/members/{user_id}` body `{"role":"analyst"}`
- `DELETE /api/v1/enterprise/organisations/{org_id}/members/{user_id}`
- `GET /api/v1/enterprise/auth/sessions` (token-free metadata)
- `POST /api/v1/enterprise/auth/logout-all` (204, invalidates caller too)

All endpoints require bearer authentication and enforce policy server-side. A membership being omitted from the UI is *not* the security boundary.

## Local validation

Run from repository root in PowerShell:

```powershell
cd frontend
npm run lint
npm run build
npm test
cd ..\backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..
docker compose -f compose.full.yaml up -d --build
docker compose -f compose.full.yaml ps -a
```

For multi-user manual testing, use `python -m scripts.create_user` in a backend environment configured against the same DB, never a public sign-up route. Keep these test identities synthetic.

## Important boundaries — not yet production certified

- **Not** a production identity provider, SSO, MFA or complete password-reset/invitation flow. Provisioning still requires an operator CLI.
- Public analytics/warehouse/demo endpoints serve **synthetic shared** data, not private organisation-scoped data. This patch does **not** convert them into tenant-secure endpoints.
- No arbitrary sensitive file ingestion, encrypted dataset store, row-level dataset ACL, immutable external audit system or certified tenant-isolation review.
- Access tokens remain in React memory, expire after eight hours and are not persistent on refresh. Further hardening should consider credential rotation, CSRF/cookie architecture if adopting cookies, session concurrency policy, IP-level throttling, security headers and phishing-resistant MFA.
- Access-control tests use SQLite and mocked application engine; validate PostgreSQL deployment and API integration separately.
- Do not expose the local security prototype with real company data or credentials to the public internet.
- Zero paid dependencies; compatible with the existing local Docker Compose architecture.
