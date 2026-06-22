export type PilotStatus = 'active' | 'paused'

export type DashboardCountBucket = {
  value: string
  label: string
  count: number
}

export type DashboardValueInputs = {
  monthly_minutes: number
  qualifying_responses_count: number
  flag_to_organisation: {
    yes_count: number
    no_count: number
  }
}

export type DashboardData = {
  available: boolean
  enterprise_name: string | null
  pilot_name: string | null
  pilot_status: PilotStatus | null
  problem_categories: DashboardCountBucket[]
  engagement_signals: DashboardCountBucket[]
  value_unlocked: DashboardValueInputs
}

export type DashboardLoadState =
  | { status: 'loading' }
  | { status: 'ready'; data: DashboardData; isTestMode: boolean; tokenKey: string }
  | { status: 'unavailable' }
  | { status: 'error' }
