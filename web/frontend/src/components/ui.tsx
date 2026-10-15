import clsx from 'clsx'
import { X } from 'lucide-react'
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import type { Stage } from '../api'

export const cx = clsx

export const STAGE_META: Record<Stage, { label: string; dot: string; text: string }> = {
  new: { label: 'Unreviewed', dot: 'bg-zinc-400', text: 'text-muted' },
  shortlisted: { label: 'Shortlisted', dot: 'bg-amber-400', text: 'text-amber-500 dark:text-amber-300' },
  interview: { label: 'Ready to interview', dot: 'bg-emerald-400', text: 'text-emerald-600 dark:text-emerald-300' },
  rejected: { label: 'Rejected', dot: 'bg-rose-500', text: 'text-rose-600 dark:text-rose-300' },
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
        'inline-flex items-center gap-1.5 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
        size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-9 px-3.5 text-sm',
        variant === 'primary' && 'bg-accent text-white hover:brightness-110 dark:text-zinc-950',
        variant === 'secondary' && 'border border-line bg-panel hover:bg-raised',
        variant === 'ghost' && 'text-muted hover:bg-raised hover:text-fg',
        variant === 'danger' && 'bg-rose-600 text-white hover:bg-rose-500',
        className,
      )}
    >
      {children}
    </button>
  )
}

export function StagePill({ stage, by }: { stage: Stage; by?: string | null }) {
  const m = STAGE_META[stage]
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-line px-2.5 py-0.5 text-xs">
      <span className={cx('size-1.5 rounded-full', m.dot)} />
      <span className={m.text}>{m.label}</span>
      {by === 'agent' && stage === 'shortlisted' && <span className="text-faint">· AI</span>}
    </span>
  )
}

export function ScoreRing({ score, size = 40, passed }: { score: number; size?: number; passed?: boolean }) {
  const r = (size - 6) / 2
  const c = 2 * Math.PI * r
  const color = passed ? '#34d399' : score >= 0.4 ? '#fbbf24' : '#a1a1aa'
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} title={`Fit score ${score.toFixed(3)}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--line)" strokeWidth={4} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={4} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - Math.min(1, score))} />
      </svg>
      <span className="absolute inset-0 grid place-items-center font-mono text-[11px] font-medium">
        {Math.round(score * 100)}
      </span>
    </div>
  )
}

export function Avatar({ id }: { id: string }) {
  const n = [...id].reduce((a, ch) => a + ch.charCodeAt(0), 0)
  const hues = [262, 199, 152, 24, 330, 45, 280, 173]
  const h = hues[n % hues.length]
  return (
    <div className="grid size-9 shrink-0 place-items-center rounded-full font-mono text-[11px] font-semibold"
      style={{ background: `hsl(${h} 70% 55% / 0.16)`, color: `hsl(${h} 75% 62%)` }} aria-hidden>
      {id.replace(/^[A-Z]0*/, '').slice(0, 3) || id}
    </div>
  )
}

export function Chip({ children, tone = 'default', title }: { children: ReactNode; tone?: 'default' | 'good' | 'warn' | 'bad' | 'accent'; title?: string }) {
  return (
    <span title={title} className={cx(
      'inline-flex items-center gap-1 whitespace-nowrap rounded-md border px-1.5 py-0.5 text-[11px] leading-4',
      tone === 'default' && 'border-line text-muted',
      tone === 'good' && 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300',
      tone === 'warn' && 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-300',
      tone === 'bad' && 'border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-300',
      tone === 'accent' && 'border-accent/30 bg-accent-soft text-accent',
    )}>{children}</span>
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
          'fadein absolute z-30 mt-1 min-w-48 rounded-xl border border-line bg-panel p-1 shadow-xl shadow-black/20',
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
      'flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-sm hover:bg-raised disabled:opacity-40',
      danger && 'text-rose-500',
    )}>{children}</button>
  )
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    if (open) document.addEventListener('keydown', k)
    return () => document.removeEventListener('keydown', k)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4 backdrop-blur-sm" onMouseDown={onClose}>
      <div role="dialog" aria-label={title} onMouseDown={(e) => e.stopPropagation()}
        className={cx('fadein max-h-[88vh] w-full overflow-auto rounded-2xl border border-line bg-panel shadow-2xl', wide ? 'max-w-3xl' : 'max-w-lg')}>
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
          <h2 className="font-semibold">{title}</h2>
          <button onClick={onClose} className="rounded-md p-1 text-muted hover:bg-raised" aria-label="Close"><X size={16} /></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

export function Bar({ value, className }: { value: number; className?: string }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-raised">
      <div className={cx('h-full rounded-full', className ?? 'bg-accent')} style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
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
      <div className="fixed bottom-4 right-4 z-[60] flex w-96 flex-col gap-2" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={cx('fadein rounded-xl border bg-panel p-3.5 shadow-xl shadow-black/20',
            t.tone === 'error' ? 'border-rose-500/40' : 'border-line')}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className={cx('text-sm font-medium', t.tone === 'error' && 'text-rose-500')}>{t.title}</div>
                {t.body && <div className="mt-1 text-xs text-muted">{t.body}</div>}
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
      <div className="mb-3 grid size-11 place-items-center rounded-xl border border-line bg-raised text-muted">{icon}</div>
      <div className="font-medium">{title}</div>
      {body && <div className="mt-1 max-w-sm text-sm text-muted">{body}</div>}
    </div>
  )
}
