# Development plan

OpsIntelligence is being built in seven phases. Each phase should leave the application working, tested, and documented before the next begins.

The later phases describe the intended direction rather than a fixed implementation contract. Their details will be refined as the domain model and data become clearer.

Only Phase 1 is currently authorised.

## Phase 1 — Application foundation

Establish a reliable local development environment and a maintainable starting point.

Scope:

- React, TypeScript, Vite, and Tailwind frontend.
- Responsive application shell with accessible navigation.
- Live API connection status with failure handling and retry.
- FastAPI backend with environment-based settings and CORS.
- Separate process health and database readiness endpoints.
- PostgreSQL running through Docker Compose with persistent storage.
- SQLAlchemy engine configuration and an empty Alembic baseline.
- Structured application logging.
- Initial backend and frontend tests.
- Formatting, linting, strict TypeScript checking, and dependency records.
- Setup instructions, architecture documentation, and verification notes.

Completion means the local stack runs, the browser reaches the API, the API reaches PostgreSQL, automated checks pass, and the documented commands reproduce the setup.

No business tables, operational dashboards, data imports, predictions, or recommendations belong in this phase.

## Phase 2 — Operational domain and synthetic data

Agree on the business concepts before building their screens.

Scope:

- Define orders, shipments, warehouses, and inventory.
- Document relationships, identifiers, statuses, and validation rules.
- Add reviewed database migrations.
- Create repeatable synthetic seed data.
- Implement a focused set of validated API operations.
- Add database integration tests.

Completion means the API can store and retrieve a coherent set of operational records, with tests covering important validation and persistence behaviour.

The domain design should explain business assumptions rather than hide them in code.

## Phase 3 — Operational visibility

Build useful operational views from the data introduced in Phase 2.

Scope:

- Order and shipment lists with appropriate filtering and pagination.
- Detail views for investigating individual records.
- Inventory and warehouse views.
- Clearly defined delivery-performance indicators.
- Charts where they help answer an operational question.
- Loading, empty, error, and success states.
- Responsive and keyboard-accessible interactions.

Completion means every displayed metric can be traced to a documented calculation and real API data. Sample records may be synthetic; displayed results must still be calculated honestly.

## Phase 4 — Data engineering

Introduce a repeatable path for preparing and loading operational data.

Scope:

- Document data sources and reuse permissions.
- Validate incoming records and report rejected data.
- Separate extraction, transformation, and loading responsibilities.
- Make imports repeatable without accidental duplication.
- Record import outcomes and useful diagnostic information.
- Use pandas where it simplifies a demonstrated data-processing need.

Completion means an import can be rerun predictably and failures can be investigated without manually inspecting every source record.

## Phase 5 — Delivery-delay prediction

Develop and evaluate a model against a clear operational question.

Scope:

- Define the prediction target and when a prediction would be made.
- Establish a simple baseline.
- Create features available at prediction time.
- Use evaluation splits that avoid leakage.
- Select metrics appropriate to the operational cost of mistakes.
- Persist the model with its feature and evaluation metadata.
- Integrate predictions without making application startup depend on training.

Completion means the model has a reproducible evaluation and documented limitations. A complex model is not required if it does not improve on the baseline.

## Phase 6 — Evidence-based decision support

Turn operational observations into explainable recommendations.

Scope:

- Start with deterministic rules and documented thresholds.
- Identify the records and calculations supporting each recommendation.
- Distinguish observed facts from predicted outcomes.
- Explain uncertainty and missing evidence.
- Evaluate recommendation behaviour with representative scenarios.
- Consider optional local Ollama integration only if it adds clear value.

Completion means an operations user can understand why a recommendation appeared and inspect its supporting evidence.

Paid AI APIs and mandatory language-model dependencies remain out of scope.

## Phase 7 — Hardening and delivery

Prepare the application for a reviewed deployment and continued maintenance.

Scope:

- Add GitHub Actions for appropriate automated checks.
- Review authentication and authorisation requirements.
- Review configuration, error handling, and secret management.
- Assess logging, monitoring, backups, and recovery.
- Review accessibility and representative user flows.
- Prepare deployment configuration and operating instructions.
- Verify current hosting terms and free-tier limitations.

Cloudflare Pages, Render, and Supabase are provisional options, not guaranteed deployment choices.

Completion requires an explicitly approved deployment plan that stays within the $0 AUD budget. No billing activation, paid resources, or external deployment should happen without approval.

## Working agreements

For each phase:

1. Describe the problem and acceptance criteria.
2. Inspect the existing implementation before changing it.
3. Build in small, reviewable steps.
4. Run checks relevant to the change.
5. Document decisions, limitations, and verification results.
6. Review completion before expanding the scope.

Keep the application as one modular backend unless a concrete requirement justifies a more complex architecture.

Do not begin Phase 2 until it is explicitly requested.