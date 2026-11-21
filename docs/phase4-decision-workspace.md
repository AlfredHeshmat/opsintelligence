# Phase 4 — Industry decision workspace (safe foundation)

This milestone introduces a **working** industry selection, scenario validation and local CSV schema preview UI. It does **not** implement universal optimisation, active MCP connections, cloud data ingestion, real API key handling or production security.

## Routes

- `GET /api/v1/workspace/industries` — industry-specific KPI and goal templates, solver availability.
- `POST /api/v1/workspace/scenario/validate` — validates objectives and constraints as configuration, *not an optimisation result*.
- `POST /api/v1/workspace/data/preview` — capped CSV structural inspection (200 KB, 10k rows, 80 columns); does not persist file contents or return row data. Input is still transmitted to the local backend; never submit sensitive content without authorization.
- `GET /api/v1/workspace/connections/capabilities` — explicitly discloses missing production capabilities.

## Security boundary

Do not expose current demo endpoints publicly. The existing Phase 1–3 seed/train/optimisation endpoints lack production-grade authentication, tenant access controls, abuse protection, and resource quotas. CSV preview is a structural demonstration and **not** a secure enterprise file ingestion pipeline. API-key, MCP and database connectors are deliberately disabled: there is no browser secret input or credential persistence.

Production connection work requires: authenticated user and organization membership, RBAC and per-tool authorization, isolated tenant data/keys, vault-backed encrypted secret handling, credential rotation and revocation, HTTPS, auditing, connector allowlists, SSRF protection (including redirects/DNS rebinding), schema mapping with user confirmation, bounded requests/jobs, incident controls and review of source-system terms. No arbitrary MCP server invocation until these safeguards are implemented and tested.

## Planned reusable decision engine

`IndustrySpec -> DataMapping -> DecisionSpec(objectives, units, constraints, uncertainty) -> SolverAdapter -> Feasibility/optimality evidence -> ScenarioComparator -> Auditable DecisionReport`

Only the warehouse optimisation adapter exists today. Other industry templates **must not** be presented as computed recommendations until domain equations and constraints are validated and an appropriate solver is integrated. CAPEX reduction is an entered business target, not a computed savings claim.
