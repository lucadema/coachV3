import type { DashboardStuckSignalMetric } from '../types'

const STUCK_FLAG_ORDER = [
  'previously_raised',
  'no_owner_identified',
  'both_signals_present',
]

const COMBINED_SIGNAL_ORDER = ['still_trying', 'redirected', 'gave_up']

export type StuckSignalTone = 'raised' | 'owner' | 'both' | 'trying' | 'redirected' | 'gave-up'

export type StuckSignalDisplayMetric = DashboardStuckSignalMetric & {
  percentage: number
  tone: StuckSignalTone
}

const STUCK_TONES: Record<string, StuckSignalTone> = {
  previously_raised: 'raised',
  no_owner_identified: 'owner',
  both_signals_present: 'both',
  still_trying: 'trying',
  redirected: 'redirected',
  gave_up: 'gave-up',
}

export function percentageOfDenominator(count: number, denominator: number): number {
  if (count <= 0 || denominator <= 0) {
    return 0
  }

  return Math.round((count / denominator) * 100)
}

export function buildStuckFlagMetrics(
  metrics: DashboardStuckSignalMetric[],
): StuckSignalDisplayMetric[] {
  return orderMetrics(metrics, STUCK_FLAG_ORDER)
}

export function buildCombinedStuckSignals(
  metrics: DashboardStuckSignalMetric[],
): StuckSignalDisplayMetric[] {
  return orderMetrics(metrics, COMBINED_SIGNAL_ORDER)
}

function orderMetrics(
  metrics: DashboardStuckSignalMetric[],
  order: string[],
): StuckSignalDisplayMetric[] {
  const byValue = new Map(metrics.map((metric) => [metric.value, metric]))

  return order
    .map((value) => byValue.get(value))
    .filter((metric): metric is DashboardStuckSignalMetric => Boolean(metric))
    .map((metric) => ({
      ...metric,
      count: Math.max(0, metric.count),
      denominator: Math.max(0, metric.denominator),
      percentage: percentageOfDenominator(metric.count, metric.denominator),
      tone: STUCK_TONES[metric.value] ?? 'raised',
    }))
}
