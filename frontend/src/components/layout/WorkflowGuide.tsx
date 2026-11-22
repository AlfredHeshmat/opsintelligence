import { useState } from 'react'

const stages = [
 {id:'workspace',title:'Understand',description:'Inspect source KPIs and alert signals'},
 {id:'intelligence',title:'Explore',description:'Filter product performance and trends'},
 {id:'optimization',title:'Optimise',description:'Set capacity constraints and solve'},
 {id:'simulation',title:'Compare',description:'Test model assumptions and cost ranges'},
 {id:'industry-pilots',title:'Extend',description:'Review other industry formulations'},
]

export function WorkflowGuide({activePage}:{activePage:string}){
 const index=stages.findIndex(stage=>stage.id===activePage)
 const [expanded,setExpanded]=useState(false)
 const current=stages[index]
 return <nav aria-label="Guided operational workflow" className="enterprise-panel mb-6 p-4 sm:p-5">
  <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-sm font-semibold text-ink">From insight to decision</h2><p className="mt-1 text-xs text-muted">{current?`Step ${index+1} of ${stages.length}: ${current.title} — ${current.description}`:"Choose a workflow stage to get started"}</p></div><button type="button" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)} className="secondary-action">{expanded?"Hide workflow":"Show all steps"}</button></div>
  {expanded&&<ol className="workflow-grid mt-4">{stages.map((stage,idx)=><li key={stage.id}>
   <a href={`#${stage.id}`} className={`workflow-step ${index===idx?'workflow-current':''}`} aria-current={index===idx?'step':undefined}>
    <span className="workflow-number">{String(idx+1).padStart(2,'0')}</span>
    <span className="min-w-0"><span className="block text-sm font-semibold">{stage.title}</span><span className="mt-0.5 block text-[11px] leading-4 text-muted">{stage.description}</span></span>
   </a>
  </li>)}</ol>}
 </nav>
}
