import { Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, type LibraryItem } from '../api'
import { Button, Chip, cx, Modal, Spinner, useToast } from './ui'

/** Choose which already-parsed resumes a new role screens. Nothing is added until the recruiter saves. */
export default function PoolPicker({ open, onClose, jobId, onDone }: { open: boolean; onClose: () => void; jobId: string; onDone: () => void }) {
  const [items, setItems] = useState<LibraryItem[] | null>(null)
  const [picked, setPicked] = useState<Set<string>>(new Set())
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const toast = useToast()

  useEffect(() => {
    if (!open) return
    setItems(null); setQ('')
    api.library(jobId).then((l) => { setItems(l); setPicked(new Set(l.filter((x) => x.in_pool && !x.own_upload).map((x) => x.id))) })
      .catch((e) => toast({ title: 'Could not load resumes', body: e.message, tone: 'error' }))
  }, [open, jobId, toast])

  const shown = useMemo(() => (items ?? []).filter((x) => !x.own_upload &&
    `${x.id} ${x.title} ${x.skills.join(' ')} ${x.source}`.toLowerCase().includes(q.toLowerCase())), [items, q])
  const choosable = (items ?? []).filter((x) => !x.own_upload)
  const before = new Set(choosable.filter((x) => x.in_pool).map((x) => x.id))
  const adds = [...picked].filter((c) => !before.has(c)).length
  const removes = [...before].filter((c) => !picked.has(c)).length
  const allShown = shown.length > 0 && shown.every((x) => picked.has(x.id))

  const toggle = (id: string) => setPicked((p) => { const n = new Set(p); if (n.has(id)) n.delete(id); else n.add(id); return n })
  const setShown = (on: boolean) => setPicked((p) => { const n = new Set(p); shown.forEach((x) => (on ? n.add(x.id) : n.delete(x.id))); return n })
  const save = async (ids: string[]) => {
    setBusy(true)
    try {
      const r = await api.setPool(jobId, ids)
      toast({ title: `${r.size} candidate${r.size === 1 ? '' : 's'} in this role`, body: `${r.added.length} added, ${r.removed.length} removed. Screened from cached extractions, with no LLM call.` })
      onDone(); onClose()
    } catch (e) {
      toast({ title: 'Could not update candidates', body: (e as Error).message, tone: 'error' })
    } finally { setBusy(false) }
  }

  return (
    <Modal open={open} onClose={onClose} title="Choose candidates" wide>
      {!items ? <div className="grid place-items-center py-12"><Spinner /></div> : (
        <div className="space-y-3">
          <p className="text-[13px] text-muted">Pick already-parsed resumes to screen for this role. Resumes uploaded to this role are always included.</p>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex h-8 min-w-48 flex-1 items-center gap-2 rounded-md border border-line bg-panel px-2.5 focus-within:border-accent">
              <Search size={14} className="text-faint" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search title, skill or ID" aria-label="Search resumes" className="h-full min-w-0 flex-1 bg-transparent text-[13px] outline-none" />
            </div>
            <Button variant="ghost" onClick={() => setShown(!allShown)}>{allShown ? 'Clear' : 'Select'} {q ? 'matching' : 'all'} ({shown.length})</Button>
          </div>
          <div className="max-h-[48vh] divide-y divide-line-soft overflow-auto rounded-lg border border-line">
            {shown.map((x) => (
              <label key={x.id} className={cx('flex cursor-pointer items-start gap-3 px-3 py-2.5 hover:bg-raised/60', picked.has(x.id) && 'bg-accent-soft/50')}>
                <input type="checkbox" checked={picked.has(x.id)} onChange={() => toggle(x.id)} className="mt-1 accent-[var(--accent)]" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 text-[13px]">
                    <span className="font-medium">{x.id}</span>
                    <span className="truncate text-muted">{x.title || 'No role found'}{x.years != null && ` · ${x.years} yrs`}</span>
                    {x.source !== 'benchmark corpus' && <Chip>{x.source}</Chip>}
                    {!x.parsed && <Chip tone="warn">not parsed</Chip>}
                  </div>
                  {x.skills.length > 0 && <div className="truncate text-xs text-faint">{x.skills.join(' · ')}</div>}
                </div>
              </label>
            ))}
            {shown.length === 0 && <div className="px-3 py-8 text-center text-[13px] text-muted">No resumes match "{q}".</div>}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="mr-auto text-xs text-muted">{picked.size} selected{adds || removes ? ` · +${adds} / −${removes}` : ''}</span>
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button onClick={() => save(choosable.map((x) => x.id))} disabled={busy}>Add all {choosable.length}</Button>
            <Button variant="primary" onClick={() => save([...picked])} disabled={busy || (adds === 0 && removes === 0)}>{busy && <Spinner />}Save selection</Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
