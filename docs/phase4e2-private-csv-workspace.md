# Phase 4E.2 — Private logistics CSV workspace

## What was implemented

* A private project order importer at `POST /api/v1/enterprise/organisations/{org_id}/projects/{project_id}/orders/import`. Its request body is **raw UTF-8 CSV** with `Content-Type: text/csv` and a simple `X-Filename` header; the browser sends the selected file as an `ArrayBuffer`. This does **not** require `python-multipart` or paid infrastructure.
* Strict CSV schema for the supplied fictional **Acme Logistics 500 Orders** file: `order_id,order_date,warehouse_id,sku,quantity,priority,promised_date,shipped_date,status,unit_price_aud,unit_cost_aud,shipping_cost_aud,destination_region`. Headers and order must match exactly. Import limit: 2 MB, 2,000 rows, valid dates and numeric bounds, unique order IDs; only logistics projects supported in this increment.
* Postgres-backed `project_datasets` and `project_orders` tables added by Alembic revision `0006`, with organisation and project ownership and import provenance (SHA-256, timestamp, filename). Raw files are not retained.
* Atomic replacement: validate the **entire** file first; then replace the prior dataset and its orders within one database transaction, preserving previous data after validation failure. Duplicate byte-identical import is rejected.
* Authorised private endpoints: `/orders/summary` and `/orders` with **server-side pagination** and optional exact SKU/status filtering. All queries validate user membership and project ownership in their `org_id` scope. Members with Viewer access can read; Analyst/Admin/Owner can import.
* New enterprise navigation to Projects, Data upload, Project analytics, Project orders, Optimisation roadmap, Data connectors and Security audit. The selected project drives private data access; other industries show an explicit unsupported-adapter message.
* Dashboard cards for order count, pending orders, dispatches recorded after promised date, gross order sales, an **estimated** margin (price minus per-unit cost minus per-order shipping cost) and warehouse count. A simple order-status distribution chart and paginated table are supplied without any commercial BI dependency.

## Try it locally

1. Apply the update package over your existing `feature/phase4e-enterprise-security` source from the project root.
2. Run `npm run lint`, `npm run build`, `npm test` in `frontend`; then `python -m pytest -q` in `backend` using its `.venv`.
3. Run `docker compose -f compose.full.yaml up -d --build` **from the project root**. The migration container must finish with `Exited (0)`; do not delete the Postgres volume.
4. Visit `http://127.0.0.1:8080`, select **Enterprise sign in**, and sign in to your fictional **Acme Logistics Australia** owner account.
5. Select **Acme Warehouse Optimisation** under Projects. Click **Data upload** and choose `acme_logistics_500_synthetic_orders.csv` from your earlier ChatGPT download. Validate & import. A successful result should report **500 orders**; then open **Project analytics** and **Project orders** to examine the records. No credentials, DB connection string or sensitive data is required.
6. Test a Viewer account (read permitted; import denied) and another organisation (access denied, 404), after provisioned in the local environment.

## Security and scope boundaries

- **Prototype only:** Do not upload personal or confidential company data. Local company signup is not production-hardened; session tokens are held in React memory; invitations/email verification, MFA, production abuse controls and fine-grained project-level grants remain future work.
- Reads require **organisation membership**. Project records are scoped to that organisation. All imports require at least Analyst. Authorisation is enforced by FastAPI, not solely the interface.
- The importer is **not** an arbitrary enterprise data ingestion platform. It accepts one fixed schema for logistics; no Excel/PDF/JSON, no automatic mapping or asynchronous job orchestration. The 2 MB application check does not replace deployment-level request-size limits or malware monitoring for internet-facing use.
- Private analytics **do not** reuse the demo order database. They are simple descriptive statistics, **not a modelled optimisation**. The **Optimisation roadmap** explains that a secure project-specific solver adapter, objective, constraints and validation must be developed before claiming optimal decisions on an imported company project.
- Raw source rows do not leave the self-hosted API/database, aside from being displayed to authorised local users. The source filename is non-sensitive metadata; no credentials are collected through the CSV form.
- No paid libraries, managed cloud services, Power BI or third-party API dependencies are introduced.
