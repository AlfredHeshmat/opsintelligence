import { useState } from 'react'
import type { FormEvent } from 'react'
import { ConnectorRegistry } from './ConnectorRegistry'
import { ProjectDataStudio } from './ProjectDataStudio'

type Organisation = {id:number;name:string;role:string}
type Identity = {user:{id:number;email:string};organisations:Organisation[]}
type Project = {id:number;name:string;industry_id:string;organisation_id:number}
type Member = {user_id:number;email:string;role:string}
type Invitation = {id:number;email:string;role:string;status:string;expires_at:string;created_at:string}
type InvitationIssued = Invitation & {code:string}
type Audit = {id:number;action:string;resource_type:string;resource_id:number|null;created_at:string}
const API=(import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/,'')

// Token is intentionally kept in React memory. Refresh clears the session.
// No cookies, localStorage, sessionStorage, or persisted credentials.
export function OrganisationWorkspace({onExit}:{onExit?:()=>void}){
 const [token,setToken]=useState<string|null>(null)
 const [email,setEmail]=useState('')
 const [password,setPassword]=useState('')
 const [registering,setRegistering]=useState(false)
 const [companyName,setCompanyName]=useState('')
 const [confirmPassword,setConfirmPassword]=useState('')
 const [identity,setIdentity]=useState<Identity|null>(null)
 const [selectedOrg,setSelectedOrg]=useState<number|null>(null)
 const [projects,setProjects]=useState<Project[]>([])
 const [selectedProject,setSelectedProject]=useState<number|null>(null)
 const [members,setMembers]=useState<Member[]>([])
 const [invitations,setInvitations]=useState<Invitation[]>([])
 const [issuedCode,setIssuedCode]=useState('')
 const [inviteEmail,setInviteEmail]=useState('')
 const [inviteRole,setInviteRole]=useState('viewer')
 const [redeemCode,setRedeemCode]=useState('')
 const [redeemEmail,setRedeemEmail]=useState('')
 const [redeemPassword,setRedeemPassword]=useState('')
 const [acceptingInvite,setAcceptingInvite]=useState(false)
 const [audits,setAudits]=useState<Audit[]>([])
 const [projectName,setProjectName]=useState('')
 const [industry,setIndustry]=useState('agriculture')
 const [message,setMessage]=useState('')
 const [busy,setBusy]=useState(false)
 const [auditBusy,setAuditBusy]=useState(false)

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
  setSelectedProject(previous=>list.some(p=>p.id===previous)?previous:(list[0]?.id??null))
  if(role==='owner'||role==='admin'){
   const [team,events,invites]=await Promise.all([call<Member[]>(`/organisations/${id}/members`,bearer),call<Audit[]>(`/organisations/${id}/audit`,bearer),call<Invitation[]>(`/organisations/${id}/invitations`,bearer)])
   setMembers(team);setAudits(events);setInvitations(invites)
  }else{setMembers([]);setAudits([]);setInvitations([])}
 }
 async function refreshAudit(){
  if(!token||selectedOrg===null||!admin)return
  setAuditBusy(true)
  try{setAudits(await call<Audit[]>(`/organisations/${selectedOrg}/audit`,token))}
  catch(err){setMessage(err instanceof Error?err.message:'Could not refresh audit history')}
  finally{setAuditBusy(false)}
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
 async function registerCompany(e:FormEvent<HTMLFormElement>){
  e.preventDefault();setMessage('')
  if(password!==confirmPassword){setMessage('Passwords do not match.');return}
  if(password.length<12){setMessage('Use at least 12 characters for your password.');return}
  setBusy(true)
  try{
   const response=await fetch(`${API}/api/v1/enterprise/auth/register-company`,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({organisation_name:companyName,email,password})
   })
   const body=await response.json().catch(()=>null) as {detail?:string;message?:string}|null
   if(!response.ok)throw new Error(body?.detail||`Registration unavailable (${response.status})`)
   setPassword('');setConfirmPassword('');setCompanyName('');setRegistering(false)
   setMessage('Company account created. Sign in using your new credentials. Email verification is not enabled in this local prototype.')
  }catch(err){setMessage(err instanceof Error?err.message:'Registration failed')}
  finally{setBusy(false)}
 }
 async function chooseOrg(id:number){
  if(!token||!identity)return
  const org=identity.organisations.find(o=>o.id===id);if(!org)return
  setIssuedCode('')
  setBusy(true);setMessage('');try{await loadOrg(token,id,org.role);setSelectedOrg(id)}catch(err){setMessage(String(err))}finally{setBusy(false)}
 }
 async function addProject(e:FormEvent<HTMLFormElement>){
  e.preventDefault();if(!token||selectedOrg===null)return
  setBusy(true);setMessage('');try{
   await call(`/organisations/${selectedOrg}/projects`,token,{method:'POST',body:JSON.stringify({name:projectName,industry_id:industry})})
   setProjectName('');await loadOrg(token,selectedOrg,current?.role||'viewer');setMessage('Project created in the selected organisation.')
  }catch(err){setMessage(String(err))}finally{setBusy(false)}
 }
 async function issueInvitation(e:FormEvent<HTMLFormElement>){
  e.preventDefault();if(!token||selectedOrg===null||!current)return
  setBusy(true);setMessage('');setIssuedCode('')
  try{
   const issued=await call<InvitationIssued>(`/organisations/${selectedOrg}/invitations`,token,{method:'POST',body:JSON.stringify({email:inviteEmail,role:inviteRole})})
   setIssuedCode(issued.code);setInviteEmail('')
   await loadOrg(token,selectedOrg,current.role)
   setMessage('Invitation created. Copy the code securely now; it will not be shown again.')
  }catch(err){setMessage(err instanceof Error?err.message:'Invitation creation failed')}
  finally{setBusy(false)}
 }
 async function cancelInvitation(invitation:Invitation){
  if(!token||selectedOrg===null||!current)return
  if(!window.confirm(`Revoke the pending invitation for ${invitation.email}?`))return
  setBusy(true);setMessage('');setIssuedCode('')
  try{
   await call(`/organisations/${selectedOrg}/invitations/${invitation.id}`,token,{method:'DELETE'})
   await loadOrg(token,selectedOrg,current.role)
   setMessage('Invitation revoked.')
  }catch(err){setMessage(err instanceof Error?err.message:'Could not revoke invitation')}
  finally{setBusy(false)}
 }
 async function redeemInvitation(e:FormEvent<HTMLFormElement>){
  e.preventDefault();setBusy(true);setMessage('')
  try{
   const response=await fetch(`${API}/api/v1/enterprise/auth/invitations/accept`,{
    method:'POST',headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})},
    body:JSON.stringify({code:redeemCode,email:redeemEmail,password:token?undefined:redeemPassword||undefined}),
   })
   const result=await response.json().catch(()=>null) as {detail?:string;message?:string}|null
   if(!response.ok)throw new Error(result?.detail||`Invitation not accepted (${response.status})`)
   setRedeemCode('');setRedeemPassword('');setAcceptingInvite(false)
   if(token){
    const updated=await call<Identity>('/auth/me',token)
    setIdentity(updated)
    const org=updated.organisations.find(o=>o.id===selectedOrg)||updated.organisations.at(-1)
    if(org){setSelectedOrg(org.id);await loadOrg(token,org.id,org.role)}
   }
   setMessage(token?'Invitation accepted. Organisation added to your account.':'Invitation accepted. Sign in using your new employee credentials.')
  }catch(err){setMessage(err instanceof Error?err.message:'Could not accept invitation')}
  finally{setBusy(false)}
 }
 async function changeRole(member:Member,role:string){
  if(!token||selectedOrg===null||!current||member.role===role)return
  setBusy(true);setMessage('')
  try{
   await call(`/organisations/${selectedOrg}/members/${member.user_id}`,token,{method:'PATCH',body:JSON.stringify({role})})
   await loadOrg(token,selectedOrg,current.role)
   setMessage(`Updated permissions for ${member.email}.`)
  }catch(err){setMessage(err instanceof Error?err.message:'Role change failed')}
  finally{setBusy(false)}
 }
 async function removeMember(member:Member){
  if(!token||selectedOrg===null||!current)return
  if(!window.confirm(`Remove ${member.email} from ${current.name}? This immediately revokes their organisation access.`))return
  setBusy(true);setMessage('')
  try{
   await call(`/organisations/${selectedOrg}/members/${member.user_id}`,token,{method:'DELETE'})
   await loadOrg(token,selectedOrg,current.role)
   setMessage(`Removed ${member.email} from ${current.name}.`)
  }catch(err){setMessage(err instanceof Error?err.message:'Could not remove member')}
  finally{setBusy(false)}
 }
 async function revokeAllSessions(){
  if(!token)return
  if(!window.confirm('Sign out every active session for your account, including this one?'))return
  try{await call('/auth/logout-all',token,{method:'POST'})}
  catch(err){setMessage(err instanceof Error?err.message:'Could not revoke all sessions');return}
  setIssuedCode('');setInvitations([]);setToken(null);setIdentity(null);setSelectedOrg(null);setProjects([]);setSelectedProject(null);setMembers([]);setAudits([]);setPassword('');onExit?.()
 }
 async function logout(){
  const prior=token;setIssuedCode('');setInvitations([]);setToken(null);setIdentity(null);setSelectedOrg(null);setProjects([]);setSelectedProject(null);setMembers([]);setAudits([]);setPassword('');setMessage('Signed out. Session cleared from this browser tab.')
  if(prior)try{await call('/auth/logout',prior,{method:'POST'})}catch{/* session already cleared locally */}
  onExit?.()
 }
 const current=identity?.organisations.find(o=>o.id===selectedOrg)
 const editable=current?.role==='owner'||current?.role==='admin'||current?.role==='analyst'
 const admin=current?.role==='owner'||current?.role==='admin'
 const input='mt-2 w-full rounded-lg border border-line bg-white px-3 py-2.5 text-sm text-ink'
 return <section id="enterprise-workspace" className="mt-6 scroll-mt-24 space-y-5" aria-label="Secure organisation workspace">
  <div className="rounded-2xl border border-line bg-surface p-6 shadow-panel">
   <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-widest text-brand">Phase 4E.3 · Employee onboarding</p><h2 className="mt-2 text-2xl font-semibold text-ink">Organisation workspace</h2><p className="mt-2 max-w-3xl text-sm text-muted">Private project order imports and reporting, organisation permissions, and audit history. Public optimisation demonstrations remain <strong>separate synthetic models</strong>; imported project data is not yet connected to a solver.</p></div><span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900">Local security prototype · Not production certified</span></div>
   {message&&<p role="status" className="mt-4 rounded-lg border border-line bg-canvas p-3 text-sm">{message}</p>}
   {!token?<div className="mt-6 max-w-md space-y-4">
     <div className="flex gap-2" role="group" aria-label="Account access"><button type="button" aria-pressed={!registering} className={`rounded-lg px-4 py-2 text-sm font-semibold ${!registering?'bg-brand text-white':'border border-line'}`} onClick={()=>{setRegistering(false);setMessage('');setPassword('')}}>Sign in</button><button type="button" aria-pressed={registering} className={`rounded-lg px-4 py-2 text-sm font-semibold ${registering?'bg-brand text-white':'border border-line'}`} onClick={()=>{setRegistering(true);setMessage('');setPassword('')}}>Create company account</button></div>
     {registering?<form onSubmit={e=>void registerCompany(e)} className="space-y-4"><h3 className="font-semibold">Create a company workspace</h3><p className="text-xs leading-5 text-muted">Local prototype registration. The creator becomes the organisation owner. Existing company employees must be added by their administrator; signup does not grant access to another company.</p><label className="block text-sm">Company name<input required minLength={2} maxLength={120} autoComplete="organization" className={input} value={companyName} onChange={e=>setCompanyName(e.target.value)}/></label><label className="block text-sm">Work email<input required type="email" maxLength={254} autoComplete="email" className={input} value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="block text-sm">Password (12 characters minimum)<input required type="password" minLength={12} maxLength={256} autoComplete="new-password" className={input} value={password} onChange={e=>setPassword(e.target.value)}/></label><label className="block text-sm">Confirm password<input required type="password" minLength={12} maxLength={256} autoComplete="new-password" className={input} value={confirmPassword} onChange={e=>setConfirmPassword(e.target.value)}/></label><button disabled={busy} className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy?'Creating company…':'Create company account'}</button></form>:<form onSubmit={e=>void signIn(e)} className="space-y-4"><p className="text-sm font-medium">Sign in with your organisation account</p><label className="block text-sm">Email<input type="email" autoComplete="username" required value={email} onChange={e=>setEmail(e.target.value)} className={input}/></label><label className="block text-sm">Password<input type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} className={input}/></label><button disabled={busy} className="rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy?'Authenticating…':'Sign in'}</button></form>}
     <div className="rounded-xl border border-line bg-canvas p-4">
      <button type="button" aria-expanded={acceptingInvite} onClick={()=>{setAcceptingInvite(v=>!v);setMessage('')}} className="text-sm font-semibold text-brand underline underline-offset-4">Have an employee invitation code?</button>
      {acceptingInvite&&<form onSubmit={e=>void redeemInvitation(e)} className="mt-4 space-y-3"><p className="text-xs leading-5 text-muted">Your company administrator must send you a one-time code. For an existing account, sign in first and use Join another organisation.</p><label className="block text-sm">Invitation code<input required autoComplete="off" minLength={24} className={input} value={redeemCode} onChange={e=>setRedeemCode(e.target.value)}/></label><label className="block text-sm">Invited email<input required type="email" className={input} value={redeemEmail} onChange={e=>setRedeemEmail(e.target.value)}/></label><label className="block text-sm">Create employee password (12+ characters)<input required minLength={12} type="password" autoComplete="new-password" className={input} value={redeemPassword} onChange={e=>setRedeemPassword(e.target.value)}/></label><button disabled={busy} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Accept invitation and create account</button></form>}
     </div>
     <p className="text-xs leading-5 text-muted">Registration is available only when enabled on the local server. Invitation codes are manually shared; email verification and production abuse controls are not implemented. Do not enter real company credentials.</p>{onExit&&<button type="button" onClick={onExit} className="text-sm font-semibold text-brand underline underline-offset-4">← Back to welcome</button>}</div>:
    <div className="mt-6 space-y-5"><div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-canvas p-4"><div><p className="text-sm font-semibold">{identity?.user.email}</p><p className="text-xs text-muted">Authenticated local identity · Session not persisted in browser storage</p></div><div className="flex flex-wrap gap-2"><button className="rounded-lg border border-line bg-white px-4 py-2 text-sm" onClick={()=>void revokeAllSessions()}>Sign out all devices</button><button className="rounded-lg border border-line bg-white px-4 py-2 text-sm" onClick={()=>void logout()}>Sign out</button></div></div>
    <div className="grid gap-5 lg:grid-cols-2"><label className="block text-sm font-medium">Active organisation<select value={selectedOrg??''} onChange={e=>void chooseOrg(Number(e.target.value))} className={input}>{identity?.organisations.map(o=><option value={o.id} key={o.id}>{o.name} · {o.role}</option>)}</select></label><div className="rounded-xl border border-line p-4"><p className="text-xs text-muted">Workspace permissions</p><p className="mt-2 font-semibold">{current?.role||'No membership'}</p><p className="mt-1 text-xs text-muted">Projects are scoped by membership and organisation ID.</p></div></div>
    <details className="rounded-xl border border-line p-4"><summary className="cursor-pointer text-sm font-semibold text-brand">Join another organisation with an invitation</summary><form className="mt-3 grid gap-3 sm:grid-cols-2" onSubmit={e=>void redeemInvitation(e)}><label className="block text-sm">Invitation code<input required minLength={24} autoComplete="off" className={input} value={redeemCode} onChange={e=>setRedeemCode(e.target.value)}/></label><label className="block text-sm">Invited email<input required type="email" className={input} value={redeemEmail} onChange={e=>setRedeemEmail(e.target.value)}/></label><div className="sm:col-span-2"><button disabled={busy} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Accept invitation</button><p className="mt-2 text-xs text-muted">You must be signed in as the email named on the invitation. An invitation cannot change your existing password.</p></div></form></details>
    <div id="enterprise-projects" className="grid scroll-mt-24 gap-5 lg:grid-cols-2"><div className="rounded-xl border border-line p-5"><h3 className="font-semibold">Organisation projects</h3><p className="mt-1 text-xs text-muted">Choose a project to access its own secure dataset and dashboard</p><div className="mt-4 space-y-2">{projects.length?projects.map(p=><button type="button" onClick={()=>{setSelectedProject(p.id);window.location.hash="enterprise-data"}} className={`flex w-full justify-between gap-3 rounded-lg border p-3 text-left text-sm ${selectedProject===p.id?"border-teal-400 bg-brand-soft":"border-transparent bg-canvas"}`} key={p.id}><strong>{p.name}</strong><span className="text-muted">{p.industry_id} · Open →</span></button>):<p className="text-sm text-muted">No projects yet.</p>}</div>{editable&&<form onSubmit={e=>void addProject(e)} className="mt-5 space-y-3"><label className="block text-sm">Project name<input required minLength={2} maxLength={120} className={input} value={projectName} onChange={e=>setProjectName(e.target.value)}/></label><label className="block text-sm">Industry<select className={input} value={industry} onChange={e=>setIndustry(e.target.value)}><option value="agriculture">Agriculture & AgriTech</option><option value="technology">Technology & Software</option><option value="logistics">Logistics & Warehousing</option><option value="mining">Mining & Resources</option><option value="airline">Aviation</option></select></label><button disabled={busy} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Create project</button></form>}</div>
     <div className="rounded-xl border border-line p-5"><h3 className="font-semibold">Membership and permissions</h3>{admin?<><p className="mt-2 text-xs leading-5 text-muted">Each employee has an individual account. Only owners can grant or manage administrator roles; owner membership and your own membership cannot be changed here. Access changes are enforced by the API and recorded in audit history.</p><div className="mt-4 space-y-2">{members.map(m=>{const self=m.user_id===identity?.user.id;const protectedMember=self||m.role==='owner'||(m.role==='admin'&&current?.role!=='owner');const canGrantAdmin=current?.role==='owner';return <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-canvas p-3 text-sm" key={m.user_id}><div className="min-w-0"><strong className="break-all">{m.email}</strong><p className="mt-1 text-xs text-muted">{m.role}{self?' · Your account':''}</p></div>{!protectedMember?<div className="flex flex-wrap items-center gap-2"><label className="text-xs text-muted">Role <select aria-label={`Role for ${m.email}`} className="ml-1 rounded-lg border border-line bg-white px-2 py-2 text-sm text-ink" disabled={busy} value={m.role} onChange={e=>void changeRole(m,e.target.value)}><option value="viewer">Viewer</option><option value="analyst">Analyst</option>{canGrantAdmin&&<option value="admin">Administrator</option>}</select></label><button type="button" disabled={busy} onClick={()=>void removeMember(m)} className="rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-800 disabled:opacity-50" aria-label={`Remove ${m.email}`}>Remove</button></div>:<span className="text-xs text-muted">Protected membership</span>}</div>})}</div><div className="mt-5 rounded-xl border border-teal-200 bg-brand-soft p-4"><h4 className="font-semibold">Invite an employee</h4><p className="mt-1 text-xs text-muted">Codes expire after 7 days and work only for the invited email. Share the code privately; no paid email service is needed.</p><form className="mt-3 space-y-3" onSubmit={e=>void issueInvitation(e)}><label className="block text-sm">Employee email<input type="email" required className={input} value={inviteEmail} onChange={e=>setInviteEmail(e.target.value)}/></label><label className="block text-sm">Assign role<select className={input} value={inviteRole} onChange={e=>setInviteRole(e.target.value)}><option value="viewer">Viewer</option><option value="analyst">Analyst</option>{current?.role==='owner'&&<option value="admin">Administrator</option>}</select></label><button disabled={busy} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Create invitation code</button></form>{issuedCode&&<div className="mt-3 rounded-lg border border-amber-300 bg-white p-3"><p className="text-xs font-semibold text-amber-900">Copy this code now — it is shown only once</p><p className="mt-2 break-all font-mono text-xs" data-testid="issued-invitation-code">{issuedCode}</p><button type="button" className="mt-2 rounded-lg border border-line px-3 py-2 text-xs font-semibold" onClick={()=>void navigator.clipboard.writeText(issuedCode)}>Copy invitation code</button></div>}</div><div className="mt-4"><h4 className="text-sm font-semibold">Recent invitations</h4><div className="mt-2 space-y-2">{invitations.length?invitations.map(inv=><div key={inv.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-canvas p-3 text-xs"><span className="min-w-0 break-all"><strong>{inv.email}</strong> · {inv.role} · {inv.status}<br/>Expires {new Date(inv.expires_at).toLocaleDateString()}</span>{inv.status==='pending'&&(inv.role!=='admin'||current?.role==='owner')&&<button type="button" disabled={busy} onClick={()=>void cancelInvitation(inv)} className="rounded-lg border border-red-200 px-3 py-1.5 font-semibold text-red-800">Revoke</button>}</div>):<p className="text-xs text-muted">No invitations yet.</p>}</div></div></>:<p className="mt-3 text-sm text-muted">Member management requires administrator permissions.</p>}</div></div>
     {token&&selectedOrg!==null&&projects.find(p=>p.id===selectedProject)&&<ProjectDataStudio key={`${selectedOrg}:${selectedProject}`} project={projects.find(p=>p.id===selectedProject)!} token={token} canEdit={Boolean(editable)} onImported={()=>void refreshAudit()}/>}
     <div id="enterprise-connectors" className="scroll-mt-24"/>
     {token&&selectedOrg!==null&&<ConnectorRegistry token={token} organisationId={selectedOrg} role={current?.role||'viewer'} onAuditChange={refreshAudit}/>}
     {admin&&<div id="enterprise-audit" className="scroll-mt-24 rounded-xl border border-line p-5"><div className="flex items-center justify-between gap-3"><h3 className="font-semibold">Security audit</h3><button type="button" disabled={auditBusy} onClick={()=>void refreshAudit()} className="rounded-lg border border-line px-3 py-1.5 text-xs disabled:opacity-50">Refresh audit</button></div><p className="mt-1 text-xs text-muted">Recent organisation events · No tokens or passwords logged</p><div className="mt-3 space-y-2">{audits.length?audits.map(a=><div className="flex flex-wrap justify-between gap-2 border-b border-line py-2 text-xs" key={a.id}><span className="font-semibold">{a.action}</span><span className="text-muted">{a.resource_type} · {a.created_at.slice(0,19).replace('T',' ')}</span></div>):<p className="text-sm text-muted">No organisation audit events yet.</p>}</div></div>}
    </div>}
  </div>
 </section>
}
