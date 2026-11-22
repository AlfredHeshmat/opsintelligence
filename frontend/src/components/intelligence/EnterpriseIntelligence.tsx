import { useEffect, useMemo, useState } from 'react'

const API = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

type Product = {sku:string;orders:number;units:number;revenue:number;pending_units:number;available_inventory:number;on_time_rate:number|null}
type Performance = {synthetic:boolean;period_days:number;as_of_date?:string;products:Product[];totals:{orders:number;units:number;revenue:number;on_time_rate:number|null}}
type ModelReport = {synthetic:boolean;model:string;trained_on:number;tested_on:number;accuracy:number;balanced_accuracy:number;precision:number;recall:number;f1:number;roc_auc:number|null;majority_baseline_accuracy:number;positive_class_rate_training:number;limitations:string}
type Prediction = {order_id:number;sku:string;quantity:number;priority:number;delay_probability:number;risk_level:string}
type Predictions = {predictions:Prediction[];high_risk_count:number;synthetic:boolean;model:string}
type Simulation = {baseline_cost:number;run_id:number;assumptions:{trials:number;seed:number;delay_probability:number;late_penalty_per_unit:number;shipping_cost_multiplier:number};results:{expected_plan_cost:number;plan_cost_p10:number;plan_cost_p90:number;expected_improvement:number;improvement_p10:number;improvement_p90:number;probability_below_baseline:number};limitations:string}

type Props = {runId:number|null; refreshKey:number}
const money=(n:number)=>new Intl.NumberFormat('en-AU',{style:'currency',currency:'AUD',maximumFractionDigits:0}).format(n)
const pct=(n:number|null)=>n===null?'—':`${n.toFixed(1)}%`
async function get<T>(path:string, init?:RequestInit):Promise<T>{
 const response=await fetch(`${API}/api/v1${path}`,init)
 if(!response.ok){let message=`HTTP ${response.status}`;try{const payload=await response.json() as {detail?:string};if(payload.detail)message=payload.detail}catch{/* ignore */}throw new Error(message)}
 return response.json() as Promise<T>
}
const post=(payload:unknown):RequestInit=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})

function Metric({label,value,detail}:{label:string;value:string;detail?:string}){
 return <div className="rounded-xl border border-line bg-canvas p-4"><p className="text-xs text-muted">{label}</p><p className="mt-2 text-xl font-semibold tracking-tight text-ink">{value}</p>{detail&&<p className="mt-1 text-xs text-muted">{detail}</p>}</div>
}

export function EnterpriseIntelligence({runId,refreshKey}:Props){
 const [period,setPeriod]=useState(30)
 const [sku,setSku]=useState('')
 const [performance,setPerformance]=useState<Performance|null>(null)
 const [model,setModel]=useState<ModelReport|null>(null)
 const [predictions,setPredictions]=useState<Predictions|null>(null)
 const [sim,setSim]=useState<Simulation|null>(null)
 const [previousSim,setPreviousSim]=useState<Simulation|null>(null)
 const [delay,setDelay]=useState(20)
 const [penalty,setPenalty]=useState(8)
 const [costFactor,setCostFactor]=useState(100)
 const [trials,setTrials]=useState(1000)
 const [busy,setBusy]=useState('')
 const [message,setMessage]=useState('')
 const [problem,setProblem]=useState('')
 const [allSkus,setAllSkus]=useState<string[]>([])

 useEffect(()=>{
  let active=true
  void get<Performance>('/products/performance?days=365').then(data=>{if(active)setAllSkus(data.products.map(p=>p.sku))}).catch(()=>{})
  return()=>{active=false}
 },[refreshKey])
 useEffect(()=>{
  let active=true
  setProblem('')
  const params=new URLSearchParams({days:String(period)})
  if(sku)params.set('sku',sku)
  void Promise.all([get<Performance>(`/products/performance?${params}`),get<{report:ModelReport|null}>('/predictions/model')]).then(([data,report])=>{
   if(active){setPerformance(data);setModel(report.report)}
  }).catch(e=>{if(active)setProblem(String(e))})
  return()=>{active=false}
 },[period,sku,refreshKey])
 useEffect(()=>{
  let active=true
  if(!model){setPredictions(null);return()=>{active=false}}
  const params=new URLSearchParams({limit:'100'})
  if(sku)params.set('sku',sku)
  void get<Predictions>(`/predictions/delays?${params}`).then(data=>{if(active)setPredictions(data)}).catch(e=>{if(active)setProblem(String(e))})
  return()=>{active=false}
 },[model,sku,refreshKey])
 useEffect(()=>{setSim(null);setPreviousSim(null)},[runId])
 const assumptionsChanged=Boolean(sim&&(Math.abs(sim.assumptions.delay_probability-delay/100)>0.00001||sim.assumptions.late_penalty_per_unit!==penalty||Math.abs(sim.assumptions.shipping_cost_multiplier-costFactor/100)>0.00001||sim.assumptions.trials!==trials))
 const products=performance?.products??[]
 const maxOrders=Math.max(1,...products.map(p=>p.orders))
 const avgRisk=useMemo(()=>{
  const predictionsList=predictions?.predictions??[]
  return predictionsList.length?predictionsList.reduce((a,p)=>a+p.delay_probability,0)/predictionsList.length:null
 },[predictions])
 async function train(){setBusy('train');setProblem('');setMessage('');try{
  const result=await get<ModelReport>('/predictions/train',{method:'POST'})
  setModel(result);setMessage(`Model trained on ${result.trained_on} synthetic records and evaluated on ${result.tested_on} holdout records.`)
 }catch(e){setProblem(e instanceof Error?e.message:String(e))}finally{setBusy('')}
 }
 async function simulate(){if(!runId)return;setBusy('simulate');setProblem('');setMessage('');try{
  const result=await get<Simulation>('/scenarios/compare',post({optimization_run_id:runId,trials,seed:42,delay_probability:delay/100,late_penalty_per_unit:penalty,shipping_cost_multiplier:costFactor/100}))
  setPreviousSim(sim)
  setSim(result)
 }catch(e){setProblem(e instanceof Error?e.message:String(e))}finally{setBusy('')}
 }
 function exportCsv(){
  if(!products.length)return
  const columns=['sku','orders','units','revenue','pending_units','available_inventory','on_time_rate'] as const
  const lines=[columns.join(','),...products.map(p=>columns.map(key=>p[key]??'').join(','))]
  const blob=new Blob([lines.join('\r\n')],{type:'text/csv;charset=utf-8'})
  const url=URL.createObjectURL(blob)
  const a=document.createElement('a');a.href=url;a.download=`opsintelligence-products-${period}d.csv`;a.click();URL.revokeObjectURL(url)
 }
 return <section id="intelligence" className="mt-6 scroll-mt-24 space-y-6">
  <div className="rounded-2xl border border-line bg-surface p-6 shadow-panel">
   <div className="flex flex-wrap items-start justify-between gap-4">
    <div><p className="text-xs font-semibold uppercase tracking-widest text-brand">Business intelligence</p><h2 className="mt-1 text-xl font-semibold">Product performance explorer</h2><p className="mt-1 text-sm text-muted">Adjust reporting period and SKU to inspect database-derived product statistics.</p></div>
    <button type="button" disabled={!products.length} onClick={exportCsv} className="rounded-lg border border-line px-4 py-2 text-sm font-medium hover:bg-canvas disabled:opacity-50">Export CSV</button>
   </div>
   <div className="mt-5 flex flex-wrap gap-3">
    <label className="text-sm text-muted">Reporting window <select value={period} onChange={e=>setPeriod(Number(e.target.value))} className="mt-1 block min-w-36 rounded-lg border border-line bg-white px-3 py-2 text-ink"><option value={7}>7 days</option><option value={30}>30 days</option><option value={90}>90 days</option><option value={365}>365 days</option></select></label>
    <label className="text-sm text-muted">Product / SKU <select value={sku} onChange={e=>setSku(e.target.value)} className="mt-1 block min-w-36 rounded-lg border border-line bg-white px-3 py-2 text-ink"><option value="">All products</option>{allSkus.map(s=><option value={s} key={s}>{s}</option>)}</select></label>
    <span className="self-end pb-2 text-xs text-muted">Reporting anchored to the newest order date in the dataset</span>
   </div>
   {performance&&<><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Orders" value={String(performance.totals.orders)}/><Metric label="Units ordered" value={performance.totals.units.toLocaleString()}/><Metric label="Recorded revenue" value={money(performance.totals.revenue)} detail="Gross order value; not profit"/><Metric label="On-time deliveries" value={pct(performance.totals.on_time_rate)} detail="Delivered orders in selected window"/></div>
    <div className="mt-6 grid gap-6 lg:grid-cols-2">
     <div><h3 className="mb-3 text-sm font-semibold">Demand by product</h3><div className="space-y-3">{products.map(p=><div key={p.sku}><div className="mb-1 flex justify-between text-xs"><span>{p.sku}</span><span>{p.orders} orders</span></div><div className="h-3 rounded-full bg-canvas"><div className="h-full rounded-full bg-teal-600" style={{width:`${100*p.orders/maxOrders}%`}}/></div></div>)}{!products.length&&<p className="text-sm text-muted">No orders for these filters.</p>}</div></div>
     <div className="overflow-x-auto"><h3 className="mb-3 text-sm font-semibold">Product breakdown</h3><table className="w-full text-left text-xs"><thead><tr className="border-b border-line text-muted"><th className="p-2">SKU</th><th className="p-2 text-right">Revenue</th><th className="p-2 text-right">Pending units</th><th className="p-2 text-right">On time</th></tr></thead><tbody>{products.map(p=><tr key={p.sku} className="border-b border-line/60"><td className="p-2 font-medium">{p.sku}</td><td className="p-2 text-right">{money(p.revenue)}</td><td className="p-2 text-right">{p.pending_units}</td><td className="p-2 text-right">{pct(p.on_time_rate)}</td></tr>)}</tbody></table></div>
    </div></>}
  </div>
  <section id="predictions" className="rounded-2xl border border-line bg-surface p-6 shadow-panel scroll-mt-24">
   <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-widest text-brand">Predictive analytics</p><h2 className="mt-1 text-xl font-semibold">Delay risk prediction</h2><p className="mt-1 text-sm text-muted">Chronological holdout evaluation · synthetic learning data · decision-time features only</p></div><button disabled={busy!==''} onClick={()=>void train()} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-hover disabled:opacity-50">{busy==='train'?'Training…':model?'Retrain model':'Train delay model'}</button></div>
   {!model?<p className="mt-5 rounded-lg bg-canvas p-4 text-sm text-muted">No model trained yet. Train the local model to see evaluated performance and order risk scores.</p>:<>
    <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Holdout F1" value={model.f1.toFixed(2)} detail="Synthetic holdout only"/><Metric label="Holdout ROC-AUC" value={model.roc_auc===null?'Unavailable':model.roc_auc.toFixed(2)}/><Metric label="Holdout accuracy" value={pct(model.accuracy*100)} detail={`Majority baseline ${pct(model.majority_baseline_accuracy*100)}`}/><Metric label="Average pending risk" value={avgRisk===null?'—':pct(avgRisk*100)} detail="Model estimated, not observed"/></div>
    {(model.f1===0||model.recall===0||model.accuracy<=model.majority_baseline_accuracy)&&<div role="status" className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950"><strong>Model quality warning</strong><p className="mt-1 text-xs leading-5">The model does not outperform the majority-class accuracy baseline or fails to detect delayed orders at its evaluated threshold. Risk scores are exploratory and must not drive production decisions.</p></div>}
    <p className="mt-3 text-xs text-muted">Training: {model.trained_on} records · Holdout: {model.tested_on} records · Precision {model.precision.toFixed(2)} · Recall {model.recall.toFixed(2)}. Do not interpret model scores as validated real-world forecasts.</p>
    <div className="mt-5 overflow-x-auto"><h3 className="mb-2 text-sm font-semibold">Pending orders at risk {sku&&`· ${sku}`}</h3><table className="w-full text-left text-sm"><thead><tr className="border-b border-line text-muted"><th className="p-2">Order</th><th className="p-2">SKU</th><th className="p-2 text-right">Units</th><th className="p-2 text-right">Estimated risk</th><th className="p-2">Level</th></tr></thead><tbody>{(predictions?.predictions??[]).slice().sort((a,b)=>b.delay_probability-a.delay_probability).slice(0,12).map(p=><tr key={p.order_id} className="border-b border-line/60"><td className="p-2">#{p.order_id}</td><td className="p-2">{p.sku}</td><td className="p-2 text-right">{p.quantity}</td><td className="p-2 text-right">{pct(p.delay_probability*100)}</td><td className="p-2 capitalize">{p.risk_level}</td></tr>)}</tbody></table></div>
   </>}
  </section>
  <section id="simulation" className="rounded-2xl border border-line bg-surface p-6 shadow-panel scroll-mt-24">
   <p className="text-xs font-semibold uppercase tracking-widest text-brand">Decision scenarios</p><h2 className="mt-1 text-xl font-semibold">What-if risk simulator</h2><p className="mt-1 text-sm text-muted">Change business assumptions, rerun a seeded Monte Carlo simulation and compare the previously solved allocation against the defer-all baseline.</p>
   {!runId?<p className="mt-5 rounded-lg bg-canvas p-4 text-sm text-muted">Run “Solve allocation” in the optimisation panel first to unlock scenario comparison.</p>:<>
    <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
     <label className="text-sm text-muted">Additional delay probability <span className="font-semibold text-ink">{delay}%</span><input className="mt-3 w-full accent-teal-600" aria-label="Additional delay probability" type="range" min="0" max="100" step="5" value={delay} onChange={e=>setDelay(Number(e.target.value))}/></label>
     <label className="text-sm text-muted">Delay penalty per unit (AUD)<input className="mt-1 w-full rounded-lg border border-line px-3 py-2 text-ink" type="number" min="0" max="10000" value={penalty} onChange={e=>setPenalty(Math.max(0,Number(e.target.value)))}/></label>
     <label className="text-sm text-muted">Shipping decision cost factor <span className="font-semibold text-ink">{costFactor}%</span><input aria-label="Shipping cost factor" className="mt-3 w-full accent-teal-600" type="range" min="50" max="200" step="5" value={costFactor} onChange={e=>setCostFactor(Number(e.target.value))}/></label>
     <label className="text-sm text-muted">Simulation trials<select value={trials} onChange={e=>setTrials(Number(e.target.value))} className="mt-1 block w-full rounded-lg border border-line bg-white px-3 py-2 text-ink"><option value={500}>500</option><option value={1000}>1,000</option><option value={3000}>3,000</option></select></label>
    </div>
    <button onClick={()=>void simulate()} disabled={busy!==''} className="mt-5 rounded-lg bg-brand px-5 py-2.5 font-semibold text-white hover:bg-brand-hover disabled:opacity-50">{busy==='simulate'?'Simulating…':'Run scenario comparison'}</button>
    {assumptionsChanged&&<p role="status" className="mt-2 text-xs font-medium text-amber-800">Inputs changed. The results below describe the previous run; select Run scenario comparison to recalculate.</p>}
    {sim&&<><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Illustrative baseline" value={money(sim.baseline_cost)} detail="Defer-all penalty"/><Metric label="Expected plan cost" value={money(sim.results.expected_plan_cost)} detail="Monte Carlo average"/><Metric label="Expected improvement" value={money(sim.results.expected_improvement)} detail="May be negative"/><Metric label="Chance plan beats baseline" value={pct(100*sim.results.probability_below_baseline)}/></div>
      <div className="mt-5 rounded-xl border border-line bg-white p-4 sm:p-5" aria-label="Scenario run comparison">
       <div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="text-sm font-semibold">Scenario comparison</h3><p className="mt-1 text-xs text-muted">The current and previous runs use the same warehouse decision run #{sim.run_id}. Only the declared simulation assumptions differ.</p></div><span className="rounded-full bg-brand-soft px-2.5 py-1 text-xs font-semibold text-brand">{previousSim?'2 runs compared':'1 run recorded'}</span></div>
       {previousSim?<>
        <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[470px] text-left text-xs"><thead><tr className="border-b border-line text-muted"><th className="py-2">Assumption / outcome</th><th>Previous run</th><th>Latest run</th></tr></thead><tbody>
         <tr className="border-b border-line/70"><td className="py-2">Additional delay risk</td><td>{(previousSim.assumptions.delay_probability*100).toFixed(0)}%</td><td>{(sim.assumptions.delay_probability*100).toFixed(0)}%</td></tr>
         <tr className="border-b border-line/70"><td className="py-2">Delay penalty per unit</td><td>{money(previousSim.assumptions.late_penalty_per_unit)}</td><td>{money(sim.assumptions.late_penalty_per_unit)}</td></tr>
         <tr className="border-b border-line/70"><td className="py-2">Shipping cost factor</td><td>{(previousSim.assumptions.shipping_cost_multiplier*100).toFixed(0)}%</td><td>{(sim.assumptions.shipping_cost_multiplier*100).toFixed(0)}%</td></tr>
         <tr className="border-b border-line/70"><td className="py-2">Simulation trials</td><td>{previousSim.assumptions.trials.toLocaleString()}</td><td>{sim.assumptions.trials.toLocaleString()}</td></tr>
         <tr className="font-semibold"><td className="py-2">Expected model cost</td><td>{money(previousSim.results.expected_plan_cost)}</td><td>{money(sim.results.expected_plan_cost)}</td></tr>
        </tbody></table></div>
        <p className="mt-3 text-sm font-semibold">Change in expected plan cost: <span className={sim.results.expected_plan_cost>previousSim.results.expected_plan_cost?'text-amber-800':'text-brand'}>{sim.results.expected_plan_cost>=previousSim.results.expected_plan_cost?'+':'−'}{money(Math.abs(sim.results.expected_plan_cost-previousSim.results.expected_plan_cost))}</span></p>
        <p className="mt-1 text-xs text-muted">Monte Carlo estimates depend on assumptions and sampling; differences are not realised savings or causal effects.</p>
       </>:<p className="mt-3 text-xs text-muted">Change an assumption and run the comparison again to see side-by-side inputs and outcomes.</p>}
       <div className="mt-4 space-y-3" role="img" aria-label="Expected modelled costs relative to the illustrative baseline">
        {[...(previousSim?[{name:'Previous',cost:previousSim.results.expected_plan_cost}]:[]),{name:'Latest',cost:sim.results.expected_plan_cost},{name:'Baseline',cost:sim.baseline_cost}].map(row=><div key={row.name} className="grid grid-cols-[64px_1fr_72px] items-center gap-2 text-xs"><span className="text-muted">{row.name}</span><div className="h-2.5 overflow-hidden rounded-full bg-canvas"><div className={`h-full rounded-full ${row.name==='Baseline'?'bg-slate-400':'bg-teal-600'}`} style={{width:`${Math.max(0,Math.min(100,100*row.cost/Math.max(sim.baseline_cost,sim.results.expected_plan_cost,previousSim?.results.expected_plan_cost??0,1)))}%`}}/></div><span className="text-right font-semibold tabular-nums">{money(row.cost)}</span></div>)}
       </div>
      </div>
      <div className="mt-5 rounded-xl border border-line p-4"><h3 className="text-sm font-semibold">Simulated cost range (10th–90th percentile)</h3><div className="mt-3 flex justify-between text-sm font-semibold"><span>{money(sim.results.plan_cost_p10)}</span><span>{money(sim.results.plan_cost_p90)}</span></div><p className="mt-2 text-xs text-muted">10th and 90th percentile modelled costs across the selected simulation trials.</p><p className="mt-3 text-xs text-muted">Expected improvement range: {money(sim.results.improvement_p10)} to {money(sim.results.improvement_p90)}. Distribution is assumption-driven; this is not a statistical confidence interval for realised savings.</p></div>
     </>}
   </>}
  </section>
  {(problem||message)&&<div role={problem?'alert':'status'} className={`rounded-xl border p-4 text-sm ${problem?'border-red-200 bg-red-50 text-red-800':'border-teal-200 bg-teal-50 text-teal-900'}`}>{problem||message}</div>}
  <p className="text-xs text-muted">Demonstration only. Actual history, ML-estimated risk and hypothetical scenario outputs are separate quantities; no claims of realised business savings are made.</p>
 </section>
}
