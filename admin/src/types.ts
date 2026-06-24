export type EnterpriseStatus = 'active' | 'paused' | 'closed'
export type PilotStatus = 'draft' | 'active' | 'paused' | 'closed'
export type TokenType = 'glimpse_app' | 'dashboard'
export type TokenStatus = 'active' | 'revoked' | 'expired'

export type Enterprise = {
  id: string
  name: string
  status: EnterpriseStatus
  notes: string
  created_at: string
  updated_at: string
}

export type Pilot = {
  id: string
  enterprise_id: string
  name: string
  status: PilotStatus
  start_at: string | null
  end_at: string | null
  notes: string
  feedback_pack_id: string | null
  created_at: string
  updated_at: string
}

export type FeedbackPackOption = {
  id: string
  label: string
  title: string
}

export type AccessLink = {
  token_id: string
  pilot_id: string
  token_type: TokenType
  status: TokenStatus
  full_access_link: string | null
  token_prefix: string
  created_at: string
  expires_at: string | null
  last_used_at: string | null
  revoked_at: string | null
}

export type PilotSummary = {
  pilot_id: string
  pilot_status: PilotStatus
  sessions_count: number
  last_activity_at: string | null
  feedback_records_count: number
  link_statuses: Partial<Record<TokenType, TokenStatus>>
}
