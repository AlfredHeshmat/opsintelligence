import { useRef, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

function Sidebar({ onNavigate, activeSection }: { onNavigate?: () => void; activeSection: string }) {
  return (
    <div className="flex h-full flex-col bg-sidebar text-white">
      <a
        href="#workspace"
        onClick={onNavigate}
        className="flex items-center gap-3 px-6 py-7"
      >
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand font-bold">
          OI
        </span>

        <span>
          <span className="block text-base font-semibold tracking-tight">
            OpsIntelligence
          </span>
          <span className="text-xs text-slate-400">
            Operations command centre
          </span>
        </span>
      </a>

      <nav aria-label="Main navigation" className="px-4 py-6">
        <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
          Workspace
        </p>

        <a
          href="#workspace"
          onClick={onNavigate}
          className={`flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium hover:bg-slate-700 ${activeSection === 'workspace' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}
        >
          <span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" />
          Overview
        </a>

        <a href="#enterprise-workspace" onClick={onNavigate} className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'enterprise-workspace' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}><span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" /> Organisation security</a>
        <a href="#decision-workspace" onClick={onNavigate} className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'decision-workspace' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}><span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" /> Industry & scenarios</a>
        <a href="#connections" onClick={onNavigate} className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'connections' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}><span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" /> Data connections</a>
        <a
          href="#optimization"
          onClick={onNavigate}
          className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'optimization' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}
        >
          <span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" />
          Optimisation
        </a>
        <a href="#intelligence" onClick={onNavigate} className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'intelligence' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}><span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" /> Business intelligence</a>
        <a href="#predictions" onClick={onNavigate} className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'predictions' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}><span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" /> Delay predictions</a>
        <a href="#simulation" onClick={onNavigate} className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'simulation' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}><span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" /> What-if simulator</a>
        <a
          href="#orders"
          onClick={onNavigate}
          className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'orders' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}
        >
          <span aria-hidden="true" className="size-2 rounded-sm bg-teal-300" />
          Orders
        </a>
        <a
          href="#connection"
          onClick={onNavigate}
          className={`mt-2 flex items-center gap-3 rounded-lg px-3 py-3 text-sm hover:bg-sidebar-hover hover:text-white ${activeSection === 'connection' ? 'bg-sidebar-hover text-white font-semibold' : 'text-slate-300'}`}
        >
          <span
            aria-hidden="true"
            className="size-2 rounded-full border border-slate-400"
          />
          API connection
        </a>
      </nav>

      <div className="mx-4 mt-auto mb-5 rounded-xl border border-white/10 p-4">
        <p className="text-sm font-medium">Local workspace</p>
        <p className="mt-2 text-xs leading-relaxed text-slate-400">
          Your application runs locally. Operational analytics and optimisation demo.
        </p>
      </div>
    </div>
  )
}

export function AppShell({ children }: { children: ReactNode }) {
  const navigation = useRef<HTMLDialogElement>(null)
  const [section,setSection] = useState('Overview')
  const [activeSection,setActiveSection] = useState(window.location.hash.slice(1) || 'workspace')
  useEffect(()=>{
    const names:Record<string,string>={'workspace':'Overview','enterprise-workspace':'Organisation security','decision-workspace':'Industry & scenarios','connections':'Data connections','optimization':'Optimisation','intelligence':'Business intelligence','predictions':'Delay predictions','simulation':'What-if simulator','orders':'Orders','connection':'API connection'}
    const update=()=>{const hash=window.location.hash.slice(1)||'workspace';setActiveSection(hash);setSection(names[hash]||'Overview')}
    window.addEventListener('hashchange',update);update()
    return ()=>window.removeEventListener('hashchange',update)
  },[])

  function closeNavigation() {
    navigation.current?.close()
  }

  return (
    <div className="min-h-screen bg-canvas">
      <a
        href="#main-content"
        className="sr-only fixed top-3 left-3 z-50 rounded-lg bg-surface px-4 py-3 text-ink shadow-panel focus:not-sr-only"
      >
        Skip to content
      </a>

      <aside className="fixed inset-y-0 left-0 hidden w-64 lg:block">
        <Sidebar activeSection={activeSection} />
      </aside>

      <dialog
        ref={navigation}
        aria-label="Main navigation"
        className="fixed inset-0 m-0 h-dvh max-h-none w-72 max-w-[85vw] border-0 bg-sidebar p-0 text-white backdrop:bg-slate-950/50"
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            const bounds = event.currentTarget.getBoundingClientRect()

            if (
              event.clientX < bounds.left ||
              event.clientX > bounds.right ||
              event.clientY < bounds.top ||
              event.clientY > bounds.bottom
            ) {
              closeNavigation()
            }
          }
        }}
      >
        <div className="flex justify-end px-4 pt-4">
          <button
            type="button"
            onClick={closeNavigation}
            className="rounded-lg px-3 py-2 text-sm hover:bg-sidebar-hover"
          >
            Close menu
          </button>
        </div>

        <div className="h-[calc(100%-4rem)]">
          <Sidebar onNavigate={closeNavigation} activeSection={activeSection} />
        </div>
      </dialog>

      <div className="min-w-0 lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-line bg-surface">
          <div className="flex h-18 items-center justify-between gap-4 px-5 sm:px-8">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => navigation.current?.showModal()}
                className="rounded-lg border border-line px-3 py-2 text-sm font-medium hover:bg-canvas lg:hidden"
                aria-haspopup="dialog"
              >
                Menu
              </button>

              <div>
                <p className="text-xs text-muted">Workspace</p>
                <p className="text-sm font-semibold">{section}</p>
              </div>
            </div>

            <span className="rounded-full border border-line px-3 py-1 text-xs font-medium text-muted">
              Local environment
            </span>
          </div>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10"
        >
          {children}
        </main>
      </div>
    </div>
  )
}
