# Phase 4E.3 — Employee invitations and permission gates

## Implemented

- Organisation owners and admins can invite individual employees with **viewer** or **analyst** roles; only owners may invite an **admin**.
- Create returns an unpredictable, URL-safe **one-time invitation code**, **only once**. The database stores SHA-256 of the code, never the plaintext. Listing invitation metadata never returns the code or digest.
- Codes expire after **seven days**, may be revoked, and become unusable immediately after acceptance. Re-inviting an expired, revoked, or accepted email replaces its prior code, but active invitations must be explicitly revoked first.
- New employees can create an individual identity and accept an invitation in the same transaction. Existing accounts **must first sign in as the invited email**; possession of a code cannot reset their password or claim the account.
- User membership is granted by the backend, scoped to one organisation. Role and tenant checks apply to invitation creation, listing, revocation, and project access.
- Security audits record `invitation.created`, `invitation.revoked`, and `invitation.accepted`; event records do **not** include codes, passwords or bearer tokens.
- The interface supports manually sharing a code privately, eliminating the need for a paid email or messaging integration.

## Local user journey

1. Sign in as owner of Acme Logistics Australia, open **Organisation workspace → Membership and permissions**.
2. Enter a test employee email, select **Viewer** or **Analyst**, click **Create invitation code**.
3. Copy the invitation code immediately and share it through a trusted channel. There is no email delivery in this prototype.
4. A new employee opens **Enterprise Sign In → Have an employee invitation code?**, enters the code, invited email, and their own new password. Then they sign in normally.
5. An existing user signs in, expands **Join another organisation with an invitation**, then enters code and invited email (no password change).
6. The owner can review the invitation status, revoke pending invitations, and view audit records.

## Verification

`npm run lint && npm run build && npm test` in `frontend/`.

`python -m pytest -q` in `backend/` using the backend virtualenv.

`docker compose -f compose.full.yaml up -d --build` from the repository root. Check migration `0007` exits 0 and no existing database volume is removed.

## Deliberate limitations before public deployment

- **Not a production identity provider**: no email address verification, automatic invitation delivery, MFA, CAPTCHA, abuse-rate limiting, password reset or password compromise monitoring.
- Manual code distribution proves possession of a code, **not verified ownership of an email inbox**. Use only fictional company records and local demonstration accounts.
- The legacy `POST /organisations/{org_id}/members` authenticated-admin endpoint still supports direct addition of already-existing accounts (retained for backwards compatibility). It should be retired or made explicitly consent-based before internet-facing deployment.
- Session tokens remain in React memory and expire after eight hours; browser reload loses the login. Stronger session lifecycle and CSRF/cookie architecture require separate evaluation.
- Dataset permissions currently use organisation roles; project-specific ACLs, sensitivity classifications, and independent penetration testing remain future work.

**Security rule:** Avoid exposing public enterprise write APIs and real company data until remaining identity and tenancy controls are thoroughly implemented and tested.
