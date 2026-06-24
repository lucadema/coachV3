export type FeedbackQuestionType =
  | 'boolean'
  | 'likert_1_5'
  | 'single_select'
  | 'multi_select'
  | 'short_text'
  | 'free_text'

export type FeedbackOption = {
  value: string
  label: string
  numeric_value?: number | null
}

export type FeedbackQuestion = {
  id: string
  type: FeedbackQuestionType
  text: string
  required: boolean
  placeholder?: string | null
  true_label?: string | null
  false_label?: string | null
  options?: FeedbackOption[]
}

export type FeedbackFormConfig = {
  show_feedback: boolean
  feedback_pack_id?: string
  title?: string
  survey_query?: string | null
  description?: string | null
  questions?: FeedbackQuestion[]
}

export type FeedbackValue = boolean | number | string | string[] | null

export type FeedbackState = Record<string, FeedbackValue>

export function createDefaultFeedbackState(): FeedbackState {
  return {}
}
