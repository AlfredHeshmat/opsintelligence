# OpsIntelligence — recruiter walkthrough

## 90-second public demonstration

1. **Welcome:** Select *Explore interactive demo*; the public route must not expose enterprise secrets.
2. **Understand:** Open *Overview*. Synthetic order, inventory and delivery metrics demonstrate API/database integration. Select dates and measures in the trend explorer.
3. **Explore:** Filter and sort *Operational orders*. Exported rows are a **bounded, public synthetic preview**, not a database-wide extract.
4. **Optimise:** Select *Optimisation*. Define capacity/labour constraints, run the solver and inspect its **status and per-order decisions**. Its defer-all baseline is modelled, not observed operational cost.
5. **Compare:** Choose *What-if simulator*. Run two assumption sets. Note sampling variance and the 10th–90th simulated range; a simulated probability is not a real-world guarantee.
6. **Extend:** Explore industry solver examples. Explain which industry formulations are executable and which industry contracts are preparation templates.

## Optional local enterprise demonstration (not public)

With fictional accounts on an isolated local Docker installation:

- Create a fictional organisation owner and a logistics project.
- Import the approved synthetic 13-column CSV and review project-scoped KPIs and order pagination.
- Issue an expiring invitation; onboard an Analyst. Test that Analyst can read authorised project data and execute bounded optimisation.
- Run capacity 100 and capacity 50 against the same dataset and defer-penalty assumption. Compare *saved runs*, SHA-256 provenance, solver status and explicit model limitations.
- Demonstrate restricted role permissions and audit records; never share passwords, raw invitation tokens or session headers.

## Key technical discussion points

- **Full-stack:** React/TypeScript, FastAPI, typed HTTP APIs, PostgreSQL, Alembic.
- **Operations research:** Binary dispatch/defer MILP, capacities, certified solver status, transparent assumptions.
- **Data engineering:** Strict CSV validation, atomic replacement, project scoping, dataset fingerprints, history preservation.
- **Security:** Role-based access checks and organisation-scoped API queries, revocable invitations and auditable actions. Prototype security boundary, not a formal certification.
- **Reliability:** Docker Compose, backend/frontend tests, migration upgrade/downgrade and smoke checks in GitHub Actions.
- **Engineering judgement:** No paid services required; honest distinction between synthetic data and operational evidence.

## Do not claim

- Real company savings, verified live shipment decisions, or comprehensive cross-industry global optimum.
- Production-readiness for sensitive business information, security certification, or unlimited-scale optimisation.
- A deployed public URL or licensed third-party BI system until independently established.
