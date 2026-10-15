import { BarChart3, BriefcaseBusiness, ChevronRight, CloudOff, Moon, PanelLeft, Radio, Sun } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, type Settings } from './api'
import { cx, ToastProvider, useToast } from './components/ui'
import InsightsPage from './pages/InsightsPage'
import JobsPage from './pages/JobsPage'
import JobWorkspace from './pages/JobWorkspace'

export type Route = { page: 'jobs' } | { page: 'job'; id: string } | { page: 'insights' }

function parseHash(): Route {
  const h = window.location.hash.replace(/^#\/?/, '')
  const [a, b] = h.split('/')
  if (a === 'jobs' && b) return { page: 'job', id: b }
  if (a === 'insights') return { page: 'insights' }
  return { page: 'jobs' }
}

export const go = (r: Route) => {
  window.location.hash = r.page === 'job' ? `/jobs/${r.id}` : `/${r.page}`
}

function Shell() {
  const [route, setRoute] = useState<Route>(parseHash)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [dark, setDark] = useState(() => localStorage.getItem('theme') !== 'light')
  const [collapsed, setCollapsed] = useState(false)
  const [crumb, setCrumb] = useState<string>('')
  const toast = useToast()

  useEffect(() => {
    const f = () => setRoute(parseHash())
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  }, [])
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try { localStorage.setItem('theme', dark ? 'dark' : 'light') } catch { /* private mode */ }
  }, [dark])
  useEffect(() => { api.settings().then(setSettings).catch((e) => toast({ title: 'Backend unreachable', body: String(e.message), tone: 'error' })) }, [toast])

  const toggleLive = useCallback(async () => {
    if (!settings) return
    const s = await api.setLive(settings.offline)
    setSettings({ ...settings, ...s })
    toast({ title: s.offline ? 'Cache-only mode' : 'Live Gemini calls enabled',
      body: s.offline ? 'Everything is served from the committed cache. New resumes/JDs cannot be parsed.' : 'New resumes, JDs and explanations will call the API (uses quota).' })
  }, [settings, toast])

  const nav = [
    { key: 'jobs', label: 'Jobs', icon: BriefcaseBusiness, active: route.page !== 'insights', to: { page: 'jobs' } as Route },
    { key: 'insights', label: 'Insights', icon: BarChart3, active: route.page === 'insights', to: { page: 'insights' } as Route },
  ]

  return (
    <div className="flex h-full">
      <aside className={cx('flex shrink-0 flex-col border-r border-line bg-panel transition-all', collapsed ? 'w-16' : 'w-56')}>
        <div className="flex h-14 items-center gap-2.5 px-4">
          <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-accent font-bold text-white dark:text-zinc-950">H</div>
          {!collapsed && <div className="leading-tight"><div className="text-sm font-semibold">HYT Screening</div><div className="text-[11px] text-faint">AI-assisted hiring</div></div>}
        </div>
        <nav className="mt-2 flex flex-col gap-0.5 px-2">
          {nav.map((n) => (
            <button key={n.key} onClick={() => go(n.to)} title={n.label} className={cx(
              'flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm transition-colors',
              n.active ? 'bg-raised font-medium text-fg' : 'text-muted hover:bg-raised hover:text-fg')}>
              <n.icon size={17} />{!collapsed && n.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto space-y-2 p-3">
          {settings && !collapsed && (
            <div className="rounded-xl border border-line p-3 text-[11px] leading-5 text-muted">
              <div className="mb-1 font-medium text-fg">Agent</div>
              <div>Model <span className="font-mono text-fg">{settings.model}</span></div>
              <div>Auto-shortlist ≥ <span className="font-mono text-fg">{settings.t_high}</span></div>
              <div className="mt-1 text-faint">LLM reads · code judges · never rejects</div>
            </div>
          )}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line px-5">
          <button onClick={() => setCollapsed((c) => !c)} className="rounded-md p-1.5 text-muted hover:bg-raised" aria-label="Toggle sidebar"><PanelLeft size={17} /></button>
          <div className="h-4 w-px bg-line" />
          <div className="flex min-w-0 items-center gap-1.5 text-sm">
            <button onClick={() => go({ page: route.page === 'insights' ? 'insights' : 'jobs' })} className="text-muted hover:text-fg">
              {route.page === 'insights' ? 'Insights' : 'Jobs'}
            </button>
            {route.page === 'job' && crumb && <><ChevronRight size={14} className="text-faint" /><span className="truncate font-medium">{crumb}</span></>}
          </div>
          <div className="ml-auto flex items-center gap-2">
            {settings && (
              <button onClick={toggleLive} title="Toggle live Gemini calls" className={cx(
                'flex h-8 items-center gap-1.5 rounded-full border px-3 text-xs',
                settings.offline ? 'border-line text-muted' : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-500')}>
                {settings.offline ? <CloudOff size={13} /> : <Radio size={13} />}
                {settings.offline ? 'Cache-only' : 'Live API'}
              </button>
            )}
            <button onClick={() => setDark((d) => !d)} className="rounded-md p-2 text-muted hover:bg-raised" aria-label="Toggle theme">
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </header>
        <main className="min-h-0 flex-1 overflow-hidden">
          {route.page === 'jobs' && <JobsPage settings={settings} />}
          {route.page === 'job' && <JobWorkspace key={route.id} id={route.id} settings={settings} onTitle={setCrumb} />}
          {route.page === 'insights' && <InsightsPage />}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return <ToastProvider><Shell /></ToastProvider>
}
