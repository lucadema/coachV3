import type { DashboardCountBucket } from '../types'

export type ChartBucket = DashboardCountBucket & {
  percentage: number
}

export const ENGAGEMENT_SIGNAL_ORDER = [
  'no_visible_risk',
  'frustration_signal',
  'voice_suppression_signal',
  'disengagement_risk',
]

export function totalCount(buckets: DashboardCountBucket[]): number {
  return buckets.reduce((sum, bucket) => sum + Math.max(0, bucket.count), 0)
}

export function percentageOfTotal(count: number, total: number): number {
  if (total <= 0 || count <= 0) {
    return 0
  }

  return Math.round((count / total) * 100)
}

export function buildProblemCategoryBars(buckets: DashboardCountBucket[]): ChartBucket[] {
  const total = totalCount(buckets)
  return buckets
    .map((bucket, index) => ({
      ...bucket,
      count: Math.max(0, bucket.count),
      percentage: percentageOfTotal(bucket.count, total),
      originalIndex: index,
    }))
    .sort((left, right) => {
      if (right.count !== left.count) {
        return right.count - left.count
      }
      return left.originalIndex - right.originalIndex
    })
    .map((bucket) => ({
      value: bucket.value,
      label: bucket.label,
      count: bucket.count,
      percentage: bucket.percentage,
    }))
}

export function buildEngagementSignalSegments(buckets: DashboardCountBucket[]): ChartBucket[] {
  const total = totalCount(buckets)
  const bucketsByValue = new Map(buckets.map((bucket) => [bucket.value, bucket]))

  return ENGAGEMENT_SIGNAL_ORDER.map((value) => {
    const bucket = bucketsByValue.get(value) ?? {
      value,
      label: value,
      count: 0,
    }
    return {
      ...bucket,
      count: Math.max(0, bucket.count),
      percentage: percentageOfTotal(bucket.count, total),
    }
  })
}
