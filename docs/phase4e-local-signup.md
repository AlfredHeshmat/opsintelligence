# Phase 4E: Local company registration prototype

- Welcome → Enterprise sign in → **Create company account**. The registrant creates a new, isolated organisation with an `owner` membership.
- Existing employees do **not** gain access to a company by entering its name. Organisation administrators add already provisioned users. Invitation-based employee signup is a future feature.
- Endpoint `POST /api/v1/enterprise/auth/register-company` accepts `organisation_name`, `email`, `password` (12–256 chars); responds 201. No session token is created: the new owner signs in separately. Existing emails return 409. Changes are atomic and logged as `organisation.registered`.
- **Local demo only**: `OPS_ENABLE_LOCAL_SIGNUP=false` by default in FastAPI settings; `compose.full.yaml` enables it for the loopback-bound local demo using `${OPS_ENABLE_LOCAL_SIGNUP:-true}`. **Before public deployment, set `OPS_ENABLE_LOCAL_SIGNUP=false`.**
- No email verification, password reset, invitation acceptance, distributed rate limiting, anti-bot protection, MFA, secret rotation, or independent security review. Do not use this flow for real company data or production public registration.
- Existing users and organisations are preserved. No database migration required. No paid services.
