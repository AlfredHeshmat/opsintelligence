import { useState } from 'react'

type AccessMode = 'demo' | 'enterprise'

export function AccessGate({ onChoose, publicDemoOnly = false }: { onChoose: (mode: AccessMode) => void; publicDemoOnly?: boolean }) {
 const [showDetails, setShowDetails] = useState(false)
 return <div className="access-page min-h-screen bg-canvas text-ink">
  <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-5 py-8 sm:px-10">
   <header className="flex flex-wrap items-center justify-between gap-4">
    <div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-brand text-sm font-black text-white shadow-panel">OI</span><div><p className="font-bold tracking-tight">OpsIntelligence</p><p className="text-xs text-muted">Operational intelligence & decision optimisation</p></div></div>
    <span className="rounded-full border border-line bg-white px-3 py-1.5 text-xs font-medium text-muted">{publicDemoOnly ? 'Public portfolio demonstration' : 'Self-hosted · Open-source stack'}</span>
   </header>
   <main className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[1.05fr_1fr] lg:gap-20">
    <section className="max-w-2xl">
     <span className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-brand-soft px-3 py-1.5 text-xs font-bold text-brand"><span aria-hidden="true" className="size-2 rounded-full bg-teal-600"/>INSIGHT → DECISION → IMPACT</span>
     <h1 className="mt-7 text-4xl font-bold leading-tight tracking-[-.045em] sm:text-5xl xl:text-6xl">Turn operational complexity into <span className="text-brand">clear decisions.</span></h1>
     <p className="mt-6 max-w-xl text-base leading-8 text-muted">Explore warehouse performance, industry optimisation, model limitations and scenario comparisons in one transparent decision-intelligence workspace.</p>
     <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
      {[['01','Understand','Trace KPIs to their source'],['02','Optimise','Apply explicit constraints'],['03','Explain','Compare assumptions & results']].map(([n,title,desc])=><div className="rounded-xl border border-line bg-white/80 p-4" key={n}><p className="text-xs font-bold text-brand">{n}</p><p className="mt-2 text-sm font-bold">{title}</p><p className="mt-1 text-xs leading-5 text-muted">{desc}</p></div>)}
     </div>
    </section>
    <section aria-label="Choose your access mode" className="rounded-3xl border border-line bg-white p-6 shadow-panel sm:p-8">
     <p className="text-xs font-bold uppercase tracking-[.16em] text-brand">WELCOME TO OPSINTELLIGENCE</p>
     <h2 className="mt-2 text-2xl font-bold tracking-tight">Choose how to continue</h2>
     <p className="mt-2 text-sm leading-6 text-muted">{publicDemoOnly ? "The interactive public demonstration uses synthetic and hypothetical examples only." : "Your selection determines which workspace and data you can access."}</p>
     <div className="mt-7 space-y-4">
      <div className="rounded-2xl border border-teal-200 bg-[#f2faf8] p-5">
       <div className="flex items-center gap-3"><span aria-hidden="true" className="grid size-10 place-items-center rounded-lg bg-white text-xl text-brand">◇</span><div><h3 className="font-bold">Explore interactive demo</h3><p className="text-xs text-muted">No account required</p></div></div>
       <p className="mt-3 text-sm leading-6 text-muted">View dashboards, optimisation models and scenario simulations using synthetic or hypothetical examples.</p>
       <button type="button" onClick={()=>onChoose('demo')} className="mt-4 w-full rounded-xl bg-brand px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-brand-hover">Enter demo workspace <span aria-hidden="true">→</span></button>
      </div>
      {!publicDemoOnly && <div className="rounded-2xl border border-line bg-white p-5">
       <div className="flex items-center gap-3"><span aria-hidden="true" className="grid size-10 place-items-center rounded-lg bg-canvas text-xl text-ink">▣</span><div><h3 className="font-bold">Enterprise sign in</h3><p className="text-xs text-muted">Individual account · Role-based access</p></div></div>
       <p className="mt-3 text-sm leading-6 text-muted">Sign in to your organisation, or create a new company account in local prototype mode.</p>
       <button type="button" onClick={()=>onChoose('enterprise')} className="mt-4 w-full rounded-xl border border-line bg-white px-5 py-3 text-sm font-bold text-ink transition-colors hover:bg-canvas">Sign in or create account <span aria-hidden="true">→</span></button>
      </div>}
     </div>
     {!publicDemoOnly && <button type="button" aria-expanded={showDetails} onClick={()=>setShowDetails(v=>!v)} className="mt-5 text-left text-xs font-semibold text-brand underline underline-offset-4">{showDetails?'Hide':'What does each mode allow?'}</button>}
     {showDetails&&!publicDemoOnly&&<div className="mt-3 rounded-lg bg-canvas p-4 text-xs leading-6 text-muted"><p><strong className="text-ink">Demo:</strong> public synthetic operations and bounded examples only; no access to enterprise identities or credentials.</p><p className="mt-2"><strong className="text-ink">Enterprise:</strong> authenticated local security prototype. Private access is enforced by its protected APIs; real-company production ingestion is not enabled.</p></div>}
    </section>
   </main>
   <footer className="border-t border-line py-5 text-xs leading-6 text-muted">{publicDemoOnly ? "Public synthetic portfolio demonstration" : "Free, self-hosted demonstration"} · Mathematical optimality applies only to explicitly defined models · Not certified for production or real company data</footer>
  </div>
 </div>
}
