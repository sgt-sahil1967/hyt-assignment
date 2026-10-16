import clsx from 'clsx'
import { X } from 'lucide-react'
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import type { Stage } from '../api'

export const cx = clsx

export const STAGE_META: Record<Stage, { label: string; dot: string }> = {
  new: { label: 'Unreviewed', dot: 'bg-faint' },
  shortlisted: { label: 'Shortlisted', dot: 'bg-accent' },
  interview: { label: 'Interview', dot: 'bg-good' },
  rejected: { label: 'Rejected', dot: 'bg-bad' },
}

export function Button({
  children, onClick, variant = 'secondary', size = 'md', disabled, title, className, type = 'button',
}: {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
  disabled?: boolean
  title?: string
  className?: string
  type?: 'button' | 'submit'
}) {
  return (
    <button
      type={type}
      title={title}
      disabled={disabled}
      onClick={onClick}
      className={cx(
        'inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
        size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-8 px-3 text-[13px]',
        variant === 'primary' && 'bg-accent text-white hover:brightness-110 dark:text-zinc-950',
        variant === 'secondary' && 'border border-line bg-panel text-fg hover:bg-raised',
        variant === 'ghost' && 'text-muted hover:bg-raised hover:text-fg',
        variant === 'danger' && 'bg-bad text-white hover:brightness-110',
        className,
      )}
    >
      {children}
    </button>
  )
}

export function IconButton({ children, onClick, label, active }: { children: ReactNode; onClick?: () => void; label: string; active?: boolean }) {
  return (
    <button onClick={onClick} aria-label={label} title={label}
      className={cx('grid size-8 shrink-0 place-items-center rounded-md transition-colors', active ? 'bg-raised text-fg' : 'text-muted hover:bg-raised hover:text-fg')}>
      {children}
    </button>
  )
}

export function Dot({ className }: { className: string }) {
  return <span className={cx('inline-block size-1.5 shrink-0 rounded-full', className)} />
}

export function StagePill({ stage, by }: { stage: Stage; by?: string | null }) {
  const m = STAGE_META[stage]
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap text-[13px] text-muted">
      <Dot className={m.dot} />
      <span className={stage === 'new' ? 'text-faint' : 'text-fg'}>{m.label}</span>
      {by === 'agent' && stage === 'shortlisted' && <span className="text-faint" title="Shortlisted by the agent">· agent</span>}
    </span>
  )
}

/** Fit score as a plain number with a thin bar under it: green when the agent would shortlist. */
export function Score({ score, passed, large }: { score: number; passed?: boolean; large?: boolean }) {
  return (
    <div className={cx('shrink-0', large ? 'w-16' : 'w-11')} title={`Fit score ${score.toFixed(3)}`}>
      <div className={cx('num font-medium', large ? 'text-2xl' : 'text-[13px]', passed ? 'text-good' : 'text-fg')}>{Math.round(score * 100)}</div>
      <div className="mt-1 h-[3px] w-full overflow-hidden rounded-full bg-raised">
        <div className={cx('h-full rounded-full', passed ? 'bg-good' : 'bg-faint')} style={{ width: `${Math.min(1, score) * 100}%` }} />
      </div>
    </div>
  )
}

export function Chip({ children, tone = 'default', title }: { children: ReactNode; tone?: 'default' | 'good' | 'warn' | 'bad' | 'accent'; title?: string }) {
  return (
    <span title={title} className={cx(
      'inline-flex items-center gap-1 whitespace-nowrap rounded px-1.5 py-px text-[11px] font-medium leading-4',
      tone === 'default' && 'bg-raised text-muted',
      tone === 'good' && 'bg-good/10 text-good',
      tone === 'warn' && 'bg-warn/10 text-warn',
      tone === 'bad' && 'bg-bad/10 text-bad',
      tone === 'accent' && 'bg-accent-soft text-accent',
    )}>{children}</span>
  )
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button role="switch" aria-checked={checked} aria-label={label} onClick={() => onChange(!checked)}
      className={cx('relative h-5 w-9 shrink-0 rounded-full transition-colors', checked ? 'bg-accent' : 'bg-line')}>
      <span className={cx('absolute top-0.5 size-4 rounded-full bg-white shadow transition-all', checked ? 'left-[18px]' : 'left-0.5')} />
    </button>
  )
}

export function Segmented<T extends string>({ value, options, onChange, label, size = 'md' }: {
  value: T; options: { value: T; label: ReactNode; title?: string }[]; onChange: (v: T) => void; label: string; size?: 'sm' | 'md'
}) {
  return (
    <div className="inline-flex rounded-md bg-raised p-0.5" role="radiogroup" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} role="radio" aria-checked={value === o.value} title={o.title} onClick={() => onChange(o.value)}
          className={cx('rounded-[5px] transition-colors', size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
            value === o.value ? 'bg-panel font-medium text-fg shadow-sm' : 'text-muted hover:text-fg')}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Tabs<T extends string>({ value, tabs, onChange, className }: {
  value: T; tabs: { value: T; label: ReactNode; count?: number }[]; onChange: (v: T) => void; className?: string
}) {
  return (
    <div className={cx('flex gap-5 overflow-x-auto border-b border-line', className)} role="tablist">
      {tabs.map((t) => (
        <button key={t.value} role="tab" aria-selected={value === t.value} onClick={() => onChange(t.value)} className={cx(
          '-mb-px flex shrink-0 items-center gap-1.5 border-b-2 pb-2.5 pt-1 text-[13px] transition-colors',
          value === t.value ? 'border-fg font-medium text-fg' : 'border-transparent text-muted hover:text-fg')}>
          {t.label}
          {t.count != null && <span className="num text-xs text-faint">{t.count}</span>}
        </button>
      ))}
    </div>
  )
}

export function Menu({ trigger, children, align = 'right' }: { trigger: ReactNode; children: (close: () => void) => ReactNode; align?: 'left' | 'right' }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const h = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false) }
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', h)
    document.addEventListener('keydown', k)
    return () => { document.removeEventListener('mousedown', h); document.removeEventListener('keydown', k) }
  }, [open])
  return (
    <div className="relative" ref={ref}>
      <div onClick={(e) => { e.stopPropagation(); setOpen((o) => !o) }}>{trigger}</div>
      {open && (
        <div onClick={(e) => e.stopPropagation()} className={cx(
          'fadein absolute z-30 mt-1 min-w-44 rounded-lg border border-line bg-panel p-1 shadow-lg shadow-black/10 dark:shadow-black/40',
          align === 'right' ? 'right-0' : 'left-0',
        )}>
          {children(() => setOpen(false))}
        </div>
      )}
    </div>
  )
}

export function MenuItem({ children, onClick, disabled, danger }: { children: ReactNode; onClick: () => void; disabled?: boolean; danger?: boolean }) {
  return (
    <button disabled={disabled} onClick={onClick} className={cx(
      'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-[13px] hover:bg-raised disabled:opacity-40',
      danger && 'text-bad',
    )}>{children}</button>
  )
}

function useEscape(open: boolean, onClose: () => void) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    if (open) document.addEventListener('keydown', k)
    return () => document.removeEventListener('keydown', k)
  }, [open, onClose])
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  useEscape(open, onClose)
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onMouseDown={onClose}>
      <div role="dialog" aria-label={title} onMouseDown={(e) => e.stopPropagation()}
        className={cx('fadein max-h-[88vh] w-full overflow-auto rounded-xl border border-line bg-panel shadow-2xl', wide ? 'max-w-2xl' : 'max-w-lg')}>
        <div className="flex items-center justify-between px-5 pb-1 pt-4">
          <h2 className="text-[15px] font-semibold">{title}</h2>
          <IconButton onClick={onClose} label="Close"><X size={16} /></IconButton>
        </div>
        <div className="px-5 pb-5 pt-2">{children}</div>
      </div>
    </div>
  )
}

/** Panel sliding in from the right over the page (requirements editor, candidate detail). */
export function Sheet({ open, onClose, title, children, width = 'w-[min(560px,100%)]', side = 'right', header }: {
  open: boolean; onClose: () => void; title: string; children: ReactNode; width?: string; side?: 'left' | 'right'; header?: ReactNode
}) {
  useEscape(open, onClose)
  if (!open) return null
  return (
    <div className="absolute inset-0 z-20 flex bg-black/20 dark:bg-black/40" onMouseDown={onClose} style={{ justifyContent: side === 'right' ? 'flex-end' : 'flex-start' }}>
      <aside role="dialog" aria-label={title} onMouseDown={(e) => e.stopPropagation()}
        className={cx('slidein flex h-full flex-col bg-panel shadow-2xl', width, side === 'right' ? 'border-l border-line' : 'border-r border-line')}>
        {header ?? (
          <div className="flex h-12 shrink-0 items-center justify-between border-b border-line px-5">
            <h2 className="text-sm font-semibold">{title}</h2>
            <IconButton onClick={onClose} label="Close"><X size={16} /></IconButton>
          </div>
        )}
        {children}
      </aside>
    </div>
  )
}

export function Bar({ value, className }: { value: number; className?: string }) {
  return (
    <div className="h-1 w-full overflow-hidden rounded-full bg-raised">
      <div className={cx('h-full rounded-full', className ?? 'bg-accent')} style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
    </div>
  )
}

export function Callout({ tone = 'default', icon, children }: { tone?: 'default' | 'warn' | 'bad' | 'accent'; icon?: ReactNode; children: ReactNode }) {
  return (
    <div className={cx('flex gap-2.5 rounded-lg p-3 text-[13px] leading-5',
      tone === 'default' && 'bg-raised text-muted',
      tone === 'warn' && 'bg-warn/10 text-fg',
      tone === 'bad' && 'bg-bad/10 text-fg',
      tone === 'accent' && 'bg-accent-soft text-fg')}>
      {icon && <span className={cx('mt-0.5 shrink-0', tone === 'warn' && 'text-warn', tone === 'bad' && 'text-bad', tone === 'accent' && 'text-accent')}>{icon}</span>}
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}

// ---------------------------------------------------------------- toasts
type Toast = { id: number; title: string; body?: ReactNode; tone?: 'default' | 'error'; action?: { label: string; run: () => void } }
const ToastCtx = createContext<(t: Omit<Toast, 'id'>) => void>(() => {})
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([])
  const push = useCallback((t: Omit<Toast, 'id'>) => {
    const id = Date.now() + Math.random()
    setItems((x) => [...x, { ...t, id }])
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 6500)
  }, [])
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-4 right-4 z-[60] flex w-[min(380px,calc(100%-2rem))] flex-col gap-2" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className="fadein rounded-lg border border-line bg-panel p-3 shadow-lg shadow-black/10 dark:shadow-black/40">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className={cx('text-[13px] font-medium', t.tone === 'error' && 'text-bad')}>{t.title}</div>
                {t.body && <div className="mt-0.5 text-xs text-muted">{t.body}</div>}
              </div>
              {t.action && <Button size="sm" onClick={() => { t.action!.run(); setItems((x) => x.filter((i) => i.id !== t.id)) }}>{t.action.label}</Button>}
            </div>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function Spinner() {
  return <div className="size-4 animate-spin rounded-full border-2 border-line border-t-accent" />
}

export function Empty({ icon, title, body }: { icon: ReactNode; title: string; body?: ReactNode }) {
  return (
    <div className="grid place-items-center py-16 text-center">
      <div className="mb-3 text-faint">{icon}</div>
      <div className="text-[13px] font-medium">{title}</div>
      {body && <div className="mt-1 max-w-sm text-[13px] text-muted">{body}</div>}
    </div>
  )
}

export function PageHeader({ title, sub, actions }: { title: ReactNode; sub?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {sub && <div className="mt-1 text-[13px] text-muted">{sub}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

const REASON_SHORT: Record<string, string> = {
  MISSING_MUST_HAVE: 'Missing must-have', AMBIGUOUS_EVIDENCE: 'Weak evidence', BORDERLINE_SCORE: 'Borderline score',
  BELOW_THRESHOLD: 'Below threshold', LOW_FIT: 'Low fit', OVERQUALIFIED: 'Overqualified', SUSPECTED_MANIPULATION: 'Possible manipulation',
  EXTRACTION_FAILED: 'Not parsed', SPARSE_RESUME: 'Sparse resume', LOW_CONFIDENCE_DATES: 'Unclear dates', NON_ENGLISH: 'Non-English',
  CAREER_SWITCH: 'Career switch', LOCATION_MISMATCH: 'Location',
}
export const reasonLabel = (code: string) =>
  REASON_SHORT[code] ?? code.toLowerCase().replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
