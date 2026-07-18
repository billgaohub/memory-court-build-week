import type { Mode } from '../types'

export default function ModeBadge({ mode }: { mode: Mode }) {
  return (
    <span className={`mode-badge mode-badge--${mode}`}>
      <span className="mode-badge__dot" aria-hidden="true" />
      {mode === 'live' ? 'LIVE · GPT-5.6' : 'REPLAY MODE'}
    </span>
  )
}
