import { useEffect, useState } from 'react'
import { CoachApiError, initialiseSession, sendUserMessage } from './api/coachClient'
import {
  buildBackendTurnStateUpdate,
  buildMissingSessionResetState,
} from './flow/sessionState'
import { BackendResponsePlaceholder } from './screens/BackendResponsePlaceholder'
import { DiscussionScreen } from './screens/DiscussionScreen'
import { InformationScreen } from './screens/InformationScreen'
import { LaunchScreen } from './screens/LaunchScreen'
import { OnboardingCompleteScreen } from './screens/OnboardingCompleteScreen'
import { PrivacyScreen } from './screens/PrivacyScreen'
import { ProblemInputScreen } from './screens/ProblemInputScreen'
import { WelcomeScreen } from './screens/WelcomeScreen'
import type { OnboardingStep } from './types/onboarding'
import type { BackendSessionView, FrontendScreen } from './types/session'

type AppStep = OnboardingStep | 'coaching' | 'backend_response'

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
  const [cachedPathwaysMessage, setCachedPathwaysMessage] = useState('')
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

  function applyBackendTurnResponse(
    response: Parameters<typeof buildBackendTurnStateUpdate>[0],
    activeSessionId: string,
    previousScreen: FrontendScreen,
  ) {
    const update = buildBackendTurnStateUpdate(response, cachedPathwaysMessage)
    const stayedInCoaching = previousScreen === 'coaching' && update.uiScreen === 'coaching'

    setSessionId(update.sessionView?.session_id ?? activeSessionId)
    setSessionView(update.sessionView)
    setCoachMessage(update.coachMessage)
    setCachedPathwaysMessage(update.cachedPathwaysMessage)
    setResolvedScreen(update.uiScreen)
    setLastBackendPreviousScreen(previousScreen)
    setLastBackendStayedInCoaching(stayedInCoaching)
    setStep(update.uiScreen === 'coaching' ? 'coaching' : 'backend_response')
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
