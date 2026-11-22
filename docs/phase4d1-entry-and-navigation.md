# Phase 4D.1 — Welcome experience, access choices and separated workspaces

## Delivered

- Every new page load initially presents a single welcome/access-choice screen.
- Public **Explore interactive demo** enters the existing synthetic / hypothetical calculation flow without credentials.
- **Enterprise sign in** navigates to the existing protected organisation workspace. Its account login, session handling, membership checks, connector registry and audit calls remain backed by the existing FastAPI enterprise endpoints.
- The left navigation is scoped to the chosen mode. Demo navigation displays one topic at a time (including independent projections for Business intelligence, Predictions, Simulation, Operations and Data connections), avoiding the previous long-document scrolling confusion.
- Each demo page includes purpose-driven guidance; context and model limitations remain visible.
- Demo exit returns to the welcome screen. The authenticated organisation sign-out revokes the session through the existing endpoint before returning to welcome (the browser token remains in memory and is not stored on disk).
- No new paid dependency, cloud-hosting service or licence is introduced.

## IMPORTANT limitations

This is **not** a production-certified authentication or multitenant analytics rollout. Demo APIs are intentionally public, serving synthetic examples, and must never be connected to actual company data without audited authorisation and tenant isolation. The organisation security prototype already existed; this phase reorganises user entry and its frontend presentation. The existing organisation login requires a locally bootstrapped account. Do not use real company passwords or datasets.

User sessions are **not persisted** across a browser refresh; refresh returns to welcome. Enterprise sign-out uses a server-side logout request, but if the server cannot be reached a locally held token may remain valid until expiration. Additional session lifecycle, CSRF/threat modelling, MFA and cross-tenant adversarial tests are required for real deployments.

The demo workspace still mounts its existing analytics modules as a single React tree and selects the visible view with CSS. This is an incremental user experience improvement, not yet route-level code splitting or full independent nested routes. Future phases should refactor routes and data fetching per-view and isolate user-supplied data more rigorously.

## Local verification

```powershell
cd C:\Users\Lenny\Documents\opsintelligence\frontend
npm ci
npm run build
npm test
cd ..
docker compose -f compose.full.yaml up -d --build
```

Browser checklist:

1. Open `http://127.0.0.1:8080` in a new tab: the first screen must offer two access choices.
2. Select Demo, check sidebar views Overview / Industry Solver Lab / What-if simulator / Data connections and verify that only the selected content is visible.
3. Exit Demo and enter Enterprise. Ensure the existing sign-in form appears, not public KPIs or unauthenticated organisation records.
4. Sign in with the already provisioned *local development* account, select an organisation, and inspect membership and access controls. Sign out to return to Welcome.
5. Refresh the browser, check that the entry screen appears again and no enterprise token persists.
6. Verify API `/api/v1/health` and `/api/v1/ready`, then run existing industry solver regression tests.

