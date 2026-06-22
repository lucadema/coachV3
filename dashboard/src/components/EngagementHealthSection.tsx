import { buildEngagementSignalSegments, totalCount } from '../data/dashboardTransforms'
import type { DashboardCountBucket } from '../types'
import { StackedSignalBar } from './StackedSignalBar'

type EngagementHealthSectionProps = {
  buckets: DashboardCountBucket[]
}

export function EngagementHealthSection({ buckets }: EngagementHealthSectionProps) {
  const total = totalCount(buckets)
  const segments = buildEngagementSignalSegments(buckets)

  return (
    <section className="dashboard-section" aria-labelledby="engagement-health-title">
      <div className="section-header">
        <div>
          <p className="eyebrow">Section 2</p>
          <h2 id="engagement-health-title">Engagement Health Signals</h2>
        </div>
        {total > 0 ? <span>{total} signal assessments</span> : null}
      </div>
      {total > 0 ? (
        <StackedSignalBar segments={segments} />
      ) : (
        <p className="empty-state">No engagement health signals yet.</p>
      )}
    </section>
  )
}
