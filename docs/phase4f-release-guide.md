# Phase 4F — Release readiness, security boundaries and free hosting

## Feature acceptance checklist

- [ ] `npm run lint`, `npm run build`, and `npm test` pass without new warnings/errors.
- [ ] `python -m pytest -q` passes in the genuine PostgreSQL driver environment; record counts and any deprecations.
- [ ] `docker compose -f compose.full.yaml up -d --build` succeeds with migration task `Exited (0)` and backend/db healthy.
- [ ] Clean-browser welcome -> demo -> exit flow works; no enterprise account required to view synthetic demo.
- [ ] Demo navigation search, keyboard focus, collapsed workflow guide, charts, tables and scenario comparisons work on desktop and mobile widths.
- [ ] Owner -> invite -> Analyst -> project analytics -> optimisation -> saved history works with **synthetic** data.
- [ ] Viewer cannot upload/solve; Analyst cannot manage members/invitations; unauthenticated requests receive 401 and cross-organisation access is denied.
- [ ] Invalid CSV leaves previous valid import and optimisation history intact; older fingerprints are labelled historical.
- [ ] All displayed optimality language is scoped to the model; costs are labelled illustrative rather than achieved savings.

## Public hosting security gate

**Do not directly expose the current local Docker stack or private enterprise routes to the internet.** Current Compose binds the frontend to loopback and allows local self-registration by default for the test workflow. Do not simply change the bound host address or forward router ports.

Before any public hosting:

1. Deploy only the synthetic recruiter demo, or place enterprise functions behind appropriately hardened auth and an independent security review.
2. Set `OPS_ENABLE_LOCAL_SIGNUP=false`, `OPS_ALLOW_LEGACY_MEMBER_ADD=false`, `OPS_READONLY_CONNECTORS_ENABLED=false`; remove connector binding secrets and operator-only configuration.
3. Do not put any `.env`, database files, real-user data, passwords, session tokens or invitation codes in frontend assets, Git history, screenshots or README.
4. Ensure HTTPS, secure proxy headers, appropriate host restrictions, CORS and CSP, request rate limits, logs, observability, backup/restore, CSRF/cookie safeguards if cookies are introduced, and secret rotation.
5. Investigate public registration/verification/MFA/password recovery, per-project policy, tenancy penetration tests, dependency alerts, supply-chain integrity and data retention before enabling real enterprise access.
6. Confirm third-party licence terms, free-tier resource caps, and that a hosted free service can handle the installed scipy/scikit-learn stack and PostgreSQL before committing to it.

## Hosting plan (not deployed)

**Preferred sequence**

1. Produce an isolated public synthetic demo with no public enterprise credentials, insecure signup or company-data ingestion. Keep labels honest for any static mock solver output.
2. Evaluate zero-subscription React static hosting separately from backend compute and persistent PostgreSQL. A frontend-only hosting service does not automatically provide FastAPI or a database.
3. If a full-stack free tier passes reproducibility and inactivity/restart testing, deploy backend + free PostgreSQL with schema migrations and confirm API proxy/CORS. Check external site terms at that time.
4. Otherwise publish the frontend-only synthetic demo and link the reproducible local full-stack Docker workflow on GitHub, explicitly explaining which interactions are simulated versus live.
5. Attach the live URL, architecture diagram, tests and a 90-second workflow video to the GitHub repository and resume once verified.

## Existing local workflow

```powershell
cd C:\Users\Lenny\Documents\opsintelligence
# Preserve existing .env and PostgreSQL volume.
docker compose -f compose.full.yaml up -d --build
docker compose -f compose.full.yaml ps -a
Invoke-RestMethod http://127.0.0.1:8080/api/v1/health
Invoke-RestMethod http://127.0.0.1:8080/api/v1/ready
```

Do **not** run `docker compose down -v`. Deployment decision and public URL are deliberately deferred until the product has passed final checks.

## Known limitations

- No verified publicly accessible website or production SLA.
- Local authentication prototype; browser sessions intentionally stored only in memory and cleared on refresh.
- No implemented public-facing password reset/MFA/email verification/production signup flow.
- Logistics CSV format is bounded and fixed; no general-purpose untrusted document parsing.
- Private optimisation uses pending-order dispatch/defer planning with a single total handling capacity, not live warehouse routing, inventory, workforce scheduling or an across-industry universal optimum.
- Some earlier phase docs reflect historical development state; README and this guide describe present intended release scope.
