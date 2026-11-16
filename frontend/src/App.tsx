import { AppShell } from './components/layout/AppShell'
import { ApiStatus } from './components/layout/ApiStatus'

export default function App() {
  return (
    <AppShell>
      <section id="workspace" className="scroll-mt-24">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-widest text-brand">
            Operations workspace
          </span>

          <span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-medium text-brand">
            Foundation
          </span>
        </div>

        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Welcome to OpsIntelligence
        </h1>

        <p className="mt-3 max-w-2xl text-base leading-relaxed text-muted">
          One workspace for operational visibility and informed decisions. Your
          application foundation starts here.
        </p>
      </section>

      <div className="mt-8 grid items-start gap-6 xl:grid-cols-[1.5fr_1fr]">
        <section className="rounded-2xl border border-line bg-surface p-6 shadow-panel sm:p-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">
            Getting started
          </p>

          <h2 className="mt-4 text-xl font-semibold">
            A clearer view of your operations
          </h2>

          <p className="mt-3 text-sm leading-7 text-muted">
            This workspace will bring orders, shipments, inventory and warehouse
            performance together. Operational data and workflows will be
            introduced in later phases.
          </p>

          <a
            href="#connection"
            className="mt-6 inline-flex items-center gap-3 rounded-lg bg-brand px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-hover"
          >
            View API connection
            <span aria-hidden="true">→</span>
          </a>

          <div className="mt-8 border-t border-line pt-5">
            <p className="text-sm font-medium">Built around evidence</p>

            <p className="mt-2 text-sm leading-6 text-muted">
              Future insights will use synthetic or legally reusable data, with
              recommendations grounded in operational evidence.
            </p>
          </div>
        </section>

        <ApiStatus />
      </div>

      <footer className="mt-10 border-t border-line pt-5 text-xs leading-6 text-muted">
        OpsIntelligence · Local workspace · Phase 1
      </footer>
    </AppShell>
  )
}
