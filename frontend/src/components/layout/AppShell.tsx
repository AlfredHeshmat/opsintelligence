import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

type Section = { id: string; name: string; symbol: string }
const groups: { heading: string; links: Section[] }[] = [
  { heading: 'COMMAND CENTRE', links: [
    {id:'workspace',name:'Overview',symbol:'▦'},
    {id:'intelligence',name:'Business intelligence',symbol:'◫'},
    {id:'orders',name:'Operational orders',symbol:'≡'},
  ] },
  { heading: 'DECISION INTELLIGENCE', links: [
    {id:'optimization',name:'Optimisation',symbol:'◇'},
    {id:'industry-pilots',name:'Industry solver lab',symbol:'▤'},
    {id:'decision-workspace',name:'Industry & scenarios',symbol:'▥'},
    {id:'predictions',name:'Delay predictions',symbol:'◷'},
    {id:'simulation',name:'What-if simulator',symbol:'↗'},
  ] },
  { heading: 'PLATFORM', links: [
    {id:'connections',name:'Data connections',symbol:'⇄'},
    {id:'connection',name:'API status',symbol:'◉'},
  ] },
]
const lookup = Object.fromEntries(groups.flatMap(group => group.links.map(link => [link.id,link.name])))

function Sidebar({activeSection, onNavigate, mode, onExit}:{activeSection:string;onNavigate?:()=>void;mode:'demo'|'enterprise';onExit:()=>void}){
 return <div className="flex h-full flex-col bg-sidebar text-white">
  <a href={mode==='demo'?'#workspace':'#enterprise-workspace'} onClick={onNavigate} className="flex items-center gap-3 border-b border-white/10 px-5 py-6">
    <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand text-sm font-extrabold tracking-tight shadow-lg shadow-black/10">OI</span>
    <span className="min-w-0"><span className="block text-base font-bold tracking-tight">OpsIntelligence</span><span className="block text-[11px] text-slate-400">Decision intelligence platform</span></span>
  </a>
  <nav aria-label="Main navigation" className="min-h-0 flex-1 space-y-5 overflow-y-auto px-3 py-5">
   {(mode==='demo'?groups:[{heading:'ENTERPRISE WORKSPACE',links:[{id:'enterprise-workspace',name:'Company overview',symbol:'▦'},{id:'enterprise-projects',name:'Projects',symbol:'▣'},{id:'enterprise-data',name:'Data upload',symbol:'⇧'},{id:'enterprise-analytics',name:'Project analytics',symbol:'◫'},{id:'enterprise-orders',name:'Project orders',symbol:'≡'},{id:'enterprise-decisions',name:'Optimisation roadmap',symbol:'◇'}]},{heading:'ADMINISTRATION',links:[{id:'enterprise-connectors',name:'Data connectors',symbol:'⇄'},{id:'enterprise-audit',name:'Security audit',symbol:'⊡'}]}]).map(group=><div key={group.heading}>
    <p className="mb-2 px-3 text-[10px] font-bold tracking-[.18em] text-slate-500">{group.heading}</p>
    <div className="space-y-0.5">{group.links.map(link=><a key={link.id} href={`#${link.id}`} onClick={onNavigate} aria-current={activeSection===link.id?'page':undefined} className={`group flex items-center gap-3 rounded-lg border-l-2 px-3 py-2.5 text-[13px] transition-colors ${activeSection===link.id?'border-teal-300 bg-sidebar-hover font-semibold text-white':'border-transparent text-slate-300 hover:bg-white/7 hover:text-white'}`}>
      <span aria-hidden="true" className={`grid size-6 shrink-0 place-items-center rounded-md text-base ${activeSection===link.id?'bg-teal-500/15 text-teal-300':'text-slate-500 group-hover:text-teal-300'}`}>{link.symbol}</span>{link.name}
    </a>)}</div>
   </div>)}
  </nav>
  <div className="mx-4 mb-4 rounded-xl border border-white/10 bg-white/5 p-3">
    <div className="flex items-center gap-2 text-xs font-semibold"><span className="size-2 rounded-full bg-teal-300"/>{mode==='demo'?'Public demonstration':'Local enterprise prototype'}</div>
    <p className="mt-2 text-[11px] leading-5 text-slate-400">{mode==='demo'?'Synthetic and hypothetical inputs only.':'Protected organisation APIs. Not certified for real data.'}</p>
    {mode==='demo'&&<button type="button" onClick={onExit} className="mt-3 w-full rounded-lg border border-white/20 px-3 py-2 text-xs font-semibold text-white hover:bg-white/10">Exit demo</button>}
  </div>
 </div>
}

export function AppShell({children,mode='demo',onExit=()=>{}}:{children:ReactNode;mode?:'demo'|'enterprise';onExit?:()=>void}){
 const navigation=useRef<HTMLDialogElement>(null)
 const [activeSection,setActiveSection]=useState(()=>window.location.hash.slice(1)||(mode==='demo'?'workspace':'enterprise-workspace'))
 useEffect(()=>{
  const update=()=>setActiveSection(window.location.hash.slice(1)||(mode==='demo'?'workspace':'enterprise-workspace'))
  window.addEventListener('hashchange',update)
  return()=>window.removeEventListener('hashchange',update)
 },[mode])
 return <div data-active-page={activeSection} data-access-mode={mode} className="min-h-screen bg-canvas">
  <a href="#main-content" className="sr-only fixed left-3 top-3 z-50 rounded-lg bg-surface px-4 py-3 text-ink shadow-panel focus:not-sr-only">Skip to content</a>
  <aside className="fixed inset-y-0 left-0 hidden w-[272px] lg:block"><Sidebar activeSection={activeSection} mode={mode} onExit={onExit}/></aside>
  <dialog ref={navigation} aria-label="Main navigation" className="fixed inset-0 m-0 h-dvh max-h-none w-[272px] max-w-[85vw] border-0 bg-sidebar p-0 text-white backdrop:bg-slate-950/60" onClick={event=>{if(event.target===event.currentTarget)navigation.current?.close()}}>
   <div className="flex justify-end bg-sidebar px-3 pt-3"><button type="button" onClick={()=>navigation.current?.close()} className="rounded-md border border-white/20 px-3 py-1.5 text-xs text-white">Close menu</button></div>
   <div className="h-[calc(100%-3rem)]"><Sidebar activeSection={activeSection} mode={mode} onExit={onExit} onNavigate={()=>navigation.current?.close()}/></div>
  </dialog>
  <div className="min-w-0 lg:pl-[272px]">
   <header className="sticky top-0 z-20 border-b border-line/80 bg-white/95 backdrop-blur">
    <div className="mx-auto flex h-[74px] max-w-[1512px] items-center justify-between gap-3 px-4 sm:px-8">
     <div className="flex min-w-0 items-center gap-4">
      <button type="button" onClick={()=>navigation.current?.showModal()} className="rounded-lg border border-line px-3 py-2 text-sm font-medium lg:hidden" aria-haspopup="dialog">☰ <span className="sr-only">Open menu</span></button>
      <div className="min-w-0"><p className="text-[11px] font-medium text-muted">OpsIntelligence / Workspace</p><h1 className="truncate text-sm font-bold tracking-tight sm:text-base">{mode==='enterprise'?({'enterprise-workspace':'Company overview','enterprise-projects':'Projects','enterprise-data':'Data upload','enterprise-analytics':'Project analytics','enterprise-orders':'Project orders','enterprise-decisions':'Optimisation roadmap','enterprise-connectors':'Data connectors','enterprise-audit':'Security audit'} as Record<string,string>)[activeSection]||'Enterprise workspace':lookup[activeSection]||'Overview'}</h1></div>
     </div>
     <div className="flex items-center gap-3"><span className="hidden text-[11px] text-muted md:block">{mode==='demo'?'Decision intelligence · demonstration':'Private organisation workspace'}</span><span className="inline-flex items-center gap-2 rounded-full border border-line bg-canvas px-3 py-1.5 text-[11px] font-semibold text-muted"><span className="size-2 rounded-full bg-teal-600"/>{mode==='demo'?'Demo mode':'Enterprise mode'}</span></div>
    </div>
   </header>
   <main id="main-content" tabIndex={-1} className="mx-auto max-w-[1512px] px-4 py-7 sm:px-8 sm:py-9">{children}</main>
  </div>
 </div>
}
