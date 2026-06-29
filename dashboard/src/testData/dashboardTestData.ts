import type { DashboardData, DashboardTestDataOptions } from '../types'

const DEFAULT_ENTERPRISE_NAME = 'Aether Works'
const DEFAULT_PILOT_NAME = 'Leadership Clarity Pilot'
const DEFAULT_SESSION_COUNT = 50
const PATHWAYS_PER_SESSION = 4
const AVERAGE_MONTHLY_MINUTES_PER_RESPONSE = 4260

const PROBLEM_CATEGORIES = [
  ['organisational_friction', 'Organisational friction', 28],
  ['lack_of_clarity_alignment', 'Lack of clarity and alignment', 16],
  ['poor_decision_making', 'Poor decision-making', 18],
  ['siloed_thinking', 'Siloed thinking', 10],
  ['strategy_execution_gap', 'Strategy/execution gap', 14],
  ['inability_to_adapt', 'Inability to adapt', 14],
] as const

const ENGAGEMENT_SIGNALS = [
  ['no_visible_risk', 'No visible risk', 20],
  ['frustration_signal', 'Frustration signal', 45],
  ['voice_suppression_signal', 'Voice suppression signal', 10],
  ['disengagement_risk', 'Disengagement risk', 25],
] as const

const ACTION_OWNERSHIP_GENERATED = [
  ['self_actionable', 'Self-actionable', 7],
  ['escalation_required', 'Escalation needed', 17],
  ['system_change', 'System change', 1],
  ['disengagement_signal', 'Absorbing it', 2],
] as const

const ACTION_OWNERSHIP_HEARTED = [
  ['self_actionable', 'Self-actionable', 1],
  ['escalation_required', 'Escalation needed', 6],
  ['system_change', 'System change', 0],
  ['disengagement_signal', 'Absorbing it', 1],
] as const

export function createDashboardTestData(options: DashboardTestDataOptions = {}): DashboardData {
  const sessionCount = positiveIntegerOrDefault(options.sessionCount, DEFAULT_SESSION_COUNT)
  const generatedPathwayCount = sessionCount * PATHWAYS_PER_SESSION
  const flagYesCount = percentageCount(sessionCount, 0.88)
  const previouslyRaisedCount = percentageCount(sessionCount, 0.75)
  const noOwnerCount = percentageCount(sessionCount, 0.75)
  const bothSignalsCount = Math.min(
    previouslyRaisedCount,
    noOwnerCount,
    percentageCount(sessionCount, 0.63),
  )
  const [stillTryingCount, redirectedCount, gaveUpCount] = distributeByWeights(
    previouslyRaisedCount,
    [4, 1, 1],
  )

  return {
    available: true,
    enterprise_name: options.enterpriseName || DEFAULT_ENTERPRISE_NAME,
    pilot_name: options.pilotName || DEFAULT_PILOT_NAME,
    pilot_status: 'active',
    problem_categories: weightedBuckets(sessionCount, PROBLEM_CATEGORIES),
    engagement_signals: weightedBuckets(sessionCount, ENGAGEMENT_SIGNALS),
    value_unlocked: {
      monthly_minutes: sessionCount * AVERAGE_MONTHLY_MINUTES_PER_RESPONSE,
      qualifying_responses_count: sessionCount,
      flag_to_organisation: {
        yes_count: flagYesCount,
        no_count: sessionCount - flagYesCount,
      },
    },
    action_ownership: {
      generated: weightedBuckets(generatedPathwayCount, ACTION_OWNERSHIP_GENERATED),
      hearted: weightedBuckets(sessionCount, ACTION_OWNERSHIP_HEARTED),
    },
    stuck_signal: {
      classified_sessions_count: sessionCount,
      flags: [
        {
          value: 'previously_raised',
          label: 'Previously raised',
          count: previouslyRaisedCount,
          denominator: sessionCount,
          description:
            'Issues had already been raised through normal channels and had not resolved.',
        },
        {
          value: 'no_owner_identified',
          label: 'No owner identified',
          count: noOwnerCount,
          denominator: sessionCount,
          description: 'The accountable person or route to ownership was unclear.',
        },
        {
          value: 'both_signals_present',
          label: 'Both signals present',
          count: bothSignalsCount,
          denominator: sessionCount,
          description:
            'The issue was already raised and still has no clear owner. This is the strongest stuck signal.',
        },
      ],
      combined_signals: [
        {
          value: 'still_trying',
          label: 'Still trying',
          count: stillTryingCount,
          denominator: previouslyRaisedCount,
          description:
            'Previously raised, then chose an escalation pathway. They have not given up, but they need a response.',
        },
        {
          value: 'redirected',
          label: 'Redirected',
          count: redirectedCount,
          denominator: previouslyRaisedCount,
          description:
            'Previously raised, then chose a self-actionable path. They found a way forward despite the block.',
        },
        {
          value: 'gave_up',
          label: 'Gave up',
          count: gaveUpCount,
          denominator: previouslyRaisedCount,
          description:
            'Previously raised, then chose to absorb the problem. At scale, growth here is a leading risk signal.',
        },
      ],
    },
  }
}

function weightedBuckets<T extends readonly [string, string, number]>(
  total: number,
  rows: readonly T[],
) {
  const counts = distributeByWeights(
    total,
    rows.map((row) => row[2]),
  )

  return rows.map(([value, label], index) => ({
    value,
    label,
    count: counts[index] ?? 0,
  }))
}

function distributeByWeights(total: number, weights: readonly number[]): number[] {
  const safeTotal = Math.max(0, Math.floor(total))
  const safeWeights = weights.map((weight) => Math.max(0, weight))
  const weightTotal = safeWeights.reduce((sum, weight) => sum + weight, 0)

  if (safeTotal === 0 || weightTotal === 0) {
    return weights.map(() => 0)
  }

  const weightedCounts = safeWeights.map((weight, index) => {
    const exact = (safeTotal * weight) / weightTotal
    return {
      index,
      floor: Math.floor(exact),
      remainder: exact - Math.floor(exact),
    }
  })
  const counts = weightedCounts.map((item) => item.floor)
  let remaining = safeTotal - counts.reduce((sum, count) => sum + count, 0)

  weightedCounts
    .slice()
    .sort((left, right) => {
      if (right.remainder !== left.remainder) {
        return right.remainder - left.remainder
      }
      return left.index - right.index
    })
    .forEach((item) => {
      if (remaining <= 0) {
        return
      }
      counts[item.index] += 1
      remaining -= 1
    })

  return counts
}

function percentageCount(total: number, ratio: number): number {
  return Math.min(total, Math.max(0, Math.round(total * ratio)))
}

function positiveIntegerOrDefault(value: number | undefined, fallback: number): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 1) {
    return fallback
  }

  return value
}
