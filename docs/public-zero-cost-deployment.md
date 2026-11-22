# Public portfolio deployment — $0/free-tier plan

This is a **synthetic-only recruiter demo**, not the enterprise application and not a production SaaS. The full enterprise app remains runnable locally via `compose.full.yaml`.

## Recommended split

- **Frontend:** Cloudflare Pages, free static hosting, source folder `frontend`, build `npm ci && npm run build`, output `dist`.
- **Backend:** Render Free Web Service using `backend/Dockerfile.public` with Docker context `backend`. Note 512 MB RAM and idle spin-down; CPU/ML imports may exceed free-instance resources. Do not upgrade to paid automatically.
- **PostgreSQL:** Neon Free project **dedicated solely to synthetic data**, never point at your existing Docker database or any real organisation database. Check current free quotas and usage settings before signup.
- The public app has no authentication and no enterprise access. The existing CI remains unchanged.

All three services have nominally free offerings, but usage limits, account verification, capacity, terms, and potential future provider charges differ. We cannot guarantee that the full backend performs reliably within the free resource limits, particularly SciPy/scikit-learn. **Stop if any service requires a payment or upgrades.** Never create metered paid resources.

## Step A — Create free accounts and synthetic database

1. Create a free Neon project and database named `opsintelligence_public_demo`; obtain its PostgreSQL connection URL with TLS (`sslmode=require`). **Do not put the URL in GitHub, screenshots, frontend env vars or chat.** Keep it in the Render service's private environment settings.
2. Create a free Cloudflare Pages project from the repo `AlfredHeshmat/opsintelligence`, branch `main`. Set root directory `frontend`, build command `npm ci && npm run build`, output directory `dist`.
3. **Before deploying the frontend**, set two build-time environment variables in Cloudflare Pages:
   - `VITE_PUBLIC_DEMO_ONLY=true`
   - `VITE_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com` (replace after creating the Render service)
4. Deploy to obtain the Pages hostname, e.g. `https://your-choice.pages.dev`. Pages' generated HTTPS hostname costs nothing on the free tier.

## Step B — Backend on free Render Docker web service

1. Connect the same GitHub repository, branch `main`, and choose Docker Web Service, **Free** instance type.
2. **Recommended:** use the repository-root `render.yaml` as a free Web Service Blueprint, which sets the Dockerfile and build context. Alternatively, create a Docker Web Service manually and set Docker context `backend` and Dockerfile path `backend/Dockerfile.public` (UI labels may differ). The working directory inside the image is `/app`.
3. Add server-side environment variables (never mark these as frontend/public):
   - `OPS_PUBLIC_DEMO_ONLY=true` **required**, otherwise the public entrypoint refuses startup.
   - `OPS_ENABLE_LOCAL_SIGNUP=false` **required**, fail-closed if enabled.
   - `OPS_ALLOW_LEGACY_MEMBER_ADD=false`
   - `OPS_READONLY_CONNECTORS_ENABLED=false`
   - `DATABASE_URL=<dedicated Neon synthetic-only PostgreSQL URL>`
   - `CORS_ORIGINS=["https://YOUR-PROJECT.pages.dev"]` (valid JSON array with exact origin, no slash at end).
   - `PORT=10000`
4. Use the Dockerfile's default command (`python -m scripts.public_entrypoint`). Do not use the local `scripts.container_entrypoint`, because it expects Docker Compose database variables.
5. Start the service. The entrypoint enforces public-only mode, runs Alembic migrations, creates deterministic synthetic demo data on an empty database, and serves FastAPI on `$PORT`. Database migration failure aborts startup.
6. Confirm `https://YOUR-RENDER-SERVICE.onrender.com/api/v1/health` returns `{"status":"healthy"}`; `/api/v1/ready` returns connected when Neon is available.
7. Confirm `/api/v1/enterprise/auth/login` returns 404, and `/api/v1/data/seed` returns 403. No real company accounts should exist in this fresh database.

## Step C — Connect and verify

1. Set Cloudflare Pages `VITE_API_BASE_URL` to the actual `https://...onrender.com` address and redeploy the `main` branch. This value is public and intentionally contains no secrets.
2. Visit the Pages HTTPS URL in an incognito browser. It should display only `Enter demo workspace`; **Enterprise Sign In must not appear**.
3. Check operations overview and 240 synthetic records, Industry Solver Lab, and the optimiser. Run a small what-if simulation. Data and savings must be clearly labelled synthetic/hypothetical. The backend may take time to wake after 15 minutes idle.
4. In DevTools Network confirm API calls target Render HTTPS, never `127.0.0.1` or a real private server.
5. Verify the app on desktop and mobile. Do not add test login credentials or secret DATABASE_URL to the README.
6. Add the actual Pages URL to the README after confirmation. This project patch **does not publish a service** or create an account on your behalf.

## Public-mode security boundaries and limitations

- Public mode **does not register enterprise identity, connector or private project-data API routes**. This is stronger than hiding UI buttons.
- Public frontend build hides enterprise sign-in and prevents switching to enterprise mode. The public demo is not an alternative login to private data.
- The seed/reset POST is disabled in public mode. The API's remaining bounded optimisation/ML demonstration POSTs have a basic **per-process** shared rate budget, **not** an edge WAF or robust abuse prevention. A public solver still uses server resources and some public demo runs are stored in the dedicated synthetic database.
- Never deploy the normal enterprise Docker Compose stack or seed your actual local PostgreSQL database to a public URL.
- Render Free services spin down with inactivity; Neon Free has resource quotas. The first request after idle can be slow and heavy scientific Python dependencies may exceed Render's 512 MB RAM budget. If the complete stack cannot run reliably at $0, deploy a static-only portfolio walkthrough and keep the full live stack local. Do not label static screenshots as live API-driven computation.
- Before deploying, independently review `backend/Dockerfile.public`, entrypoint, cloud environment variables, CORS, quota limits, and secrets. This is not a security certification.

## Local developer checks

```powershell
cd C:\Users\Lenny\Documents\opsintelligence\frontend
npm ci
npm run lint
npm run build
npm test
cd ..\backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..
docker compose -f compose.full.yaml up -d --build
```

The standard local Compose setup remains unchanged. Public deployment does not migrate or delete your local data. Your local Acme account is **not** a production credential; don't use it on the public site.
