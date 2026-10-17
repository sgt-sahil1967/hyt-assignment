import { ArrowDownUp, Check, ChevronDown, Eye, FileUp, History, LayoutGrid, List, ListChecks, MoreHorizontal, Search, ShieldAlert, SlidersHorizontal, Tag, UploadCloud, Users, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type Candidate, type JobDetail, type Requirement, type Settings, type Stage } from '../api'
import CandidateDrawer, { friendlyError } from '../components/CandidateDrawer'
import PoolPicker from '../components/PoolPicker'
import RequirementsPanel from '../components/RequirementsPanel'
import { Button, Callout, Chip, cx, Dot, Empty, IconButton, Menu, MenuItem, Modal, reasonLabel, Score, Segmented, Sheet, Spinner, STAGE_META, StagePill, Switch, Tabs, useToast } from '../components/ui'

type Tab = 'suggested' | 'shortlisted' | 'review' | 'interview' | 'rejected'
type Sort = 'score' | 'years' | 'must'
const EDU = ['none', 'diploma', 'bachelor', 'master', 'phd']
const eduRank = (e: string) => Math.max(0, EDU.indexOf(e))
const inTab = (x: Candidate, t: Tab) =>
  t === 'suggested' ? x.stage === 'new' || x.stage === 'shortlisted'
    : t === 'review' ? x.stage === 'new' && x.queue === 'review'
      : x.stage === t
const SORT_LABEL: Record<Sort, string> = { score: 'Best fit', must: 'Must-have coverage', years: 'Experience' }

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
  const [editingReqs, setEditingReqs] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activity, setActivity] = useState(false)
  const [picking, setPicking] = useState(false)
  const toast = useToast()

  const reload = useCallback(async () => {
    const [j, c] = await Promise.all([api.job(id), api.candidates(id)])
    setJob(j)
    setCands(c)
    onTitle(j.title)
    return { j, c }
  }, [id, onTitle])
  useEffect(() => {
    reload()
      .then(({ j, c }) => { if (j.kind === 'custom' && c.length === 0) setPicking(true) }) // a new role starts empty
      .catch((e) => toast({ title: 'Could not load job', body: e.message, tone: 'error' }))
  }, [reload, toast])

  const reportDiff = (title: string, d: { entered_shortlist: string[]; left_shortlist: string[] }, undo?: () => Promise<unknown>) =>
    toast({
      title,
      body: d.entered_shortlist.length + d.left_shortlist.length === 0 ? 'Shortlist unchanged.' : (
        <>{d.entered_shortlist.length > 0 && <div><b className="text-good">+{d.entered_shortlist.length}</b> joined the shortlist: {d.entered_shortlist.slice(0, 6).join(', ')}{d.entered_shortlist.length > 6 ? '…' : ''}</div>}
          {d.left_shortlist.length > 0 && <div><b className="text-bad">−{d.left_shortlist.length}</b> left: {d.left_shortlist.slice(0, 6).join(', ')}{d.left_shortlist.length > 6 ? '…' : ''}</div>}</>),
      action: undo ? { label: 'Undo', run: () => { undo().then(reload) } } : undefined,
    })

  const applyReqs = async (reqs: Requirement[], my: number | null | undefined) => {
    const prev = job!.edited ? job!.requirements : null
    const prevYears = job!.min_years
    const d = await api.setRequirements(id, reqs, my)
    await reload()
    reportDiff('Requirements updated, candidates re-ranked', d, () => (prev ? api.setRequirements(id, prev, prevYears) : api.reset(id)))
  }
  const reset = async () => { const d = await api.reset(id); await reload(); reportDiff('Restored the parsed requirements', d) }
  const toggleFilter = (k: string) => setReqFilters((s) => { const n = new Set(s); if (n.has(k)) n.delete(k); else n.add(k); return n })

  const counts = useMemo(() => Object.fromEntries((['suggested', 'shortlisted', 'review', 'interview', 'rejected'] as Tab[])
    .map((t) => [t, (cands ?? []).filter((x) => inTab(x, t)).length])) as Record<Tab, number>, [cands])

  const filtered = useMemo(() => {
    const c = (cands ?? []).filter((x) => {
      if (!inTab(x, tab)) return false
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
  const nMust = job.requirements.filter((r) => r.level === 'must').length
  const nNice = job.requirements.filter((r) => r.level === 'nice').length

  const move = async (cid: string, s: Stage) => {
    if (s === 'rejected') { setSelected(cid); return }
    await api.move(id, cid, s)
    await reload()
    toast({ title: `${cid} moved to ${STAGE_META[s].label}` })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-line bg-panel px-4 pt-5 md:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold tracking-tight">{job.title}</h1>
            <div className="mt-0.5 text-[13px] text-muted">
              {[job.location.replace(', United Kingdom', ''), job.job_type, `${cands.length} applicants`].filter(Boolean).join(' · ')}
              {job.edited && <span className="text-accent"> · requirements edited</span>}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {job.kind === 'custom' && <Button onClick={() => setPicking(true)}><Users size={14} />Candidates<span className="text-faint">{cands.length}</span></Button>}
            <Button onClick={() => setEditingReqs(true)}><ListChecks size={14} />Requirements<span className="text-faint">{nMust} must · {nNice} nice</span></Button>
            <ThresholdControl job={job} cands={cands} onApply={async (t) => { const d = await api.setThreshold(id, t); await reload(); reportDiff(`Auto-shortlist threshold set to ${t.toFixed(2)}`, d, () => api.setThreshold(id, job.threshold)) }} />
            <Button variant="primary" onClick={() => setUploading(true)}><FileUp size={14} />Add resumes</Button>
            <Menu trigger={<IconButton label="More"><MoreHorizontal size={16} /></IconButton>}>
              {(close) => (<>
                <MenuItem onClick={() => { setActivity(true); close() }}><History size={14} />Activity log</MenuItem>
                <MenuItem onClick={() => { setShowLabels((s) => !s); close() }}><Tag size={14} />{showLabels ? 'Hide' : 'Show'} golden-set labels</MenuItem>
              </>)}
            </Menu>
          </div>
        </div>
        <Tabs className="mt-4" value={tab} onChange={setTab} tabs={[
          { value: 'suggested', label: 'Suggested', count: counts.suggested },
          { value: 'shortlisted', label: 'Shortlisted', count: counts.shortlisted },
          { value: 'review', label: 'Needs review', count: counts.review },
          { value: 'interview', label: 'Interview', count: counts.interview },
          { value: 'rejected', label: 'Rejected', count: counts.rejected },
        ]} />
      </div>

      <div className="flex flex-wrap items-center gap-2 px-4 py-3 md:px-6">
        <div className="flex h-8 min-w-48 flex-1 items-center gap-2 rounded-md border border-line bg-panel px-2.5 focus-within:border-accent md:max-w-xs">
          <Search size={14} className="text-faint" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search ID, title or skill" aria-label="Search candidates"
            className="h-full min-w-0 flex-1 bg-transparent text-[13px] outline-none" />
          {q && <button onClick={() => setQ('')} aria-label="Clear search" className="text-faint hover:text-fg"><X size={13} /></button>}
        </div>
        <Menu align="left" trigger={<Button variant="ghost"><SlidersHorizontal size={14} />Filter{activeFilters > 0 && <span className="num rounded bg-accent-soft px-1 text-[11px] text-accent">{activeFilters}</span>}</Button>}>
          {() => (
            <div className="w-72 space-y-4 p-3 text-[13px]">
              <label className="block">
                <div className="mb-1 flex justify-between text-xs"><span className="text-muted">Min. years of experience</span><span className="num">{minYears}</span></div>
                <input type="range" min={0} max={8} step={0.5} value={minYears} onChange={(e) => setMinYears(+e.target.value)} className="w-full" />
              </label>
              <label className="block">
                <div className="mb-1 text-xs text-muted">Min. education</div>
                <select value={minEdu} onChange={(e) => setMinEdu(e.target.value)} className="h-8 w-full rounded-md border border-line bg-panel px-2 text-[13px]">
                  <option value="none">Any</option><option value="bachelor">Bachelor's or higher</option><option value="master">Master's or higher</option><option value="phd">PhD</option>
                </select>
              </label>
              <label className="block">
                <div className="mb-1 flex justify-between text-xs"><span className="text-muted">Min. fit score</span><span className="num">{Math.round(minScore * 100)}</span></div>
                <input type="range" min={0} max={1} step={0.05} value={minScore} onChange={(e) => setMinScore(+e.target.value)} className="w-full" />
              </label>
              <div>
                <div className="mb-1.5 text-xs text-muted">Must show evidence for</div>
                <div className="flex flex-wrap gap-1">
                  {scored.map((r) => {
                    const k = r.key ?? `${r.level}-${r.name}`
                    return (
                      <button key={k} onClick={() => toggleFilter(k)} className={cx('rounded px-1.5 py-0.5 text-[11px]',
                        reqFilters.has(k) ? 'bg-accent-soft text-accent' : 'bg-raised text-muted hover:text-fg')}>
                        {reqFilters.has(k) && <Check size={10} className="mr-0.5 inline" />}{r.name}
                      </button>
                    )
                  })}
                </div>
              </div>
              <label className="flex items-center justify-between text-xs text-muted">Hide flagged or unparsed resumes<Switch checked={hideFlagged} onChange={setHideFlagged} label="Hide flagged" /></label>
              {activeFilters > 0 && <Button size="sm" variant="ghost" onClick={() => { setMinYears(0); setMinEdu('none'); setMinScore(0); setReqFilters(new Set()); setHideFlagged(false) }}>Clear filters</Button>}
            </div>
          )}
        </Menu>
        <Menu align="left" trigger={<Button variant="ghost"><ArrowDownUp size={14} />{SORT_LABEL[sort]}<ChevronDown size={13} /></Button>}>
          {(close) => (<>
            {(['score', 'must', 'years'] as Sort[]).map((s) => (
              <MenuItem key={s} onClick={() => { setSort(s); close() }}>{sort === s ? <Check size={14} /> : <span className="w-3.5" />}{SORT_LABEL[s]}</MenuItem>
            ))}
          </>)}
        </Menu>
        <div className="ml-auto">
          <Segmented label="View" value={view} onChange={setView} options={[
            { value: 'list', label: <List size={14} />, title: 'List' },
            { value: 'matrix', label: <LayoutGrid size={14} />, title: 'Evidence matrix' },
          ]} />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-auto px-4 pb-6 md:px-6">
        {cands.length === 0 ? (
          <div className="grid place-items-center py-16 text-center">
            <Users size={20} className="mb-3 text-faint" />
            <div className="text-[13px] font-medium">No candidates in this role yet</div>
            <div className="mt-1 max-w-sm text-[13px] text-muted">Choose from resumes that are already parsed, or upload new ones.</div>
            <div className="mt-4 flex gap-2">
              {job.kind === 'custom' && <Button variant="primary" onClick={() => setPicking(true)}><Users size={14} />Choose candidates</Button>}
              <Button onClick={() => setUploading(true)}><FileUp size={14} />Upload resumes</Button>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <Empty icon={<Search size={20} />} title="No candidates here" body={tab === 'interview' ? 'Move candidates here from the shortlist. Only a person can do that.' : activeFilters || q ? 'Try loosening the filters.' : undefined} />
        ) : view === 'list' ? (
          <CandidateTable rows={filtered} job={job} selected={selected} onSelect={setSelected} showLabels={showLabels} infoCodes={settings?.info_codes ?? []} onMove={move} />
        ) : (
          <Matrix rows={filtered} reqs={scored} selected={selected} onSelect={setSelected} />
        )}
      </div>

      <Sheet open={editingReqs} onClose={() => setEditingReqs(false)} title="Requirements" width="w-[min(420px,100%)]">
        <RequirementsPanel job={job} applicants={cands.length} filters={reqFilters} onToggleFilter={toggleFilter} onApply={applyReqs} onReset={reset} />
      </Sheet>
      {selected && (
        <CandidateDrawer jobId={id} cid={selected} settings={settings} showLabels={showLabels} onClose={() => setSelected(null)} onChanged={reload} />
      )}
      <UploadModal open={uploading} onClose={() => setUploading(false)} jobId={id} offline={settings?.offline ?? true} onDone={reload} />
      <PoolPicker open={picking} onClose={() => setPicking(false)} jobId={id} onDone={reload} />
      <ActivityModal open={activity} onClose={() => setActivity(false)} jobId={id} />
    </div>
  )
}

function MustHaves({ c, must }: { c: Candidate; must: Requirement[] }) {
  if (must.length === 0) return <span className="text-xs text-faint">—</span>
  const s = must.map((r) => ({ r, v: c.evidence[r.key ?? `must-${r.name}`]?.strength ?? 0 }))
  const met = s.filter((x) => x.v >= 0.5).length
  return (
    <div className="flex items-center gap-2" title={s.map(({ r, v }) => `${v >= 1 ? '✓ used' : v >= 0.5 ? '✓ listed' : v > 0 ? '~ weak' : '✕ missing'}  ${r.name}`).join('\n')}>
      <span className={cx('num w-8 text-[13px]', met === must.length ? 'text-fg' : 'text-muted')}>{met}/{must.length}</span>
      <span className="flex gap-0.5">
        {s.slice(0, 8).map(({ r, v }) => <span key={r.id} className={cx('h-3 w-1.5 rounded-sm', v >= 1 ? 'bg-good' : v >= 0.5 ? 'bg-good/50' : v > 0 ? 'bg-warn/60' : 'bg-line')} />)}
      </span>
    </div>
  )
}

function CandidateTable({ rows, job, selected, onSelect, onMove, showLabels, infoCodes }: {
  rows: Candidate[]; job: JobDetail; selected: string | null; onSelect: (id: string) => void
  onMove: (cid: string, s: Stage) => void; showLabels: boolean; infoCodes: string[]
}) {
  const must = job.requirements.filter((r) => r.level === 'must')
  const cols = 'grid-cols-[minmax(180px,1.4fr)_110px_minmax(140px,1fr)_56px_140px_32px] max-lg:grid-cols-[minmax(160px,1fr)_56px_120px_32px] max-sm:grid-cols-[minmax(0,1fr)_48px_32px]'
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-panel">
      <div className={cx('grid gap-4 border-b border-line px-4 py-2 text-xs text-faint', cols)}>
        <span>Candidate</span><span className="max-lg:hidden">Must-haves</span><span className="max-lg:hidden">Note</span><span>Fit</span><span className="max-sm:hidden">Stage</span><span />
      </div>
      {rows.map((c) => {
        const note = c.blocking[0] ?? c.reasons.find((r) => !infoCodes.includes(r)) ?? c.reasons[0]
        return (
          <div key={c.id} onClick={() => onSelect(c.id)} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && onSelect(c.id)}
            className={cx('group grid cursor-pointer items-center gap-4 border-b border-line-soft px-4 py-2.5 last:border-b-0 transition-colors', cols,
              selected === c.id ? 'bg-accent-soft' : 'hover:bg-raised/60')}>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-[13px] font-medium">
                {c.id}
                {c.manipulation && <span title="Possible manipulation"><ShieldAlert size={13} className="text-bad" /></span>}
                {c.uploaded && <Chip>uploaded</Chip>}
                {showLabels && c.label != null && <Chip tone="accent" title={`Golden-set label: relevance ${c.label}/3, ideal ${c.ideal}`}>L{c.label}</Chip>}
              </div>
              <div className="truncate text-xs text-muted">{c.title || 'No role found'} · {c.years} yrs{c.extraction_error ? ' · not parsed' : ''}</div>
            </div>
            <div className="max-lg:hidden"><MustHaves c={c} must={must} /></div>
            <div className="truncate text-xs text-muted max-lg:hidden">
              {note ? <span className="inline-flex items-center gap-1.5"><Dot className={c.blocking.length ? 'bg-warn' : 'bg-faint'} />{reasonLabel(note)}{c.reasons.length > 1 && <span className="text-faint">+{c.reasons.length - 1}</span>}</span> : <span className="text-faint">—</span>}
            </div>
            <Score score={c.score} passed={c.decision === 'advance'} />
            <div className="max-sm:hidden"><StagePill stage={c.stage} by={c.stage_by} /></div>
            <div className="flex justify-end opacity-60 group-hover:opacity-100" onClick={(e) => e.stopPropagation()}>
              <Menu trigger={<IconButton label={`Move ${c.id}`}><MoreHorizontal size={15} /></IconButton>}>
                {(close) => (<>
                  {(['shortlisted', 'interview'] as Stage[]).map((s) => (
                    <MenuItem key={s} disabled={c.stage === s} onClick={() => { onMove(c.id, s); close() }}>
                      <Dot className={STAGE_META[s].dot} />Move to {STAGE_META[s].label.toLowerCase()}
                    </MenuItem>
                  ))}
                  <MenuItem danger disabled={c.stage === 'rejected'} onClick={() => { onMove(c.id, 'rejected'); close() }}>
                    <Dot className="bg-bad" />Reject…
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
  const cell = (s: number) => s >= 1 ? 'bg-good' : s >= 0.5 ? 'bg-good/45' : s > 0 ? 'bg-warn/60' : 'bg-raised'
  return (
    <div className="overflow-auto rounded-lg border border-line bg-panel">
      <table className="text-xs">
        <thead>
          <tr className="border-b border-line">
            <th className="sticky left-0 z-10 bg-panel px-3 py-2 text-left font-normal text-faint">Candidate</th>
            <th className="px-2 py-2 font-normal text-faint">Fit</th>
            {reqs.map((r) => (
              <th key={r.id} className="h-28 px-1 align-bottom font-normal" title={`${r.level}: ${r.name}`}>
                <div className={cx('mx-auto w-4 whitespace-nowrap text-left [writing-mode:vertical-rl] rotate-180', r.level === 'must' ? 'font-medium text-fg' : 'text-faint')}>{r.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id} onClick={() => onSelect(c.id)} className={cx('cursor-pointer border-b border-line-soft', selected === c.id ? 'bg-accent-soft' : 'hover:bg-raised/60')}>
              <td className="sticky left-0 bg-panel px-3 py-1.5 font-medium">{c.id}</td>
              <td className="num px-2 py-1.5 text-center">{Math.round(c.score * 100)}</td>
              {reqs.map((r) => {
                const s = c.evidence[r.key ?? `${r.level}-${r.name}`]?.strength ?? 0
                return <td key={r.id} className="p-0.5"><div className={cx('mx-auto size-4 rounded-sm', cell(s))} title={`${r.name}: ${s}`} /></td>
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex flex-wrap gap-4 border-t border-line px-3 py-2 text-[11px] text-muted">
        {[['bg-good', 'used in a role'], ['bg-good/45', 'listed'], ['bg-warn/60', 'learning'], ['bg-raised', 'missing']].map(([c, l]) => (
          <span key={l} className="inline-flex items-center gap-1.5"><span className={cx('size-3 rounded-sm', c)} />{l}</span>
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
    const blocked = cands.filter((c) => !c.locked && !c.gates_passed && c.score >= t).length // above the threshold, held back by a gate
    return { enter: [...would].filter((x) => !now.has(x)).length, leave: [...now].filter((x) => !would.has(x)).length, total: would.size, blocked }
  }, [cands, t])
  return (
    <Menu trigger={<Button>Threshold <span className="num text-muted">{Math.round(job.threshold * 100)}</span><ChevronDown size={13} /></Button>}>
      {(close) => (
        <div className="w-72 space-y-3 p-3">
          <div>
            <div className="text-[13px] font-medium">Auto-shortlist threshold for this role</div>
            <p className="mt-0.5 text-xs text-muted">Candidates who meet every must-have and score at least this are shortlisted by the agent. Default {Math.round(job.default_threshold * 100)} (Settings → Decision).</p>
          </div>
          <input type="range" min={0.2} max={0.8} step={0.01} value={t} onChange={(e) => setT(+e.target.value)} className="w-full" aria-label="Threshold" />
          <div className="flex items-center justify-between text-xs">
            <span className="num text-base font-medium">{Math.round(t * 100)}</span>
            <span className="text-muted"><b className="num text-fg">{preview.total}</b> shortlisted · <span className="text-good">+{preview.enter}</span> <span className="text-bad">−{preview.leave}</span></span>
          </div>
          {preview.blocked > 0 && (
            <p className="text-xs text-muted"><b className="num text-fg">{preview.blocked}</b> more score at or above this but are held back by a missing must-have or a flag, so the threshold cannot shortlist them. Change that under Requirements.</p>
          )}
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
            className={cx('flex cursor-pointer flex-col items-center gap-2 rounded-lg border border-dashed p-8 text-center', drag ? 'border-accent bg-accent-soft' : 'border-line')}>
            <UploadCloud size={22} className="text-faint" />
            <div className="text-[13px]">Drop PDF, .docx, .html or .txt files, or click to browse</div>
            <div className="text-xs text-faint">Hidden text and injection attempts are stripped and flagged before any model sees the file.</div>
            <input type="file" multiple accept=".pdf,.docx,.html,.htm,.txt" className="hidden" onChange={(e) => setFiles((f) => [...f, ...Array.from(e.target.files ?? [])])} />
          </label>
          {files.length > 0 && <ul className="space-y-1 text-[13px]">{files.map((f, i) => <li key={i} className="flex items-center justify-between rounded-md bg-raised px-2.5 py-1.5"><span className="truncate">{f.name}</span><button onClick={() => setFiles((x) => x.filter((_, j) => j !== i))} className="text-faint hover:text-fg" aria-label={`Remove ${f.name}`}><X size={14} /></button></li>)}</ul>}
          {offline && <Callout tone="warn">Cache only is on, so a new resume can't be parsed. It will be added and escalated as not parsed. Turn off Cache only in Settings → Model to score it.</Callout>}
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={close}>Cancel</Button><Button variant="primary" disabled={!files.length || busy} onClick={go}>{busy ? <Spinner /> : <FileUp size={14} />}Screen {files.length || ''}</Button></div>
        </div>
      ) : (
        <div className="space-y-2">
          {results.map((r, i) => (
            <div key={i} className="flex items-center justify-between gap-3 rounded-md border border-line p-2.5 text-[13px]">
              <div className="min-w-0"><div className="truncate font-medium">{String(r.filename)}</div>
                <div className="text-xs text-muted">{r.error ? String(r.error) : `${r.id} · fit ${Math.round(Number(r.score) * 100)}${(r.reasons as string[])?.length ? ' · ' + (r.reasons as string[]).map(reasonLabel).join(', ') : ''}`}</div>
                {typeof r.warning === 'string' && r.warning && <div className="mt-0.5 text-xs text-warn">{r.warning}</div>}
                {typeof r.extraction_error === 'string' && r.extraction_error && <div className="mt-0.5 text-xs text-warn">Not parsed yet: {friendlyError(r.extraction_error)} Open the candidate to retry.</div>}</div>
              {r.decision === 'advance' ? <Chip tone="good">shortlisted</Chip> : r.error ? <Chip tone="bad">failed</Chip> : <Chip tone="warn">for review</Chip>}
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
      {!items ? <Spinner /> : items.length === 0 ? <Empty icon={<Eye size={20} />} title="No activity yet" body="Stage moves, requirement edits and threshold changes are recorded here." /> : (
        <ol className="space-y-2.5 border-l border-line pl-4">
          {items.map((h, i) => (
            <li key={i} className="text-[13px]">
              <div className="font-medium">{h.candidate ? `${h.candidate}: ` : ''}{h.action.replace(/_/g, ' ')}</div>
              <div className="text-xs text-faint">by {h.by} · {new Date(h.at).toLocaleString()}</div>
              {h.note && <div className="text-xs text-muted">"{h.note}"</div>}
            </li>
          ))}
        </ol>
      )}
    </Modal>
  )
}
