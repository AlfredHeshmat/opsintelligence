# Phase 4C — Operator-provisioned, read-only PostgreSQL previews

This phase introduces an **opt-in synthetic-data preview**, not unrestricted enterprise connectivity.

## Boundaries

- Off by default (`OPS_READONLY_CONNECTORS_ENABLED=false`).
- Only PostgreSQL connector records with `metadata_approved` status and `public` or `internal` classification qualify. Disabled connectors cannot run checks or previews.
- All requests require authenticated **owner/admin** membership in the exact organisation.
- The operator configures a per-organisation/per-connector binding outside the application. No password, hostname, arbitrary query, or SQL can be supplied through the API or browser.
- Only operator-allowlisted `schema.table` names may be previewed; identifiers are safely quoted. Results are limited to 25 rows, with a 2-second statement timeout and a transaction-level read-only restriction.
- Success and driver-failure events are audited without logging DSNs or credentials.
- Previewed rows are not persisted by OpsIntelligence, exported, used to train models, or fed automatically into the optimisation engine.

## Safe setup for synthetic data only

1. Keep the default disabled configuration for ordinary use.
2. Provision a **separate, synthetic-only** PostgreSQL database and a low-privilege login. Grant only `CONNECT`, `USAGE` on the selected schema, and `SELECT` on the specific demo tables; deny writes.
3. Look up the exact organisation and connector identifiers in the Enterprise Workspace. Create/approve a new connector with classification `internal`, not your previously disabled one.
4. Locally, configure the backend runtime with an operator-controlled environment variable (do not commit its value):

```text
OPS_READONLY_CONNECTORS_ENABLED=true
OPS_PG_CONNECTOR_BINDINGS_JSON={"1":{"7":{"dsn":"postgresql://readonly_user:REDACTED@synthetic-db/synthetic","tables":["public.demo_orders"]}}}
```

Replace all placeholders with **your** IDs and a dedicated synthetic data source. For Docker Compose, the environment variables above are passed to the backend container only. Avoid committing `.env` or sharing screenshots with connection strings.

5. Rebuild/recreate the backend if necessary and use **Check operator-provisioned read-only connection**, then select an allowlisted table and click **Preview up to 25 rows**. Audits should show `connector.connection_checked` and `connector.table_previewed`.
6. To revoke, disable the connector or set `OPS_READONLY_CONNECTORS_ENABLED=false` and recreate the backend container.

**Security limitations:** This is not an enterprise credential vault, egress firewall, complete data loss prevention solution, fine-grained row/column security system, or production-grade external connector service. DSNs in environment variables may be visible to authorised Docker/container administrators. Never point the preview at private company data or attach a privileged database account. SQL execution can only be made safe with read-only database grants in addition to application-level guards. A dedicated connector worker, secret manager, network policy, per-tenant quotas, privacy review, authenticated session hardening and penetration testing are future requirements.

## API

- `POST /api/v1/enterprise/organisations/{org}/connectors/{connector}/connection-check` — read-only transaction check and allowlisted table names.
- `POST /api/v1/enterprise/organisations/{org}/connectors/{connector}/table-preview` — JSON `{ "table": "public.demo_orders" }`, returning at most 25 rows.

Both operations are authenticated, organisation-scoped and use no-store response headers. They cannot execute user-provided SQL.

## Validation

Run `python -m pytest -q` in `backend`, `npm run build` and `npm test` in `frontend`, and Docker Compose build/smoke tests. Security tests cover disabled-by-default behaviour, role isolation, cross-tenant denial, state transitions, classification restrictions, malformed table names, and audit events. A database integration test with a dedicated, restricted Postgres account remains required before claiming end-to-end connector verification.
