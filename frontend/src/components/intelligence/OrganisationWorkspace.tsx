import { useState } from 'react'
import type { FormEvent } from 'react'
import { ConnectorRegistry } from './ConnectorRegistry'

type Organisation = {id:number;name:string;role:string}
type Identity = {user:{id:number;email:string};organisations:Organisation[]}
type Project = {id:number;name:string;industry_id:string;organisation_id:number}
type Member = {user_id:number;email:string;role:string}
type Audit = {id:number;action:string;resource_type:string;resource_id:number|null;created_at:string}
const API=(import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/,'')

// Token is intentionally kept in React memory. Refresh clears the session.
// No cookies, localStorage, sessionStorage, or persisted credentials.
export function OrganisationWorkspace(){
 const [token,setToken]=useState<string|null>(null)
 const [email,setEmail]=useState('')
 const [password,setPassword]=useState('')
 const [identity,setIdentity]=useState<Identity|null>(null)
 const [selectedOrg,setSelectedOrg]=useState<number|null>(null)
 const [projects,setProjects]=useState<Project[]>([])
 const [members,setMembers]=useState<Member[]>([])
 const [audits,setAudits]=useState<Audit[]>([])
 const [projectName,setProjectName]=useState('')
 const [industry,setIndustry]=useState('agriculture')
 const [memberEmail,setMemberEmail]=useState('')
 const [memberRole,setMemberRole]=useState('viewer')
 const [message,setMessage]=useState('')
 const [busy,setBusy]=useState(false)

 async function call<T>(path:string, bearer:string, init?:RequestInit):Promise<T>{
  const response=await fetch(`${API}/api/v1/enterprise${path}`,{
   ...init,headers:{'Content-Type':'application/json',Authorization:`Bearer ${bearer}`,...init?.headers},
  })
  if(!response.ok){const body=await response.json().catch(()=>null) as {detail?:string}|null;throw new Error(body?.detail||`Request failed: ${response.status}`)}
  if(response.status===204)return undefined as T
  return await response.json() as T
 }
 async function loadOrg(bearer:string,id:number,role:string){
  const list=await call<Project[]>(`/organisations/${id}/projects`,bearer)
  setProjects(list)
  if(role==='owner'||role==='admin'){
   const [team,events]=await Promise.all([call<Member[]>(`/organisations/${id}/members`,bearer),call<Audit[]>(`/organisations/${id}/audit`,bearer)])
   setMembers(team);setAudits(events)
  }else{setMembers([]);setAudits([])}
 }
 async function signIn(e:FormEvent<HTMLFormElement>){
  e.preventDefault();setBusy(true);setMessage('')
  try{
   const response=await fetch(`${API}/api/v1/enterprise/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})})
   if(!response.ok)throw new Error(response.status===429?'Too many attempts. Try later.':'Invalid credentials or local service unavailable')
   const result=await response.json() as {access_token:string}
   const profile=await call<Identity>('/auth/me',result.access_token)
   setToken(result.access_token);setIdentity(profile);setPassword('')
   const first=profile.organisations[0];setSelectedOrg(first?.id??null)
   if(first)await loadOrg(result.access_token,first.id,first.role)
  }catch(err){setMessage(err instanceof Error?err.message:'Login unavailable')}
  finally{setBusy(false)}
 }
 async function chooseOrg(id:number){
  if(!token||!identity)return
  const org=identity.organisations.find(o=>o.id===id);if(!org)return
  setBusy(true);setMessage('');try{await loadOrg(token,id,org.role);setSelectedOrg(id)}catch(err){setMessage(String(err))}finally{setBusy(false)}
 }
 async function addProject(e:FormEvent<HTMLFormElement>){
  e.preventDefault();if(!token||selectedOrg===null)return
  setBusy(true);setMessage('');try{
   await call(`/organisations/${selectedOrg}/projects`,token,{method:'POST',body:JSON.stringify({name:projectName,industry_id:industry})})
   setProjectName('');await loadOrg(token,selectedOrg,current?.role||'viewer');setMessage('Project created in the selected organisation.')
  }catch(err){setMessage(String(err))}finally{setBusy(false)}
 }
 async function addMember(e:FormEvent<HTMLFormElement>){
  e.preventDefault();if(!token||selectedOrg===null)return
  setBusy(true);setMessage('');try{
   await call(`/organisations/${selectedOrg}/members`,token,{method:'POST',body:JSON.stringify({email:memberEmail,role:memberRole})})
   setMemberEmail('');await loadOrg(token,selectedOrg,current?.role||'viewer');setMessage('Existing user added to organisation.')
  }catch(err){setMessage(String(err))}finally{setBusy(false)}
 }
 async function logout(){
  const prior=token;setToken(null);setIdentity(null);setSelectedOrg(null);setProjects([]);setMembers([]);setAudits([]);setPassword('');setMessage('Signed out. Session cleared from this browser tab.')
  if(prior)try{await call('/auth/logout',prior,{method:'POST'})}catch{/* session already cleared locally */}
 }
 const current=identity?.organisations.find(o=>o.id===selectedOrg)
 const editable=current?.role==='owner'||current?.role==='admin'||current?.role==='analyst'
 const admin=current?.role==='owner'||current?.role==='admin'
 const input='mt-2 w-full rounded-lg border border-line bg-white px-3 py-2.5 text-sm text-ink'
 return <section id="enterprise-workspace" className="mt-6 scroll-mt-24 space-y-5" aria-label="Secure organisation workspace">
  <div className="rounded-2xl border border-line bg-surface p-6 shadow-panel">
   <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-widest text-brand">Phase 4B.1 · Identity foundation</p><h2 className="mt-2 text-2xl font-semibold text-ink">Organisation workspace</h2><p className="mt-2 max-w-3xl text-sm text-muted">Authenticated projects, organisation permissions, and audit history. Existing operations and optimisation are public <strong>synthetic demos</strong>, not tenant-isolated business records.</p></div><span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">Local security prototype · Not production certified</span></div>
   {message&&<p role="status" className="mt-4 rounded-lg border border-line bg-canvas p-3 text-sm">{message}</p>}
   {!token?<form onSubmit={e=>void signIn(e)} className="mt-6 max-w-md space-y-4"><p className="text-sm font-medium">Sign in with your locally bootstrapped administrator account</p><label className="block text-sm">Email<input type="email" autoComplete="username" required value={email} onChange={e=>setEmail(e.target.value)} className={input}/></label><label className="block text-sm">Password<input type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} className={input}/></label><button disabled={busy} className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy?'Authenticating…':'Sign in'}</button><p className="text-xs leading-5 text-muted">Accounts are created using a local server-side CLI, never with an unauthenticated browser registration form. Your token is held in memory until logout or refresh. Do not enter real company credentials.</p></form>:
    <div className="mt-6 space-y-5"><div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-canvas p-4"><div><p className="text-sm font-semibold">{identity?.user.email}</p><p className="text-xs text-muted">Authenticated local identity · Session not persisted in browser storage</p></div><button className="rounded-lg border border-line bg-white px-4 py-2 text-sm" onClick={()=>void logout()}>Sign out</button></div>
    <div className="grid gap-5 lg:grid-cols-2"><label className="block text-sm font-medium">Active organisation<select value={selectedOrg??''} onChange={e=>void chooseOrg(Number(e.target.value))} className={input}>{identity?.organisations.map(o=><option value={o.id} key={o.id}>{o.name} · {o.role}</option>)}</select></label><div className="rounded-xl border border-line p-4"><p className="text-xs text-muted">Workspace permissions</p><p className="mt-2 font-semibold">{current?.role||'No membership'}</p><p className="mt-1 text-xs text-muted">Projects are scoped by membership and organisation ID.</p></div></div>
    <div className="grid gap-5 lg:grid-cols-2"><div className="rounded-xl border border-line p-5"><h3 className="font-semibold">Organisation projects</h3><p className="mt-1 text-xs text-muted">Private project metadata · No company datasets connected</p><div className="mt-4 space-y-2">{projects.length?projects.map(p=><div className="flex justify-between gap-3 rounded-lg bg-canvas p-3 text-sm" key={p.id}><strong>{p.name}</strong><span className="text-muted">{p.industry_id}</span></div>):<p className="text-sm text-muted">No projects yet.</p>}</div>{editable&&<form onSubmit={e=>void addProject(e)} className="mt-5 space-y-3"><label className="block text-sm">Project name<input required minLength={2} maxLength={120} className={input} value={projectName} onChange={e=>setProjectName(e.target.value)}/></label><label className="block text-sm">Industry<select className={input} value={industry} onChange={e=>setIndustry(e.target.value)}><option value="agriculture">Agriculture & AgriTech</option><option value="technology">Technology & Software</option><option value="logistics">Logistics & Warehousing</option><option value="mining">Mining & Resources</option><option value="airline">Aviation</option></select></label><button disabled={busy} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Create project</button></form>}</div>
     <div className="rounded-xl border border-line p-5"><h3 className="font-semibold">Membership and permissions</h3>{admin?<><div className="mt-4 space-y-2">{members.map(m=><div className="flex justify-between rounded-lg bg-canvas p-3 text-sm" key={m.user_id}><span>{m.email}</span><strong>{m.role}</strong></div>)}</div><form className="mt-4 space-y-3" onSubmit={e=>void addMember(e)}><label className="block text-sm">Existing user email<input type="email" required className={input} value={memberEmail} onChange={e=>setMemberEmail(e.target.value)}/></label><label className="block text-sm">Assign role<select className={input} value={memberRole} onChange={e=>setMemberRole(e.target.value)}><option value="viewer">Viewer</option><option value="analyst">Analyst</option><option value="admin">Administrator</option></select></label><button disabled={busy} className="rounded-lg border border-line px-4 py-2 text-sm disabled:opacity-50">Add existing user</button></form></>:<p className="mt-3 text-sm text-muted">Member management requires administrator permissions.</p>}</div></div>
     {token&&selectedOrg!==null&&<ConnectorRegistry token={token} organisationId={selectedOrg} admin={!!admin}/>}
     {admin&&<div className="rounded-xl border border-line p-5"><h3 className="font-semibold">Security audit</h3><p className="mt-1 text-xs text-muted">Recent organisation events · No tokens or passwords logged</p><div className="mt-3 space-y-2">{audits.length?audits.map(a=><div className="flex flex-wrap justify-between gap-2 border-b border-line py-2 text-xs" key={a.id}><span className="font-semibold">{a.action}</span><span className="text-muted">{a.resource_type} · {a.created_at.slice(0,19).replace('T',' ')}</span></div>):<p className="text-sm text-muted">No organisation audit events yet.</p>}</div></div>}
    </div>}
  </div>
 </section>
}
