import type { CaseSummary, Mode } from '../types'
import { PlayIcon } from './Icons'

interface CasePanelProps {
  cases: CaseSummary[]
  selectedId: string
  mode: Mode
  liveAvailable: boolean
  busy: boolean
  onSelect: (id: string) => void
  onRun: () => void
  onReplay: () => void
}

export default function CasePanel({
  cases,
  selectedId,
  mode,
  liveAvailable,
  busy,
  onSelect,
  onRun,
  onReplay,
}: CasePanelProps) {
  const selected = cases.find((item) => item.id === selectedId) ?? cases[0]

  return (
    <aside className="panel case-panel" aria-label="Case controls">
      <div className="panel-heading">
        <span className="panel-index">01</span>
        <h2>Case file</h2>
      </div>

      <label className="field-label" htmlFor="case-select">Active case</label>
      <select
        id="case-select"
        value={selectedId}
        onChange={(event) => onSelect(event.target.value)}
        disabled={busy}
      >
        {cases.map((item) => (
          <option key={item.id} value={item.id}>{item.title}</option>
        ))}
      </select>

      {selected ? (
        <div className="case-brief">
          <p className="case-provenance">
            {selected.provenance === 'competition_period' ? 'BUILD WEEK CASE' : 'PRE-EXISTING CASE'}
          </p>
          <h3>{selected.title}</h3>
          <p>{selected.tagline}</p>
          <dl className="profile-list">
            {Object.entries(selected.profile).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll('_', ' ')}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}

      <div className="state-grid" aria-label="Initial cognitive state">
        {selected ? Object.entries(selected.initial_state).map(([key, value]) => (
          <div className="state-cell" key={key}>
            <span>{key.replaceAll('_', ' ')}</span>
            <strong>{value}</strong>
          </div>
        )) : null}
      </div>

      <div className="case-actions">
        <button className="button button--primary" onClick={onRun} disabled={busy || !liveAvailable}>
          <PlayIcon />
          {busy ? 'Auditing…' : 'Run live audit'}
        </button>
        <button className="button button--quiet" onClick={onReplay} disabled={busy}>
          {mode === 'replay' ? 'Restart replay' : 'View demo replay'}
        </button>
      </div>

      <p className="limits-note">
        Boundaries: 8 model calls · 3 proposals · Guard adjudicates structured patches only.
      </p>
    </aside>
  )
}
