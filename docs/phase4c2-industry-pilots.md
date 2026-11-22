# Phase 4C.2 — Three bounded industry optimisation pilots

## Scope and evidence

The `industry-pilots` endpoints and UI offer three **mathematically solved, synthetic-input** integer assignment case studies. This phase **does not yet ingest public observations from UCI, ABARES or Google**, and it does not provide production-ready crop, logistics-network or cloud workload optimisation. Public source links are research references and must not be misrepresented as inputs to the demonstration output.

- Logistics: each order chooses an eligible economy or express fulfilment option under handling-unit and express-slot limits, minimising assumed costs.
- Agriculture: each field chooses wheat or barley under water and input-budget limits, maximising **assumed** gross margin. These numbers are not observed yield responses. Field-level yield prediction alone cannot justify irrigation or crop changes.
- Technology: each workload chooses an eligible region under CPU and region-slot limits, minimising **assumed** costs. SLA/latency and residency compliance have **not** been estimated or tested.

## Mathematical contract

For item \(i\), option \(j\), let binary \(x_{ij}\) denote selection. For each item, \(\sum_j x_{ij}=1\). For each resource \(r\), \(\sum_{ij} a_{ijr}x_{ij}\le C_r\). Minimise \(\sum c_{ij}x_{ij}\) for logistics and technology, or maximise \(\sum m_{ij}x_{ij}\) for agriculture. The solver uses SciPy's HiGHS-backed `milp` and reports `optimal` only on status 0, followed by explicit feasibility checks. Timeout, unproven optimality and infeasibility must not be labelled optimal. A production rollout needs domain-specific constraints and independent validation of all costs, demand, and response coefficients.

## Routes (public synthetic demonstration only)

- `GET /api/v1/industry-pilots/catalogue` — source catalogue, explicit limitations
- `GET /api/v1/industry-pilots/presets/{logistics|agriculture|technology}` — hypothetical cases
- `POST /api/v1/industry-pilots/solve` — bounded JSON assignment input
- `POST /api/v1/industry-pilots/solve-csv` — bounded decision-options CSV plus separate resource capacities

**Security:** These routes are public synthetic demos and not tenant-isolated enterprise uploads. Never submit confidential data, personal information, API credentials, or regulated records. Inputs are capped at 100 KB CSV, 400 options and 80 items and processed without persistence. Server rate limiting, job isolation, malware scanning, data classification, object storage, per-tenant execution and authenticated data onboarding are prerequisites for any enterprise upload feature.

## Data sources — research, not incorporated measurements

| Industry | Source | Rights/attribution | Useful observations | Critical missing factors |
| --- | --- | --- | --- | --- |
| Logistics | [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | CC BY 4.0; cite UCI dataset | Purchase transactions, product quantities and dates | Supplier lead times, shipment eligibility, actual costs and capacity |
| Agriculture | [ABARES Australian Crop Report](https://www.agriculture.gov.au/abares/research-topics/agricultural-outlook/australian-crop-report) | Review individual release's Australian Government licensing and attribution | Aggregate crop yield, area and production | Field soil, water/crop responses, real input cost and decision constraints |
| Technology | [Google Borg cluster traces](https://github.com/google/cluster-data) | CC BY; cite Google trace publications | Machine resource usage and workload traces | Region prices, SLA outcomes, residency requirements and placement constraints |

Do not insert dataset downloads into the repo by default. First review licensing, minimize and validate observations, create a reproducible transformation script and `SOURCE.md`, record checksums, and attribute sources. Public traces may be old or nonrepresentative. No actual company identity is inferred from public aggregate data.

## Validation

Run `cd backend && .\\.venv\\Scripts\\python.exe -m pytest -q` and `cd frontend && npm ci && npm run build && npm test` in Windows PowerShell, followed by `docker compose -f compose.full.yaml up -d --build` and `/api/v1/health`. The new `test_industry_pilots.py` independently enumerates every small preset and verifies objectives and resource feasibility. Test both valid and infeasible CSV cases, and confirm the existing warehouse optimiser still passes.

## Production gap

These assignment pilots establish a reusable model interface, but are not yet data-to-solver pipelines for raw business files. Non-tabular uploads (PDF/Excel/documents), credentials, background jobs, solver-run persistence, instance-size limits, sensitivity analysis, uncertainty propagation, and certified production adapters are further phases. Continue to identify prediction/evaluation limitations, including the existing delay classifier's zero positive-class F1 score.

## Optional local observed-data bridge: UCI retail export

There is an offline `backend/scripts/retail_dataset_to_pilot.py` transformer for a legally downloaded and locally CSV-exported UCI workbook. It aggregates positive `StockCode` / `Quantity` observations into anonymised SKU demand statistics. It then constructs an **explicitly hypothetical** economy-versus-express allocation case; costs, resource use, and capacities are assumptions, **not** facts in UCI. The generated `scenario` JSON can be posted to `/industry-pilots/solve`; it is not a generic arbitrary raw-dataset optimiser.

PowerShell example after CSV export:

```powershell
cd C:\Users\Lenny\Documents\opsintelligence\backend
.\.venv\Scripts\python.exe -m scripts.retail_dataset_to_pilot --input "C:\Users\Lenny\Downloads\OnlineRetail.csv" --output "C:\Users\Lenny\Downloads\retail_pilot.json"
```

The script does not fetch data, includes its source-file SHA-256, excludes cancelled/nonpositive transactions, aggregates SKU counts and discards customer ID and invoice fields. Keep exported source data and generated JSON outside the Git repository until dataset licensing, personal-data exposure and retention policies have been reviewed. Source CSV schema is specific to UCI exports; use a bounded sample <=30MB and 300,000 rows. No dataset was downloaded in the AI development environment.
