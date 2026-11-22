import { useEffect, useState } from 'react'

type Industry = 'logistics' | 'agriculture' | 'technology'
type Option = { item_id: string; option_id: string; objective_value: number; resources: Record<string, number> }
type Scenario = { industry: Industry; objective: string; capacities: Record<string, number>; options: Option[]; input_provenance: string }
type Result = { status: string; objective_value: number | null; message: string; input_provenance: string; decisions: {item_id:string;option_id:string;contribution:number}[]; constraint_usage: Record<string, {used:number;limit:number}>; assumptions?:string[] }
type Catalogue = { data_sources: {industry:string;name:string;url:string;license:string;use:string;missing:string}[] }
const API = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const labels: Record<Industry,string> = {logistics:'Logistics & supply chain',agriculture:'Agriculture & AgriTech',technology:'Technology & cloud'}
const pretty = (str:string) => str.replaceAll('_',' ')

export function IndustryPilotStudio() {
  const [industry,setIndustry] = useState<Industry>('logistics')
  const [scenario,setScenario] = useState<Scenario|null>(null)
  const [catalogue,setCatalogue] = useState<Catalogue|null>(null)
  const [csvText,setCsvText] = useState('')
  const [fileName,setFileName] = useState('')
  const [result,setResult] = useState<Result|null>(null)
  const [busy,setBusy] = useState(false)
  const [error,setError] = useState('')
  const [mode,setMode] = useState<'demo'|'csv'>('demo')
  useEffect(()=>{
    let active=true
    void fetch(`${API}/api/v1/industry-pilots/presets/${industry}`).then(async r=>{if(!r.ok)throw new Error('Could not retrieve industry pilot'); return r.json() as Promise<{scenario:Scenario}>}).then(data=>{if(active)setScenario(data.scenario)}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Pilot unavailable')})
    return()=>{active=false}
  },[industry])
  useEffect(()=>{void fetch(`${API}/api/v1/industry-pilots/catalogue`).then(r=>r.ok?r.json():Promise.reject(new Error('Source catalogue unavailable'))).then(setCatalogue).catch(()=>{})},[])
  async function run(){
    if(!scenario)return
    setBusy(true);setError('');setResult(null)
    const payload=mode==='csv'?{industry, capacities:scenario.capacities,csv_text:csvText}:scenario
    try{
      const response=await fetch(`${API}/api/v1/industry-pilots/${mode==='csv'?'solve-csv':'solve'}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      const output=await response.json() as Result & {detail?:string}
      if(!response.ok)throw new Error(typeof output.detail==='string'?output.detail:`Scenario rejected (${response.status})`)
      setResult(output)
    }catch(e){setError(e instanceof Error?e.message:'Solver request failed')}
    finally{setBusy(false)}
  }
  async function readCSV(file?:File){setCsvText('');setFileName('');setResult(null);setError('');if(!file)return;if(file.size>100000){setError('Maximum CSV size is 100 KB');return}if(!file.name.toLowerCase().endsWith('.csv')){setError('Choose a CSV file');return}setCsvText(await file.text());setFileName(file.name)}
  return <section id="industry-pilots" className="mt-6 scroll-mt-24 rounded-2xl border border-line bg-surface p-6 shadow-panel" aria-labelledby="pilot-heading">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-widest text-brand">MULTI-INDUSTRY SOLVER LAB</p><h2 id="pilot-heading" className="mt-2 text-xl font-semibold text-ink">Verified assignment-model pilots</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-muted">Three constrained integer models share a mathematical engine. The choices and coefficients below are <strong>hypothetical</strong>, not observed company performance. Global optimality applies only to the displayed finite model.</p></div><span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs text-amber-900">Public synthetic demo · no sensitive data</span></div>
    <div className="mt-6 grid gap-4 md:grid-cols-2"><label className="text-sm font-medium text-ink">Industry pilot<select className="mt-2 block w-full rounded-lg border border-line bg-white p-3" value={industry} onChange={e=>{setIndustry(e.target.value as Industry);setScenario(null);setResult(null);setCsvText('');setFileName('');setError('');setMode('demo')}}>{(Object.keys(labels) as Industry[]).map(k=><option key={k} value={k}>{labels[k]}</option>)}</select></label><label className="text-sm font-medium text-ink">Input method<select className="mt-2 block w-full rounded-lg border border-line bg-white p-3" value={mode} onChange={e=>{setMode(e.target.value as 'demo'|'csv');setResult(null);setError('')}}><option value="demo">Built-in hypothetical case</option><option value="csv">Upload non-confidential decision-options CSV</option></select></label></div>
    {scenario&&<div className="mt-5 rounded-xl bg-canvas p-4"><p className="font-semibold text-ink">Model: {pretty(scenario.objective)}</p><p className="mt-1 text-xs text-muted">Each item must choose exactly one eligible option. Editable resource capacities apply to both built-in and CSV cases. This is not a general crop-response, routing or cloud-SLA optimiser.</p><div className="mt-3 grid gap-3 sm:grid-cols-2">{Object.entries(scenario.capacities).map(([k,v])=><label key={k} className="text-sm text-muted">{pretty(k)}<input className="mt-1 block w-full rounded-lg border border-line bg-white px-3 py-2 text-ink" type="number" min="0" max="1000000" step="any" value={v} onChange={e=>{setScenario(prev=>prev?{...prev,capacities:{...prev.capacities,[k]:e.target.value===''?0:Number(e.target.value)}}:prev);setResult(null)}}/></label>)}</div></div>}
    {mode==='csv'&&<div className="mt-4 rounded-xl border border-line p-4"><label className="block text-sm font-medium">Choose a local CSV (max 100 KB)<input type="file" accept=".csv,text/csv" className="mt-2 block w-full text-sm" onChange={e=>void readCSV(e.target.files?.[0])}/></label><p className="mt-2 text-xs text-muted">Required columns: item_id, option_id, objective_value, {scenario?Object.keys(scenario.capacities).join(', '):'resource columns'}. One row per eligible decision. Do not upload private, financial or personally identifying information; this demo endpoint is public.</p>{fileName&&<p className="mt-2 text-sm">Loaded locally: {fileName}</p>}</div>}
    <div className="mt-5 flex flex-wrap items-center gap-3"><button className="rounded-lg bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-hover disabled:opacity-50" disabled={busy||!scenario||(mode==='csv'&&!csvText)} onClick={()=>void run()}>{busy?'Solving…':'Solve this decision model'}</button><span className="text-xs text-muted">No external service actions or persistent dataset uploads</span></div>
    {error&&<p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
    {result&&<div role="status" aria-live="polite" className={`mt-6 rounded-xl border p-5 ${result.status==='optimal'?'border-teal-200 bg-teal-50/30':'border-amber-200 bg-amber-50/40'}`}><p className={`mb-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${result.status==='optimal'?'bg-teal-100 text-teal-900':'bg-amber-100 text-amber-900'}`}>{result.status==='optimal'?'Optimal for formulated model':'No certified optimum'}</p><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold text-ink">Solver outcome: {result.status.replaceAll('_',' ')}</h3><span className="text-xs text-muted">Input provenance: {pretty(result.input_provenance)}</span></div><p className="mt-2 text-sm text-muted">{result.message}</p>{result.objective_value!==null&&<p className="mt-4 text-3xl font-semibold text-ink">{new Intl.NumberFormat('en-AU',{maximumFractionDigits:2}).format(result.objective_value)} <span className="text-sm font-normal text-muted">{industry==='agriculture'?'hypothetical margin (AUD)':'hypothetical cost units'}</span></p>}
      <div className="mt-4 grid gap-4 lg:grid-cols-2"><div><h4 className="text-sm font-semibold">Selected assignments</h4><div className="mt-2 max-h-64 overflow-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b border-line"><th className="py-2">Item</th><th>Decision</th><th className="text-right">Value</th></tr></thead><tbody>{result.decisions.map(d=><tr key={d.item_id} className="border-b border-line/60"><td className="py-2">{d.item_id}</td><td>{d.option_id}</td><td className="text-right">{d.contribution}</td></tr>)}</tbody></table></div></div><div><h4 className="text-sm font-semibold">Verified resource limits</h4>{Object.entries(result.constraint_usage).map(([k,v])=><div className="mt-3" key={k}><div className="flex justify-between gap-2 text-xs"><span>{pretty(k)}</span><span>{v.used} / {v.limit}</span></div><div className="mt-1 h-2 rounded-full bg-slate-200"><div className="h-2 rounded-full bg-teal-700" style={{width:`${v.limit?Math.min(100,100*v.used/v.limit):0}%`}}/></div></div>)}</div></div>
      <p className="mt-4 text-xs text-muted">No baseline improvement or realised savings claimed. The model treats cost, margin and resource coefficients as supplied inputs, not independently validated facts.</p></div>}
    {catalogue&&<div className="mt-6 border-t border-line pt-5"><h3 className="font-semibold">Authentic data sources — research references</h3><p className="mt-1 text-xs leading-5 text-muted">These sources have not been downloaded or used as coefficients in the built-in pilot cases. They require transformation, attribution and explicit business assumptions.</p><div className="mt-3 grid gap-3 md:grid-cols-3">{catalogue.data_sources.map(src=><article className="rounded-xl bg-canvas p-4" key={src.industry}><a href={src.url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-brand underline">{src.name}</a><p className="mt-2 text-xs text-muted">{src.use}</p><p className="mt-2 text-xs text-muted">Missing inputs: {src.missing}</p><p className="mt-2 text-xs text-muted">Licence: {src.license}</p></article>)}</div></div>}
  </section>
}
