import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ProjectOptimisation } from './ProjectOptimisation'

export type Project = {id:number;name:string;industry_id:string;organisation_id:number}
type Dataset = {id:number;row_count:number;source_filename:string;sha256:string;imported_at:string}
type Summary = {dataset:Dataset|null;total_orders:number;pending_orders:number;late_deliveries:number;gross_sales_aud:number;estimated_margin_aud:number;warehouse_count:number;status_counts:Record<string,number>}
type Order = {order_id:string;order_date:string;warehouse_id:string;sku:string;quantity:number;priority:string;status:string;promised_date:string;shipped_date:string|null;unit_price_aud:number;unit_cost_aud:number;shipping_cost_aud:number;destination_region:string}
type Page = {total:number;limit:number;offset:number;items:Order[]}
const API=(import.meta.env.VITE_API_BASE_URL??'http://127.0.0.1:8000').replace(/\/$/,'')
const MAX_SIZE=2_000_000
const money=(n:number)=>new Intl.NumberFormat('en-AU',{style:'currency',currency:'AUD',maximumFractionDigits:2}).format(n)
async function api<T>(url:string,token:string,init?:RequestInit):Promise<T>{
 const response=await fetch(url,{...init,headers:{Authorization:`Bearer ${token}`,...init?.headers}})
 if(!response.ok){const data=await response.json().catch(()=>null) as {detail?:string}|null;throw new Error(data?.detail||`Request failed (${response.status})`)}
 return response.json() as Promise<T>
}

/** Tenant-scoped CSV pilot, deliberately separate from the shared synthetic demo tables. */
export function ProjectDataStudio({project,token,canEdit,onImported}:{project:Project;token:string;canEdit:boolean;onImported?:()=>void}){
 const [summary,setSummary]=useState<Summary|null>(null)
 const [page,setPage]=useState<Page|null>(null)
 const [file,setFile]=useState<File|null>(null)
 const [status,setStatus]=useState('')
 const [error,setError]=useState('')
 const [filter,setFilter]=useState('')
 const [offset,setOffset]=useState(0)
 const [uploading,setUploading]=useState(false)
 const base=`${API}/api/v1/enterprise/organisations/${project.organisation_id}/projects/${project.id}`
 useEffect(()=>{
  let active=true
  const params=new URLSearchParams({offset:String(offset),limit:'25'})
  if(filter)params.set('status',filter)
  Promise.all([api<Summary>(`${base}/orders/summary`,token),api<Page>(`${base}/orders?${params}`,token)])
   .then(([summaryResult,pageResult])=>{if(active){setSummary(summaryResult);setPage(pageResult);setError('')}})
   .catch(e=>{if(active)setError(e instanceof Error?e.message:'Project data unavailable')})
  return()=>{active=false}
 },[base,token,offset,filter,status])
 async function upload(event:FormEvent<HTMLFormElement>){
  event.preventDefault()
  if(!file)return
  if(!file.name.toLowerCase().endsWith('.csv')||file.size>MAX_SIZE){setError('Choose a CSV file no larger than 2 MB.');return}
  if(summary?.dataset&&!window.confirm('Replace the existing project dataset? Validation is completed before replacement.'))return
  setUploading(true);setError('');setStatus('')
  try{
   const raw=await file.arrayBuffer()
   await api(`${base}/orders/import`,token,{method:'POST',headers:{'Content-Type':'text/csv','X-Filename':file.name},body:raw})
   setFile(null);setOffset(0);setFilter('');setStatus(`Imported ${file.name} into ${project.name}.`);onImported?.()
  }catch(e){setError(e instanceof Error?e.message:'Import failed; prior dataset retained')}
  finally{setUploading(false)}
 }
 if(project.industry_id!=='logistics')return <section id="enterprise-data" className="scroll-mt-24 rounded-2xl border border-line bg-white p-6"><h2 className="text-xl font-bold">Project data</h2><p className="mt-2 text-sm text-muted">Structured CSV import currently supports Logistics & Warehousing projects only. Other industry adapters are not yet implemented.</p></section>
 return <div className="space-y-5" aria-label="Private project data studio">
  <section id="enterprise-data" className="scroll-mt-24 rounded-2xl border border-line bg-white p-6 shadow-panel">
   <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-brand">PROJECT DATA · PRIVATE WORKSPACE</p><h2 className="mt-2 text-2xl font-bold">{project.name}</h2><p className="mt-2 text-sm text-muted">Upload a validated order CSV, then explore only this project's stored records. This is not the public synthetic demo.</p></div><span className="rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand">Organisation-scoped</span></div>
   {error&&<p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
   {status&&<p role="status" className="mt-4 rounded-lg border border-teal-200 bg-brand-soft p-3 text-sm text-brand">{status}</p>}
   {summary?.dataset&&<div className="mt-5 rounded-xl bg-canvas p-4 text-sm"><strong>Imported dataset:</strong> {summary.dataset.source_filename} · {summary.dataset.row_count.toLocaleString()} records · {new Date(summary.dataset.imported_at).toLocaleString('en-AU')}<p className="mt-1 break-all text-xs text-muted">SHA-256: {summary.dataset.sha256}</p></div>}
   {canEdit?<form onSubmit={e=>void upload(e)} className="mt-5 space-y-3"><label className="block text-sm font-semibold" htmlFor="project-csv">Select a logistics orders CSV (UTF-8, ≤2 MB, up to 2,000 rows)</label><input id="project-csv" type="file" accept=".csv,text/csv" onChange={e=>setFile(e.target.files?.[0]??null)} className="block w-full rounded-lg border border-line bg-canvas p-3 text-sm"/><p className="text-xs leading-5 text-muted">The importer requires the 13 columns in the Acme Logistics sample, in the same order. Imports are all-or-nothing. Re-import replaces this project's previous CSV; no raw file is retained.</p><button disabled={!file||uploading} className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40">{uploading?'Validating and importing…':summary?.dataset?'Validate & replace dataset':'Validate & import CSV'}</button></form>:<p className="mt-4 text-sm text-muted">Your Viewer role permits authorised reading, not uploading. Ask an Analyst or administrator to import data.</p>}
  </section>
  <section id="enterprise-analytics" className="scroll-mt-24 rounded-2xl border border-line bg-white p-6 shadow-panel"><h2 className="text-xl font-bold">Project analytics</h2><p className="mt-1 text-sm text-muted">Calculated from private PostgreSQL records. Gross sales and margin are illustrative, not realised profit; margin subtracts unit cost and a per-order shipping cost.</p>
   {!summary?.dataset?<p className="mt-5 rounded-lg bg-canvas p-4 text-sm text-muted">No project dataset imported. Start with the CSV upload above.</p>:<><div className="mt-5 grid grid-cols-2 gap-3 xl:grid-cols-3">{[{label:'Orders',value:summary.total_orders.toLocaleString()},{label:'Pending',value:summary.pending_orders.toLocaleString()},{label:'Recorded late dispatches',value:summary.late_deliveries.toLocaleString()},{label:'Gross sales',value:money(summary.gross_sales_aud)},{label:'Estimated order margin',value:money(summary.estimated_margin_aud)},{label:'Warehouses',value:summary.warehouse_count.toLocaleString()}].map(k=><div key={k.label} className="rounded-xl border border-line bg-canvas p-4"><p className="text-xs text-muted">{k.label}</p><p className="mt-2 text-2xl font-bold tabular-nums">{k.value}</p></div>)}</div><div className="mt-5"><h3 className="text-sm font-bold">Order status breakdown</h3><div className="mt-3 space-y-3">{Object.entries(summary.status_counts).map(([key,count])=><div key={key}><div className="flex justify-between text-xs"><span className="capitalize">{key}</span><strong>{count}</strong></div><div className="mt-1 h-2 rounded-full bg-canvas"><div className="h-2 rounded-full bg-teal-600" style={{width:`${100*count/Math.max(1,summary.total_orders)}%`}}/></div></div>)}</div></div></>}
  </section>
  <section id="enterprise-orders" className="scroll-mt-24 rounded-2xl border border-line bg-white p-6 shadow-panel"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-bold">Project orders</h2><p className="mt-1 text-sm text-muted">Server-side pagination and status filtering. Only authorised project data is returned.</p></div><label className="text-sm">Status <select className="ml-2 rounded-lg border border-line bg-white px-3 py-2" value={filter} onChange={e=>{setFilter(e.target.value);setOffset(0)}}><option value="">All statuses</option>{['pending','shipped','delivered','cancelled'].map(s=><option key={s} value={s}>{s}</option>)}</select></label></div>
   <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[740px] text-left text-xs"><thead><tr className="border-b border-line text-muted">{['Order','Date','Warehouse','SKU','Units','Status','Promised','Region'].map(h=><th key={h} className="px-3 py-3 font-semibold">{h}</th>)}</tr></thead><tbody>{page?.items.map(o=><tr key={o.order_id} className="border-b border-line/70 hover:bg-canvas"><td className="px-3 py-3 font-medium">{o.order_id}</td><td className="px-3 py-3">{o.order_date}</td><td className="px-3 py-3">{o.warehouse_id}</td><td className="px-3 py-3">{o.sku}</td><td className="px-3 py-3">{o.quantity}</td><td className="px-3 py-3 capitalize">{o.status}</td><td className="px-3 py-3">{o.promised_date}</td><td className="px-3 py-3">{o.destination_region}</td></tr>)}</tbody></table></div>
   {!page?.items.length&&<p className="mt-4 text-sm text-muted">No orders to display.</p>}<div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted"><span>Showing {page?.total?offset+1:0}–{Math.min(offset+25,page?.total??0)} of {page?.total??0} orders</span><div className="flex gap-2"><button type="button" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-25))} className="rounded-lg border border-line px-3 py-2 disabled:opacity-40">Previous</button><button type="button" disabled={offset+25>=(page?.total??0)} onClick={()=>setOffset(offset+25)} className="rounded-lg border border-line px-3 py-2 disabled:opacity-40">Next</button></div></div>
  </section>
  <ProjectOptimisation project={project} token={token} canRun={canEdit} datasetHash={summary?.dataset?.sha256??null} />
 </div>
}
