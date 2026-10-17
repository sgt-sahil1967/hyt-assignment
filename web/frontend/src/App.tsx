import { BarChart3, BriefcaseBusiness, ChevronRight, PanelLeft, Settings2, Workflow } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, type Settings } from './api'
import { cx, Dot, IconButton, ToastProvider, useToast } from './components/ui'
import HowItWorksPage from './pages/HowItWorksPage'
import InsightsPage from './pages/InsightsPage'
import JobsPage from './pages/JobsPage'
import JobWorkspace from './pages/JobWorkspace'
import SettingsPage, { type Theme } from './pages/SettingsPage'

export type Route = { page: 'jobs' } | { page: 'job'; id: string } | { page: 'insights' } | { page: 'how' } | { page: 'settings' }

function parseHash(): Route {
  const h = window.location.hash.replace(/^#\/?/, '')
  const [a, b] = h.split('/')
  if (a === 'jobs' && b) return { page: 'job', id: b }
  if (a === 'insights') return { page: 'insights' }
  if (a === 'how') return { page: 'how' }
  if (a === 'settings') return { page: 'settings' }
  return { page: 'jobs' }
}

export const go = (r: Route) => {
  window.location.hash = r.page === 'job' ? `/jobs/${r.id}` : `/${r.page}`
}

const readTheme = (): Theme => {
  try { return (localStorage.getItem('theme') as Theme) || 'system' } catch { return 'system' }
}

function Shell() {
  const [route, setRoute] = useState<Route>(parseHash)
  const [settings, setSettings] = useState<Settings | null>(null)
  const [theme, setTheme] = useState<Theme>(readTheme)
  const [collapsed, setCollapsed] = useState(false)
  const [crumb, setCrumb] = useState<string>('')
  const toast = useToast()

  useEffect(() => {
    const f = () => setRoute(parseHash())
    window.addEventListener('hashchange', f)
    return () => window.removeEventListener('hashchange', f)
  }, [])
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => document.documentElement.classList.toggle('dark', theme === 'dark' || (theme === 'system' && mq.matches))
    apply()
    try { localStorage.setItem('theme', theme) } catch { /* private mode */ }
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [theme])
  const refreshSettings = useCallback(() => api.settings().then(setSettings)
    .catch((e) => toast({ title: 'Backend unreachable', body: String(e.message), tone: 'error' })), [toast])
  useEffect(() => { refreshSettings() }, [refreshSettings])

  const section = route.page === 'job' ? 'jobs' : route.page
  const nav = [
    { key: 'jobs', label: 'Jobs', icon: BriefcaseBusiness, to: { page: 'jobs' } as Route },
    { key: 'how', label: 'How it works', icon: Workflow, to: { page: 'how' } as Route },
    { key: 'insights', label: 'Insights', icon: BarChart3, to: { page: 'insights' } as Route },
    { key: 'settings', label: 'Settings', icon: Settings2, to: { page: 'settings' } as Route },
  ]
  const sectionLabel = nav.find((n) => n.key === section)?.label ?? 'Jobs'

  return (
    <div className="flex h-full">
      <aside className={cx('flex shrink-0 flex-col border-r border-line bg-panel transition-[width] max-md:hidden', collapsed ? 'w-14' : 'w-52')}>
        <div className="flex h-12 items-center gap-2.5 px-4">
          <div className="grid size-6 shrink-0 place-items-center rounded-md bg-fg text-[11px] font-bold text-bg">H</div>
          {!collapsed && <span className="text-[13px] font-semibold">HYT Screening</span>}
        </div>
        <nav className="mt-2 flex flex-col gap-px px-2">
          {nav.map((n) => (
            <button key={n.key} onClick={() => go(n.to)} title={n.label} className={cx(
              'flex h-8 items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors',
              section === n.key ? 'bg-raised font-medium text-fg' : 'text-muted hover:bg-raised hover:text-fg')}>
              <n.icon size={16} strokeWidth={1.8} />{!collapsed && n.label}
            </button>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-line bg-panel px-3 md:px-4">
          <IconButton onClick={() => setCollapsed((c) => !c)} label="Toggle sidebar"><PanelLeft size={16} /></IconButton>
          <div className="flex min-w-0 items-center gap-1.5 text-[13px]">
            <button onClick={() => go({ page: section as 'jobs' | 'insights' | 'how' | 'settings' })} className={cx(route.page === 'job' ? 'text-muted hover:text-fg' : 'font-medium')}>
              {sectionLabel}
            </button>
            {route.page === 'job' && crumb && <><ChevronRight size={14} className="shrink-0 text-faint" /><span className="truncate font-medium">{crumb}</span></>}
          </div>
          <nav className="ml-2 flex gap-1 md:hidden">
            {nav.map((n) => <IconButton key={n.key} label={n.label} active={section === n.key} onClick={() => go(n.to)}><n.icon size={16} /></IconButton>)}
          </nav>
          {settings && (
            <button onClick={() => go({ page: 'settings' })} title="Change in Settings → Model"
              className="ml-auto flex h-7 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 text-xs text-muted hover:bg-raised">
              <Dot className={settings.offline ? 'bg-faint' : 'bg-good'} />
              {settings.offline ? 'Cache only' : 'Live API'}
            </button>
          )}
        </header>
        <main className="relative min-h-0 flex-1 overflow-hidden">
          {route.page === 'jobs' && <JobsPage settings={settings} />}
          {route.page === 'job' && <JobWorkspace key={route.id} id={route.id} settings={settings} onTitle={setCrumb} />}
          {route.page === 'insights' && <InsightsPage />}
          {route.page === 'how' && <HowItWorksPage />}
          {route.page === 'settings' && <SettingsPage theme={theme} onTheme={setTheme} onChanged={refreshSettings} />}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return <ToastProvider><Shell /></ToastProvider>
}
