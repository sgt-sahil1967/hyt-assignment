import { AlertTriangle, CheckCircle2, CircleDashed, Lock, Play, RefreshCw, ShieldAlert, Undo2, X, XCircle } from 'lucide-react'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, type CandidateDetail, type Comparison, type Evidence, type Settings, type Stage } from '../api'
import { Bar, Button, Callout, Chip, cx, IconButton, reasonLabel, Score, Sheet, Spinner, StagePill, Tabs, useToast } from './ui'

const DEFAULT_WEIGHTS = { must_have: 0.5, nice_to_have: 0.15, experience: 0.2, role_relevance: 0.15 }
const COMP_LABEL: Record<string, string> = { must_have: 'Must-haves', nice_to_have: 'Nice-to-haves', experience: 'Experience', role_relevance: 'Role relevance' }

export function friendlyError(e: string): string {
  if (/daily quota/i.test(e)) return 'The free daily Gemini quota is used up on every configured key. It resets daily; then press Retry.'
  if (/CacheMiss|offline/i.test(e)) return 'Cache only is on and this text has never been parsed. Turn it off in Settings → Model, then Retry.'
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
  if (s >= 0.5) return <CheckCircle2 size={15} className={s >= 1 ? 'text-good' : 'text-good/60'} />
  if (s > 0) return <CircleDashed size={15} className="text-warn" />
  return <XCircle size={15} className="text-bad/70" />
}

function highlight(text: string, quotes: string[]): ReactNode[] {
  const qs = [...new Set(quotes.filter((q) => q && q.length > 1))].sort((a, b) => b.length - a.length)
  if (!qs.length) return [text]
  const re = new RegExp(`(${qs.map((q) => q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
  return text.split(re).map((part, i) => (i % 2 ? <mark key={i} className="ev">{part}</mark> : part))
}

function Block({ title, children, right }: { title: string; children: ReactNode; right?: ReactNode }) {
  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-medium text-faint">{title}</h3>
        {right}
      </div>
      {children}
    </section>
  )
}

type Tab = 'summary' | 'evidence' | 'compare' | 'resume' | 'activity'

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
  const [tab, setTab] = useState<Tab>('summary')
  const [rejecting, setRejecting] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [cmp, setCmp] = useState<Comparison | null>(null)
  const [cmpBusy, setCmpBusy] = useState<false | 'base' | 'llm'>(false)
  const toast = useToast()

  const load = () => api.candidate(jobId, cid).then(setC).catch((e) => toast({ title: 'Could not load candidate', body: e.message, tone: 'error' }))
  useEffect(() => { setC(null); setCmp(null); setRejecting(false); setNote(''); load() }, [jobId, cid]) // eslint-disable-line react-hooks/exhaustive-deps

  const quotes = useMemo(() => (c?.full_evidence ?? []).filter((e) => e.strength > 0).map((e) => e.quote ?? ''), [c])
  const weights = settings?.weights ?? DEFAULT_WEIGHTS
  const wsum = Object.values(weights).reduce((a, b) => a + b, 0) || 1

  const move = async (stage: Stage, n?: string) => {
    setBusy(true)
    try {
      await api.move(jobId, cid, stage, n)
      toast({ title: `${cid} moved to ${stage === 'interview' ? 'interview' : stage}`, body: 'Logged in the activity trail. The agent will not override this.' })
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
        : { title: `${cid} parsed`, body: `Fit ${Math.round(r.score * 100)} · ${r.decision}` })
      await load(); onChanged()
    } finally { setBusy(false) }
  }
  const explain = async () => {
    setBusy(true)
    try { const r = await api.explain(jobId, cid); setC((x) => (x ? { ...x, explanation: r.explanation } : x)) } catch (e) {
      toast({ title: 'Explanation unavailable', body: (e as Error).message, tone: 'error' })
    } finally { setBusy(false) }
  }

  // Baselines run only when the recruiter asks for them (never on open), and the LLM one only on a second click.
  const runCompare = async (llm: boolean) => {
    setCmpBusy(llm ? 'llm' : 'base')
    try { setCmp(await api.compare(jobId, cid, llm)) } catch (e) {
      toast({ title: 'Comparison failed', body: (e as Error).message, tone: 'error' })
    } finally { setCmpBusy(false) }
  }

  const header = (
    <div className="shrink-0 border-b border-line px-5 pt-4">
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-semibold">{cid}</h2>
            {c?.uploaded && <Chip>uploaded</Chip>}
            {c && <span className="num text-xs text-faint">#{c.rank} for this role</span>}
          </div>
          {c && <div className="mt-0.5 text-[13px] text-muted">{c.title || 'No role found'} · {c.years} yrs · <span className="capitalize">{c.education}</span>{c.location ? ` · ${c.location}` : ''}</div>}
          {c && (
            <div className="mt-2 flex items-center gap-2">
              <StagePill stage={c.stage} by={c.stage_by} />
              {c.locked && <span className="inline-flex items-center gap-1 text-xs text-faint"><Lock size={11} />set by {c.stage_by}</span>}
            </div>
          )}
        </div>
        {c && <Score score={c.score} large passed={c.gates_passed && c.decision === 'advance'} />}
        <IconButton onClick={onClose} label="Close"><X size={16} /></IconButton>
      </div>
      {c && (
        <div className="mt-3 flex flex-wrap gap-2">
          {c.stage !== 'interview' && <Button size="sm" variant="primary" onClick={() => move('interview')} disabled={busy}>Move to interview</Button>}
          {c.stage !== 'shortlisted' && <Button size="sm" onClick={() => move('shortlisted')} disabled={busy}>Shortlist</Button>}
          {c.stage !== 'rejected' && <Button size="sm" variant="ghost" onClick={() => setRejecting((r) => !r)} disabled={busy}>Reject…</Button>}
          {c.locked && <Button size="sm" variant="ghost" onClick={unlock} title="Let the agent decide this stage again"><Undo2 size={12} />Return to agent</Button>}
        </div>
      )}
      <Tabs className="mt-3 border-b-0" value={tab} onChange={setTab} tabs={[
        { value: 'summary', label: 'Summary' }, { value: 'evidence', label: 'Evidence' }, { value: 'compare', label: 'Compare' },
        { value: 'resume', label: 'Resume' }, { value: 'activity', label: 'Activity', count: c?.history.length || undefined },
      ]} />
    </div>
  )

  return (
    <Sheet open onClose={onClose} title={`Candidate ${cid}`} header={header}>
      {!c ? <div className="grid flex-1 place-items-center"><Spinner /></div> : (
        <div className="min-h-0 flex-1 space-y-6 overflow-auto p-5">
          {rejecting && (
            <div className="rounded-lg border border-bad/30 p-3">
              <label className="text-[13px] font-medium" htmlFor="reject-note">Why reject? <span className="font-normal text-muted">Required: the agent never rejects, so a person records the reason.</span></label>
              <textarea id="reject-note" value={note} onChange={(e) => setNote(e.target.value)} rows={2} autoFocus
                className="mt-2 w-full rounded-md border border-line bg-panel p-2 text-[13px] outline-none focus:border-bad" placeholder="e.g. role needs 5 days on site; candidate is remote-only" />
              <div className="mt-2 flex justify-end gap-2">
                <Button size="sm" variant="ghost" onClick={() => setRejecting(false)}>Cancel</Button>
                <Button size="sm" variant="danger" disabled={!note.trim() || busy} onClick={() => move('rejected', note)}>Reject</Button>
              </div>
            </div>
          )}

          {c.extraction_error && (
            <Callout tone="warn" icon={<AlertTriangle size={15} />}>
              <div className="font-medium">The resume was read, but the AI parse didn't run</div>
              <div className="mt-0.5 text-xs text-muted">{friendlyError(c.extraction_error)} Until then the score reflects an empty profile, so the agent escalated.</div>
              <Button size="sm" className="mt-2" onClick={retry} disabled={busy || !!settings?.offline} title={settings?.offline ? 'Turn off Cache only first' : ''}><RefreshCw size={12} />Retry parsing</Button>
            </Callout>
          )}
          {(c.sanitizer_flags.injection_suspected || c.sanitizer_flags.hidden_text_removed || c.manipulation) && (
            <Callout tone="bad" icon={<ShieldAlert size={15} />}>
              <div className="font-medium">Possible manipulation, so never auto-shortlisted</div>
              <div className="mt-0.5 text-xs text-muted">
                {c.sanitizer_flags.hidden_text_removed && `${c.sanitizer_flags.chars_removed} hidden characters removed before parsing. `}
                {c.injection_matches.length > 0 && <>Text aimed at an AI: <i>"{c.injection_matches[0]}"</i>.</>}
                {!c.sanitizer_flags.injection_suspected && !c.sanitizer_flags.hidden_text_removed && 'A long skills list with almost no evidence of use (keyword stuffing).'}
              </div>
            </Callout>
          )}

          {tab === 'summary' && (<>
            <Block title="Agent decision">
              <p className="text-[13px] font-medium">
                {c.decision === 'advance' ? 'Shortlisted: meets every must-have and the score threshold.' : 'Escalated to you. The agent does not reject.'}
              </p>
              {c.reasons.length > 0 && (
                <ul className="mt-2 space-y-2">
                  {c.reasons.map((r) => {
                    const info = settings?.info_codes?.includes(r)
                    return (
                      <li key={r} className="text-[13px]">
                        <span className={cx('font-medium', r === 'SUSPECTED_MANIPULATION' || r === 'MISSING_MUST_HAVE' ? 'text-bad' : info ? 'text-muted' : 'text-warn')}>{reasonLabel(r)}</span>
                        {info && <span className="text-xs text-faint"> · information only</span>}
                        <div className="text-xs text-muted">{c.reason_help[r] ?? settings?.reason_help?.[r]}</div>
                      </li>
                    )
                  })}
                </ul>
              )}
              {showLabels && c.label != null && (
                <p className="mt-3 text-xs text-muted">
                  Golden-set label (evaluation only): relevance <b className="text-fg">{c.label}/3</b>, ideal <b className="text-fg">{c.ideal}</b>
                  {c.ideal && c.ideal !== c.decision && <span className="text-warn"> · the agent disagrees</span>}
                </p>
              )}
            </Block>

            <Block title="Why" right={(!c.explanation || c.explanation_stale) && (
              <Button size="sm" variant="ghost" onClick={explain} disabled={busy || !!settings?.offline} title={settings?.offline ? 'Turn off Cache only to generate' : ''}><RefreshCw size={12} />Generate</Button>)}>
              {c.explanation && c.explanation_stale && (
                <p className="mb-2 text-xs text-warn">Outdated: written before the requirements, threshold or settings changed, so it may not match the current decision.</p>
              )}
              {c.explanation
                ? <p className={cx('text-[13px] leading-6', c.explanation_stale && 'text-faint')}>{highlight(c.explanation, quotes)}</p>
                : <p className="text-[13px] text-faint">No explanation cached for this pair.{settings?.offline ? ' Turn off Cache only to generate one.' : ''}</p>}
              <p className="mt-2 text-xs text-faint">Written by the LLM from the scorer's output only. Every quote is checked against the resume.</p>
            </Block>

            {c.gaps.length > 0 && (
              <Block title="Gaps to probe in interview">
                <ul className="list-disc space-y-0.5 pl-5 text-[13px] text-muted">{c.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
              </Block>
            )}
          </>)}

          {tab === 'evidence' && (<>
            <Block title="Score breakdown">
              <div className="space-y-2.5">
                {(Object.keys(DEFAULT_WEIGHTS) as (keyof typeof DEFAULT_WEIGHTS)[]).map((k) => {
                  const v = c.components[k]
                  return (
                    <div key={k} className="grid grid-cols-[130px_1fr_36px] items-center gap-3 text-[13px]">
                      <span className="text-muted">{COMP_LABEL[k]} <span className="num text-xs text-faint">{Math.round((weights[k] / wsum) * 100)}%</span></span>
                      {v == null ? <span className="text-xs text-faint">not available</span> : <Bar value={v} />}
                      <span className="num text-right">{v == null ? '–' : Math.round(v * 100)}</span>
                    </div>
                  )
                })}
                {c.blocking.includes('MISSING_MUST_HAVE') && <p className="text-xs text-muted">Score × {settings?.missing_must_have_cap ?? 0.6} because a must-have has no evidence.</p>}
              </div>
            </Block>
            <Block title="Requirements">
              <ul className="space-y-2.5">
                {c.full_evidence.map((e, i) => (
                  <li key={i} className="flex gap-2.5">
                    <span className="mt-0.5"><EvidenceIcon s={e.strength} /></span>
                    <div className="min-w-0 flex-1">
                      <div className="text-[13px]"><span className="font-medium">{e.requirement}</span> <span className="text-xs text-faint">{e.level === 'must' ? 'must-have' : 'nice-to-have'}</span></div>
                      <div className="text-xs text-muted">{basisText(e)}{e.quote && e.strength > 0 ? <> · "{e.quote}"</> : null}</div>
                    </div>
                  </li>
                ))}
              </ul>
            </Block>
          </>)}

          {tab === 'compare' && (
            <CompareView data={cmp} busy={cmpBusy} offline={!!settings?.offline} onRun={runCompare} />
          )}

          {tab === 'resume' && (
            <Block title="Resume, with contact details masked">
              <pre className="whitespace-pre-wrap font-sans text-[13px] leading-6 text-muted">{highlight(c.masked_text, quotes)}</pre>
              <p className="mt-3 text-xs text-faint">Highlights mark the evidence the scorer used. Names and contact details are masked before any model sees the text.</p>
            </Block>
          )}

          {tab === 'activity' && (
            c.history.length === 0 ? <p className="text-[13px] text-faint">No actions by people yet.</p> : (
              <ol className="space-y-3 border-l border-line pl-4">
                {[...c.history].reverse().map((h, i) => (
                  <li key={i} className="text-[13px]">
                    <div className="font-medium">{h.action.replace(/_/g, ' ')}</div>
                    <div className="text-xs text-faint">by {h.by} · {new Date(h.at).toLocaleString()}</div>
                    {h.note && <div className="text-xs text-muted">"{h.note}"</div>}
                  </li>
                ))}
              </ol>
            )
          )}
        </div>
      )}
    </Sheet>
  )
}

function CompareView({ data, busy, offline, onRun }: {
  data: Comparison | null; busy: false | 'base' | 'llm'; offline: boolean; onRun: (llm: boolean) => void
}) {
  if (!data) {
    return (
      <div className="rounded-lg border border-dashed border-line p-5 text-center">
        <div className="text-[13px] font-medium">How would simpler methods have judged this candidate?</div>
        <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-muted">
          Scores this role's applicants with keyword overlap, TF-IDF and embeddings, then shows this candidate's rank and
          decision under each, next to the pipeline. LLM zero-shot is read from the cache only, so no API call is made.
        </p>
        <Button className="mx-auto mt-3" variant="primary" onClick={() => onRun(false)} disabled={!!busy}>
          {busy ? <Spinner /> : <Play size={13} />}Run comparison
        </Button>
        {busy && <p className="mt-2 text-xs text-faint">The first run for a role takes a few seconds; after that it's instant.</p>}
      </div>
    )
  }
  const zs = data.systems.find((s) => s.key === 'llm_zeroshot')
  const fmt = (v: number | null) => (v == null ? '–' : v >= 0.1 || v === 0 ? v.toFixed(2) : v.toFixed(3))
  return (
    <div className="space-y-4">
      {data.label && (
        <p className="text-xs text-muted">Golden-set label: relevance <b className="text-fg">{data.label.relevance}/3</b>, ideal decision <b className="text-fg">{data.label.ideal}</b>. ✓ and ✕ mark agreement with it.</p>
      )}
      <div className="overflow-hidden rounded-lg border border-line">
        <table className="w-full text-[13px]">
          <thead><tr className="border-b border-line text-left text-xs text-faint">
            <th className="px-3 py-2 font-normal">Method</th><th className="px-2 py-2 text-right font-normal">Rank</th>
            <th className="px-2 py-2 text-right font-normal">Score</th><th className="whitespace-nowrap px-2 py-2 text-right font-normal">Cut-off</th>
            <th className="px-3 py-2 font-normal">Decision</th>
          </tr></thead>
          <tbody>
            {data.systems.map((s) => (
              <tr key={s.key} className={cx('border-b border-line-soft last:border-b-0', s.key === 'pipeline' && 'bg-accent-soft/50')} title={s.how}>
                <td className="px-3 py-2"><div className={cx(s.key === 'pipeline' && 'font-medium')}>{s.name}</div><div className="text-xs text-faint">{s.how}</div></td>
                <td className="num px-2 py-2 text-right align-top">{s.rank == null ? <span className="text-faint">–</span> : <>#{s.rank}<span className="text-xs text-faint">/{data.pool_size}</span></>}</td>
                <td className="num px-2 py-2 text-right align-top">{fmt(s.score)}</td>
                <td className="num px-2 py-2 text-right align-top text-muted">{fmt(s.threshold)}</td>
                <td className="px-3 py-2 align-top">
                  {s.decision ? (
                    <span className={cx('whitespace-nowrap', s.decision === 'advance' ? 'text-fg' : 'text-muted')}>
                      {s.decision === 'advance' ? 'Shortlist' : 'Escalate'}
                      {s.agrees != null && <span className={cx('ml-1', s.agrees ? 'text-good' : 'text-bad')}>{s.agrees ? '✓' : '✕'}</span>}
                    </span>
                  ) : <span className="text-xs text-faint">{s.status === 'not_cached' ? 'not cached' : 'unavailable'}</span>}
                  {s.own_decision && <div className="text-xs text-faint">its own call: {s.own_decision}</div>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {zs && zs.status !== 'ok' && (
        <Callout>
          LLM zero-shot has no cached answer for this pair.{' '}
          {offline ? 'Turn off Cache only in Settings → Model to run it (one Gemini call).' : (
            <Button size="sm" className="ml-1" onClick={() => onRun(true)} disabled={!!busy}>{busy === 'llm' ? <Spinner /> : <Play size={12} />}Run it (1 Gemini call)</Button>
          )}
        </Callout>
      )}
      <p className="text-xs text-faint">
        Ranks are within this role's {data.pool_size} applicants. Each baseline shortlists when its score reaches a cut-off tuned on the dev split with the same cost matrix as the pipeline.
        Baselines have no must-have check, so their scores aren't comparable to the pipeline's; compare ranks and decisions.
      </p>
    </div>
  )
}
