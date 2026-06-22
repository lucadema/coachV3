import { buildProblemCategoryBars, totalCount } from '../data/dashboardTransforms'
import type { DashboardCountBucket } from '../types'
import { HorizontalBarChart } from './HorizontalBarChart'

type ProblemCategorySectionProps = {
  buckets: DashboardCountBucket[]
}

export function ProblemCategorySection({ buckets }: ProblemCategorySectionProps) {
  const total = totalCount(buckets)
  const bars = buildProblemCategoryBars(buckets)

  return (
    <section className="dashboard-section" aria-labelledby="problem-categories-title">
      <div className="section-header">
        <div>
          <p className="eyebrow">Section 1</p>
          <h2 id="problem-categories-title">Problem Categories</h2>
        </div>
        {total > 0 ? <span>{total} categorised sessions</span> : null}
      </div>
      {total > 0 ? (
        <HorizontalBarChart buckets={bars} />
      ) : (
        <p className="empty-state">No categorised sessions yet.</p>
      )}
    </section>
  )
}
