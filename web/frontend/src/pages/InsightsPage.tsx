/* eslint-disable @typescript-eslint/no-explicit-any */
import { FlaskConical, Scale, ShieldCheck, Target } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../api'
import { Chip, cx, Spinner } from '../components/ui'

const SYS_LABEL: Record<string, string> = { score: 'HYT pipeline', llm_zeroshot: 'LLM zero-shot', tfidf: 'TF-IDF', keyword: 'Keyword', embedding: 'Embedding' }

function Card({ title, icon, children, note }: { title: string; icon: ReactNode; children: ReactNode; note?: ReactNode }) {
  return (
    <section className="rounded-2xl border border-line bg-panel p-5">
      <h2 className="flex items-center gap-2 font-semibold">{icon}{title}</h2>
      <div className="mt-4">{children}</div>
      {note && <p className="mt-3 text-xs text-faint">{note}</p>}
    </section>
  )
}

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {sub && <div className="mt-0.5 text-[11px] text-faint">{sub}</div>}
    </div>
  )
}

function CiBars({ rows }: { rows: { label: string; mean: number; lo: number; hi: number; highlight?: boolean }[] }) {
  return (
    <div className="space-y-2.5">
      {rows.map((r) => (
        <div key={r.label} className="grid grid-cols-[120px_1fr_48px] items-center gap-3 text-xs">
          <span className={cx(r.highlight ? 'font-medium text-fg' : 'text-muted')}>{r.label}</span>
          <div className="relative h-5 rounded bg-raised">
            <div className={cx('absolute inset-y-0 left-0 rounded', r.highlight ? 'bg-accent' : 'bg-zinc-500/50')} style={{ width: `${r.mean * 100}%` }} />
            <div className="absolute top-1/2 h-px -translate-y-1/2 bg-fg/70" style={{ left: `${r.lo * 100}%`, width: `${(r.hi - r.lo) * 100}%` }} />
            <div className="absolute top-1 bottom-1 w-px bg-fg/70" style={{ left: `${r.lo * 100}%` }} />
            <div className="absolute top-1 bottom-1 w-px bg-fg/70" style={{ left: `${r.hi * 100}%` }} />
          </div>
          <span className="text-right font-mono">{r.mean.toFixed(2)}</span>
        </div>
      ))}
    </div>
  )
}

export default function InsightsPage() {
  const [d, setD] = useState<Record<string, any> | null>(null)
  const [metric, setMetric] = useState<'ndcg@5' | 'ndcg@10' | 'p@5' | 'mrr'>('ndcg@10')
  const [err, setErr] = useState<string | null>(null)
  useEffect(() => { api.insights().then(setD).catch((e) => setErr(e.message)) }, [])
  if (err) return <div className="grid h-full place-items-center text-sm text-rose-500">Could not load evaluation results: {err}</div>
  if (!d) return <div className="grid h-full place-items-center"><Spinner /></div>
  const m = d.metrics?.test
  const b = d.baselines ?? {}
  const systems = Object.entries(b).filter(([, v]: any) => v?.ranking)
  const fair = d.fairness
  const adv = d.adversarial
  const rob = d.robustness
  const abl = d.ablations

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-7xl space-y-5 px-8 py-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">How far can you trust the agent?</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted">Held-out test split: 7 jobs, 140 hand-labelled (job, resume) pairs. Thresholds were tuned on a separate dev split, then frozen. Intervals are 95% bootstrap CIs.</p>
        </div>

        {m && (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <Kpi label="Rank correlation with labels" value={m.spearman_score_vs_relevance.toFixed(2)} sub={`best baseline ${Math.max(...systems.filter(([k]) => k !== 'score').map(([, v]: any) => v.spearman)).toFixed(2)}`} />
            <Kpi label="NDCG@10" value={m.ranking['ndcg@10'].mean.toFixed(2)} sub={`CI ${m.ranking['ndcg@10'].lo.toFixed(2)}–${m.ranking['ndcg@10'].hi.toFixed(2)}`} />
            <Kpi label="Auto-shortlist precision" value={`${Math.round(m.decision.precision_auto_advance * 100)}%`} sub={`${m.decision.confusion['ideal_advance&advanced']} of ${m.decision.confusion['ideal_advance&advanced'] + m.decision.confusion['ideal_escalate&advanced']} correct`} />
            <Kpi label="Quotes verified in resume" value={`${Math.round((m.explanation_groundedness?.groundedness_rate ?? 0) * 100)}%`} sub={`${m.explanation_groundedness?.quotes} quoted spans`} />
            <Kpi label="Run-to-run flips" value={rob ? `${(rob.decision_flip_rate * 100).toFixed(0)}%` : '–'} sub={rob ? `${rob.runs} fresh runs × ${rob.pairs} pairs` : 'pending'} />
          </div>
        )}

        <div className="grid gap-5 lg:grid-cols-2">
          <Card title="Ranking vs baselines" icon={<Target size={16} className="text-accent" />}
            note="Baselines get the same pairs. Their decisions use a threshold tuned on dev with the same cost matrix.">
            <div className="mb-4 inline-flex rounded-lg border border-line p-0.5">
              {(['ndcg@5', 'ndcg@10', 'p@5', 'mrr'] as const).map((k) => (
                <button key={k} onClick={() => setMetric(k)} className={cx('rounded-md px-2.5 py-1 text-xs', metric === k ? 'bg-raised font-medium' : 'text-muted')}>{k.toUpperCase()}</button>
              ))}
            </div>
            <CiBars rows={systems.map(([k, v]: any) => ({ label: SYS_LABEL[k] ?? k, ...v.ranking[metric], highlight: k === 'score' }))
              .sort((a, z) => z.mean - a.mean)} />
            <table className="mt-5 w-full text-xs">
              <thead><tr className="text-left text-muted"><th className="pb-1.5 font-medium">System</th><th className="font-medium">Spearman</th><th className="font-medium">Precision</th><th className="font-medium">Escalated</th><th className="font-medium">Cost</th></tr></thead>
              <tbody>{systems.map(([k, v]: any) => (
                <tr key={k} className={cx('border-t border-line', k === 'score' && 'font-medium')}>
                  <td className="py-1.5">{SYS_LABEL[k] ?? k}</td><td className="font-mono">{v.spearman.toFixed(2)}</td>
                  <td className="font-mono">{v.decision.precision_auto_advance == null ? '–' : `${Math.round(v.decision.precision_auto_advance * 100)}%`}</td>
                  <td className="font-mono">{Math.round(v.decision.escalation_rate * 100)}%</td><td className="font-mono">{v.decision.expected_cost}</td>
                </tr>))}
              </tbody>
            </table>
            {b.llm_zeroshot_own_decision && (
              <p className="mt-3 rounded-lg bg-raised/60 p-2.5 text-xs text-muted">
                Asked directly, the LLM advanced <b className="text-fg">{b.llm_zeroshot_own_decision.confusion['ideal_advance&advanced'] + b.llm_zeroshot_own_decision.confusion['ideal_escalate&advanced']}</b> candidates, and
                <b className="text-rose-500"> {b.llm_zeroshot_own_decision.confusion['ideal_escalate&advanced']}</b> of them were wrong. That's why the LLM only reads and code decides.
              </p>
            )}
          </Card>

          {d.v1_1 && (
            <Card title="Post-hoc v1.1 vs frozen v1.0" icon={<FlaskConical size={16} className="text-accent" />}
              note="Changes made after the test evaluation, measured one at a time. v1.0 stays the headline. Dev results unchanged for every variant.">
              <table className="w-full text-xs">
                <thead><tr className="text-left text-muted"><th className="pb-1.5 font-medium">Version</th><th className="font-medium">Spearman</th><th className="font-medium">Recall</th><th className="font-medium">Precision</th><th className="font-medium">Escalated</th><th className="font-medium">Cost</th></tr></thead>
                <tbody>{([['A_v1_0_frozen', 'v1.0 frozen (headline)'], ['B_plus_framework_taxonomy', '+ framework categories (#25)'], ['C_v1_1_plus_career_switch_informational', 'v1.1: + CAREER_SWITCH informational (#27)']] as const).map(([k, label]) => {
                  const t = d.v1_1[k].test
                  return (
                    <tr key={k} className={cx('border-t border-line', k.startsWith('C') && 'font-medium')}>
                      <td className="py-1.5">{label}</td><td className="font-mono">{t.spearman.toFixed(3)}</td>
                      <td className="font-mono">{t.decision.recall_ideal_advance.toFixed(2)}</td><td className="font-mono">{t.decision.precision_auto_advance?.toFixed(2)}</td>
                      <td className="font-mono">{Math.round(t.decision.escalation_rate * 100)}%</td><td className="font-mono">{t.decision.expected_cost}</td>
                    </tr>)
                })}</tbody>
              </table>
              <p className="mt-3 text-xs text-muted">{d.v1_1.decision_flips_v1_0_to_v1_1.length} decisions changed, all escalate → advance, and all are candidates the labels say should advance.</p>
            </Card>
          )}

          <Card title="Where errors come from" icon={<FlaskConical size={16} className="text-accent" />}
            note="Diagnostic variants added after seeing test errors. They explain errors and are never used as headline numbers.">
            {abl && (
              <table className="w-full text-xs">
                <thead><tr className="text-left text-muted"><th className="pb-1.5 font-medium">Variant</th><th className="font-medium">Recall</th><th className="font-medium">Precision</th><th className="font-medium">Cost</th></tr></thead>
                <tbody>{Object.entries(abl).map(([k, v]: any) => (
                  <tr key={k} className="border-t border-line">
                    <td className="py-1.5">{({ frozen_system: 'Frozen system', oracle_jd_requirements: 'Correct JD requirements', career_switch_non_blocking: 'CAREER_SWITCH non-blocking', oracle_jd_and_career_switch_non_blocking: 'Both' } as Record<string, string>)[k] ?? k}</td>
                    <td className="font-mono">{v.decision.recall_ideal_advance.toFixed(2)}</td>
                    <td className="font-mono">{v.decision.precision_auto_advance?.toFixed(2) ?? '–'}</td>
                    <td className="font-mono">{v.decision.expected_cost}</td>
                  </tr>))}
                </tbody>
              </table>
            )}
            <p className="mt-3 rounded-lg border border-accent/30 bg-accent-soft p-2.5 text-xs text-muted">
              Most missed advances come from <b className="text-fg">JD requirement extraction</b>, not scoring. That's why each job opens with an editable requirements panel: a recruiter fixing JD01's two wrong must-haves shortlists all 8 good candidates.
            </p>
          </Card>

          <Card title="Fairness: counterfactual twins" icon={<Scale size={16} className="text-accent" />}
            note={fair ? `Same resume, one signal changed. ${fair.coverage ? Object.entries(fair.coverage).map(([k, v]) => `${k}: ${v}`).join(' · ') : ''}` : ''}>
            {!fair ? <p className="text-sm text-muted">Pending.</p> : (
              <div className="space-y-1.5">
                {Object.entries(fair.results?.unblinded ?? {}).map(([k, v]: any) => (
                  <div key={k} className="grid grid-cols-[1fr_80px_60px] items-center gap-3 text-xs">
                    <span className="truncate text-muted" title={k}>{k.replace(/_/g, ' ').replace(':', ' · ')}</span>
                    <span className="font-mono">|Δ| {v.mean_abs_delta.toFixed(3)}</span>
                    {v.mean_abs_delta === 0 ? <Chip tone="good">none</Chip> : v.decision_flip_rate === 0 ? <Chip tone="warn">tiny</Chip> : <Chip tone="bad">flips</Chip>}
                  </div>
                ))}
                <p className="pt-2 text-xs text-muted">No decision flipped for any signal. A caregiving gap used to be counted as a year of work; the suite caught it and it's fixed.</p>
              </div>
            )}
          </Card>

          <Card title="Adversarial resumes" icon={<ShieldCheck size={16} className="text-accent" />}
            note="4 real resumes × 8 attacks. 'Detected' means escalated as SUSPECTED_MANIPULATION.">
            {!adv ? <p className="text-sm text-muted">Pending.</p> : (
              <table className="w-full text-xs">
                <thead><tr className="text-left text-muted"><th className="pb-1.5 font-medium">Attack</th><th className="font-medium">Detected</th><th className="font-medium">Auto-shortlisted</th><th className="font-medium">Δ score</th></tr></thead>
                <tbody>{Object.entries(adv.per_attack).map(([k, v]: any) => (
                  <tr key={k} className="border-t border-line">
                    <td className="py-1.5">{k.replace(/_/g, ' ')}</td>
                    <td>{v.detection_rate === 1 ? <Chip tone="good">100%</Chip> : <Chip tone={v.detection_rate ? 'warn' : 'bad'}>{Math.round(v.detection_rate * 100)}%</Chip>}</td>
                    <td className={cx('font-mono', v.auto_advance_rate > 0 && 'text-rose-500')}>{Math.round(v.auto_advance_rate * 100)}%</td>
                    <td className="font-mono">{v.mean_score_delta >= 0 ? '+' : ''}{v.mean_score_delta.toFixed(2)}</td>
                  </tr>))}
                </tbody>
              </table>
            )}
            <p className="mt-3 text-xs text-muted">Hidden-text and injection attacks are always caught. A candidate who simply lies in the skills list can't be detected from text alone, so listed skills earn half credit and interviews verify them.</p>
          </Card>
        </div>
      </div>
    </div>
  )
}
