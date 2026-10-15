import { ArrowDownUp, Check, ChevronDown, Eye, FileUp, Gauge, History, LayoutGrid, List, MapPin, Search, ShieldAlert, SlidersHorizontal, Sparkles, UploadCloud, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type Candidate, type JobDetail, type Requirement, type Settings, type Stage } from '../api'
import CandidateDrawer, { friendlyError } from '../components/CandidateDrawer'
import RequirementsPanel from '../components/RequirementsPanel'
import { Avatar, Button, Chip, cx, Empty, Menu, MenuItem, Modal, ScoreRing, Spinner, STAGE_META, StagePill, useToast } from '../components/ui'

type Tab = 'suggested' | 'all' | 'shortlisted' | 'review' | 'interview' | 'rejected'
type Sort = 'score' | 'years' | 'must'
const EDU = ['none', 'diploma', 'bachelor', 'master', 'phd']
const eduRank = (e: string) => Math.max(0, EDU.indexOf(e))

export default function JobWorkspace({ id, settings, onTitle }: { id: string; settings: Settings | null; onTitle: (t: string) => void }) {
  const [job, setJob] = useState<JobDetail | null>(null)
  const [cands, setCands] = useState<Candidate[] | null>(null)
  const [tab, setTab] = useState<Tab>('suggested')
  const [view, setView] = useState<'list' | 'matrix'>('list')
  const [sort, setSort] = useState<Sort>('score')
  const [q, setQ] = useState('')
  const [minYears, setMinYears] = useState(0)
  const [minEdu, setMinEdu] = useState('none')
  const [minScore, setMinScore] = useState(0)
  const [reqFilters, setReqFilters] = useState<Set<string>>(new Set())
  const [hideFlagged, setHideFlagged] = useState(false)
  const [showLabels, setShowLabels] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [activity, setActivity] = useState(false)
  const toast = useToast()

  const reload = useCallback(async () => {
    const [j, c] = await Promise.all([api.job(id), api.candidates(id)])
    setJob(j); setCands(c); onTitle(j.title)
  }, [id, onTitle])
  useEffect(() => { reload().catch((e) => toast({ title: 'Could not load job', body: e.message, tone: 'error' })) }, [reload, toast])

  const reportDiff = (title: string, d: { entered_shortlist: string[]; left_shortlist: string[] }, undo?: () => Promise<unknown>) =>
    toast({
      title,
      body: d.entered_shortlist.length + d.left_shortlist.length === 0 ? 'Shortlist unchanged.' : (
        <>{d.entered_shortlist.length > 0 && <div><b className="text-emerald-500">+{d.entered_shortlist.length}</b> entered the shortlist: {d.entered_shortlist.slice(0, 6).join(', ')}{d.entered_shortlist.length > 6 ? '…' : ''}</div>}
          {d.left_shortlist.length > 0 && <div><b className="text-rose-500">−{d.left_shortlist.length}</b> left: {d.left_shortlist.slice(0, 6).join(', ')}{d.left_shortlist.length > 6 ? '…' : ''}</div>}</>),
      action: undo ? { label: 'Undo', run: () => { undo().then(reload) } } : undefined,
    })

  const applyReqs = async (reqs: Requirement[], my: number | null | undefined) => {
    const prev = job!.edited ? job!.requirements : null
    const prevYears = job!.min_years
    const d = await api.setRequirements(id, reqs, my)
    await reload()
    reportDiff('Requirements updated, candidates re-ranked', d, () => (prev ? api.setRequirements(id, prev, prevYears) : api.reset(id)))
  }
  const reset = async () => { const d = await api.reset(id); await reload(); reportDiff('Restored AI-parsed requirements', d) }
  const toggleFilter = (k: string) => setReqFilters((s) => { const n = new Set(s); if (n.has(k)) n.delete(k); else n.add(k); return n })

  const counts = useMemo(() => {
    const c = cands ?? []
    return {
      suggested: c.filter((x) => x.stage === 'new' || x.stage === 'shortlisted').length,
      all: c.length,
      shortlisted: c.filter((x) => x.stage === 'shortlisted').length,
      review: c.filter((x) => x.stage === 'new' && x.queue === 'review').length,
      interview: c.filter((x) => x.stage === 'interview').length,
      rejected: c.filter((x) => x.stage === 'rejected').length,
    }
  }, [cands])

  const filtered = useMemo(() => {
    let c = cands ?? []
    c = c.filter((x) => {
      if (tab === 'suggested' && !(x.stage === 'new' || x.stage === 'shortlisted')) return false
      if (tab === 'shortlisted' && x.stage !== 'shortlisted') return false
      if (tab === 'review' && !(x.stage === 'new' && x.queue === 'review')) return false
      if (tab === 'interview' && x.stage !== 'interview') return false
      if (tab === 'rejected' && x.stage !== 'rejected') return false
      if (x.years < minYears || eduRank(x.education) < eduRank(minEdu) || x.score < minScore) return false
      if (hideFlagged && (x.manipulation || x.extraction_error)) return false
      for (const k of reqFilters) if ((x.evidence[k]?.strength ?? 0) < 0.5) return false
      if (q && !`${x.id} ${x.title} ${x.skills.join(' ')}`.toLowerCase().includes(q.toLowerCase())) return false
      return true
    })
    const key: Record<Sort, (x: Candidate) => number> = { score: (x) => x.score, years: (x) => x.years, must: (x) => x.components.must_have ?? 0 }
    return [...c].sort((a, b) => key[sort](b) - key[sort](a) || b.score - a.score || a.id.localeCompare(b.id))
  }, [cands, tab, minYears, minEdu, minScore, hideFlagged, reqFilters, q, sort])

  const scored = useMemo(() => (job?.requirements ?? []).filter((r) => r.level === 'must' || r.level === 'nice'), [job])
  const activeFilters = (minYears > 0 ? 1 : 0) + (minEdu !== 'none' ? 1 : 0) + (minScore > 0 ? 1 : 0) + (hideFlagged ? 1 : 0) + reqFilters.size

  if (!job || !cands) return <div className="grid h-full place-items-center"><Spinner /></div>

  const tabs: { key: Tab; label: string; dot?: string; icon?: React.ReactNode }[] = [
    { key: 'suggested', label: 'Suggested', icon: <Sparkles size={14} className="text-accent" /> },
    { key: 'all', label: 'All' },
    { key: 'shortlisted', label: 'Shortlisted', dot: STAGE_META.shortlisted.dot },
    { key: 'review', label: 'Needs review', dot: 'bg-orange-400' },
    { key: 'interview', label: 'Ready to interview', dot: STAGE_META.interview.dot },
    { key: 'rejected', label: 'Rejected', dot: STAGE_META.rejected.dot },
  ]

  return (
    <div className="relative flex h-full">
      <div className="w-80 shrink-0 border-r border-line bg-panel max-lg:hidden">
        <RequirementsPanel job={job} applicants={cands.length} filters={reqFilters} onToggleFilter={toggleFilter} onApply={applyReqs} onReset={reset} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="px-6 pt-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="truncate text-xl font-semibold tracking-tight">{job.title}</h1>
              <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-line px-2 py-0.5 text-xs"><span className="size-1.5 rounded-full bg-emerald-400" />Active</span>
                <span className="inline-flex items-center gap-1"><MapPin size={13} />{job.location.replace(', United Kingdom', '')}</span>
                <span>{job.job_type}</span>
                <span>{cands.length} applicants</span>
                {job.edited && <Chip tone="accent">requirements edited by recruiter</Chip>}
              </div>
            </div>
            <div className="flex gap-2">
              <ThresholdControl job={job} cands={cands} onApply={async (t) => { const d = await api.setThreshold(id, t); await reload(); reportDiff(`Auto-shortlist threshold set to ${t.toFixed(2)}`, d, () => api.setThreshold(id, job.threshold)) }} />
              <Button onClick={() => setUploading(true)}><FileUp size={15} />Add resumes</Button>
              <Button variant="ghost" onClick={() => setActivity(true)} title="Activity log"><History size={15} /></Button>
            </div>
          </div>

          <div className="mt-5 flex gap-1 overflow-x-auto border-b border-line" role="tablist">
            {tabs.map((t) => (
              <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)} className={cx(
                '-mb-px flex shrink-0 items-center gap-1.5 border-b-2 px-3 pb-2.5 pt-1 text-sm transition-colors',
                tab === t.key ? 'border-accent font-medium text-fg' : 'border-transparent text-muted hover:text-fg')}>
                {t.icon}{t.dot && <span className={cx('size-1.5 rounded-full', t.dot)} />}{t.label}
                <span className="ml-0.5 font-mono text-xs text-faint">{counts[t.key]}</span>
              </button>
            ))}
          </div>
          <p className="mt-3 flex items-center gap-1.5 text-xs text-muted">
            <Sparkles size={13} className="text-accent" />
            {tab === 'review' ? 'Escalated by the agent with a blocking reason (missing must-have, manipulation, parse failure…). A human decides.'
              : tab === 'shortlisted' ? 'Candidates meeting every must-have and the score threshold are shortlisted automatically. Interview and reject are human-only.'
                : 'Ranked by evidence-weighted fit: must-haves 50%, nice-to-haves 15%, experience 20%, role relevance 15%.'}
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <div className="flex h-9 min-w-56 flex-1 items-center gap-2 rounded-lg border border-line bg-panel px-3 focus-within:border-accent">
              <Search size={15} className="text-faint" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by ID, title or skill…" aria-label="Search candidates"
                className="h-full min-w-0 flex-1 bg-transparent text-sm outline-none" />
            </div>
            <Menu align="left" trigger={<Button><SlidersHorizontal size={15} />Filters{activeFilters > 0 && <span className="rounded-full bg-accent px-1.5 text-[10px] font-semibold text-white dark:text-zinc-950">{activeFilters}</span>}</Button>}>
              {() => (
                <div className="w-72 space-y-4 p-3 text-sm">
                  <label className="block">
                    <div className="mb-1 flex justify-between text-xs"><span className="text-muted">Min. years of experience</span><span className="font-mono">{minYears}</span></div>
                    <input type="range" min={0} max={8} step={0.5} value={minYears} onChange={(e) => setMinYears(+e.target.value)} className="w-full accent-[var(--accent)]" />
                  </label>
                  <label className="block">
                    <div className="mb-1 text-xs text-muted">Min. education</div>
                    <select value={minEdu} onChange={(e) => setMinEdu(e.target.value)} className="h-8 w-full rounded-lg border border-line bg-bg px-2 text-sm">
                      <option value="none">Any</option><option value="bachelor">Bachelor's or higher</option><option value="master">Master's or higher</option><option value="phd">PhD</option>
                    </select>
                  </label>
                  <label className="block">
                    <div className="mb-1 flex justify-between text-xs"><span className="text-muted">Min. fit score</span><span className="font-mono">{minScore.toFixed(2)}</span></div>
                    <input type="range" min={0} max={1} step={0.05} value={minScore} onChange={(e) => setMinScore(+e.target.value)} className="w-full accent-[var(--accent)]" />
                  </label>
                  <div>
                    <div className="mb-1 text-xs text-muted">Must show evidence for</div>
                    <div className="flex flex-wrap gap-1">
                      {scored.map((r) => {
                        const k = r.key ?? `${r.level}-${r.name}`
                        return (
                          <button key={k} onClick={() => toggleFilter(k)} className={cx('rounded-md border px-1.5 py-0.5 text-[11px]',
                            reqFilters.has(k) ? 'border-accent bg-accent-soft text-accent' : 'border-line text-muted hover:text-fg')}>
                            {reqFilters.has(k) && <Check size={10} className="mr-0.5 inline" />}{r.name}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                  <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={hideFlagged} onChange={(e) => setHideFlagged(e.target.checked)} />Hide flagged / unparsed resumes</label>
                  <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} />Show golden-set labels (evaluation)</label>
                  <Button size="sm" variant="ghost" onClick={() => { setMinYears(0); setMinEdu('none'); setMinScore(0); setReqFilters(new Set()); setHideFlagged(false) }}>Clear filters</Button>
                </div>
              )}
            </Menu>
            <Menu trigger={<Button variant="ghost"><ArrowDownUp size={15} />Sort: {sort === 'score' ? 'Best score' : sort === 'years' ? 'Experience' : 'Must-have coverage'}<ChevronDown size={14} /></Button>}>
              {(close) => (<>
                {(['score', 'must', 'years'] as Sort[]).map((s) => (
                  <MenuItem key={s} onClick={() => { setSort(s); close() }}>{sort === s ? <Check size={14} /> : <span className="w-3.5" />}{s === 'score' ? 'Best score' : s === 'years' ? 'Experience' : 'Must-have coverage'}</MenuItem>
                ))}
              </>)}
            </Menu>
            <div className="inline-flex rounded-lg border border-line p-0.5" role="radiogroup" aria-label="View">
              <button role="radio" aria-checked={view === 'list'} onClick={() => setView('list')} className={cx('rounded-md p-1.5', view === 'list' ? 'bg-raised text-fg' : 'text-faint')} title="List"><List size={15} /></button>
              <button role="radio" aria-checked={view === 'matrix'} onClick={() => setView('matrix')} className={cx('rounded-md p-1.5', view === 'matrix' ? 'bg-raised text-fg' : 'text-faint')} title="Coverage matrix"><LayoutGrid size={15} /></button>
            </div>
          </div>
        </div>

        <div className="mt-3 min-h-0 flex-1 overflow-auto px-6 pb-6">
          {filtered.length === 0 ? (
            <Empty icon={<Search size={18} />} title="No candidates here" body={tab === 'interview' ? 'Move candidates here from the shortlist. Only a human can do that.' : 'Try loosening the filters.'} />
          ) : view === 'list' ? (
            <CandidateTable rows={filtered} job={job} selected={selected} onSelect={setSelected} showLabels={showLabels}
              onMove={async (cid, s) => { if (s === 'rejected') { setSelected(cid); return } await api.move(id, cid, s); await reload(); toast({ title: `${cid} → ${STAGE_META[s].label}` }) }} />
          ) : (
            <Matrix rows={filtered} reqs={scored} selected={selected} onSelect={setSelected} />
          )}
        </div>
      </div>

      {selected && (
        <CandidateDrawer jobId={id} cid={selected} settings={settings} showLabels={showLabels} onClose={() => setSelected(null)} onChanged={reload} />
      )}

      <UploadModal open={uploading} onClose={() => setUploading(false)} jobId={id} offline={settings?.offline ?? true} onDone={reload} />
      <ActivityModal open={activity} onClose={() => setActivity(false)} jobId={id} />
    </div>
  )
}

function CandidateTable({ rows, job, selected, onSelect, onMove, showLabels }: {
  rows: Candidate[]; job: JobDetail; selected: string | null; onSelect: (id: string) => void
  onMove: (cid: string, s: Stage) => void; showLabels: boolean
}) {
  const must = job.requirements.filter((r) => r.level === 'must')
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-panel">
      <div className="grid grid-cols-[minmax(220px,1.3fr)_minmax(200px,1.6fr)_70px_150px_96px] gap-3 border-b border-line px-4 py-2.5 text-xs text-muted max-xl:grid-cols-[minmax(200px,1fr)_70px_150px_96px]">
        <span>Candidate</span><span className="max-xl:hidden">Must-haves</span><span>Fit</span><span>Stage</span><span />
      </div>
      {rows.map((c) => {
        const met = must.filter((r) => (c.evidence[r.key ?? `must-${r.name}`]?.strength ?? 0) >= 0.5)
        return (
          <div key={c.id} onClick={() => onSelect(c.id)} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && onSelect(c.id)}
            className={cx('relative grid cursor-pointer grid-cols-[minmax(220px,1.3fr)_minmax(200px,1.6fr)_70px_150px_96px] items-center gap-3 border-b border-line px-4 py-3 last:border-b-0 transition-colors max-xl:grid-cols-[minmax(200px,1fr)_70px_150px_96px]',
              selected === c.id ? 'bg-accent-soft' : 'hover:bg-raised/60')}>
            <div className="flex min-w-0 items-center gap-3">
              <Avatar id={c.id} />
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 text-sm font-medium">
                  Candidate {c.id}
                  {c.manipulation && <span title="Possible manipulation"><ShieldAlert size={13} className="text-rose-500" /></span>}
                  {showLabels && c.label != null && <span className="rounded bg-raised px-1 font-mono text-[10px] text-faint" title="Golden-set relevance label">L{c.label}</span>}
                </div>
                <div className="truncate text-xs text-muted">{c.title || '—'} · {c.years} yrs{c.extraction_error ? ' · unparsed' : ''}</div>
              </div>
            </div>
            <div className="flex min-w-0 flex-wrap gap-1 max-xl:hidden">
              {must.length === 0 ? <span className="text-xs text-faint">—</span> : must.slice(0, 5).map((r) => {
                const s = c.evidence[r.key ?? `must-${r.name}`]?.strength ?? 0
                return <Chip key={r.id} tone={s >= 1 ? 'good' : s >= 0.5 ? 'good' : s > 0 ? 'warn' : 'bad'} title={`${r.name}: ${s >= 1 ? 'used' : s >= 0.5 ? 'listed' : s > 0 ? 'weak' : 'missing'}`}>{s >= 0.5 ? '✓' : s > 0 ? '~' : '✕'} {r.name}</Chip>
              })}
              {must.length > 5 && <span className="text-[11px] text-faint">+{must.length - 5}</span>}
              <span className="sr-only">{met.length} of {must.length} must-haves met</span>
            </div>
            <ScoreRing score={c.score} size={36} passed={c.decision === 'advance'} />
            <div><StagePill stage={c.stage} by={c.stage_by} /></div>
            <div className="flex justify-end" onClick={(e) => e.stopPropagation()}>
              <Menu trigger={<Button size="sm"><ArrowDownUp size={12} />Move<ChevronDown size={12} /></Button>}>
                {(close) => (<>
                  {(['shortlisted', 'interview'] as Stage[]).map((s) => (
                    <MenuItem key={s} disabled={c.stage === s} onClick={() => { onMove(c.id, s); close() }}>
                      <span className={cx('size-1.5 rounded-full', STAGE_META[s].dot)} />{STAGE_META[s].label}
                    </MenuItem>
                  ))}
                  <MenuItem danger disabled={c.stage === 'rejected'} onClick={() => { onMove(c.id, 'rejected'); close() }}>
                    <span className="size-1.5 rounded-full bg-rose-500" />Reject… (needs a reason)
                  </MenuItem>
                </>)}
              </Menu>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function Matrix({ rows, reqs, selected, onSelect }: { rows: Candidate[]; reqs: Requirement[]; selected: string | null; onSelect: (id: string) => void }) {
  const cell = (s: number) => s >= 1 ? 'bg-emerald-500' : s >= 0.5 ? 'bg-emerald-500/45' : s > 0 ? 'bg-amber-400/60' : 'bg-raised'
  return (
    <div className="overflow-auto rounded-xl border border-line bg-panel">
      <table className="text-xs">
        <thead>
          <tr className="border-b border-line">
            <th className="sticky left-0 z-10 bg-panel px-3 py-2 text-left font-medium text-muted">Candidate</th>
            <th className="px-2 py-2 font-medium text-muted">Fit</th>
            {reqs.map((r) => (
              <th key={r.id} className="h-28 px-1 align-bottom font-normal" title={`${r.level}: ${r.name}`}>
                <div className={cx('mx-auto w-4 whitespace-nowrap text-left [writing-mode:vertical-rl] rotate-180', r.level === 'must' ? 'text-fg' : 'text-faint')}>{r.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id} onClick={() => onSelect(c.id)} className={cx('cursor-pointer border-b border-line/60', selected === c.id ? 'bg-accent-soft' : 'hover:bg-raised/60')}>
              <td className="sticky left-0 bg-inherit px-3 py-1.5 font-mono">{c.id}</td>
              <td className="px-2 py-1.5 text-center font-mono">{Math.round(c.score * 100)}</td>
              {reqs.map((r) => {
                const s = c.evidence[r.key ?? `${r.level}-${r.name}`]?.strength ?? 0
                return <td key={r.id} className="p-0.5"><div className={cx('mx-auto size-5 rounded', cell(s))} title={`${r.name}: ${s}`} /></td>
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex gap-4 border-t border-line px-3 py-2 text-[11px] text-muted">
        {[['bg-emerald-500', 'used in a role'], ['bg-emerald-500/45', 'listed'], ['bg-amber-400/60', 'learning'], ['bg-raised', 'missing']].map(([c, l]) => (
          <span key={l} className="inline-flex items-center gap-1.5"><span className={cx('size-3 rounded', c)} />{l}</span>
        ))}
        <span className="ml-auto">bold = must-have</span>
      </div>
    </div>
  )
}

function ThresholdControl({ job, cands, onApply }: { job: JobDetail; cands: Candidate[]; onApply: (t: number) => Promise<void> }) {
  const [t, setT] = useState(job.threshold)
  useEffect(() => setT(job.threshold), [job.threshold])
  // preview: the agent shortlists iff every gate passes and score >= t; human-locked stages never change
  const preview = useMemo(() => {
    const would = new Set(cands.filter((c) => !c.locked && c.gates_passed && c.score >= t).map((c) => c.id))
    const now = new Set(cands.filter((c) => !c.locked && c.stage === 'shortlisted').map((c) => c.id))
    return { enter: [...would].filter((x) => !now.has(x)).length, leave: [...now].filter((x) => !would.has(x)).length, total: would.size }
  }, [cands, t])
  return (
    <Menu trigger={<Button><Gauge size={15} />Auto-shortlist ≥ {job.threshold.toFixed(2)}</Button>}>
      {(close) => (
        <div className="w-80 space-y-3 p-3">
          <div>
            <div className="text-sm font-medium">Auto-shortlist threshold</div>
            <p className="mt-0.5 text-xs text-muted">Candidates who meet every must-have and score at or above this are shortlisted by the agent. Tuned on held-out data: {job.default_threshold}.</p>
          </div>
          <input type="range" min={0.2} max={0.8} step={0.01} value={t} onChange={(e) => setT(+e.target.value)} className="w-full accent-[var(--accent)]" aria-label="Threshold" />
          <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-base">{t.toFixed(2)}</span>
            <span className="text-muted"><b className="text-fg">{preview.total}</b> shortlisted · <span className="text-emerald-500">+{preview.enter}</span> / <span className="text-rose-500">−{preview.leave}</span></span>
          </div>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="ghost" onClick={() => setT(job.default_threshold)}>Default</Button>
            <Button size="sm" variant="primary" disabled={t === job.threshold} onClick={async () => { await onApply(t); close() }}>Apply</Button>
          </div>
        </div>
      )}
    </Menu>
  )
}

function UploadModal({ open, onClose, jobId, offline, onDone }: { open: boolean; onClose: () => void; jobId: string; offline: boolean; onDone: () => void }) {
  const [files, setFiles] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState<Array<Record<string, unknown>> | null>(null)
  const [drag, setDrag] = useState(false)
  const close = () => { setFiles([]); setResults(null); onClose() }
  const go = async () => {
    setBusy(true)
    try { setResults(await api.upload(jobId, files)); onDone() } finally { setBusy(false) }
  }
  return (
    <Modal open={open} onClose={close} title="Add resumes">
      {!results ? (
        <div className="space-y-3">
          <label onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); setFiles((f) => [...f, ...Array.from(e.dataTransfer.files)]) }}
            className={cx('flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed p-8 text-center', drag ? 'border-accent bg-accent-soft' : 'border-line')}>
            <UploadCloud size={26} className="text-muted" />
            <div className="text-sm">Drop PDF, .docx, .html or .txt resumes, or click to browse</div>
            <div className="text-xs text-faint">Hidden text (white, tiny or off-page in PDFs) and injection attempts are stripped and flagged before any model sees the file. Scanned PDFs without a text layer are escalated.</div>
            <input type="file" multiple accept=".pdf,.docx,.html,.htm,.txt" className="hidden" onChange={(e) => setFiles((f) => [...f, ...Array.from(e.target.files ?? [])])} />
          </label>
          {files.length > 0 && <ul className="space-y-1 text-sm">{files.map((f, i) => <li key={i} className="flex items-center justify-between rounded-lg bg-raised px-2.5 py-1.5"><span className="truncate">{f.name}</span><button onClick={() => setFiles((x) => x.filter((_, j) => j !== i))} className="text-faint hover:text-fg" aria-label={`Remove ${f.name}`}><X size={14} /></button></li>)}</ul>}
          {offline && <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5 text-xs text-amber-600 dark:text-amber-300">Cache-only mode: a new resume can't be parsed without a Gemini call. It will be added and escalated as EXTRACTION_FAILED. Turn on Live API to score it.</p>}
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={close}>Cancel</Button><Button variant="primary" disabled={!files.length || busy} onClick={go}>{busy ? <Spinner /> : <FileUp size={15} />}Screen {files.length || ''}</Button></div>
        </div>
      ) : (
        <div className="space-y-2">
          {results.map((r, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg border border-line p-2.5 text-sm">
              <div className="min-w-0"><div className="truncate font-medium">{String(r.filename)}</div>
                <div className="text-xs text-muted">{r.error ? String(r.error) : `${r.id} · score ${Number(r.score).toFixed(2)} · ${r.decision}${(r.reasons as string[])?.length ? ' · ' + (r.reasons as string[]).join(', ') : ''}`}</div>
                {typeof r.warning === 'string' && r.warning && <div className="mt-0.5 text-xs text-amber-500">{r.warning}</div>}
                {typeof r.extraction_error === 'string' && r.extraction_error && <div className="mt-0.5 text-xs text-amber-500">Not parsed yet: {friendlyError(r.extraction_error)} Open the candidate to retry.</div>}</div>
              {r.decision === 'advance' ? <Chip tone="good">shortlisted</Chip> : r.error ? <Chip tone="bad">failed</Chip> : <Chip tone="warn">escalated</Chip>}
            </div>
          ))}
          <div className="flex justify-end"><Button onClick={close}>Done</Button></div>
        </div>
      )}
    </Modal>
  )
}

function ActivityModal({ open, onClose, jobId }: { open: boolean; onClose: () => void; jobId: string }) {
  const [items, setItems] = useState<Awaited<ReturnType<typeof api.activity>> | null>(null)
  useEffect(() => { if (open) api.activity(jobId).then(setItems) }, [open, jobId])
  return (
    <Modal open={open} onClose={onClose} title="Activity">
      {!items ? <Spinner /> : items.length === 0 ? <Empty icon={<Eye size={18} />} title="No activity yet" body="Stage moves, requirement edits and threshold changes are recorded here." /> : (
        <ol className="space-y-2.5 border-l border-line pl-4">
          {items.map((h, i) => (
            <li key={i} className="text-sm">
              <div><b className="font-medium">{h.candidate ? `${h.candidate}: ` : ''}{h.action}</b></div>
              <div className="text-xs text-faint">by {h.by} · {new Date(h.at).toLocaleString()}</div>
              {h.note && <div className="text-xs text-muted">"{h.note}"</div>}
            </li>
          ))}
        </ol>
      )}
    </Modal>
  )
}
