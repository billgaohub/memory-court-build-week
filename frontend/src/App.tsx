import { useEffect, useMemo, useState } from 'react'

import { api, ApiError } from './api'
import CasePanel from './components/CasePanel'
import DecisionTrace from './components/DecisionTrace'
import GuardPanel from './components/GuardPanel'
import ModeBadge from './components/ModeBadge'
import type { CaseSummary, HealthResponse, ReplayResponse, SessionView } from './types'

interface AppProps {
  initialSession?: SessionView
  initialCases?: CaseSummary[]
}

function replayAsSession(replay: ReplayResponse): SessionView {
  const now = Date.now() / 1000
  return {
    id: `replay-${replay.case_id}`,
    case_id: replay.case_id,
    mode: 'replay',
    model: replay.model,
    state: replay.final_state,
    events: replay.events,
    model_calls: 0,
    proposal_count: replay.events.filter((event) => event.guard !== null).length,
    invalid_count: 0,
    terminal: true,
    created_at: now,
    updated_at: now,
    replay_provenance: replay.provenance,
    replay_disclosure: replay.disclosure,
    replay_source_task_id: replay.source_task_id,
    replay_generated_at: replay.generated_at,
  }
}

export default function App({ initialSession, initialCases }: AppProps) {
  const [health, setHealth] = useState<HealthResponse | null>(
    initialSession ? {
      status: 'ok', model: initialSession.model, live_available: true,
      replay_available: true, version: 'test',
    } : null,
  )
  const [cases, setCases] = useState<CaseSummary[]>(initialCases ?? [])
  const [selectedId, setSelectedId] = useState(initialSession?.case_id ?? initialCases?.[0]?.id ?? '')
  const [session, setSession] = useState<SessionView | null>(initialSession ?? null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [fatal, setFatal] = useState<string | null>(null)

  useEffect(() => {
    if (initialSession && initialCases) return
    let active = true
    Promise.all([api.health(), api.cases()])
      .then(async ([healthResponse, caseResponse]) => {
        if (!active) return
        setHealth(healthResponse)
        setCases(caseResponse)
        const caseId = caseResponse.find(
          (item) => item.provenance === 'competition_period',
        )?.id ?? caseResponse[0]?.id ?? ''
        setSelectedId(caseId)
        if (!healthResponse.live_available && caseId) {
          const replay = await api.replay(caseId)
          if (active) setSession(replayAsSession(replay))
        }
      })
      .catch((error: unknown) => {
        if (active) setFatal(error instanceof Error ? error.message : 'Unable to reach the audit service.')
      })
    return () => { active = false }
  }, [initialCases, initialSession])

  const mode = session?.mode ?? (health?.live_available ? 'live' : 'replay')
  const events = session?.events ?? []
  const selectedCase = useMemo(
    () => cases.find((item) => item.id === selectedId),
    [cases, selectedId],
  )

  async function loadReplay(message?: string) {
    if (!selectedId) return
    const replay = await api.replay(selectedId)
    setSession(replayAsSession(replay))
    setNotice(message ?? 'Loaded a fixed, version-controlled demo trace. No live model call was made.')
  }

  async function runLive() {
    if (!selectedId) return
    setBusy(true)
    setFatal(null)
    setNotice(null)
    try {
      const created = await api.createSession(selectedId)
      const completed = await api.runSession(created.id)
      const unavailable = completed.events.some(
        (event) => event.terminal_reason === 'live_model_unavailable',
      )
      if (unavailable) {
        await loadReplay('Live model unavailable. Switched to the labeled demo replay.')
      } else {
        setSession(completed)
        setNotice('Live GPT-5.6 audit completed. Guard verdicts reflect executed structured patches.')
      }
    } catch (error) {
      if (error instanceof ApiError && ['LIVE_UNAVAILABLE', 'RATE_LIMITED'].includes(error.code ?? '')) {
        await loadReplay(`${error.message} Switched to the labeled demo replay.`)
      } else {
        setFatal(error instanceof Error ? error.message : 'The live audit could not be completed.')
      }
    } finally {
      setBusy(false)
    }
  }

  function selectCase(caseId: string) {
    setSelectedId(caseId)
    setSession(null)
    setNotice(null)
    setFatal(null)
  }

  function exportAudit() {
    if (!session || !selectedCase) return
    const payload = {
      exported_at: new Date().toISOString(),
      disclosure: session.mode === 'replay'
        ? `REPLAY MODE — ${session.replay_disclosure ?? 'fixed fixture; no live model call.'}`
        : 'LIVE — GPT-5.6 actions with structured sonuv-guard adjudication.',
      case: selectedCase,
      session,
    }
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `memory-court-${session.case_id}-${session.mode}.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#main"><span>MC</span><strong>MEMORY COURT</strong></a>
        <p>Autonomous intervention / accountable execution</p>
        <ModeBadge mode={mode} />
      </header>

      <main id="main" className="court-grid">
        <CasePanel
          cases={cases}
          selectedId={selectedId}
          mode={mode}
          liveAvailable={health?.live_available ?? false}
          busy={busy}
          onSelect={selectCase}
          onRun={runLive}
          onReplay={() => { void loadReplay() }}
        />
        <DecisionTrace events={events} replayDisclosure={session?.replay_disclosure} />
        <GuardPanel events={events} onExport={exportAudit} exportDisabled={!session} />
      </main>

      <footer className="statusbar">
        <span className={fatal ? 'statusbar__error' : ''} role="status" aria-live="polite">
          {fatal ?? notice ?? (busy ? 'GPT-5.6 is investigating within the bounded audit loop…' : 'Ready for judicial review.')}
        </span>
        <span>SESSION {session?.id.slice(0, 12).toUpperCase() ?? 'NOT STARTED'}</span>
        <span>{events.length}/8 STEPS</span>
      </footer>
    </div>
  )
}
