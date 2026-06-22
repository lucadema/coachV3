import type { ChartBucket } from '../data/dashboardTransforms'

type HorizontalBarChartProps = {
  buckets: ChartBucket[]
}

export function HorizontalBarChart({ buckets }: HorizontalBarChartProps) {
  const maxCount = Math.max(1, ...buckets.map((bucket) => bucket.count))

  return (
    <div className="horizontal-chart" aria-label="Problem category distribution">
      {buckets.map((bucket) => (
        <div className="bar-row" key={bucket.value}>
          <div className="bar-row-label">
            <span>{bucket.label}</span>
            <strong>
              {bucket.count} · {bucket.percentage}%
            </strong>
          </div>
          <div
            aria-label={`${bucket.label}: ${bucket.count}, ${bucket.percentage}%`}
            className="bar-track"
            role="img"
          >
            <span
              className="bar-fill"
              style={{
                minWidth: bucket.count > 0 ? '2px' : '0',
                width: `${(bucket.count / maxCount) * 100}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
