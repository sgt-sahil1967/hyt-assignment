import { BriefcaseBusiness, ChevronRight, Plus, Search, Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, type JobSummary, type Settings } from '../api'
import { go } from '../App'
import { Button, Callout, Modal, PageHeader, Spinner, useToast } from '../components/ui'

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
    applicants: a.applicants + j.applicants, shortlisted: a.shortlisted + j.stages.shortlisted, review: a.review + j.needs_review,
  }), { applicants: 0, shortlisted: 0, review: 0 }), [jobs])

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-6xl px-4 py-8 md:px-8">
        <PageHeader title="Open roles"
          sub={jobs ? <><span className="num text-fg">{totals.applicants}</span> applicants screened · <span className="num text-fg">{totals.shortlisted}</span> shortlisted by the agent · <span className="num text-fg">{totals.review}</span> waiting for your review</> : 'Loading…'}
          actions={<>
            <div className="flex h-8 w-56 items-center gap-2 rounded-md border border-line bg-panel px-2.5 focus-within:border-accent max-sm:w-full">
              <Search size={14} className="text-faint" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search roles" aria-label="Search roles" className="h-full min-w-0 flex-1 bg-transparent text-[13px] outline-none" />
            </div>
            <Button variant="primary" onClick={() => setCreating(true)}><Plus size={14} />New role</Button>
          </>} />

        {!jobs ? (
          <div className="grid place-items-center py-24"><Spinner /></div>
        ) : (
          <div className="mt-6 overflow-hidden rounded-lg border border-line bg-panel">
            <div className="grid grid-cols-[1fr_90px_90px_90px_20px] gap-4 border-b border-line px-4 py-2 text-xs text-faint max-md:grid-cols-[1fr_70px_20px]">
              <span>Role</span><span className="text-right max-md:hidden">Applicants</span><span className="text-right">Shortlisted</span><span className="text-right max-md:hidden">To review</span><span />
            </div>
            {shown.map((j) => (
              <button key={j.id} onClick={() => go({ page: 'job', id: j.id })}
                className="group grid w-full grid-cols-[1fr_90px_90px_90px_20px] items-center gap-4 border-b border-line-soft px-4 py-3 text-left last:border-b-0 hover:bg-raised/60 max-md:grid-cols-[1fr_70px_20px]"
                title={j.kind === 'benchmark' ? `${j.id} · golden-set ${j.split} split` : j.id}>
                <div className="min-w-0">
                  <div className="truncate text-[13px] font-medium">{j.title}</div>
                  <div className="mt-0.5 truncate text-xs text-muted">
                    {[j.location.replace(', United Kingdom', ''), j.job_type, j.level].filter(Boolean).join(' · ')}
                    {j.edited && <span className="text-accent"> · requirements edited</span>}
                  </div>
                </div>
                <span className="num text-right text-[13px] text-muted max-md:hidden">{j.applicants}</span>
                <span className="num text-right text-[13px]">{j.stages.shortlisted || <span className="text-faint" title="Nobody meets every must-have. Check the parsed requirements.">0</span>}</span>
                <span className="num text-right text-[13px] text-muted max-md:hidden">{j.needs_review}</span>
                <ChevronRight size={15} className="text-faint group-hover:text-fg" />
              </button>
            ))}
            {shown.length === 0 && <div className="px-4 py-10 text-center text-[13px] text-muted">No roles match "{q}".</div>}
          </div>
        )}
        <p className="mt-3 text-xs text-faint">The agent shortlists candidates who meet every must-have and the score threshold, and escalates everyone else to you with a reason. It never rejects.</p>
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
        <p className="text-[13px] text-muted">The agent reads must-haves, nice-to-haves, minimum years and seniority from the posting. You can edit every requirement afterwards.</p>
        {!live && <Callout tone="warn" icon={<Sparkles size={14} />}>A new job description needs a Gemini call. Turn off <b>Cache only</b> in Settings → Model first.</Callout>}
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Role title (optional)" aria-label="Role title"
          className="h-9 w-full rounded-md border border-line bg-panel px-3 text-[13px] outline-none focus:border-accent" />
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={12} placeholder="Paste the job description" aria-label="Job description"
          className="w-full rounded-md border border-line bg-panel p-3 text-[13px] outline-none focus:border-accent" />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={submit} disabled={!text.trim() || busy}>{busy ? <Spinner /> : <BriefcaseBusiness size={14} />}Parse & create</Button>
        </div>
      </div>
    </Modal>
  )
}
