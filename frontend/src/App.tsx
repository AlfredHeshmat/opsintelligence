import { useEffect, useState } from 'react'
import { AppShell } from './components/layout/AppShell'
import { AccessGate } from './components/layout/AccessGate'
import { ApiStatus } from './components/layout/ApiStatus'
import { EnterpriseIntelligence } from './components/intelligence/EnterpriseIntelligence'
import { DecisionWorkspace } from './components/intelligence/DecisionWorkspace'
import { IndustryPilotStudio } from './components/intelligence/IndustryPilotStudio'
import { OrganisationWorkspace } from './components/intelligence/OrganisationWorkspace'
import { OrdersExplorer } from './components/intelligence/OrdersExplorer'
import { TrendExplorer } from './components/intelligence/TrendExplorer'
import { WorkflowGuide } from './components/layout/WorkflowGuide'

type Overview = {synthetic: boolean; total_orders: number; pending_orders: number; delivered_orders: number; late_deliveries: number; on_time_rate: number | null; pending_units:number; daily_handling_capacity:number|null; inventory_units:number; trend: {date:string; orders:number; delayed:number}[]}
type Alert = {severity:string; metric:string; value:number; message:string}
type Decision = {order_id:number; action:string; shipping_option:string|null; estimated_cost:number}
type Run = {id:number; status:string; objective_value:number|null; baseline_cost:number|null; estimated_savings:number|null; solver_message:string; handling_capacity:number; labour_capacity_hours:number; decisions:Decision[]}
import type { OrderRecord } from './components/intelligence/ordersUtils'
type Order = OrderRecord
const API=(import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/,'')
async function request<T>(path:string, init?:RequestInit):Promise<T>{const response=await fetch(`${API}/api/v1${path}`,init);if(!response.ok){let message=`Request failed (${response.status})`;try{const body=await response.json() as {detail?:string};if(body.detail) message=body.detail}catch{/* ignore */}throw new Error(message)}return response.json() as Promise<T>}
const money=(n:number|null)=>n===null?'—':new Intl.NumberFormat('en-AU',{style:'currency',currency:'AUD',maximumFractionDigits:0}).format(n)
const pageGuidance:Record<string,string>={workspace:'Start with operational KPIs, then navigate to analytics, optimisation or scenarios.',intelligence:'Filter demand and product performance. Export the displayed synthetic results for further analysis.',orders:'Inspect source orders behind the summary KPIs. Records are generated locally.',optimization:'Define resource constraints, solve, and inspect model status before comparing scenarios.', 'industry-pilots':'Select a supported industry, review its explicit choices and constraints, then solve.', 'decision-workspace':'Describe a business scenario and validate its data contract before running an applicable solver.',connections:'Review available data sources and safe, local-only preparation steps.',predictions:'Check holdout evaluation before interpreting delay-risk estimates. Weak models are clearly flagged.',simulation:'Solve a warehouse allocation first; then compare simulation assumptions and outputs.',connection:'Check API availability and database readiness.'}
export default function App(){
 const [mode,setMode]=useState<'demo'|'enterprise'|null>(null)
 const [activePage,setActivePage]=useState(()=>window.location.hash.slice(1)||'workspace')
 useEffect(()=>{const update=()=>{setActivePage(window.location.hash.slice(1)||'workspace');window.scrollTo({top:0,behavior:'instant'})};window.addEventListener('hashchange',update);return()=>window.removeEventListener('hashchange',update)},[])
 function chooseMode(selected:'demo'|'enterprise'){setMode(selected);window.location.hash=selected==='demo'?'workspace':'enterprise-workspace';window.scrollTo(0,0)}
 function exitMode(){setMode(null);window.history.replaceState(null,'',window.location.pathname+window.location.search);setActivePage('workspace');window.scrollTo(0,0)}
 const [overview,setOverview]=useState<Overview|null>(null)
 const [orders,setOrders]=useState<Order[]>([])
 const [alerts,setAlerts]=useState<Alert[]>([])
 const [run,setRun]=useState<Run|null>(null)
 const [refreshKey,setRefreshKey]=useState(0)
 const [loading,setLoading]=useState(true)
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [handling,setHandling]=useState('')
 const [labour,setLabour]=useState('')
 async function refresh(){setLoading(true);setError('');try{const [o,r,a]=await Promise.all([request<Overview>('/operations/overview'),request<Order[]>('/orders?limit=30'),request<{alerts:Alert[]}>('/anomalies')]);setOverview(o);setOrders(r);setAlerts(a.alerts)}catch(e){setError(e instanceof Error?e.message:'Failed to load operations')}finally{setLoading(false)}}
 useEffect(()=>{
  if(mode!=='demo')return
  let active=true
  void Promise.all([request<Overview>('/operations/overview'),request<Order[]>('/orders?limit=30'),request<{alerts:Alert[]}>('/anomalies')])
   .then(([o,r,a])=>{if(active){setOverview(o);setOrders(r);setAlerts(a.alerts)}})
   .catch(e=>{if(active)setError(e instanceof Error?e.message:'Failed to load operations')})
   .finally(()=>{if(active)setLoading(false)})
  return()=>{active=false}
 },[mode])
 async function seed(){setBusy(true);setError('');try{await request('/data/seed',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({count:240,seed:42})});await refresh();setRefreshKey(k=>k+1)}catch(e){setError(e instanceof Error?e.message:'Seed failed')}finally{setBusy(false)}}
 async function solve(){setBusy(true);setError('');try{const config={handling_capacity:handling===''?null:Number(handling),labour_hours:labour===''?null:Number(labour)};setRun(await request<Run>('/optimization/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)}))}catch(e){setError(e instanceof Error?e.message:'Optimisation failed')}finally{setBusy(false)}}
 if(mode===null)return <AccessGate onChoose={chooseMode}/>
 if(mode==='enterprise')return <AppShell mode="enterprise" onExit={exitMode}><OrganisationWorkspace onExit={exitMode}/></AppShell>
 return <AppShell mode="demo" onExit={exitMode}>
  <section aria-label="Workspace guidance" className="mb-6 flex flex-wrap items-start justify-between gap-3 rounded-xl border border-line bg-white px-5 py-4 shadow-panel"><div><p className="text-xs font-bold uppercase tracking-widest text-brand">{activePage==='workspace'?'Your starting point':'Workspace guide'}</p><p className="mt-1 text-sm text-muted">{pageGuidance[activePage]??'Explore this synthetic workspace. Source data and solver assumptions are labelled throughout.'}</p></div><span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand">Public synthetic demo</span></section>
  <WorkflowGuide activePage={activePage}/>
  <section id="workspace" className="scroll-mt-24">
   <div className="flex flex-wrap items-center justify-between gap-3"><span className="text-xs font-semibold uppercase tracking-widest text-brand">OPERATIONS INTELLIGENCE · WAREHOUSE DEMO</span><span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-medium text-brand">Synthetic dataset · local</span></div>
   <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">Operations command centre</h1>
   <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">Operational visibility, constraint-aware decisions and transparent cost estimates. The warehouse operational KPIs are calculated from synthetic database records.</p>
   <div className="mt-6 flex flex-wrap gap-2" aria-label="Quick actions">
    <a href="#optimization" className="rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-hover">Run warehouse optimiser <span aria-hidden="true">↗</span></a>
    <a href="#industry-pilots" className="rounded-lg border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-brand-soft">Explore industry solvers</a>
    <a href="#decision-workspace" className="rounded-lg border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-brand-soft">Build a scenario</a>
   </div>
  </section>
  {error&&<div role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
  {loading?<p className="mt-8 text-muted">Loading operational data…</p>:overview&&overview.total_orders===0?<div className="mt-8 rounded-2xl border border-line bg-surface p-8 shadow-panel"><h2 className="text-xl font-semibold">Start with reproducible warehouse data</h2><p className="mt-3 text-sm text-muted">No operational records exist yet. Generate clearly labelled synthetic data to explore the dashboard and solver.</p><button disabled={busy} onClick={()=>void seed()} className="mt-5 rounded-lg bg-brand px-5 py-3 font-semibold text-white disabled:opacity-50">Generate demo dataset</button></div>:overview&&<>
   <div id="overview-content">
   <div className="mt-8 grid grid-cols-2 gap-4 xl:grid-cols-4">
    {([{label:'Total orders',value:overview.total_orders.toLocaleString(),detail:'All records'},{label:'Pending orders',value:overview.pending_orders.toLocaleString(),detail:`${overview.pending_units} units awaiting fulfilment`},{label:'On-time delivery',value:overview.on_time_rate===null?'—':`${overview.on_time_rate}%`,detail:`${overview.late_deliveries} recorded late`},{label:'Available inventory',value:overview.inventory_units.toLocaleString(),detail:'Units across all SKUs'}]).map(item=><section key={item.label} className="relative overflow-hidden rounded-2xl border border-line bg-surface p-5 shadow-panel"><span aria-hidden="true" className="absolute left-0 top-0 h-1 w-full bg-teal-600/70"/><p className="text-xs font-semibold uppercase tracking-wide text-muted">{item.label}</p><p className="metric-number mt-3 text-3xl font-bold text-ink sm:text-4xl">{item.value}</p><p className="mt-2 text-xs text-muted">{item.detail}</p></section>)}
   </div>
   <div className="mt-6 grid gap-6 xl:grid-cols-[1.7fr_1fr]">
    <TrendExplorer trend={overview.trend}/>
    <section className="rounded-2xl border border-line bg-surface p-6 shadow-panel"><h2 className="text-lg font-semibold">Operational alerts</h2><p className="mt-1 text-xs text-muted">Explainable rules · indicative thresholds</p><div className="mt-5 space-y-3">{alerts.length?alerts.map(alert=><div key={alert.metric} className="rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="text-xs font-semibold uppercase text-amber-800">{alert.severity} priority</p><p className="mt-1 text-sm text-ink">{alert.message}</p><p className="mt-2 text-xs text-muted">{alert.metric}: {alert.value}</p></div>):<p className="text-sm text-muted">No threshold alerts in current data.</p>}</div></section>
   </div>
   </div>
   <section id="optimization" className="mt-6 rounded-2xl border border-line bg-surface p-6 shadow-panel"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-semibold">Decision optimisation</h2><p className="mt-1 text-sm text-muted">Mixed-integer linear optimisation · order allocation with capacity and inventory constraints</p></div><span className="rounded-full bg-brand-soft px-3 py-1 text-xs text-brand">Solver-backed</span></div><div className="mt-6 grid gap-4 sm:grid-cols-3"><label className="text-sm text-muted">Handling capacity (units)<input type="number" min="0" placeholder={String(overview.daily_handling_capacity??90)} value={handling} onChange={e=>setHandling(e.target.value)} className="mt-1 block w-full rounded-lg border border-line px-3 py-2 text-ink" /></label><label className="text-sm text-muted">Labour hours<input type="number" min="0" placeholder="28" value={labour} onChange={e=>setLabour(e.target.value)} className="mt-1 block w-full rounded-lg border border-line px-3 py-2 text-ink" /></label><div className="flex items-end"><button onClick={()=>void solve()} disabled={busy} className="w-full rounded-lg bg-brand px-4 py-2.5 font-semibold text-white hover:bg-brand-hover disabled:opacity-50">{busy?'Computing…':'Solve allocation'}</button></div></div><p className="mt-3 text-xs text-muted">Baseline is deferring all pending orders. Estimated improvement is relative to this illustrative baseline, not proven savings against actual operations. Solver status must be optimal for a proven model optimum.</p>
   {run&&<div className="mt-6"><div className="grid gap-4 sm:grid-cols-4">{[{label:'Solver status',value:run.status},{label:'Model cost',value:money(run.objective_value)},{label:'Baseline cost',value:money(run.baseline_cost)},{label:'Estimated improvement',value:money(run.estimated_savings)}].map(k=><div className="rounded-xl bg-canvas p-4" key={k.label}><p className="text-xs text-muted">{k.label}</p><p className="mt-2 text-lg font-semibold">{k.value}</p></div>)}</div><div className="mt-4 flex flex-wrap items-center gap-3 rounded-lg border border-line bg-canvas px-4 py-3 text-xs text-muted"><span className="font-semibold text-ink">Run #{run.id}</span><span>{run.solver_message}</span><span className="rounded-full border border-line bg-white px-2 py-1">Input: synthetic operations</span></div><h3 className="mt-6 font-semibold">Order-level allocation decisions</h3><div className="mt-3 max-h-72 overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-line text-muted"><th className="p-2">Order</th><th className="p-2">Decision</th><th className="p-2">Shipping</th><th className="p-2 text-right">Estimated cost</th></tr></thead><tbody>{run.decisions.slice(0,100).map(d=><tr key={d.order_id} className="border-b border-line/70"><td className="p-2">#{d.order_id}</td><td className="p-2 capitalize">{d.action}</td><td className="p-2">{d.shipping_option??'—'}</td><td className="p-2 text-right">{money(d.estimated_cost)}</td></tr>)}</tbody></table></div></div>}
   </section>
    <DecisionWorkspace />
    <IndustryPilotStudio />
   <EnterpriseIntelligence runId={run?.id??null} refreshKey={refreshKey} />
   <OrdersExplorer orders={orders} />
  </>}
  <div id="connection" className="mt-6"><ApiStatus /></div>
  <footer className="mt-10 border-t border-line pt-5 text-xs text-muted">OpsIntelligence · Local warehouse operations demonstration · Synthetic data · Decisions require independent validation</footer>
 </AppShell>
}
