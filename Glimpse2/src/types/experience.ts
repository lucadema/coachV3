import type {
  BackendSessionView,
  ConversationExchange,
  ExperienceStep,
  PathwayCard,
  SynthesisReviewMode,
} from './session'
import type { FeedbackFormConfig, FeedbackState } from './feedback'
import type { SessionPdfSourceData } from '../pdf/sessionPdfTypes'

export type ExperienceSnapshot = {
  id: string
  step: ExperienceStep
  privacyAccepted: boolean
  sessionId: string | null
  sessionView: BackendSessionView | null
  coachMessage: string
  cachedPathwaysMessage: string
  synthesisMode: SynthesisReviewMode
  selectedPathwayTitle: string | null
  feedback: FeedbackState
  feedbackForm: FeedbackFormConfig | null
  sessionContent: SessionPdfSourceData
  frontendError: string | null
  isInitialisingSession: boolean
  isSubmitting: boolean
  exchanges: ConversationExchange[]
}

export type StageDefinition = {
  step: ExperienceStep
  label: string
  shortLabel: string
  progress: number
  phase: 'arrival' | 'consent' | 'setup' | 'exploration' | 'review' | 'feedback' | 'complete'
}

export type NavigationState = {
  canGoBack: boolean
  canGoForward: boolean
  isReviewingHistory: boolean
  currentIndex: number
  total: number
}

export type SelectedPathway = PathwayCard | null
