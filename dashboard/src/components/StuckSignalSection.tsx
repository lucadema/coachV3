import {
  buildCombinedStuckSignals,
  buildStuckFlagMetrics,
} from '../data/stuckSignalTransforms'
import type { DashboardStuckSignal } from '../types'

type StuckSignalSectionProps = {
  data: DashboardStuckSignal
}

export function StuckSignalSection({ data }: StuckSignalSectionProps) {
  const flags = buildStuckFlagMetrics(data.flags)
  const combinedSignals = buildCombinedStuckSignals(data.combined_signals)
  const hasSignals = flags.some((flag) => flag.count > 0)

  return (
    <section className="dashboard-section" aria-labelledby="stuck-signal-title">
      <div className="section-header">
        <div>
          <p className="eyebrow">Section 5</p>
          <h2 id="stuck-signal-title">Stuck Signal</h2>
        </div>
        {data.classified_sessions_count > 0 ? (
          <span>{data.classified_sessions_count} sessions classified</span>
        ) : null}
      </div>

      {hasSignals ? (
        <>
          <div className="section-intro">
            <p>
              These signals show whether normal channels have already failed:
              issues raised before, issues with no owner, and cases where both
              patterns appear together.
            </p>
          </div>

          <div className="stuck-card-grid">
            {flags.map((flag) => (
              <article className={`stuck-card stuck-${flag.tone}`} key={flag.value}>
                <span>{flag.label}</span>
                <strong>{flag.percentage}%</strong>
                <small>
                  {flag.count} of {flag.denominator} sessions
                </small>
                <p>{flag.description}</p>
              </article>
            ))}
          </div>

          {combinedSignals.length > 0 ? (
            <div className="stuck-combined">
              <div className="subsection-heading">
                <div>
                  <h3>Combined signal: stuck flag × chosen pathway</h3>
                  <p>
                    Cross-referencing stuck sessions with the hearted pathway
                    distinguishes persistence from redirection and withdrawal.
                  </p>
                </div>
              </div>

              <div className="stuck-combined-list">
                {combinedSignals.map((signal) => (
                  <article className="stuck-combined-row" key={signal.value}>
                    <span className={`stuck-pill stuck-${signal.tone}`}>
                      {signal.label}
                    </span>
                    <div>
                      <h4>{combinedTitle(signal.value)}</h4>
                      <p>{signal.description}</p>
                    </div>
                    <strong>
                      {signal.percentage}% · {signal.count}
                    </strong>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : (
        <p className="empty-state">No stuck signals yet.</p>
      )}
    </section>
  )
}

function combinedTitle(value: string): string {
  if (value === 'still_trying') {
    return 'Previously raised · hearted escalation'
  }
  if (value === 'redirected') {
    return 'Previously raised · hearted self-actionable path'
  }
  if (value === 'gave_up') {
    return 'Previously raised · hearted absorb path'
  }
  return 'Combined stuck signal'
}
