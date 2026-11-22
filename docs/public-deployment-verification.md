# Release acceptance checklist (public demo)

- [ ] Latest `main` green in GitHub Actions for backend, frontend, Docker smoke and migrations.
- [ ] Zero-cost plans selected without paid add-ons, unexpected card charges or metered upgrades.
- [ ] Public backend starts only with `OPS_PUBLIC_DEMO_ONLY=true` and refuses local company signup.
- [ ] Dedicated **synthetic-only** Neon database. No local Acme data migrated.
- [ ] Private enterprise API paths return 404; public demo seeding endpoint returns 403.
- [ ] No frontend enterprise login route or Company Signup choice in public build.
- [ ] Cloudflare Pages and Render origins use HTTPS; `CORS_ORIGINS` equals real Pages origin.
- [ ] Dashboard loads on first visit and after backend spin-down; acceptable cold-start UX.
- [ ] Industry Solver Lab, warehouse demo optimisation and what-if simulation work, if free RAM permits.
- [ ] Synthetic and model-specific optimality disclaimers visible and accurate.
- [ ] Basic global compute budget returns 429 on heavy repeated POSTs; abuse protections remain prototype-level.
- [ ] Mobile/keyboard paths and broken-link checks complete.
- [ ] Actual working URL added to README and resume only after live end-to-end verification.
- [ ] Existing local Docker data preserved; no `docker compose down -v` used.
