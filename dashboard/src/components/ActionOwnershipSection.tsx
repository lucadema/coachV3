import {
  buildActionOwnershipComparison,
  buildActionOwnershipTiles,
} from '../data/actionOwnershipTransforms'
import { totalCount } from '../data/dashboardTransforms'
import type { DashboardActionOwnership } from '../types'

type ActionOwnershipSectionProps = {
  data: DashboardActionOwnership
}

export function ActionOwnershipSection({ data }: ActionOwnershipSectionProps) {
  const heartedTotal = totalCount(data.hearted)
  const generatedTotal = totalCount(data.generated)
  const tiles = buildActionOwnershipTiles(data.hearted)
  const comparison = buildActionOwnershipComparison(data)

  return (
    <section className="dashboard-section" aria-labelledby="action-ownership-title">
      <div className="section-header">
        <div>
          <p className="eyebrow">Section 4</p>
          <h2 id="action-ownership-title">Action Ownership</h2>
        </div>
        {heartedTotal > 0 ? <span>{heartedTotal} choices recorded</span> : null}
      </div>

      {heartedTotal > 0 ? (
        <>
          <div className="section-intro">
            <p>
              Each heart is the signal. This shows the kind of route people chose:
              something they could act on, something needing authority, or something
              they felt they had to absorb.
            </p>
          </div>

          <div className="ownership-tile-grid">
            {tiles.map((tile) => (
              <article
                className={`ownership-tile ownership-${tile.tone}`}
                key={tile.value}
              >
                <span className="ownership-marker" />
                <strong>{tile.percentage}%</strong>
                <h3>{tile.label}</h3>
                <p>{tile.summary}</p>
                <small>
                  {tile.count} of {heartedTotal} choices
                </small>
              </article>
            ))}
          </div>

          {generatedTotal > 0 ? (
            <div className="ownership-comparison">
              <div className="subsection-heading">
                <div>
                  <h3>Generated vs chosen</h3>
                  <p>
                    The gap shows whether people are choosing the routes they can
                    walk alone, or leaning toward escalation despite other options.
                  </p>
                </div>
                <span>{generatedTotal} generated pathways</span>
              </div>

              <div className="ownership-compare-legend" aria-hidden="true">
                <span>
                  <i className="compare-dot generated" /> Generated
                </span>
                <span>
                  <i className="compare-dot hearted" /> Hearted
                </span>
              </div>

              <div className="ownership-compare-list">
                {comparison.map((row) => (
                  <div className="ownership-compare-row" key={row.value}>
                    <div className="ownership-compare-label">
                      <span>{row.label}</span>
                      <strong>
                        {row.heartedCount} · {row.heartedPercentage}%
                      </strong>
                    </div>
                    <div className="ownership-compare-bars">
                      <div className="compare-track">
                        <span
                          className="compare-fill generated"
                          style={{ width: `${row.generatedPercentage}%` }}
                        />
                        <em>{row.generatedPercentage}%</em>
                      </div>
                      <div className="compare-track">
                        <span
                          className={`compare-fill hearted ownership-${row.tone}`}
                          style={{ width: `${row.heartedPercentage}%` }}
                        />
                        <em>{row.heartedPercentage}%</em>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : (
        <p className="empty-state">No action ownership signals yet.</p>
      )}
    </section>
  )
}
