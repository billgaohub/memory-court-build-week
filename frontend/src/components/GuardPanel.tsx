import type { AuditEvent, GuardOutcome, StateChange } from '../types'
import { DownloadIcon, ScaleIcon } from './Icons'

interface GuardPanelProps {
  events: AuditEvent[]
  onExport: () => void
  exportDisabled: boolean
}

function PatchRows({ requested, applied }: { requested: Record<string, number>; applied: Record<string, number | null> }) {
  const keys = Array.from(new Set([...Object.keys(requested), ...Object.keys(applied)]))
  return (
    <div className="patch-table" role="table" aria-label="Requested and applied patch">
      <div className="patch-row patch-row--header" role="row">
        <span role="columnheader">Field</span><span role="columnheader">Asked</span><span role="columnheader">Applied</span>
      </div>
      {keys.map((key) => (
        <div className="patch-row" role="row" key={key}>
          <span role="cell">{key.replaceAll('_', ' ')}</span>
          <strong role="cell">{requested[key] ?? '—'}</strong>
          <strong role="cell">{applied[key] ?? '∅'}</strong>
        </div>
      ))}
    </div>
  )
}

function StateDiff({ changes }: { changes: Record<string, StateChange> }) {
  return (
    <div className="diff-list">
      {Object.entries(changes).map(([key, change]) => (
        <div key={key}>
          <span>{key.replaceAll('_', ' ')}</span>
          <div><del>{change.before ?? '∅'}</del><span aria-hidden="true">→</span><ins>{change.after ?? '∅'}</ins></div>
        </div>
      ))}
    </div>
  )
}

export default function GuardPanel({ events, onExport, exportDisabled }: GuardPanelProps) {
  let latest: { guard: GuardOutcome; changes: Record<string, StateChange> } | null = null
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index]
    if (event.guard) {
      latest = { guard: event.guard, changes: event.state_diff }
      break
    }
  }

  return (
    <aside className="panel guard-panel" role="region" aria-label="Guard verdict">
      <div className="panel-heading">
        <span className="panel-index">03</span>
        <h2>Guard verdict</h2>
      </div>

      {latest ? (
        <>
          <div className={`verdict verdict--${latest.guard.action.toLowerCase()}`}>
            <ScaleIcon />
            <div><span>SONUV-GUARD RULING</span><strong>{latest.guard.action}</strong></div>
          </div>
          <p className="verdict-reason">{latest.guard.reason.replaceAll('_', ' ')}</p>
          <h3 className="subheading">Patch adjudication</h3>
          <PatchRows requested={latest.guard.requested_patch} applied={latest.guard.applied_patch} />
          <h3 className="subheading">Committed state diff</h3>
          {Object.keys(latest.changes).length ? <StateDiff changes={latest.changes} /> : <p className="no-change">No state was committed.</p>}
        </>
      ) : (
        <div className="guard-empty">
          <ScaleIcon />
          <p>No intervention adjudicated</p>
          <small>Only structured state patches are sent to sonuv-guard.</small>
        </div>
      )}

      <button className="button button--export" onClick={onExport} disabled={exportDisabled}>
        <DownloadIcon /> Export audit JSON
      </button>
    </aside>
  )
}
