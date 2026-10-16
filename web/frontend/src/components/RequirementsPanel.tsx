import { Filter, Plus, RotateCcw } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { JobDetail, Level, Requirement } from '../api'
import { Button, cx, Segmented } from './ui'

const LEVELS: { value: Level; label: string }[] = [
  { value: 'must', label: 'Must' },
  { value: 'nice', label: 'Nice' },
  { value: 'ignored', label: 'Off' },
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
    { title: 'Must-have', hint: 'Missing any one lowers the score and stops auto-shortlisting.', items: draft.filter((r) => r.level === 'must') },
    { title: 'Nice-to-have', hint: 'Adds to the score, never blocks.', items: draft.filter((r) => r.level === 'nice') },
    { title: 'Turned off', hint: 'Ignored by the scorer.', items: draft.filter((r) => r.level === 'ignored') },
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
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 space-y-6 overflow-auto p-5">
        <div>
          <p className="text-[13px] leading-5 text-muted">{job.summary}</p>
          <div className="mt-3 flex gap-6 text-[13px]">
            <div><div className="text-xs text-faint">Seniority</div><div className="mt-0.5 capitalize">{job.seniority}</div></div>
            <label>
              <div className="text-xs text-faint">Min. years{job.ai_min_years != null && ` (parsed: ${job.ai_min_years})`}</div>
              <input value={minYears} onChange={(e) => setMinYears(e.target.value.replace(/[^\d.]/g, ''))} placeholder="none"
                className="mt-0.5 w-20 rounded border border-transparent bg-transparent outline-none placeholder:text-faint hover:border-line focus:border-accent" aria-label="Minimum years" />
            </label>
          </div>
        </div>

        {groups.map((g) => (g.items.length > 0 || g.title !== 'Turned off') && (
          <section key={g.title}>
            <h3 className="text-[13px] font-semibold">{g.title} <span className="num font-normal text-faint">{g.items.length}</span></h3>
            <p className="mb-2 text-xs text-faint">{g.hint}</p>
            <div className="divide-y divide-line-soft rounded-lg border border-line">
              {g.items.map((r) => {
                const key = r.key ?? `${r.level}-${r.name}`
                const live = job.requirements.find((x) => x.id === r.id)
                const cov = live?.level === r.level ? live?.coverage : null
                const changed = r.level !== r.ai_level
                const sub = [
                  r.alternatives.length > 0 && `any of ${r.alternatives.join(', ')}`,
                  cov != null && `${cov} of ${applicants} show it`,
                  r.ai_level === 'added' ? 'added by you' : changed && `parsed as ${r.ai_level}`,
                ].filter(Boolean).join(' · ')
                return (
                  <div key={r.id} className={cx('group flex items-center gap-3 px-3 py-2', changed && 'bg-accent-soft/60')}>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[13px] font-medium" title={r.name}>{r.name}</div>
                      {sub && <div className="truncate text-xs text-muted" title={sub}>{sub}</div>}
                      {live?.mapped === false && (
                        <div className="text-xs text-warn" title="Not in the skill map, so related skills (a framework implying a language) can't satisfy it. Only an exact mention counts.">
                          Exact matches only
                        </div>
                      )}
                    </div>
                    {r.level !== 'ignored' && cov != null && (
                      <button onClick={() => onToggleFilter(key)} title="Only show candidates with evidence for this" aria-pressed={filters.has(key)}
                        className={cx('rounded p-1', filters.has(key) ? 'text-accent' : 'text-faint opacity-0 hover:text-fg group-hover:opacity-100')}>
                        <Filter size={13} />
                      </button>
                    )}
                    <Segmented size="sm" label={`Level for ${r.name}`} value={r.level as Level} onChange={(v) => setLevel(r.id, v)} options={LEVELS} />
                  </div>
                )
              })}
              {g.items.length === 0 && <div className="px-3 py-2 text-xs text-faint">None</div>}
            </div>
          </section>
        ))}

        <div className="flex gap-1.5">
          <input value={adding} onChange={(e) => setAdding(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && add('nice')}
            placeholder="Add a requirement" aria-label="Add a requirement"
            className="h-8 min-w-0 flex-1 rounded-md border border-line bg-panel px-2.5 text-[13px] outline-none focus:border-accent" />
          <Button size="sm" onClick={() => add('must')} disabled={!adding.trim()} title="Add as must-have"><Plus size={12} />Must</Button>
          <Button size="sm" onClick={() => add('nice')} disabled={!adding.trim()} title="Add as nice-to-have"><Plus size={12} />Nice</Button>
        </div>

        {unscored.length > 0 && (
          <section>
            <h3 className="text-[13px] font-semibold">Not scored <span className="num font-normal text-faint">{unscored.length}</span></h3>
            <p className="mb-2 text-xs text-faint">Soft skills and methods can't be checked from a resume, so they're left to the interview.</p>
            <p className="text-xs text-muted">{unscored.map((r) => r.name).join(' · ')}</p>
          </section>
        )}
      </div>

      <div className="flex items-center gap-2 border-t border-line px-5 py-3">
        <span className="mr-auto text-xs text-muted">{dirty ? 'Re-ranks from cached extractions. People\'s stage moves are kept.' : job.edited ? 'Edited by a recruiter' : 'As parsed from the posting'}</span>
        <Button variant="ghost" onClick={onReset} disabled={!job.edited && !dirty} title="Restore the parsed requirements"><RotateCcw size={13} />Reset</Button>
        <Button variant="primary" disabled={!dirty || busy} onClick={apply}>Apply</Button>
      </div>
    </div>
  )
}
