// Typed client for the FastAPI backend (web/backend/main.py). All requests go through the Vite /api proxy.

export type Stage = 'new' | 'shortlisted' | 'interview' | 'rejected'
export type Level = 'must' | 'nice' | 'ignored' | 'unscored'

export interface Settings {
  model: string
  judge_model: string
  t_high: number
  t_low: number
  delta: number
  offline: boolean
  as_of_date: string
  info_codes: string[]
  reason_help: Record<string, string>
}

export interface JobSummary {
  id: string
  title: string
  location: string
  job_type: string
  level: string
  kind: 'benchmark' | 'custom'
  split: string
  applicants: number
  stages: Record<Stage, number>
  needs_review: number
  edited: boolean
}

export interface Requirement {
  id: string
  key?: string
  name: string
  type: string
  alternatives: string[]
  level: Level
  ai_level: string
  source: 'ai' | 'recruiter'
  coverage?: number | null
  mapped?: boolean
}

export interface JobDetail extends JobSummary {
  text: string
  summary: string
  seniority: string
  min_years: number | null
  ai_min_years: number | null
  equivalent_experience_allowed: boolean
  requirements: Requirement[]
  threshold: number
  default_threshold: number
}

export interface Candidate {
  id: string
  rank: number
  score: number
  decision: 'advance' | 'escalate'
  queue: 'advance' | 'review' | 'low_priority'
  reasons: string[]
  blocking: string[]
  gates_passed: boolean
  components: Record<'must_have' | 'nice_to_have' | 'experience' | 'role_relevance', number | null>
  years: number
  title: string
  skills: string[]
  education: string
  location: string | null
  stage: Stage
  stage_by: string | null
  locked: boolean
  evidence: Record<string, { strength: number; basis: string }>
  uploaded: boolean
  manipulation: boolean
  extraction_error: string | null
  label: number | null
  ideal: 'advance' | 'escalate' | null
}

export interface Evidence {
  requirement: string
  level: 'must' | 'nice'
  matched_skill: string | null
  strength: number
  basis: string
  quote: string | null
}

export interface HistoryItem {
  at: string
  by: string
  candidate: string | null
  action: string
  note?: string
}

export interface CandidateDetail extends Candidate {
  full_evidence: Evidence[]
  gaps: string[]
  reason_help: Record<string, string>
  masked_text: string
  sanitizer_flags: { hidden_text_removed: boolean; injection_suspected: boolean; chars_removed: number }
  injection_matches: string[]
  explanation: string | null
  explanation_stale: boolean
  history: HistoryItem[]
}

export interface Diff {
  entered_shortlist: string[]
  left_shortlist: string[]
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method, headers: {} }
  if (body instanceof FormData) init.body = body
  else if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers = { 'Content-Type': 'application/json' }
  }
  const r = await fetch(`/api${path}`, init)
  if (!r.ok) {
    let detail = r.statusText
    try {
      detail = (await r.json()).detail ?? detail
    } catch {
      /* not json */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return r.json() as Promise<T>
}

export const api = {
  settings: () => call<Settings>('GET', '/settings'),
  setLive: (live: boolean) => call<Settings>('PUT', '/settings', { live }),
  jobs: () => call<JobSummary[]>('GET', '/jobs'),
  createJob: (title: string, text: string) => call<{ id: string }>('POST', '/jobs', { title, text }),
  job: (id: string) => call<JobDetail>('GET', `/jobs/${id}`),
  candidates: (id: string) => call<Candidate[]>('GET', `/jobs/${id}/candidates`),
  candidate: (id: string, cid: string) => call<CandidateDetail>('GET', `/jobs/${id}/candidates/${cid}`),
  setRequirements: (id: string, requirements: Requirement[] | null, minYears?: number | null) =>
    call<Diff>('PUT', `/jobs/${id}/requirements`, {
      requirements,
      min_years: minYears ?? null,
      set_min_years: minYears !== undefined,
    }),
  setThreshold: (id: string, threshold: number) => call<Diff>('PUT', `/jobs/${id}/threshold`, { threshold }),
  reset: (id: string) => call<Diff>('POST', `/jobs/${id}/reset`),
  move: (id: string, cid: string, stage: Stage, note?: string) =>
    call<{ id: string; stage: Stage }>('POST', `/jobs/${id}/candidates/${cid}/stage`, { stage, note }),
  unlock: (id: string, cid: string) => call<{ id: string }>('POST', `/jobs/${id}/candidates/${cid}/unlock`),
  retry: (id: string, cid: string) =>
    call<{ id: string; extraction_error: string | null; score: number; decision: string }>('POST', `/jobs/${id}/candidates/${cid}/retry`),
  explain: (id: string, cid: string) => call<{ explanation: string }>('POST', `/jobs/${id}/candidates/${cid}/explain`),
  upload: (id: string, files: File[]) => {
    const fd = new FormData()
    files.forEach((f) => fd.append('files', f))
    return call<Array<Record<string, unknown>>>('POST', `/jobs/${id}/upload`, fd)
  },
  activity: (id: string) => call<HistoryItem[]>('GET', `/jobs/${id}/activity`),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  insights: () => call<Record<string, any>>('GET', '/insights'),
}
