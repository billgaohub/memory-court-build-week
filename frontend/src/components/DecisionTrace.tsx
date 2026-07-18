import type { AuditEvent } from '../types'

const actionLabel: Record<AuditEvent['model_action'], string> = {
  inspect_memory: 'INSPECT MEMORY',
  propose_intervention: 'PROPOSE INTERVENTION',
  finalize: 'FINALIZE',
  validation_rejected: 'VALIDATION REJECTED',
  system_stop: 'SYSTEM STOP',
}

interface DecisionTraceProps {
  events: AuditEvent[]
  replayDisclosure?: string
}

export default function DecisionTrace({ events, replayDisclosure }: DecisionTraceProps) {
  return (
    <section className="panel trace-panel" aria-label="Decision trace">
      <div className="panel-heading panel-heading--sticky">
        <span className="panel-index">02</span>
        <h2>Decision trace</h2>
        <span className="event-count">{events.length.toString().padStart(2, '0')} EVENTS</span>
      </div>

      {replayDisclosure ? (
        <div className="replay-provenance" role="note" aria-label="Replay provenance">
          <strong>RECORDED EVIDENCE</strong>
          <span>{replayDisclosure}</span>
        </div>
      ) : null}

      {events.length === 0 ? (
        <div className="trace-empty">
          <span className="trace-empty__line" aria-hidden="true" />
          <p>Awaiting an autonomous investigation.</p>
          <small>The model must inspect evidence before proposing an intervention.</small>
        </div>
      ) : (
        <ol className="trace-list">
          {events.map((event) => (
            <li className={`trace-event trace-event--${event.model_action}`} key={`${event.step}-${event.model_action}`}>
              <div className="trace-rail">
                <span>{event.step.toString().padStart(2, '0')}</span>
              </div>
              <article>
                <header>
                  <strong>{actionLabel[event.model_action]}</strong>
                  <span>{event.latency_ms == null ? 'SYSTEM' : `${event.latency_ms} MS`}</span>
                </header>
                <p>{event.rationale}</p>
                {event.observation ? <blockquote>{event.observation}</blockquote> : null}
                {!event.validation.accepted ? (
                  <div className="validation-errors">
                    {event.validation.errors.join(' · ')}
                  </div>
                ) : null}
                {event.guard ? (
                  <div className="inline-verdict">
                    <span>SONUV-GUARD</span>
                    <strong>{event.guard.action}</strong>
                  </div>
                ) : (
                  <div className="not-adjudicated">NO GUARD VERDICT — NON-INTERVENTION ACTION</div>
                )}
              </article>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
