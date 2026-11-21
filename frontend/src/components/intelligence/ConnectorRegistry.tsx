import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

type Connector = {id:number;display_name:string;kind:string;provider:string;status:string}
type ConnectorType = {provider:string;kind:string;execution_supported:boolean;credentials_supported:boolean}
const API=(import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/,'')

export function ConnectorRegistry({ token, organisationId, admin }: { token:string;organisationId:number;admin:boolean }) {
  const [types,setTypes]=useState<ConnectorType[]>([])
  const [items,setItems]=useState<Connector[]>([])
  const [name,setName]=useState('')
  const [provider,setProvider]=useState('postgresql')
  const [message,setMessage]=useState('')
  const [busy,setBusy]=useState(false)
  const root=`${API}/api/v1/enterprise`
  const headers={Authorization:`Bearer ${token}`}
  useEffect(()=>{
    let active=true
    async function load(){
      try{
        const [catalogue,list]=await Promise.all([
          fetch(`${root}/connector-types`,{headers}),
          fetch(`${root}/organisations/${organisationId}/connectors`,{headers}),
        ])
        if(!catalogue.ok||!list.ok)throw new Error('Connector catalogue unavailable')
        const c=await catalogue.json() as {connectors:ConnectorType[]}
        const l=await list.json() as Connector[]
        if(active){setTypes(c.connectors);setItems(l);setMessage('')}
      }catch{if(active)setMessage('Could not load connector metadata. Check your session and backend.')}
    }
    void load()
    return()=>{active=false}
  },[root,token,organisationId])
  async function register(e:FormEvent<HTMLFormElement>){
    e.preventDefault()
    const chosen=types.find(t=>t.provider===provider)
    if(!chosen)return
    setBusy(true);setMessage('')
    try{
      const res=await fetch(`${root}/organisations/${organisationId}/connectors`,{
        method:'POST',headers:{...headers,'Content-Type':'application/json'},
        body:JSON.stringify({display_name:name,provider,kind:chosen.kind}),
      })
      if(!res.ok)throw new Error(`Registration failed (${res.status})`)
      const saved=await res.json() as Connector
      setItems(list=>[...list,saved]);setName('');setMessage('Connector metadata registered. Data access remains disabled.')
    }catch(error){setMessage(error instanceof Error?error.message:'Could not register connector')}
    finally{setBusy(false)}
  }
  async function remove(id:number){
    setBusy(true);setMessage('')
    try{
      const res=await fetch(`${root}/organisations/${organisationId}/connectors/${id}`,{method:'DELETE',headers})
      if(!res.ok)throw new Error(`Removal failed (${res.status})`)
      setItems(list=>list.filter(item=>item.id!==id));setMessage('Connector metadata removed.')
    }catch(error){setMessage(error instanceof Error?error.message:'Could not remove connector')}
    finally{setBusy(false)}
  }
  return <div className="rounded-xl border border-line p-5 space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div><h3 className="font-semibold">Data connector registry</h3>
        <p className="mt-1 text-xs text-muted">Organisation-scoped connection catalogue. No credentials, data transfer, or live execution yet.</p></div>
      <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">Connections disabled</span>
    </div>
    {message&&<p role="status" className="rounded-lg bg-canvas p-3 text-sm">{message}</p>}
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{items.map(item=><div className="rounded-lg border border-line p-3" key={item.id}>
      <p className="text-sm font-semibold">{item.display_name}</p><p className="mt-1 text-xs text-muted">{item.provider} · {item.kind}</p>
      <p className="mt-2 text-xs font-medium text-amber-800">Not configured — no data connected</p>
      {admin&&<button disabled={busy} type="button" onClick={()=>void remove(item.id)} className="mt-3 rounded-md border border-line px-3 py-1 text-xs disabled:opacity-50">Remove</button>}
    </div>)}</div>
    {!items.length&&<p className="text-sm text-muted">No connections registered in this organisation.</p>}
    {admin?<form onSubmit={e=>void register(e)} className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
      <label className="block text-sm">Connection label<input required minLength={2} maxLength={120} value={name} onChange={e=>setName(e.target.value)} className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2.5 text-sm" placeholder="e.g. Finance reporting DB"/></label>
      <label className="block text-sm">Provider<select value={provider} onChange={e=>setProvider(e.target.value)} className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2.5 text-sm">{types.map(type=><option key={type.provider} value={type.provider}>{type.provider} ({type.kind})</option>)}</select></label>
      <button disabled={busy||!types.length} className="rounded-lg bg-brand px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">Register metadata</button>
    </form>:<p className="text-xs text-muted">Only organisation administrators and owners can register connectors.</p>}
    <p className="text-xs text-muted">Never enter real API keys here. Live connectors require a separate credential vault, host allowlists, read-only authorisation and security review.</p>
  </div>
}
