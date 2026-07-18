import type {
  CaseSummary,
  HealthResponse,
  PublicApiError,
  ReplayResponse,
  SessionView,
} from './types'

const configuredBase = import.meta.env.VITE_API_BASE_URL as string | undefined
export const API_BASE_URL = (configuredBase ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly replayUrl?: string,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!response.ok) {
    let body: PublicApiError = {}
    try {
      body = (await response.json()) as PublicApiError
    } catch {
      // A proxy may return an HTML error page. Keep the public error generic.
    }
    throw new ApiError(
      body.detail?.message ?? `Request failed (${response.status})`,
      response.status,
      body.detail?.code,
      body.detail?.replay_url,
    )
  }
  return (await response.json()) as T
}

export const api = {
  health: () => request<HealthResponse>('/api/health'),
  cases: () => request<CaseSummary[]>('/api/cases'),
  replay: (caseId: string) => request<ReplayResponse>(`/api/replays/${caseId}`),
  createSession: (caseId: string) =>
    request<SessionView>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ case_id: caseId }),
    }),
  runSession: (sessionId: string) =>
    request<SessionView>(`/api/sessions/${sessionId}/run`, { method: 'POST' }),
}
