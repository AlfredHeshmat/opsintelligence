const stages = [
 {id:'workspace',title:'Understand',description:'Inspect source KPIs and alert signals'},
 {id:'intelligence',title:'Explore',description:'Filter product performance and trends'},
 {id:'optimization',title:'Optimise',description:'Set capacity constraints and solve'},
 {id:'simulation',title:'Compare',description:'Test model assumptions and cost ranges'},
 {id:'industry-pilots',title:'Extend',description:'Review other industry formulations'},
]

export function WorkflowGuide({activePage}:{activePage:string}){
 const index=stages.findIndex(stage=>stage.id===activePage)
 return <nav aria-label="Guided operational workflow" className="enterprise-panel mb-6 p-4 sm:p-5">
  <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2"><h2 className="text-sm font-semibold text-ink">From insight to decision</h2><p className="text-xs text-muted">Suggested path · Explore in any order</p></div>
  <ol className="workflow-grid">{stages.map((stage,idx)=><li key={stage.id}>
   <a href={`#${stage.id}`} className={`workflow-step ${index===idx?'workflow-current':''}`} aria-current={index===idx?'step':undefined}>
    <span className="workflow-number">{String(idx+1).padStart(2,'0')}</span>
    <span className="min-w-0"><span className="block text-sm font-semibold">{stage.title}</span><span className="mt-0.5 block text-[11px] leading-4 text-muted">{stage.description}</span></span>
   </a>
  </li>)}</ol>
 </nav>
}
