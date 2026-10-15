import { ArrowUpRight, BriefcaseBusiness, MapPin, Plus, Sparkles, TriangleAlert } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, type JobSummary, type Settings } from '../api'
import { go } from '../App'
import { Button, Chip, Modal, Spinner, STAGE_META, useToast } from '../components/ui'

export default function JobsPage({ settings }: { settings: Settings | null }) {
  const [jobs, setJobs] = useState<JobSummary[] | null>(null)
  const [q, setQ] = useState('')
  const [creating, setCreating] = useState(false)
  const toast = useToast()

  useEffect(() => {
    api.jobs().then(setJobs).catch((e) => toast({ title: 'Could not load jobs', body: e.message, tone: 'error' }))
  }, [toast])

  const shown = useMemo(() => (jobs ?? []).filter((j) => `${j.title} ${j.location} ${j.id}`.toLowerCase().includes(q.toLowerCase())), [jobs, q])
  const totals = useMemo(() => (jobs ?? []).reduce((a, j) => ({
    applicants: a.applicants + j.applicants, shortlisted: a.shortlisted + j.stages.shortlisted,
    review: a.review + j.needs_review, interview: a.interview + j.stages.interview,
  }), { applicants: 0, shortlisted: 0, review: 0, interview: 0 }), [jobs])

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-7xl px-8 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Open roles</h1>
            <p className="mt-1 text-sm text-muted">Every applicant is screened by the agent. It shortlists strong matches and escalates the rest to you, with reasons. It never rejects.</p>
          </div>
          <div className="flex gap-2">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search roles…" aria-label="Search roles"
              className="h-9 w-56 rounded-lg border border-line bg-panel px-3 text-sm outline-none focus:border-accent" />
            <Button variant="primary" onClick={() => setCreating(true)}><Plus size={15} />New role</Button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            ['Applications screened', totals.applicants, 'across all roles'],
            ['Shortlisted by agent', totals.shortlisted, 'met every must-have and the threshold'],
            ['Waiting for review', totals.review, 'escalated with a blocking reason'],
            ['Ready to interview', totals.interview, 'moved by a recruiter'],
          ].map(([l, v, s]) => (
            <div key={l as string} className="rounded-xl border border-line bg-panel p-4">
              <div className="text-xs text-muted">{l}</div>
              <div className="mt-1 text-2xl font-semibold tabular-nums">{jobs ? v : '–'}</div>
              <div className="mt-0.5 text-[11px] text-faint">{s}</div>
            </div>
          ))}
        </div>

        {!jobs ? (
          <div className="grid place-items-center py-24"><Spinner /></div>
        ) : (
          <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {shown.map((j) => {
              const total = j.applicants || 1
              return (
                <button key={j.id} onClick={() => go({ page: 'job', id: j.id })}
                  className="group rounded-xl border border-line bg-panel p-4 text-left transition-colors hover:border-accent/50">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 text-[11px] text-faint">
                        <span className="font-mono">{j.id}</span>
                        {j.kind === 'benchmark' && <span>· golden-set {j.split}</span>}
                        {j.edited && <Chip tone="accent">requirements edited</Chip>}
                      </div>
                      <div className="mt-1 line-clamp-2 font-medium leading-snug">{j.title}</div>
                    </div>
                    <ArrowUpRight size={16} className="shrink-0 text-faint transition-colors group-hover:text-accent" />
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                    <span className="inline-flex items-center gap-1"><MapPin size={12} />{j.location.replace(', United Kingdom', '')}</span>
                    <span>{j.job_type}</span><span>{j.level}</span>
                  </div>
                  <div className="mt-4 flex h-1.5 overflow-hidden rounded-full bg-raised">
                    {(['interview', 'shortlisted'] as const).map((s) => (
                      <div key={s} className={STAGE_META[s].dot} style={{ width: `${(j.stages[s] / total) * 100}%` }} />
                    ))}
                    <div className="bg-orange-400/70" style={{ width: `${(j.needs_review / total) * 100}%` }} />
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs">
                    <span className="text-muted"><b className="font-semibold text-fg tabular-nums">{j.applicants}</b> applicants</span>
                    <span className="text-muted"><b className="font-semibold text-amber-500 tabular-nums">{j.stages.shortlisted}</b> shortlisted</span>
                    <span className="text-muted"><b className="font-semibold text-orange-400 tabular-nums">{j.needs_review}</b> to review</span>
                    {j.stages.shortlisted === 0 && (
                      <span className="inline-flex items-center gap-1 text-faint" title="Nobody meets every must-have. Review the parsed requirements.">
                        <TriangleAlert size={12} />no full match
                      </span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>
      <NewJobModal open={creating} onClose={() => setCreating(false)} live={settings ? !settings.offline : false} />
    </div>
  )
}

function NewJobModal({ open, onClose, live }: { open: boolean; onClose: () => void; live: boolean }) {
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const toast = useToast()
  const submit = async () => {
    setBusy(true)
    try {
      const r = await api.createJob(title, text)
      onClose()
      go({ page: 'job', id: r.id })
    } catch (e) {
      toast({ title: 'Could not create the role', body: (e as Error).message, tone: 'error' })
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal open={open} onClose={onClose} title="New role" wide>
      <div className="space-y-3">
        <div className="flex items-start gap-2 rounded-lg border border-accent/30 bg-accent-soft p-3 text-xs text-muted">
          <Sparkles size={14} className="mt-0.5 shrink-0 text-accent" />
          The agent parses must-haves, nice-to-haves, minimum years and seniority from the posting. You can confirm or
          edit every requirement before it ranks anyone. {!live && <b className="text-fg">Turn on Live API (top right) first: a new JD needs a Gemini call.</b>}
        </div>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Role title (optional)" aria-label="Role title"
          className="h-9 w-full rounded-lg border border-line bg-bg px-3 text-sm outline-none focus:border-accent" />
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={12} placeholder="Paste the job description…" aria-label="Job description"
          className="w-full rounded-lg border border-line bg-bg p-3 text-sm outline-none focus:border-accent" />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={submit} disabled={!text.trim() || busy}>{busy ? <Spinner /> : <BriefcaseBusiness size={15} />}Parse & create</Button>
        </div>
      </div>
    </Modal>
  )
}
