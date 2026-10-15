import { Filter, Plus, RotateCcw, Sparkles, Wand2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { JobDetail, Level, Requirement } from '../api'
import { Bar, Button, cx } from './ui'

const LEVELS: { key: Level; label: string }[] = [
  { key: 'must', label: 'Must' },
  { key: 'nice', label: 'Nice' },
  { key: 'ignored', label: 'Off' },
]

export default function RequirementsPanel({
  job, applicants, filters, onToggleFilter, onApply, onReset,
}: {
  job: JobDetail
  applicants: number
  filters: Set<string>
  onToggleFilter: (key: string) => void
  onApply: (reqs: Requirement[], minYears: number | null | undefined) => Promise<void>
  onReset: () => Promise<void>
}) {
  const [draft, setDraft] = useState<Requirement[]>(job.requirements)
  const [minYears, setMinYears] = useState<string>(job.min_years == null ? '' : String(job.min_years))
  const [adding, setAdding] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    setDraft(job.requirements)
    setMinYears(job.min_years == null ? '' : String(job.min_years))
  }, [job])

  const dirtyReqs = useMemo(() => JSON.stringify(draft.map((r) => [r.name, r.level])) !== JSON.stringify(job.requirements.map((r) => [r.name, r.level])), [draft, job])
  const myVal = minYears.trim() === '' ? null : Number(minYears)
  const dirtyYears = myVal !== job.min_years
  const dirty = dirtyReqs || dirtyYears

  const groups: { title: string; hint: string; items: Requirement[] }[] = [
    { title: 'Must-have', hint: 'Missing any one caps the score and blocks auto-shortlist', items: draft.filter((r) => r.level === 'must') },
    { title: 'Nice-to-have', hint: 'Adds to the score, never blocks', items: draft.filter((r) => r.level === 'nice') },
    { title: 'Turned off', hint: 'Ignored by the scorer', items: draft.filter((r) => r.level === 'ignored') },
  ]
  const unscored = draft.filter((r) => r.level === 'unscored')

  const setLevel = (id: string, level: Level) => setDraft((d) => d.map((r) => (r.id === id ? { ...r, level } : r)))
  const add = (level: Level) => {
    const name = adding.trim()
    if (!name) return
    setDraft((d) => [...d, { id: `added-${name.toLowerCase().replace(/\W+/g, '-')}`, name, type: 'skill', alternatives: [], level, ai_level: 'added', source: 'recruiter' }])
    setAdding('')
  }
  const apply = async () => {
    setBusy(true)
    try { await onApply(draft, dirtyYears ? myVal : undefined) } finally { setBusy(false) }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line p-4">
        <div className="flex items-center gap-1.5 text-xs font-medium text-accent"><Sparkles size={13} />Parsed from the job description</div>
        <p className="mt-1.5 text-xs leading-5 text-muted">{job.summary}</p>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div className="rounded-lg border border-line p-2">
            <div className="text-faint">Seniority</div><div className="mt-0.5 font-medium capitalize">{job.seniority}</div>
          </div>
          <label className="rounded-lg border border-line p-2">
            <div className="text-faint">Min. years {job.ai_min_years != null && <span>(AI: {job.ai_min_years})</span>}</div>
            <input value={minYears} onChange={(e) => setMinYears(e.target.value.replace(/[^\d.]/g, ''))} placeholder="none"
              className="mt-0.5 w-full bg-transparent font-medium outline-none placeholder:font-normal placeholder:text-faint" aria-label="Minimum years" />
          </label>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-5 overflow-auto p-4">
        {groups.map((g) => (g.items.length > 0 || g.title !== 'Turned off') && (
          <section key={g.title}>
            <div className="mb-2 flex items-baseline justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{g.title} <span className="text-faint">{g.items.length}</span></h3>
            </div>
            <p className="-mt-1 mb-2 text-[11px] text-faint">{g.hint}</p>
            <div className="space-y-1.5">
              {g.items.map((r) => {
                const key = r.key ?? `${r.level}-${r.name}`
                const live = job.requirements.find((x) => x.id === r.id)
                const cov = live?.level === r.level ? live?.coverage : null
                const changed = r.level !== r.ai_level
                return (
                  <div key={r.id} className={cx('rounded-lg border p-2.5', changed ? 'border-accent/40 bg-accent-soft' : 'border-line')}>
                    <div className="flex items-start gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium" title={r.name}>{r.name}</div>
                        {r.alternatives.length > 0 && <div className="truncate text-[11px] text-faint">any of: {r.alternatives.join(', ')}</div>}
                        {live?.mapped === false && (
                          <div className="mt-1 text-[11px] text-amber-500" title="This requirement isn't in the skill map, so related skills (e.g. a framework implying a language) can't satisfy it. Only an exact mention counts. Consider rewording it or adding the concrete skills you accept.">
                            ⚠ not in skill map: exact matches only
                          </div>
                        )}
                      </div>
                      {r.level !== 'ignored' && cov != null && (
                        <button onClick={() => onToggleFilter(key)} title="Only show candidates with evidence for this"
                          className={cx('rounded-md p-1', filters.has(key) ? 'bg-accent text-white dark:text-zinc-950' : 'text-faint hover:bg-raised hover:text-fg')}>
                          <Filter size={13} />
                        </button>
                      )}
                    </div>
                    {cov != null && (
                      <div className="mt-2 flex items-center gap-2">
                        <Bar value={cov / Math.max(applicants, 1)} className={r.level === 'must' ? 'bg-accent' : 'bg-sky-400'} />
                        <span className="w-14 text-right font-mono text-[10px] text-faint" title="Applicants with evidence">{cov}/{applicants}</span>
                      </div>
                    )}
                    <div className="mt-2 flex items-center justify-between">
                      <div className="inline-flex rounded-md border border-line p-0.5" role="radiogroup" aria-label={`Level for ${r.name}`}>
                        {LEVELS.map((l) => (
                          <button key={l.key} role="radio" aria-checked={r.level === l.key} onClick={() => setLevel(r.id, l.key)}
                            className={cx('rounded px-2 py-0.5 text-[11px]', r.level === l.key ? 'bg-raised font-medium text-fg' : 'text-faint hover:text-fg')}>
                            {l.label}
                          </button>
                        ))}
                      </div>
                      <span className="text-[10px] text-faint">{r.ai_level === 'added' ? 'added by you' : changed ? `AI said ${r.ai_level}` : 'AI'}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        ))}

        <div className="flex gap-1.5">
          <input value={adding} onChange={(e) => setAdding(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && add('nice')}
            placeholder="Add a requirement…" aria-label="Add a requirement"
            className="h-8 min-w-0 flex-1 rounded-lg border border-line bg-bg px-2.5 text-xs outline-none focus:border-accent" />
          <Button size="sm" onClick={() => add('must')} disabled={!adding.trim()} title="Add as must-have"><Plus size={12} />Must</Button>
          <Button size="sm" onClick={() => add('nice')} disabled={!adding.trim()} title="Add as nice-to-have">Nice</Button>
        </div>

        {unscored.length > 0 && (
          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Not scored <span className="text-faint">{unscored.length}</span></h3>
            <p className="mb-2 text-[11px] text-faint">Soft skills and methods can't be verified from a resume, so they are left to the interview.</p>
            <div className="flex flex-wrap gap-1">
              {unscored.map((r) => <span key={r.id} className="rounded-md border border-dashed border-line px-1.5 py-0.5 text-[11px] text-muted">{r.name}</span>)}
            </div>
          </section>
        )}
      </div>

      <div className="space-y-2 border-t border-line p-3">
        {dirty && <p className="text-[11px] text-muted">Re-ranks instantly from cached extractions, with no new LLM call. Human stage decisions are kept.</p>}
        <div className="flex gap-2">
          <Button variant="primary" className="flex-1 justify-center" disabled={!dirty || busy} onClick={apply}><Wand2 size={14} />Apply & re-rank</Button>
          <Button variant="ghost" onClick={onReset} disabled={!job.edited && !dirty} title="Restore the AI-parsed requirements"><RotateCcw size={14} /></Button>
        </div>
      </div>
    </div>
  )
}
