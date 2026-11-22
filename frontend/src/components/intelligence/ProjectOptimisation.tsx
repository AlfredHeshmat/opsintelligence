import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Project } from './ProjectDataStudio'

const API = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')
const cash = (n: number | null) => n === null ? 'Unavailable' : new Intl.NumberFormat('en-AU', { style: 'currency', currency: 'AUD' }).format(n)
type Decision = {order_id:string;sku:string;warehouse_id:string;units:number;priority:string;action:'dispatch'|'defer';modelled_cost_aud:number}
type Run = {id:number;model_version:string;status:string;solver_message:string;created_at:string;dataset_sha256:string;dataset_current:boolean;handling_capacity:number;defer_penalty_aud_per_unit:number;pending_orders:number;baseline_cost_aud:number|null;objective_cost_aud:number|null;decisions:Decision[]}
type List = {total:number;items:Run[]}
async function load<T>(url:string, token:string, init?:RequestInit):Promise<T>{
 const response=await fetch(url,{...init,headers:{Authorization:`Bearer ${token}`,...init?.headers}})
 if(!response.ok){const body=await response.json().catch(()=>null) as {detail?:string}|null;throw new Error(body?.detail??`Request failed (${response.status})`)}
 return response.json() as Promise<T>
}

/** All results are server-produced and tenant-authorised, never calculated in this component. */
export function ProjectOptimisation({project, token, canRun, datasetHash}:{project:Project;token:string;canRun:boolean;datasetHash:string|null}){
 const [capacity,setCapacity]=useState('100')
 const [penalty,setPenalty]=useState('12.00')
 const [busy,setBusy]=useState(false)
 const [error,setError]=useState('')
 const [runs,setRuns]=useState<Run[]>([])
 const [selected,setSelected]=useState<Run|null>(null)
 const [historyCount,setHistoryCount]=useState(0)
 const base=`${API}/api/v1/enterprise/organisations/${project.organisation_id}/projects/${project.id}/optimisation`
 useEffect(()=>{
  let active=true
  void load<List>(`${base}/runs?limit=10`,token).then(data=>{
   if(active){setRuns(data.items);setHistoryCount(data.total);setSelected(data.items[0]??null)}
  }).catch(e=>{if(active)setError(e instanceof Error?e.message:'Could not load run history')})
  return()=>{active=false}
 },[base,token])
 async function solve(e:FormEvent<HTMLFormElement>){
  e.preventDefault();if(!canRun||!datasetHash)return
  setBusy(true);setError('')
  try{
   const next=await load<Run>(`${base}/solve`,token,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({handling_capacity:Number(capacity),defer_penalty_aud_per_unit:penalty})})
   setSelected(next)
   const latest=await load<List>(`${base}/runs?limit=10`,token)
   setRuns(latest.items);setHistoryCount(latest.total)
  }catch(e){setError(e instanceof Error?e.message:'Could not solve the project model')}
  finally{setBusy(false)}
 }
 const current=selected && selected.dataset_sha256===datasetHash
 const improvement=selected?.status==='optimal'&&selected.baseline_cost_aud!==null&&selected.objective_cost_aud!==null ? selected.baseline_cost_aud-selected.objective_cost_aud : null
 const dispatched=selected?.decisions.filter(d=>d.action==='dispatch')??[]
 return <section id="enterprise-decisions" className="scroll-mt-24 rounded-2xl border border-line bg-white p-6 shadow-panel" aria-label="Project optimisation">
  <p className="text-xs font-bold uppercase tracking-widest text-brand">CONSTRAINT-AWARE DECISION PLANNING</p>
  <h2 className="mt-2 text-xl font-bold">Project optimisation</h2>
  <p className="mt-2 max-w-4xl text-sm leading-6 text-muted">Optimise <strong>only pending orders</strong> in this project's imported CSV. The model chooses dispatch or defer for each order, minimising estimated shipping costs plus an <strong>illustrative defer penalty</strong>, subject to total handling-unit capacity. Shipping costs come from the imported CSV; penalty and capacity are planning assumptions. This is not a transport routing or inventory feasibility model.</p>
  {error && <p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
  {!datasetHash && <p className="mt-4 rounded-lg bg-canvas p-4 text-sm text-muted">Upload a validated Logistics CSV under Data upload before planning dispatch.</p>}
  <form onSubmit={e=>void solve(e)} className="mt-5 grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
   <label className="block text-sm font-semibold">Handling capacity (units)
    <input type="number" min="0" max="1000000" step="1" required value={capacity} onChange={e=>setCapacity(e.target.value)} className="mt-2 block w-full rounded-lg border border-line px-3 py-3 font-normal" />
   </label>
   <label className="block text-sm font-semibold">Defer penalty (AUD/unit)
    <input type="number" min="0.01" max="1000" step="0.01" required value={penalty} onChange={e=>setPenalty(e.target.value)} className="mt-2 block w-full rounded-lg border border-line px-3 py-3 font-normal" />
   </label>
   <button disabled={!datasetHash||!canRun||busy} className="rounded-lg bg-brand px-5 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-40">{busy?'Solving…':'Run verified optimisation'}</button>
  </form>
  {!canRun&&<p className="mt-3 text-xs text-muted">Your Viewer role permits reading saved runs, not executing new optimisations.</p>}
  <p className="mt-3 text-xs leading-5 text-muted">Assumptions: priority multipliers = standard ×1, priority ×2, express ×3; all-or-nothing dispatch per order; unshipped orders only; no costs beyond the CSV shipping estimate and assumed defer penalty. Maximum 150 pending orders per interactive run. Optimality is claimed only if the MILP solver certifies it.</p>
  {selected && <div className="mt-6 rounded-2xl border border-line p-4" aria-live="polite">
   <div className="flex flex-wrap justify-between gap-2"><h3 className="font-bold">Run #{selected.id} · <span className="capitalize">{selected.status.replaceAll('_',' ')}</span></h3><span className={`rounded-full px-3 py-1 text-xs font-semibold ${current?'bg-brand-soft text-brand':'bg-amber-50 text-amber-800'}`}>{current?'Current dataset':'Older dataset snapshot'}</span></div>
   <p className="mt-1 text-xs text-muted">{new Date(selected.created_at).toLocaleString('en-AU')} · {selected.model_version} · {selected.pending_orders} pending orders</p>
   <p className="mt-1 break-all text-xs text-muted">Dataset SHA-256: {selected.dataset_sha256}</p>
   <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">{[
    ['Defer-all baseline',cash(selected.baseline_cost_aud)],['Modelled objective',cash(selected.objective_cost_aud)],['Modelled difference',cash(improvement)],['Orders dispatched',selected.status==='optimal'?String(dispatched.length):'Unverified']
   ].map(([label,value])=><div key={label} className="rounded-xl bg-canvas p-3"><p className="text-xs text-muted">{label}</p><p className="mt-2 text-lg font-bold tabular-nums">{value}</p></div>)}</div>
   <p className="mt-3 text-xs text-muted">{selected.solver_message}. Differences are relative to the assumed defer-all model, not observed business savings. The output is a planning result, not an instruction to dispatch.</p>
   {selected.decisions.length>0&&<div className="mt-4 max-h-72 overflow-auto"><table className="w-full min-w-[590px] text-left text-xs"><thead className="sticky top-0 bg-white"><tr className="border-b border-line">{['Order','Warehouse','SKU','Units','Priority','Decision','Modelled cost'].map(h=><th className="px-2 py-2" key={h}>{h}</th>)}</tr></thead><tbody>{selected.decisions.map(d=><tr className="border-b border-line/70" key={d.order_id}><td className="px-2 py-2">{d.order_id}</td><td className="px-2 py-2">{d.warehouse_id}</td><td className="px-2 py-2">{d.sku}</td><td className="px-2 py-2">{d.units}</td><td className="px-2 py-2">{d.priority}</td><td className="px-2 py-2 font-semibold capitalize">{d.action}</td><td className="px-2 py-2 tabular-nums">{cash(d.modelled_cost_aud)}</td></tr>)}</tbody></table></div>}
  </div>}
  <div className="mt-6"><h3 className="text-sm font-bold">Saved run history <span className="font-normal text-muted">({historyCount} total; latest 10 displayed)</span></h3>{runs.length===0?<p className="mt-2 text-sm text-muted">No runs yet. Submit an optimisation to create an auditable project result.</p>:<div className="mt-3 flex flex-wrap gap-2">{runs.map(run=><button type="button" key={run.id} onClick={()=>setSelected(run)} aria-pressed={selected?.id===run.id} className={`rounded-lg border px-3 py-2 text-xs ${selected?.id===run.id?'border-teal-500 bg-brand-soft text-brand':'border-line bg-white'}`}>#{run.id} · {run.status} {run.dataset_sha256!==datasetHash?'· older CSV':''}</button>)}</div>}</div>
 </section>
}
