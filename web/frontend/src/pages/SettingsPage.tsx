import { Info, RotateCcw } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type RuntimeSettings, type SettingSpec, type SettingValue } from '../api'
import { Button, Callout, cx, Segmented, Spinner, Switch, useToast } from '../components/ui'

export type Theme = 'system' | 'light' | 'dark'

const GROUPS: { key: string; blurb: string }[] = [
  { key: 'Decision', blurb: 'When the agent shortlists on its own and when it hands a candidate to you. It never rejects.' },
  { key: 'Scoring', blurb: 'How evidence in a resume turns into the fit score.' },
  { key: 'Requirements', blurb: 'How requirements parsed from a job description are interpreted.' },
  { key: 'Safety', blurb: 'Manipulation and data-quality checks. These only ever escalate.' },
  { key: 'Model', blurb: 'Which LLM reads documents, and whether it may be called at all.' },
  { key: 'Appearance', blurb: 'Stored in this browser only.' },
]

const fmt = (s: SettingSpec, v: SettingValue) =>
  typeof v === 'boolean' ? (v ? 'on' : 'off') : typeof v === 'number' ? (s.kind === 'int' ? String(v) : v.toFixed(2)) : String(v)

export default function SettingsPage({ theme, onTheme, onChanged }: { theme: Theme; onTheme: (t: Theme) => void; onChanged: () => void }) {
  const [data, setData] = useState<RuntimeSettings | null>(null)
  const [draft, setDraft] = useState<Record<string, SettingValue>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [active, setActive] = useState('Decision')
  const toast = useToast()

  const load = useCallback((d: RuntimeSettings) => {
    setData(d)
    setDraft(Object.fromEntries(d.settings.map((s) => [s.key, s.value])))
    setError(null)
  }, [])
  useEffect(() => { api.runtime().then(load).catch((e) => toast({ title: 'Could not load settings', body: e.message, tone: 'error' })) }, [load, toast])

  const byKey = useMemo(() => Object.fromEntries((data?.settings ?? []).map((s) => [s.key, s])), [data])
  const pending = useMemo(() => Object.fromEntries(Object.entries(draft).filter(([k, v]) => byKey[k] && byKey[k].value !== v)), [draft, byKey])
  const nPending = Object.keys(pending).length

  const apply = async () => {
    setBusy(true)
    try {
      const d = await api.setRuntime(pending)
      load(d)
      onChanged()
      toast({ title: `${nPending} setting${nPending > 1 ? 's' : ''} applied`, body: 'Every job re-screens with the new settings. Stage moves made by people are kept.' })
    } catch (e) {
      setError((e as Error).message)
    } finally { setBusy(false) }
  }
  const resetAll = async () => {
    setBusy(true)
    try { load(await api.resetRuntime()); onChanged(); toast({ title: 'Restored the reported configuration' }) } finally { setBusy(false) }
  }

  if (!data) return <div className="grid h-full place-items-center"><Spinner /></div>
  const overrides = Object.keys(data.overrides).length
  const groupItems = (g: string) => data.settings.filter((s) => s.group === g)
  const weights = ['must_have', 'nice_to_have', 'experience', 'role_relevance'].map((k) => [k, Number(draft[`score.weights.${k}`])] as const)
  const wsum = weights.reduce((a, [, v]) => a + v, 0) || 1

  const scrollTo = (g: string) => {
    setActive(g)
    document.getElementById(`set-${g}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-auto" onScroll={(e) => {
        const top = (e.target as HTMLElement).getBoundingClientRect().top
        const cur = GROUPS.map((g) => g.key).filter((g) => (document.getElementById(`set-${g}`)?.getBoundingClientRect().top ?? 1e9) - top < 120).pop()
        if (cur && cur !== active) setActive(cur)
      }}>
        <div className="mx-auto flex max-w-5xl gap-10 px-4 py-8 md:px-8">
          <nav className="sticky top-0 hidden h-fit w-40 shrink-0 flex-col gap-px md:flex">
            {GROUPS.map((g) => (
              <button key={g.key} onClick={() => scrollTo(g.key)} className={cx('flex h-8 items-center justify-between rounded-md px-2.5 text-left text-[13px]',
                active === g.key ? 'bg-raised font-medium text-fg' : 'text-muted hover:text-fg')}>
                {g.key}
                {groupItems(g.key).some((s) => s.value !== s.default) && <span className="size-1.5 rounded-full bg-accent" title="Changed from default" />}
              </button>
            ))}
          </nav>

          <div className="min-w-0 flex-1 space-y-10">
            <div>
              <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
              <p className="mt-1 text-[13px] text-muted">Tune the agent while it runs. Changes apply to every job at once and are saved on this server. <code className="text-xs">config.yaml</code> never changes.</p>
              {overrides > 0 && (
                <div className="mt-4">
                  <Callout tone="accent" icon={<Info size={15} />}>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span>{overrides} setting{overrides > 1 ? 's differ' : ' differs'} from the reported configuration. The numbers on the Insights page were measured with the defaults.</span>
                      <Button size="sm" onClick={resetAll} disabled={busy}><RotateCcw size={12} />Restore defaults</Button>
                    </div>
                  </Callout>
                </div>
              )}
            </div>

            {GROUPS.map((g) => (
              <section key={g.key} id={`set-${g.key}`} className="scroll-mt-6">
                <h2 className="text-[15px] font-semibold">{g.key}</h2>
                <p className="mt-0.5 text-[13px] text-muted">{g.blurb}</p>
                <div className="mt-4 divide-y divide-line-soft rounded-lg border border-line bg-panel">
                  {g.key === 'Appearance' ? (
                    <Row label="Theme" help="System follows your operating system.">
                      <Segmented label="Theme" value={theme} onChange={onTheme}
                        options={[{ value: 'system', label: 'System' }, { value: 'light', label: 'Light' }, { value: 'dark', label: 'Dark' }]} />
                    </Row>
                  ) : groupItems(g.key).map((s) => (
                    <SettingRow key={s.key} s={s} value={draft[s.key]} dirty={s.key in pending}
                      onChange={(v) => { setError(null); setDraft((d) => ({ ...d, [s.key]: v })) }} />
                  ))}
                </div>
                {g.key === 'Scoring' && (
                  <p className="mt-2 text-xs text-muted">
                    Effective split: {weights.map(([k, v]) => `${k.replace(/_/g, '-')} ${Math.round((v / wsum) * 100)}%`).join(' · ')}
                  </p>
                )}
              </section>
            ))}

            <section>
              <h2 className="text-[15px] font-semibold">Recent changes</h2>
              {data.history.length === 0 ? <p className="mt-1 text-[13px] text-faint">No changes yet.</p> : (
                <ul className="mt-3 space-y-2">
                  {data.history.map((h, i) => (
                    <li key={i} className="text-[13px]">
                      <span className="text-faint">{new Date(h.at).toLocaleString()}</span>{' '}
                      {'reset' in h.changed ? 'Restored defaults' : Object.entries(h.changed).map(([k, v]) => `${byKey[k]?.label ?? k} → ${byKey[k] ? fmt(byKey[k], v) : String(v)}`).join(', ')}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      </div>

      {(nPending > 0 || error) && (
        <div className="fadein flex flex-wrap items-center gap-3 border-t border-line bg-panel px-4 py-3 md:px-8">
          {error ? <span className="text-[13px] text-bad">{error}</span>
            : <span className="text-[13px] text-muted"><b className="font-medium text-fg">{nPending}</b> unsaved change{nPending > 1 ? 's' : ''}</span>}
          <div className="ml-auto flex gap-2">
            <Button variant="ghost" onClick={() => { setDraft(Object.fromEntries(data.settings.map((s) => [s.key, s.value]))); setError(null) }}>Discard</Button>
            <Button variant="primary" onClick={apply} disabled={busy || nPending === 0}>{busy ? <Spinner /> : null}Apply & re-screen</Button>
          </div>
        </div>
      )}
    </div>
  )
}

function Row({ label, help, children, modified, onReset }: { label: string; help?: string; children: React.ReactNode; modified?: boolean; onReset?: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3.5">
      <div className="min-w-0 flex-1 basis-64">
        <div className="flex items-center gap-2 text-[13px] font-medium">
          {label}
          {modified && onReset && (
            <button onClick={onReset} className="inline-flex items-center gap-1 rounded px-1 text-[11px] font-normal text-accent hover:bg-accent-soft" title="Reset to default">
              <span className="size-1.5 rounded-full bg-accent" />changed · reset
            </button>
          )}
        </div>
        {help && <p className="mt-0.5 text-xs leading-5 text-muted">{help}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-3">{children}</div>
    </div>
  )
}

function SettingRow({ s, value, dirty, onChange }: { s: SettingSpec; value: SettingValue; dirty: boolean; onChange: (v: SettingValue) => void }) {
  const modified = value !== s.default
  const help = [s.help, modified ? `Default: ${fmt(s, s.default)}.` : ''].filter(Boolean).join(' ')
  return (
    <div className={cx(dirty && 'bg-accent-soft/60')}>
      <Row label={s.label} help={help} modified={modified} onReset={() => onChange(s.default)}>
        {s.kind === 'bool' && <Switch checked={Boolean(value)} onChange={onChange} label={s.label} />}
        {s.kind === 'choice' && (
          <select value={String(value)} onChange={(e) => onChange(e.target.value)} aria-label={s.label}
            className="h-8 rounded-md border border-line bg-panel px-2 text-[13px] outline-none focus:border-accent">
            {s.options!.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        )}
        {(s.kind === 'float' || s.kind === 'int') && (
          <>
            <input type="range" min={s.min} max={s.max} step={s.step} value={Number(value)} aria-label={s.label}
              onChange={(e) => onChange(s.kind === 'int' ? parseInt(e.target.value) : +e.target.value)} className="w-36 max-sm:w-28" />
            <input type="number" min={s.min} max={s.max} step={s.step} value={Number(value)} aria-label={`${s.label} value`}
              onChange={(e) => e.target.value !== '' && onChange(s.kind === 'int' ? parseInt(e.target.value) : +e.target.value)}
              className="num h-8 w-16 rounded-md border border-line bg-panel px-2 text-right text-[13px] outline-none focus:border-accent" />
          </>
        )}
      </Row>
    </div>
  )
}
