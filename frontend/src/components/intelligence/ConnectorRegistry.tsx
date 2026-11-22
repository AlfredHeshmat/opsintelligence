import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'

type Connector = {id:number;display_name:string;kind:string;provider:string;status:string;purpose:string;data_classification:string;execution_enabled:boolean}
type ConnectorType = {provider:string;kind:string;execution_supported:boolean;credentials_supported:boolean}
const API=(import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/,'')

export function ConnectorRegistry({ token, organisationId, role, onAuditChange }: { token:string;organisationId:number;role:string;onAuditChange:()=>Promise<void> }) {
  const [types,setTypes]=useState<ConnectorType[]>([])
  const [items,setItems]=useState<Connector[]>([])
  const [name,setName]=useState('')
  const [purpose,setPurpose]=useState('Synthetic demonstration data source')
  const [classification,setClassification]=useState('internal')
  const [provider,setProvider]=useState('postgresql')
  const [message,setMessage]=useState('')
  const [busy,setBusy]=useState(false)
  const [connection,setConnection]=useState<{id:number;tables:string[];selected:string;rows:Record<string,string|null>[];message:string}|null>(null)
  const root=`${API}/api/v1/enterprise`
  const admin=role==='owner'||role==='admin'
  const refresh=useCallback(async()=>{
    const [catalogue,list]=await Promise.all([
      fetch(`${root}/connector-types`,{headers:{Authorization:`Bearer ${token}`}}),
      fetch(`${root}/organisations/${organisationId}/connectors`,{headers:{Authorization:`Bearer ${token}`}}),
    ])
    if(!catalogue.ok||!list.ok)throw new Error('Connector catalogue unavailable')
    const c=await catalogue.json() as {connectors:ConnectorType[]}
    setTypes(c.connectors)
    setItems(await list.json() as Connector[])
  },[root,token,organisationId])
  useEffect(()=>{
    let active=true
    void Promise.resolve().then(()=>{if(active)return refresh()}).catch(()=>{if(active)setMessage('Could not load connector metadata. Check your session and backend.')})
    return()=>{active=false}
  },[refresh])
  async function mutate(path:string,method:'POST'|'DELETE', body?:unknown){
    setBusy(true);setMessage('')
    try{
      const res=await fetch(`${root}/organisations/${organisationId}/connectors${path}`,{
        method,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
        ...(body===undefined?{}:{body:JSON.stringify(body)}),
      })
      if(!res.ok){const error=await res.json().catch(()=>({detail:`Request failed (${res.status})`})) as {detail?:string};throw new Error(error.detail||`Request failed (${res.status})`)}
      await refresh()
      await onAuditChange()
      setMessage('Connector metadata updated. No external connection or data transfer was performed.')
    }catch(error){setMessage(error instanceof Error?error.message:'Connector update failed')}
    finally{setBusy(false)}
  }
  async function probe(id:number, table?:string){
    setBusy(true);setMessage('')
    try{
      const endpoint=table?'table-preview':'connection-check'
      const response=await fetch(`${root}/organisations/${organisationId}/connectors/${id}/${endpoint}`,{
        method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
        ...(table?{body:JSON.stringify({table})}:{}),
      })
      const body=await response.json() as {detail?:string;allowed_tables?:string[];rows?:Record<string,string|null>[]}
      if(!response.ok)throw new Error(body.detail||`Connector check failed (${response.status})`)
      setConnection(previous=>({id,tables:body.allowed_tables||previous?.tables||[],
        selected:table||body.allowed_tables?.[0]||previous?.selected||'',
        rows:body.rows||[],message:table?'Showing up to 25 sampled rows.':'Read-only connection verified.'}))
      await onAuditChange()
    }catch(error){setMessage(error instanceof Error?error.message:'Connector check failed')}
    finally{setBusy(false)}
  }
  async function register(e:FormEvent<HTMLFormElement>){
    e.preventDefault()
    const chosen=types.find(t=>t.provider===provider)
    if(!chosen)return
    await mutate('', 'POST', {display_name:name,provider,kind:chosen.kind,purpose,data_classification:classification})
    setName('')
  }
  const input='mt-2 w-full rounded-lg border border-line bg-white px-3 py-2.5 text-sm text-ink'
  return <div className="rounded-xl border border-line p-5 space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div><h3 className="font-semibold">Data connector governance</h3>
        <p className="mt-1 text-xs text-muted">Organisation-scoped governance and audited controls. Optional operator-provisioned, read-only PostgreSQL preview; credentials never enter the browser.</p></div>
      <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">Real-data connections disabled by default</span>
    </div>
    {message&&<p role="status" className="rounded-lg bg-canvas p-3 text-sm">{message}</p>}
    <div className="grid gap-3 sm:grid-cols-2">{items.map(item=><div className="rounded-lg border border-line p-4" key={item.id}>
      <p className="text-sm font-semibold">{item.display_name}</p>
      <p className="mt-1 text-xs text-muted">{item.provider} · {item.kind} · {item.data_classification}</p>
      <p className="mt-2 text-xs text-muted">{item.purpose}</p>
      <p className="mt-3 text-xs font-semibold text-amber-800">{item.status.replaceAll('_',' ')} · General integrations disabled; demo preview requires explicit operator provisioning</p>
      {admin&&item.provider==='postgresql'&&item.status==='metadata_approved'&&item.data_classification!=='restricted'&&item.data_classification!=='confidential'&&<div className="mt-3">
        <button type="button" disabled={busy} onClick={()=>void probe(item.id)} className="rounded-md border border-line px-3 py-1.5 text-xs disabled:opacity-50">Check operator-provisioned read-only connection</button>
        {connection?.id===item.id&&<div className="mt-3 space-y-2 rounded-lg border border-line bg-canvas p-3">
          <p className="text-xs text-muted">{connection.message} Synthetic demonstration sources only.</p>
          {connection.tables.length>0&&<div className="flex flex-wrap items-center gap-2">
            <label className="text-xs" htmlFor={`table-${item.id}`}>Allowlisted table</label>
            <select id={`table-${item.id}`} className="rounded border border-line p-1.5 text-xs" value={connection.selected} onChange={e=>setConnection({...connection,selected:e.target.value,rows:[]})}>{connection.tables.map(t=><option key={t}>{t}</option>)}</select>
            <button type="button" disabled={busy} onClick={()=>void probe(item.id,connection.selected)} className="rounded-md border border-line px-3 py-1.5 text-xs">Preview up to 25 rows</button>
          </div>}
          {connection.rows.length>0&&<div className="overflow-auto max-h-72"><table className="w-full text-left text-xs"><thead><tr>{Object.keys(connection.rows[0]).map(key=><th key={key} className="border-b p-2">{key}</th>)}</tr></thead><tbody>{connection.rows.map((row,index)=><tr key={index}>{Object.keys(row).map(key=><td className="border-b p-2" key={key}>{row[key]}</td>)}</tr>)}</tbody></table></div>}
        </div>}
      </div>}
      {admin&&<div className="mt-3 flex flex-wrap gap-2">
        {item.status==='not_configured'&&<button disabled={busy} type="button" onClick={()=>void mutate(`/${item.id}/request-review`,'POST')} className="rounded-md border border-line px-3 py-1.5 text-xs disabled:opacity-50">Request review</button>}
        {item.status==='pending_review'&&role==='owner'&&<button disabled={busy} type="button" onClick={()=>void mutate(`/${item.id}/approve-metadata`,'POST')} className="rounded-md border border-line px-3 py-1.5 text-xs disabled:opacity-50">Approve metadata</button>}
        {item.status!=='disabled'&&<button disabled={busy} type="button" onClick={()=>void mutate(`/${item.id}/disable`,'POST')} className="rounded-md border border-line px-3 py-1.5 text-xs disabled:opacity-50">Disable</button>}
        <button disabled={busy} type="button" onClick={()=>{if(window.confirm('Remove this connector registry record?'))void mutate(`/${item.id}`,'DELETE')}} className="rounded-md border border-line px-3 py-1.5 text-xs disabled:opacity-50">Remove</button>
      </div>}
    </div>)}</div>
    {!items.length&&<p className="text-sm text-muted">No connector metadata registered in this organisation.</p>}
    {admin?<form onSubmit={e=>void register(e)} className="grid gap-3 sm:grid-cols-2">
      <label className="block text-sm">Connection label<input required minLength={2} maxLength={120} value={name} onChange={e=>setName(e.target.value)} className={input} placeholder="e.g. Warehouse analytics demo"/></label>
      <label className="block text-sm">Provider<select value={provider} onChange={e=>setProvider(e.target.value)} className={input}>{types.map(type=><option key={type.provider} value={type.provider}>{type.provider} ({type.kind})</option>)}</select></label>
      <label className="block text-sm">Purpose<input required minLength={10} maxLength={300} value={purpose} onChange={e=>setPurpose(e.target.value)} className={input}/></label>
      <label className="block text-sm">Data classification<select value={classification} onChange={e=>setClassification(e.target.value)} className={input}><option value="public">Public</option><option value="internal">Internal</option><option value="confidential">Confidential</option><option value="restricted">Restricted</option></select></label>
      <div className="sm:col-span-2"><button disabled={busy||!types.length} className="rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">Register connector metadata</button></div>
    </form>:<p className="text-xs text-muted">Administrator permissions are required to register connectors.</p>}
    <p className="text-xs text-muted">Metadata approval never grants database access. Never enter passwords, connection strings or API keys into the fields above.</p>
  </div>
}
