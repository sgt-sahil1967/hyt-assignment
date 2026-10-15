import { AlertTriangle, BadgeCheck, Bot, CalendarCheck, CheckCircle2, CircleDashed, CircleSlash, FileText, History, Lock, RefreshCw, ShieldAlert, Sparkles, Star, Undo2, X, XCircle } from 'lucide-react'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, type CandidateDetail, type Evidence, type Settings, type Stage } from '../api'
import { Avatar, Bar, Button, Chip, cx, ScoreRing, Spinner, StagePill, useToast } from './ui'

const WEIGHTS = { must_have: 0.5, nice_to_have: 0.15, experience: 0.2, role_relevance: 0.15 }
const COMP_LABEL: Record<string, string> = { must_have: 'Must-have coverage', nice_to_have: 'Nice-to-have coverage', experience: 'Experience fit', role_relevance: 'Role relevance' }

export function friendlyError(e: string): string {
  if (/daily quota/i.test(e)) return 'The free daily Gemini quota is used up on every configured key. It resets daily; then press Retry.'
  if (/CacheMiss|offline/i.test(e)) return 'Cache-only mode is on and this text has never been parsed. Turn on Live API (top right), then Retry.'
  if (/schema/i.test(e)) return 'The model returned malformed output twice.'
  return e
}

export function basisText(e: Pick<Evidence, 'basis' | 'strength'>): string {
  const b = e.basis
  if (b === 'missing') return 'No evidence in the resume'
  if (b === 'degree') return 'Degree on the resume'
  if (b.startsWith('degree:')) return 'Degree in an unrelated field'
  if (b === 'equivalent_experience') return 'Covered by equivalent experience'
  const [prof, tax] = b.split('+')
  const how = prof === 'used' ? 'Used in a role or project' : prof === 'listed' ? 'Listed in skills only' : prof === 'learning' ? 'Learning / exposure only' : prof
  if (tax?.startsWith('taxonomy:')) {
    const [child, parent] = tax.replace('taxonomy:', '').split('->')
    return `${how} · ${child} implies ${parent}`
  }
  return how
}

function EvidenceIcon({ s }: { s: number }) {
  if (s >= 1) return <CheckCircle2 size={15} className="text-emerald-500" />
  if (s >= 0.5) return <BadgeCheck size={15} className="text-emerald-400/80" />
  if (s > 0) return <CircleDashed size={15} className="text-amber-400" />
  return <XCircle size={15} className="text-rose-500/80" />
}

function highlight(text: string, quotes: string[]): ReactNode[] {
  const qs = [...new Set(quotes.filter((q) => q && q.length > 1))].sort((a, b) => b.length - a.length)
  if (!qs.length) return [text]
  const re = new RegExp(`(${qs.map((q) => q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
  return text.split(re).map((part, i) => (i % 2 ? <mark key={i} className="ev">{part}</mark> : part))
}

function Section({ title, icon, children, right }: { title: string; icon: ReactNode; children: ReactNode; right?: ReactNode }) {
  return (
    <section className="border-t border-line px-5 py-4">
      <div className="mb-2.5 flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">{icon}{title}</h3>
        {right}
      </div>
      {children}
    </section>
  )
}

export default function CandidateDrawer({
  jobId, cid, settings, showLabels, onClose, onChanged,
}: {
  jobId: string
  cid: string
  settings: Settings | null
  showLabels: boolean
  onClose: () => void
  onChanged: () => void
}) {
  const [c, setC] = useState<CandidateDetail | null>(null)
  const [rejecting, setRejecting] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const toast = useToast()

  const load = () => api.candidate(jobId, cid).then(setC).catch((e) => toast({ title: 'Could not load candidate', body: e.message, tone: 'error' }))
  useEffect(() => { setC(null); setRejecting(false); setNote(''); load() }, [jobId, cid]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', k)
    return () => document.removeEventListener('keydown', k)
  }, [onClose])

  const quotes = useMemo(() => (c?.full_evidence ?? []).filter((e) => e.strength > 0).map((e) => e.quote ?? ''), [c])

  const move = async (stage: Stage, n?: string) => {
    setBusy(true)
    try {
      await api.move(jobId, cid, stage, n)
      toast({ title: `${cid} → ${stage === 'interview' ? 'Ready to interview' : stage}`, body: 'Logged in the activity trail. The agent will not override this decision.' })
      setRejecting(false); setNote('')
      await load(); onChanged()
    } catch (e) {
      toast({ title: 'Move failed', body: (e as Error).message, tone: 'error' })
    } finally { setBusy(false) }
  }
  const unlock = async () => { await api.unlock(jobId, cid); await load(); onChanged() }
  const retry = async () => {
    setBusy(true)
    try {
      const r = await api.retry(jobId, cid)
      toast(r.extraction_error
        ? { title: 'Still could not parse', body: friendlyError(r.extraction_error), tone: 'error' }
        : { title: `${cid} parsed`, body: `Score ${r.score.toFixed(2)} · ${r.decision}` })
      await load(); onChanged()
    } finally { setBusy(false) }
  }
  const explain = async () => {
    setBusy(true)
    try { const r = await api.explain(jobId, cid); setC((x) => (x ? { ...x, explanation: r.explanation } : x)) } catch (e) {
      toast({ title: 'Explanation unavailable', body: (e as Error).message, tone: 'error' })
    } finally { setBusy(false) }
  }

  return (
    <aside className="slidein absolute inset-y-0 right-0 z-20 flex w-[min(540px,100%)] flex-col border-l border-line bg-panel shadow-2xl shadow-black/40" aria-label={`Candidate ${cid}`}>
      <div className="flex items-center justify-between px-5 pt-4">
        <span className="font-mono text-xs text-faint">#{c?.rank ?? '…'} of this job</span>
        <button onClick={onClose} className="rounded-md p-1 text-muted hover:bg-raised" aria-label="Close panel"><X size={16} /></button>
      </div>
      {!c ? <div className="grid flex-1 place-items-center"><Spinner /></div> : (
        <div className="min-h-0 flex-1 overflow-auto">
          <div className="flex items-start gap-3 px-5 pb-4 pt-2">
            <Avatar id={c.id} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold">Candidate {c.id}</h2>
                {c.uploaded && <Chip tone="accent">uploaded</Chip>}
              </div>
              <div className="text-sm text-muted">{c.title || 'No role found'} · {c.years} yrs · <span className="capitalize">{c.education}</span>{c.location ? ` · ${c.location}` : ''}</div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <StagePill stage={c.stage} by={c.stage_by} />
                {c.locked && <span className="inline-flex items-center gap-1 text-[11px] text-faint"><Lock size={11} />set by {c.stage_by}</span>}
              </div>
            </div>
            <ScoreRing score={c.score} size={56} passed={c.gates_passed && c.decision === 'advance'} />
          </div>

          <div className="flex flex-wrap gap-2 px-5 pb-4">
            {c.stage !== 'shortlisted' && <Button size="sm" onClick={() => move('shortlisted')} disabled={busy}><Star size={13} />Shortlist</Button>}
            {c.stage !== 'interview' && <Button size="sm" variant="primary" onClick={() => move('interview')} disabled={busy}><CalendarCheck size={13} />Ready to interview</Button>}
            {c.stage !== 'rejected' && <Button size="sm" variant="ghost" onClick={() => setRejecting((r) => !r)} disabled={busy}><CircleSlash size={13} />Reject…</Button>}
            {c.locked && <Button size="sm" variant="ghost" onClick={unlock} title="Let the agent decide this stage again"><Undo2 size={13} />Return to agent</Button>}
          </div>
          {rejecting && (
            <div className="mx-5 mb-4 rounded-xl border border-rose-500/30 bg-rose-500/5 p-3">
              <label className="text-xs font-medium" htmlFor="reject-note">Reason (required: the agent never rejects, so a human records why)</label>
              <textarea id="reject-note" value={note} onChange={(e) => setNote(e.target.value)} rows={2}
                className="mt-1.5 w-full rounded-lg border border-line bg-bg p-2 text-sm outline-none focus:border-rose-500" placeholder="e.g. needs on-site 5 days, candidate is remote-only" />
              <div className="mt-2 flex justify-end gap-2">
                <Button size="sm" variant="ghost" onClick={() => setRejecting(false)}>Cancel</Button>
                <Button size="sm" variant="danger" disabled={!note.trim() || busy} onClick={() => move('rejected', note)}>Reject candidate</Button>
              </div>
            </div>
          )}

          {c.extraction_error && (
            <div className="mx-5 mb-4 flex gap-2.5 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
              <AlertTriangle size={18} className="shrink-0 text-amber-500" />
              <div className="min-w-0 flex-1">
                <div className="font-medium text-amber-600 dark:text-amber-300">The resume text was read, but the AI parse didn't run</div>
                <div className="mt-0.5 text-xs text-muted">{friendlyError(c.extraction_error)} Until it's parsed, the score reflects an empty profile, so the agent escalated instead of judging.</div>
                <Button size="sm" className="mt-2" onClick={retry} disabled={busy || !!settings?.offline} title={settings?.offline ? 'Turn on Live API first' : ''}>
                  <RefreshCw size={12} />Retry parsing
                </Button>
              </div>
            </div>
          )}

          {(c.sanitizer_flags.injection_suspected || c.sanitizer_flags.hidden_text_removed || c.manipulation) && (
            <div className="mx-5 mb-4 flex gap-2.5 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-sm">
              <ShieldAlert size={18} className="shrink-0 text-rose-500" />
              <div>
                <div className="font-medium text-rose-500">Possible manipulation: never auto-shortlisted</div>
                <div className="mt-0.5 text-xs text-muted">
                  {c.sanitizer_flags.hidden_text_removed && `${c.sanitizer_flags.chars_removed} hidden characters removed before parsing. `}
                  {c.injection_matches.length > 0 && <>Instructions aimed at an AI: <i>"{c.injection_matches[0]}"</i>.</>}
                  {!c.sanitizer_flags.injection_suspected && !c.sanitizer_flags.hidden_text_removed && 'Unusually long skills list with no evidence of use (keyword stuffing).'}
                </div>
              </div>
            </div>
          )}

          <Section title="Agent decision" icon={<Bot size={13} />}>
            <div className={cx('rounded-xl border p-3', c.decision === 'advance' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-line bg-raised/40')}>
              <div className="text-sm font-medium">
                {c.decision === 'advance'
                  ? `Auto-shortlisted: met every must-have and the score threshold${c.reasons.length ? ' (notes below are information only)' : ''}`
                  : 'Escalated to you. The agent does not reject.'}
              </div>
              {c.reasons.length > 0 && (
                <ul className="mt-2 space-y-1.5">
                  {c.reasons.map((r) => (
                    <li key={r} className="flex gap-2 text-xs">
                      <Chip tone={r === 'SUSPECTED_MANIPULATION' || r === 'MISSING_MUST_HAVE' ? 'bad' : settings?.info_codes?.includes(r) ? 'default' : 'warn'}>
                        {settings?.info_codes?.includes(r) && 'ⓘ '}{r}
                      </Chip>
                      <span className="text-muted">{c.reason_help[r] ?? settings?.reason_help?.[r]}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {showLabels && c.label != null && (
              <div className="mt-2 rounded-lg border border-dashed border-line p-2 text-xs text-muted">
                Golden-set label (evaluation only): relevance <b className="text-fg">{c.label}/3</b>, ideal decision <b className="text-fg">{c.ideal}</b>
                {c.ideal && c.ideal !== c.decision && <span className="ml-1 text-amber-500">· the agent disagrees</span>}
              </div>
            )}
          </Section>

          <Section title="Why" icon={<Sparkles size={13} />} right={
            (!c.explanation || c.explanation_stale) && <Button size="sm" variant="ghost" onClick={explain} disabled={busy || !!settings?.offline} title={settings?.offline ? 'Turn on Live API to generate' : ''}><RefreshCw size={12} />Generate</Button>}>
            {c.explanation && c.explanation_stale && (
              <div className="mb-2 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5 text-xs text-amber-600 dark:text-amber-300">
                <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                Outdated: written before the requirements or threshold were edited, so it may contradict the current decision. {settings?.offline ? 'Turn on Live API to regenerate.' : 'Regenerate to update.'}
              </div>
            )}
            {c.explanation
              ? <p className={cx('text-sm leading-6', c.explanation_stale && 'text-faint line-through decoration-faint/40')}>{highlight(c.explanation, quotes)}</p>
              : <p className="text-xs text-faint">No cached explanation for this pair. {settings?.offline ? 'Turn on Live API to generate one.' : ''}</p>}
            <p className="mt-2 text-[11px] text-faint">Written by the LLM from the scorer's output only. Every quoted span is checked against the resume.</p>
          </Section>

          <Section title="Score breakdown" icon={<FileText size={13} />}>
            <div className="space-y-2.5">
              {(Object.keys(WEIGHTS) as (keyof typeof WEIGHTS)[]).map((k) => {
                const v = c.components[k]
                return (
                  <div key={k} className="grid grid-cols-[150px_1fr_44px] items-center gap-3 text-xs">
                    <span className="text-muted">{COMP_LABEL[k]} <span className="text-faint">×{WEIGHTS[k]}</span></span>
                    {v == null ? <span className="text-faint">n/a (renormalised)</span> : <Bar value={v} />}
                    <span className="text-right font-mono">{v == null ? '–' : v.toFixed(2)}</span>
                  </div>
                )
              })}
              {c.blocking.includes('MISSING_MUST_HAVE') && <p className="text-[11px] text-amber-500">Score multiplied by 0.6 because a must-have has no evidence.</p>}
            </div>
          </Section>

          <Section title="Requirements" icon={<CheckCircle2 size={13} />}>
            <ul className="space-y-2">
              {c.full_evidence.map((e, i) => (
                <li key={i} className="flex gap-2.5">
                  <EvidenceIcon s={e.strength} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium">{e.requirement}</span>
                      <span className="text-[10px] uppercase tracking-wide text-faint">{e.level}</span>
                    </div>
                    <div className="text-xs text-muted">{basisText(e)}{e.quote && e.strength > 0 ? <> · <span className="font-mono text-[11px]">"{e.quote}"</span></> : null}</div>
                  </div>
                </li>
              ))}
            </ul>
            {c.gaps.length > 0 && (
              <div className="mt-3 rounded-lg bg-raised/60 p-2.5">
                <div className="mb-1 flex items-center gap-1 text-xs font-medium"><AlertTriangle size={12} className="text-amber-500" />Gaps to probe</div>
                <ul className="list-disc space-y-0.5 pl-5 text-xs text-muted">{c.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
              </div>
            )}
          </Section>

          <Section title="Resume (masked)" icon={<FileText size={13} />}>
            <pre className="whitespace-pre-wrap rounded-xl border border-line bg-bg p-3 font-mono text-[11.5px] leading-5 text-muted">{highlight(c.masked_text, quotes)}</pre>
            <p className="mt-1.5 text-[11px] text-faint">Highlights mark the evidence the scorer used. Name and contact details are masked before any model sees the text.</p>
          </Section>

          <Section title="Activity" icon={<History size={13} />}>
            {c.history.length === 0 ? <p className="text-xs text-faint">No human actions yet.</p> : (
              <ol className="space-y-2 border-l border-line pl-3">
                {[...c.history].reverse().map((h, i) => (
                  <li key={i} className="text-xs">
                    <span className="font-medium">{h.action}</span> <span className="text-faint">by {h.by} · {new Date(h.at).toLocaleString()}</span>
                    {h.note && <div className="text-muted">"{h.note}"</div>}
                  </li>
                ))}
              </ol>
            )}
          </Section>
        </div>
      )}
    </aside>
  )
}
