import type { DashboardActionOwnership, DashboardCountBucket } from '../types'
import { percentageOfTotal, totalCount } from './dashboardTransforms'

const ACTION_OWNERSHIP_ORDER = [
  'self_actionable',
  'escalation_required',
  'system_change',
  'disengagement_signal',
]

export type ActionOwnershipTone = 'self' | 'escalation' | 'system' | 'disengagement'

export type ActionOwnershipDisplayBucket = DashboardCountBucket & {
  percentage: number
  tone: ActionOwnershipTone
  summary: string
}

export type ActionOwnershipComparisonRow = {
  value: string
  label: string
  generatedCount: number
  generatedPercentage: number
  heartedCount: number
  heartedPercentage: number
  tone: ActionOwnershipTone
}

const OWNERSHIP_METADATA: Record<
  string,
  { tone: ActionOwnershipTone; summary: string }
> = {
  self_actionable: {
    tone: 'self',
    summary: 'Chose a path they can walk alone',
  },
  escalation_required: {
    tone: 'escalation',
    summary: 'Chose a path requiring someone with authority',
  },
  system_change: {
    tone: 'system',
    summary: 'Chose a path needing structural or process change',
  },
  disengagement_signal: {
    tone: 'disengagement',
    summary: 'Chose to manage rather than resolve',
  },
}

export function buildActionOwnershipTiles(
  buckets: DashboardCountBucket[],
): ActionOwnershipDisplayBucket[] {
  const total = totalCount(buckets)

  return orderedOwnershipBuckets(buckets)
    .filter((bucket) => bucket.count > 0)
    .map((bucket) => withOwnershipDisplay(bucket, total))
}

export function buildActionOwnershipComparison(
  data: DashboardActionOwnership,
): ActionOwnershipComparisonRow[] {
  const generatedTotal = totalCount(data.generated)
  const heartedTotal = totalCount(data.hearted)
  const generatedByValue = bucketMap(data.generated)
  const heartedByValue = bucketMap(data.hearted)

  return ACTION_OWNERSHIP_ORDER.map((value) => {
    const generated = generatedByValue.get(value)
    const hearted = heartedByValue.get(value)
    const label = hearted?.label ?? generated?.label ?? value
    const generatedCount = Math.max(0, generated?.count ?? 0)
    const heartedCount = Math.max(0, hearted?.count ?? 0)
    const metadata = OWNERSHIP_METADATA[value] ?? OWNERSHIP_METADATA.self_actionable

    return {
      value,
      label,
      generatedCount,
      generatedPercentage: percentageOfTotal(generatedCount, generatedTotal),
      heartedCount,
      heartedPercentage: percentageOfTotal(heartedCount, heartedTotal),
      tone: metadata.tone,
    }
  }).filter((row) => row.generatedCount > 0 || row.heartedCount > 0)
}

function orderedOwnershipBuckets(buckets: DashboardCountBucket[]): DashboardCountBucket[] {
  const byValue = bucketMap(buckets)
  return ACTION_OWNERSHIP_ORDER.map((value) => byValue.get(value)).filter(
    (bucket): bucket is DashboardCountBucket => Boolean(bucket),
  )
}

function bucketMap(buckets: DashboardCountBucket[]): Map<string, DashboardCountBucket> {
  return new Map(
    buckets.map((bucket) => [
      bucket.value,
      {
        ...bucket,
        count: Math.max(0, bucket.count),
      },
    ]),
  )
}

function withOwnershipDisplay(
  bucket: DashboardCountBucket,
  total: number,
): ActionOwnershipDisplayBucket {
  const metadata = OWNERSHIP_METADATA[bucket.value] ?? OWNERSHIP_METADATA.self_actionable
  return {
    ...bucket,
    percentage: percentageOfTotal(bucket.count, total),
    tone: metadata.tone,
    summary: metadata.summary,
  }
}
