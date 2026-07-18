export type Mode = 'live' | 'replay'
export type GuardAction = 'COMMIT' | 'REPAIR' | 'REJECT' | 'FORGET'

export interface CaseSummary {
  id: string
  title: string
  tagline: string
  provenance: 'pre_existing' | 'competition_period'
  profile: Record<string, string | number>
  initial_state: Record<string, number>
}

export interface StateChange {
  before: number | null
  after: number | null
}

export interface GuardOutcome {
  action: GuardAction
  reason: string
  requested_patch: Record<string, number>
  applied_patch: Record<string, number | null>
}

export interface AuditEvent {
  mode: Mode
  step: number
  model: string
  model_action:
    | 'inspect_memory'
    | 'propose_intervention'
    | 'finalize'
    | 'validation_rejected'
    | 'system_stop'
  rationale: string
  validation: { accepted: boolean; errors: string[] }
  guard: GuardOutcome | null
  state_diff: Record<string, StateChange>
  observation?: string | null
  terminal: boolean
  terminal_reason: string | null
  latency_ms?: number | null
}

export interface SessionView {
  id: string
  case_id: string
  mode: Mode
  model: string
  state: Record<string, number | null>
  events: AuditEvent[]
  model_calls: number
  proposal_count: number
  invalid_count: number
  terminal: boolean
  created_at: number
  updated_at: number
}

export interface ReplayResponse {
  case_id: string
  mode: 'replay'
  label: 'REPLAY MODE'
  model: string
  initial_state: Record<string, number>
  final_state: Record<string, number | null>
  events: AuditEvent[]
}

export interface HealthResponse {
  status: 'ok'
  model: string
  live_available: boolean
  replay_available: boolean
  version: string
}

export interface PublicApiError {
  detail?: {
    code?: string
    message?: string
    replay_url?: string
  }
}
