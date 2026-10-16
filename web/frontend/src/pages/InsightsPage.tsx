/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../api'
import { Callout, Chip, cx, PageHeader, Segmented, Spinner, Tabs } from '../components/ui'

const SYS_LABEL: Record<string, string> = { score: 'HYT pipeline', llm_zeroshot: 'LLM zero-shot', tfidf: 'TF-IDF', keyword: 'Keyword', embedding: 'Embedding' }
type Tab = 'accuracy' | 'errors' | 'versions' | 'safety'

function Panel({ title, children, note }: { title: string; children: ReactNode; note?: ReactNode }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5">
      <h2 className="text-[13px] font-semibold">{title}</h2>
      <div className="mt-4">{children}</div>
      {note && <p className="mt-4 text-xs text-faint">{note}</p>}
    </section>
  )
}

function Table({ head, rows, bold }: { head: string[]; rows: ReactNode[][]; bold?: (i: number) => boolean }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead><tr className="text-left text-xs text-faint">{head.map((h, i) => <th key={i} className={cx('pb-2 font-normal', i > 0 && 'text-right')}>{h}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => (
          <tr key={i} className={cx('border-t border-line-soft', bold?.(i) && 'font-medium')}>
            {r.map((c, j) => <td key={j} className={cx('py-2', j > 0 && 'num pl-3 text-right')}>{c}</td>)}
          </tr>))}
        </tbody>
      </table>
    </div>
  )
}

function CiBars({ rows }: { rows: { label: string; mean: number; lo: number; hi: number; highlight?: boolean }[] }) {
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r.label} className="grid grid-cols-[110px_1fr_40px] items-center gap-3 text-[13px]">
          <span className={cx(r.highlight ? 'font-medium' : 'text-muted')}>{r.label}</span>
          <div className="relative h-4 rounded-sm bg-raised">
            <div className={cx('absolute inset-y-0 left-0 rounded-sm', r.highlight ? 'bg-accent' : 'bg-faint/40')} style={{ width: `${r.mean * 100}%` }} />
            <div className="absolute top-1/2 h-px -translate-y-1/2 bg-fg/60" style={{ left: `${r.lo * 100}%`, width: `${(r.hi - r.lo) * 100}%` }} />
          </div>
          <span className="num text-right">{r.mean.toFixed(2)}</span>
        </div>
      ))}
    </div>
  )
}

const pct = (x: number | null | undefined) => (x == null ? '–' : `${Math.round(x * 100)}%`)

export default function InsightsPage() {
  const [d, setD] = useState<Record<string, any> | null>(null)
  const [overrides, setOverrides] = useState(0)
  const [tab, setTab] = useState<Tab>('accuracy')
  const [metric, setMetric] = useState<'ndcg@5' | 'ndcg@10' | 'p@5' | 'mrr'>('ndcg@10')
  const [err, setErr] = useState<string | null>(null)
  useEffect(() => {
    api.insights().then(setD).catch((e) => setErr(e.message))
    api.runtime().then((r) => setOverrides(Object.keys(r.overrides).filter((k) => k !== 'llm.offline').length)).catch(() => {})
  }, [])
  if (err) return <div className="grid h-full place-items-center text-[13px] text-bad">Could not load evaluation results: {err}</div>
  if (!d) return <div className="grid h-full place-items-center"><Spinner /></div>
  const m = d.metrics?.test
  const b = d.baselines ?? {}
  const systems = Object.entries(b).filter(([, v]: any) => v?.ranking)
  const { fairness: fair, adversarial: adv, robustness: rob, ablations: abl } = d
  const conf = m?.decision.confusion
  const zs = b.llm_zeroshot_own_decision?.confusion

  const kpis: [string, string, string][] = m ? [
    ['Rank correlation', m.spearman_score_vs_relevance.toFixed(2), `best baseline ${Math.max(...systems.filter(([k]) => k !== 'score').map(([, v]: any) => v.spearman)).toFixed(2)}`],
    ['NDCG@10', m.ranking['ndcg@10'].mean.toFixed(2), `95% CI ${m.ranking['ndcg@10'].lo.toFixed(2)}–${m.ranking['ndcg@10'].hi.toFixed(2)}`],
    ['Shortlist precision', pct(m.decision.precision_auto_advance), `${conf['ideal_advance&advanced']} of ${conf['ideal_advance&advanced'] + conf['ideal_escalate&advanced']} correct`],
    ['Quotes verified', pct(m.explanation_groundedness?.groundedness_rate ?? 0), `${m.explanation_groundedness?.quotes} quoted spans`],
    ['Run-to-run flips', rob ? `${(rob.decision_flip_rate * 100).toFixed(0)}%` : '–', rob ? `${rob.runs} runs × ${rob.pairs} pairs` : 'pending'],
  ] : []

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 md:px-8">
        <PageHeader title="How far can you trust the agent?"
          sub="Held-out test split: 7 jobs, 140 labelled (job, resume) pairs. Thresholds were tuned on a separate dev split, then frozen." />
        {overrides > 0 && <Callout tone="accent">These numbers were measured with the default settings. {overrides} setting{overrides > 1 ? 's are' : ' is'} currently changed in Settings.</Callout>}

        {m && (
          <div className="grid grid-cols-2 rounded-lg border border-line bg-panel sm:grid-cols-3 lg:grid-cols-5 lg:divide-x lg:divide-line">
            {kpis.map(([l, v, s]) => (
              <div key={l} className="p-4">
                <div className="text-xs text-muted">{l}</div>
                <div className="num mt-1 text-xl font-semibold">{v}</div>
                <div className="mt-0.5 text-xs text-faint">{s}</div>
              </div>
            ))}
          </div>
        )}

        <Tabs value={tab} onChange={setTab} tabs={[
          { value: 'accuracy', label: 'Accuracy vs baselines' }, { value: 'errors', label: 'Where errors come from' },
          { value: 'versions', label: 'Versions' }, { value: 'safety', label: 'Fairness & attacks' },
        ]} />

        {tab === 'accuracy' && (
          <div className="grid gap-5 lg:grid-cols-2">
            <Panel title="Ranking quality" note="Bars show the mean; the line is the 95% bootstrap interval. Baselines are scored on the same pairs.">
              <div className="mb-4"><Segmented label="Metric" value={metric} onChange={setMetric} options={(['ndcg@5', 'ndcg@10', 'p@5', 'mrr'] as const).map((k) => ({ value: k, label: k.toUpperCase() }))} /></div>
              <CiBars rows={systems.map(([k, v]: any) => ({ label: SYS_LABEL[k] ?? k, ...v.ranking[metric], highlight: k === 'score' })).sort((a, z) => z.mean - a.mean)} />
            </Panel>
            <Panel title="Decisions" note="Each baseline's threshold is tuned on dev with the same cost matrix (missing a good candidate costs 5, advancing a weak one costs 1).">
              <Table head={['System', 'Spearman', 'Precision', 'Escalated', 'Cost']} bold={(i) => systems[i][0] === 'score'}
                rows={systems.map(([k, v]: any) => [SYS_LABEL[k] ?? k, v.spearman.toFixed(2), pct(v.decision.precision_auto_advance), pct(v.decision.escalation_rate), v.decision.expected_cost])} />
              {zs && (
                <p className="mt-4 text-[13px] text-muted">
                  Asked to decide directly, the LLM advanced <b className="text-fg">{zs['ideal_advance&advanced'] + zs['ideal_escalate&advanced']}</b> candidates, and <b className="text-bad">{zs['ideal_escalate&advanced']}</b> were wrong. That's why the LLM only reads and code decides.
                </p>
              )}
            </Panel>
          </div>
        )}

        {tab === 'errors' && abl && (
          <Panel title="Diagnostic variants" note="Added after seeing test errors, to explain them. Never used as headline numbers.">
            <Table head={['Variant', 'Recall', 'Precision', 'Cost']} bold={(i) => i === 0}
              rows={Object.entries(abl).map(([k, v]: any) => [
                ({ frozen_system: 'Frozen system', oracle_jd_requirements: 'Correct JD requirements', career_switch_non_blocking: 'Career switch non-blocking', oracle_jd_and_career_switch_non_blocking: 'Both' } as Record<string, string>)[k] ?? k,
                v.decision.recall_ideal_advance.toFixed(2), v.decision.precision_auto_advance?.toFixed(2) ?? '–', v.decision.expected_cost])} />
            <p className="mt-4 text-[13px] text-muted">
              Most missed advances come from <b className="text-fg">reading the job description</b>, not from scoring. That's why every role has editable requirements: fixing JD01's two wrong must-haves shortlists all 8 good candidates.
            </p>
          </Panel>
        )}

        {tab === 'versions' && d.v1_1 && (
          <Panel title="Changes made after the test evaluation" note="Each change is measured on its own. v1.0 stays the headline; dev results are unchanged for every variant.">
            <Table head={['Version', 'Spearman', 'Recall', 'Precision', 'Escalated', 'Cost']} bold={(i) => i === 0}
              rows={[
                ...([['A_v1_0_frozen', 'v1.0 frozen (headline)'], ['B_plus_framework_taxonomy', '+ framework categories'], ['C_v1_1_plus_career_switch_informational', 'v1.1: career switch informational']] as const).map(([k, label]) => {
                  const t = d.v1_1[k].test
                  return [label, t.spearman.toFixed(3), t.decision.recall_ideal_advance.toFixed(2), t.decision.precision_auto_advance?.toFixed(2), pct(t.decision.escalation_rate), t.decision.expected_cost]
                }),
                ...(d.posthoc?.E_v1_2 ? [(() => { const t = d.posthoc.E_v1_2.golden_test; return ['v1.2: four real-data fixes', t.spearman.toFixed(3), t.recall_ideal_advance.toFixed(2), t.precision_auto_advance?.toFixed(2), pct(t.escalation_rate), t.expected_cost] })()] : []),
              ]} />
            <p className="mt-4 text-[13px] text-muted">{d.v1_1.decision_flips_v1_0_to_v1_1.length} decisions changed from v1.0 to v1.1, all from escalate to advance, and all for candidates the labels say should advance.</p>
            {d.real_set && (
              <p className="mt-2 text-[13px] text-muted">
                Real-resume sanity set (50 Kaggle pairs, labels pending review): Spearman <b className="text-fg">{d.real_set.systems.score.spearman.toFixed(2)}</b> vs ≤ {Math.max(d.real_set.systems.tfidf.spearman, d.real_set.systems.embedding.spearman, d.real_set.systems.keyword.spearman).toFixed(2)} for baselines; {d.real_set.decision_current.confusion['ideal_advance&advanced']}/{d.real_set.ideal_advance} good candidates advanced, {d.real_set.decision_current.confusion['ideal_escalate&advanced']} wrong advances.
              </p>
            )}
          </Panel>
        )}

        {tab === 'safety' && (
          <div className="grid gap-5 lg:grid-cols-2">
            <Panel title="Fairness: counterfactual twins" note={fair?.coverage ? `Same resume, one signal changed. ${Object.entries(fair.coverage).map(([k, v]) => `${k}: ${v}`).join(' · ')}` : undefined}>
              {!fair ? <p className="text-[13px] text-muted">Pending.</p> : (<>
                <Table head={['Signal changed', 'Mean |Δ score|', '']}
                  rows={Object.entries(fair.results?.unblinded ?? {}).map(([k, v]: any) => [
                    <span className="text-muted">{k.replace(/_/g, ' ').replace(':', ' · ')}</span>, v.mean_abs_delta.toFixed(3),
                    v.mean_abs_delta === 0 ? <Chip tone="good">none</Chip> : v.decision_flip_rate === 0 ? <Chip tone="warn">tiny</Chip> : <Chip tone="bad">flips</Chip>])} />
                <p className="mt-4 text-[13px] text-muted">No decision flipped for any signal. A caregiving gap used to count as a year of work; the suite caught it and it's fixed.</p>
              </>)}
            </Panel>
            <Panel title="Adversarial resumes" note="4 resumes × 8 attacks. Detected means escalated as possible manipulation.">
              {!adv ? <p className="text-[13px] text-muted">Pending.</p> : (<>
                <Table head={['Attack', 'Detected', 'Shortlisted', 'Δ score']}
                  rows={Object.entries(adv.per_attack).map(([k, v]: any) => [
                    k.replace(/_/g, ' '), pct(v.detection_rate),
                    <span className={cx(v.auto_advance_rate > 0 && 'text-bad')}>{pct(v.auto_advance_rate)}</span>,
                    `${v.mean_score_delta >= 0 ? '+' : ''}${v.mean_score_delta.toFixed(2)}`])} />
                <p className="mt-4 text-[13px] text-muted">Hidden-text and injection attacks are always caught. A candidate who simply lies in the skills list can't be detected from text alone, so listed skills earn half credit and interviews verify them.</p>
              </>)}
            </Panel>
          </div>
        )}
      </div>
    </div>
  )
}
