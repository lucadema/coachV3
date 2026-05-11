import { useEffect, useState } from 'react'
import { CoachApiError, initialiseSession, sendUserMessage } from './api/coachClient'
import { isRefinedSynthesisWaitingForPathways, parsePathwayCards } from './flow/sessionFlow'
import {
  buildBackendTurnStateUpdate,
  buildMissingSessionResetState,
} from './flow/sessionState'
import { BackendResponsePlaceholder } from './screens/BackendResponsePlaceholder'
import { ClosedScreen } from './screens/ClosedScreen'
import { DiscussionScreen } from './screens/DiscussionScreen'
import { FeedbackScreen } from './screens/FeedbackScreen'
import { InformationScreen } from './screens/InformationScreen'
import { LaunchScreen } from './screens/LaunchScreen'
import { OnboardingCompleteScreen } from './screens/OnboardingCompleteScreen'
import { PathwaysScreen } from './screens/PathwaysScreen'
import { PrivacyScreen } from './screens/PrivacyScreen'
import { ProblemInputScreen } from './screens/ProblemInputScreen'
import {
  SynthesisReviewScreen,
  type SynthesisReviewMode,
} from './screens/SynthesisReviewScreen'
import { WelcomeScreen } from './screens/WelcomeScreen'
import { createDefaultFeedbackState, type FeedbackState } from './types/feedback'
import type { OnboardingStep } from './types/onboarding'
import type { BackendSessionView, FrontendScreen } from './types/session'

type AppStep =
  | OnboardingStep
  | 'coaching'
  | 'synthesis_review'
  | 'pathways'
  | 'feedback'
  | 'closed'
  | 'backend_response'

const SCREEN_DELAYS: Partial<Record<AppStep, number>> = {
  launch: 3000,
  welcome: 4000,
}

function getErrorMessage(error: unknown, fallbackMessage: string) {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallbackMessage
}

function App() {
  const [step, setStep] = useState<AppStep>('launch')
  const [hasAcknowledgedPrivacy, setHasAcknowledgedPrivacy] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessionView, setSessionView] = useState<BackendSessionView | null>(null)
  const [coachMessage, setCoachMessage] = useState('')
  const [resolvedScreen, setResolvedScreen] = useState<FrontendScreen | null>(null)
  const [lastBackendPreviousScreen, setLastBackendPreviousScreen] =
    useState<FrontendScreen | null>(null)
  const [lastBackendStayedInCoaching, setLastBackendStayedInCoaching] = useState<boolean | null>(
    null,
  )
  const [synthesisMode, setSynthesisMode] = useState<SynthesisReviewMode>('review')
  const [cachedPathwaysMessage, setCachedPathwaysMessage] = useState('')
  const [feedback, setFeedback] = useState<FeedbackState>(() => createDefaultFeedbackState())
  const [frontendError, setFrontendError] = useState<string | null>(null)
  const [isInitialisingSession, setIsInitialisingSession] = useState(false)
  const [isSubmittingProblem, setIsSubmittingProblem] = useState(false)

  useEffect(() => {
    const delay = SCREEN_DELAYS[step]

    if (delay === undefined) {
      return undefined
    }

    const nextStep: AppStep = step === 'launch' ? 'welcome' : 'privacy'
    const timeoutId = window.setTimeout(() => {
      setStep(nextStep)
    }, delay)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [step])

  async function ensureSessionId() {
    if (sessionId) {
      return sessionId
    }

    const session = await initialiseSession()

    if (!session.session_id) {
      throw new CoachApiError('The backend did not return a session id.')
    }

    setSessionId(session.session_id)
    setSessionView(session)
    setResolvedScreen('problem_input')

    return session.session_id
  }

  function applyBackendTurnUpdate(
    update: ReturnType<typeof buildBackendTurnStateUpdate>,
    activeSessionId: string,
    previousScreen: FrontendScreen,
  ) {
    const stayedInCoaching = previousScreen === 'coaching' && update.uiScreen === 'coaching'

    setSessionId(update.sessionView?.session_id ?? activeSessionId)
    setSessionView(update.sessionView)
    setCoachMessage(update.coachMessage)
    setCachedPathwaysMessage(update.cachedPathwaysMessage)
    setResolvedScreen(update.uiScreen)
    setLastBackendPreviousScreen(previousScreen)
    setLastBackendStayedInCoaching(stayedInCoaching)

    if (update.uiScreen === 'coaching') {
      setStep('coaching')
      return
    }

    if (update.uiScreen === 'synthesis_review') {
      setSynthesisMode('review')
      setStep('synthesis_review')
      return
    }

    if (update.uiScreen === 'pathways') {
      setStep('pathways')
      return
    }

    if (update.uiScreen === 'feedback') {
      setStep('feedback')
      return
    }

    setStep('backend_response')
  }

  function applyBackendTurnResponse(
    response: Parameters<typeof buildBackendTurnStateUpdate>[0],
    activeSessionId: string,
    previousScreen: FrontendScreen,
  ) {
    const update = buildBackendTurnStateUpdate(response, cachedPathwaysMessage)
    applyBackendTurnUpdate(update, activeSessionId, previousScreen)
  }

  async function handleStartSession() {
    if (sessionId) {
      setFrontendError(null)
      setStep('problem_input')
      return
    }

    setFrontendError(null)
    setIsInitialisingSession(true)

    try {
      await ensureSessionId()
      setStep('problem_input')
    } catch (error) {
      setFrontendError(
        getErrorMessage(
          error,
          'Unable to start a backend session. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsInitialisingSession(false)
    }
  }

  function resetAfterMissingSession() {
    const resetState = buildMissingSessionResetState()

    setSessionId(resetState.sessionId)
    setSessionView(resetState.sessionView)
    setCoachMessage(resetState.coachMessage)
    setCachedPathwaysMessage(resetState.cachedPathwaysMessage)
    setResolvedScreen(resetState.uiScreen)
    setFrontendError(resetState.frontendNotice)
    setStep('information')
  }

  async function handleProblemContinue(problemText: string) {
    const trimmedProblemText = problemText.trim()

    if (!trimmedProblemText) {
      return
    }

    setFrontendError(null)
    setIsSubmittingProblem(true)

    try {
      const activeSessionId = await ensureSessionId()
      const response = await sendUserMessage(activeSessionId, trimmedProblemText)

      applyBackendTurnResponse(response, activeSessionId, 'problem_input')
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      setFrontendError(
        getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsSubmittingProblem(false)
    }
  }

  async function handleCoachingContinue(userMessage: string) {
    const trimmedUserMessage = userMessage.trim()

    if (!trimmedUserMessage) {
      return
    }

    setFrontendError(null)
    setIsSubmittingProblem(true)

    try {
      const activeSessionId = await ensureSessionId()
      const response = await sendUserMessage(activeSessionId, trimmedUserMessage)

      applyBackendTurnResponse(response, activeSessionId, 'coaching')
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      setFrontendError(
        getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsSubmittingProblem(false)
    }
  }

  async function handleSynthesisAccept() {
    setFrontendError(null)
    setIsSubmittingProblem(true)

    try {
      const activeSessionId = await ensureSessionId()
      const response = await sendUserMessage(activeSessionId, 'yes')

      applyBackendTurnResponse(response, activeSessionId, 'synthesis_review')
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      setFrontendError(
        getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsSubmittingProblem(false)
    }
  }

  function handleOpenSynthesisRefinement() {
    setFrontendError(null)
    setSynthesisMode('refinement_open')
  }

  async function handleSubmitSynthesisRefinement(feedback: string) {
    const trimmedFeedback = feedback.trim()

    if (!trimmedFeedback) {
      return
    }

    setFrontendError(null)
    setIsSubmittingProblem(true)

    try {
      const activeSessionId = await ensureSessionId()
      const response = await sendUserMessage(activeSessionId, trimmedFeedback)
      const update = buildBackendTurnStateUpdate(response, cachedPathwaysMessage)

      if (isRefinedSynthesisWaitingForPathways(update.sessionView)) {
        setSessionId(update.sessionView?.session_id ?? activeSessionId)
        setSessionView(update.sessionView)
        setCoachMessage(update.coachMessage)
        setCachedPathwaysMessage(update.cachedPathwaysMessage)
        setResolvedScreen('synthesis_review')
        setLastBackendPreviousScreen('synthesis_review')
        setLastBackendStayedInCoaching(false)
        setSynthesisMode('awaiting_pathways_after_refinement')
        setStep('synthesis_review')
        return
      }

      applyBackendTurnUpdate(update, activeSessionId, 'synthesis_review')
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      setFrontendError(
        getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsSubmittingProblem(false)
    }
  }

  async function handleContinueToPathways() {
    setFrontendError(null)
    setIsSubmittingProblem(true)

    try {
      const activeSessionId = await ensureSessionId()
      const response = await sendUserMessage(activeSessionId, 'continue')

      setSynthesisMode('review')
      applyBackendTurnResponse(response, activeSessionId, 'synthesis_review')
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      setFrontendError(
        getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsSubmittingProblem(false)
    }
  }

  async function handlePathwaysContinue() {
    setFrontendError(null)
    setIsSubmittingProblem(true)

    try {
      const activeSessionId = await ensureSessionId()
      const response = await sendUserMessage(activeSessionId, 'continue')

      applyBackendTurnResponse(response, activeSessionId, 'pathways')
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      setFrontendError(
        getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
      )
    } finally {
      setIsSubmittingProblem(false)
    }
  }

  function handleFeedbackClose(nextFeedback: FeedbackState) {
    setFeedback(nextFeedback)
    setStep('closed')
  }

  if (step === 'launch') {
    return <LaunchScreen />
  }

  if (step === 'welcome') {
    return <WelcomeScreen />
  }

  if (step === 'privacy') {
    return (
      <PrivacyScreen
        hasAcknowledged={hasAcknowledgedPrivacy}
        onAcknowledgedChange={setHasAcknowledgedPrivacy}
        onContinue={() => {
          if (!hasAcknowledgedPrivacy) {
            return
          }

          setStep('information')
        }}
      />
    )
  }

  if (step === 'information') {
    return (
      <InformationScreen
        error={frontendError}
        isLoading={isInitialisingSession}
        onStartSession={handleStartSession}
      />
    )
  }

  if (step === 'problem_input') {
    return (
      <ProblemInputScreen
        error={frontendError}
        isLoading={isInitialisingSession || isSubmittingProblem}
        onContinue={handleProblemContinue}
      />
    )
  }

  if (step === 'coaching') {
    return (
      <DiscussionScreen
        coachMessage={coachMessage}
        error={frontendError}
        isLoading={isSubmittingProblem}
        onContinue={handleCoachingContinue}
      />
    )
  }

  if (step === 'synthesis_review') {
    return (
      <SynthesisReviewScreen
        error={frontendError}
        isLoading={isSubmittingProblem}
        mode={synthesisMode}
        onAccept={handleSynthesisAccept}
        onContinueToPathways={handleContinueToPathways}
        onOpenRefinement={handleOpenSynthesisRefinement}
        onSubmitRefinement={handleSubmitSynthesisRefinement}
        synthesisText={coachMessage}
      />
    )
  }

  if (step === 'pathways') {
    const pathwaysText = coachMessage || cachedPathwaysMessage

    return (
      <PathwaysScreen
        error={frontendError}
        isLoading={isSubmittingProblem}
        onContinue={handlePathwaysContinue}
        pathways={parsePathwayCards(pathwaysText)}
        rawPathwaysText={pathwaysText}
      />
    )
  }

  if (step === 'feedback') {
    return (
      <FeedbackScreen
        feedback={feedback}
        onChange={setFeedback}
        onClose={handleFeedbackClose}
      />
    )
  }

  if (step === 'closed') {
    return <ClosedScreen />
  }

  if (step === 'backend_response') {
    return (
      <BackendResponsePlaceholder
        coachMessage={coachMessage}
        error={frontendError}
        previousScreen={lastBackendPreviousScreen}
        resolvedScreen={resolvedScreen}
        sessionView={sessionView}
        stayedInCoaching={lastBackendStayedInCoaching}
      />
    )
  }

  return <OnboardingCompleteScreen />
}

export default App
