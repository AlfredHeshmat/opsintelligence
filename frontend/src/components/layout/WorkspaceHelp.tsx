import { useState } from 'react'
import type { ReactNode } from 'react'

/** Lightweight, dependency-free help for unfamiliar enterprise workflows. */
export function WorkspaceHelp({title, children}:{title:string;children:ReactNode}){
 const [expanded,setExpanded]=useState(false)
 return <div className="workspace-help rounded-xl border border-line bg-white/90 p-3 sm:p-4">
  <button type="button" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)} className="flex w-full items-center justify-between gap-3 text-left text-sm font-semibold text-ink">
   <span><span aria-hidden="true" className="mr-2 inline-grid size-5 place-items-center rounded-full bg-brand-soft text-xs text-brand">?</span>{title}</span>
   <span aria-hidden="true" className="text-brand">{expanded?'−':'+'}</span>
  </button>
  {expanded&&<div className="mt-3 border-t border-line pt-3 text-sm leading-6 text-muted">{children}</div>}
 </div>
}
