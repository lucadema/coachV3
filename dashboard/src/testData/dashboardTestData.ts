import type { DashboardData } from '../types'

type SeededRandom = () => number

const PROBLEM_CATEGORIES = [
  ['organisational_friction', 'Organisational friction'],
  ['lack_of_clarity_alignment', 'Lack of clarity and alignment'],
  ['poor_decision_making', 'Poor decision-making'],
  ['siloed_thinking', 'Siloed thinking'],
  ['strategy_execution_gap', 'Strategy/execution gap'],
  ['inability_to_adapt', 'Inability to adapt'],
] as const

const ENGAGEMENT_SIGNALS = [
  ['no_visible_risk', 'No visible risk'],
  ['frustration_signal', 'Frustration signal'],
  ['voice_suppression_signal', 'Voice suppression signal'],
  ['disengagement_risk', 'Disengagement risk'],
] as const

export function createSeededRandom(seed: number): SeededRandom {
  let state = seed >>> 0
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0
    return state / 0x100000000
  }
}

export function createDashboardTestData(seed = 120626): DashboardData {
  const random = createSeededRandom(seed)

  return {
    available: true,
    enterprise_name: 'Aether Works',
    pilot_name: 'Leadership Clarity Pilot',
    pilot_status: 'active',
    problem_categories: PROBLEM_CATEGORIES.map(([value, label], index) => ({
      value,
      label,
      count: Math.max(1, Math.round(3 + random() * 18 - index * 0.8)),
    })),
    engagement_signals: ENGAGEMENT_SIGNALS.map(([value, label], index) => ({
      value,
      label,
      count: Math.max(1, Math.round(14 - index * 2.4 + random() * 6)),
    })),
    value_unlocked: {
      monthly_minutes: 60 * (42 + Math.round(random() * 18)),
      qualifying_responses_count: 9 + Math.round(random() * 8),
      flag_to_organisation: {
        yes_count: 8 + Math.round(random() * 8),
        no_count: 2 + Math.round(random() * 5),
      },
    },
  }
}
