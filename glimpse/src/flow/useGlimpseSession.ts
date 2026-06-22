import { useEffect, useState } from 'react'
import {
  CoachApiError,
  getFeedbackForm,
  initialiseSession,
  recordSessionEvent,
  sendUserMessage,
  submitFeedback,
} from '../api/coachClient'
import { isRefinedSynthesisWaitingForPathways, parsePathwayCards } from './sessionFlow'
import {
  buildBackendTurnStateUpdate,
  buildMissingSessionResetState,
} from './sessionState'
import { downloadSessionPdf } from '../pdf/sessionPdfDownload'
import { buildSessionPdfData } from '../pdf/sessionPdfLayout'
import type { SessionPdfSourceData } from '../pdf/sessionPdfTypes'
import {
  createDefaultFeedbackState,
  type FeedbackFormConfig,
  type FeedbackState,
} from '../types/feedback'
import type { OnboardingStep } from '../types/onboarding'
import type { BackendSessionView, FrontendScreen } from '../types/session'
import type { SynthesisReviewMode } from '../types/synthesis'

export type GlimpseStep =
  | OnboardingStep
  | 'coaching'
  | 'synthesis_review'
  | 'pathways'
  | 'feedback_query'
  | 'feedback'
  | 'closed'
  | 'backend_response'

const SCREEN_DELAYS: Partial<Record<GlimpseStep, number>> = {
  launch: 3000,
  welcome: 4000,
}

function getErrorMessage(error: unknown, fallbackMessage: string) {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallbackMessage
}

export function useGlimpseSession() {
  const [step, setStep] = useState<GlimpseStep>('launch')
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
  const [selectedPathwayTitle, setSelectedPathwayTitle] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<FeedbackState>(() => createDefaultFeedbackState())
  const [feedbackForm, setFeedbackForm] = useState<FeedbackFormConfig | null>(null)
  const [sessionContent, setSessionContent] = useState<SessionPdfSourceData>({})
  const [frontendError, setFrontendError] = useState<string | null>(null)
  const [isInitialisingSession, setIsInitialisingSession] = useState(false)
  const [isSubmittingProblem, setIsSubmittingProblem] = useState(false)

  useEffect(() => {
    const delay = SCREEN_DELAYS[step]

    if (delay === undefined) {
      return undefined
    }

    const nextStep: GlimpseStep = step === 'launch' ? 'welcome' : 'privacy'
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
      if (update.coachMessage) {
        setSessionContent((currentContent) => ({
          ...currentContent,
          synthesis: update.coachMessage,
        }))
      }
      setSynthesisMode('review')
      setStep('synthesis_review')
      return
    }

    if (update.uiScreen === 'pathways') {
      const pathwaysText = update.coachMessage || update.cachedPathwaysMessage

      setSessionContent((currentContent) => ({
        ...currentContent,
        pathways: parsePathwayCards(pathwaysText),
        rawPathwaysText: pathwaysText,
      }))
      setStep('pathways')
      return
    }

    if (update.uiScreen === 'feedback') {
      void loadFeedbackForm(activeSessionId, 'feedback_query')
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

  function handlePrivacyContinue() {
    if (!hasAcknowledgedPrivacy) {
      return
    }

    setStep('information')
  }

  function resetAfterMissingSession() {
    const resetState = buildMissingSessionResetState()

    setSessionId(resetState.sessionId)
    setSessionView(resetState.sessionView)
    setCoachMessage(resetState.coachMessage)
    setCachedPathwaysMessage(resetState.cachedPathwaysMessage)
    setResolvedScreen(resetState.uiScreen)
    setSessionContent({})
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

      setSessionContent((currentContent) => ({
        ...currentContent,
        problemStatement: trimmedProblemText,
      }))
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

  async function handleSubmitSynthesisRefinement(feedbackText: string) {
    const trimmedFeedback = feedbackText.trim()

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
        setSessionContent((currentContent) => ({
          ...currentContent,
          synthesis: update.coachMessage,
        }))
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

  async function loadFeedbackForm(
    activeSessionId: string,
    nextStep: Extract<GlimpseStep, 'feedback_query' | 'feedback'> = 'feedback',
  ) {
    try {
      const form = await getFeedbackForm(activeSessionId)
      if (!form.show_feedback) {
        setStep('closed')
        return
      }
      setFeedbackForm(form)
      setStep(nextStep)
    } catch {
      setStep('closed')
    }
  }

  function handleSelectedPathwayChange(pathway: { title: string }) {
    setSelectedPathwayTitle((currentTitle) =>
      currentTitle === pathway.title ? null : pathway.title,
    )
  }

  function handleFeedbackQueryAccept() {
    setStep('feedback')
  }

  function handleFeedbackQuerySkip() {
    setStep('closed')
  }

  function handleFeedbackClose(nextFeedback: FeedbackState) {
    setFeedback(nextFeedback)
    setStep('closed')
    if (sessionId && feedbackForm?.feedback_pack_id) {
      void submitFeedback(sessionId, feedbackForm.feedback_pack_id, nextFeedback).catch(
        () => undefined,
      )
    }
  }

  function handleStartNewSession() {
    setSessionId(null)
    setSessionView(null)
    setCoachMessage('')
    setResolvedScreen(null)
    setLastBackendPreviousScreen(null)
    setLastBackendStayedInCoaching(null)
    setSynthesisMode('review')
    setCachedPathwaysMessage('')
    setSelectedPathwayTitle(null)
    setFeedback(createDefaultFeedbackState())
    setFeedbackForm(null)
    setSessionContent({})
    setFrontendError(null)
    setIsInitialisingSession(false)
    setIsSubmittingProblem(false)
    setStep('information')
  }

  async function handleDownloadPdf(pdfSource: SessionPdfSourceData = sessionContent) {
    setFrontendError(null)

    try {
      await downloadSessionPdf(buildSessionPdfData(pdfSource))
      if (sessionId) {
        void recordSessionEvent(sessionId, { event: 'pdf_downloaded' }).catch(() => undefined)
      }
    } catch (error) {
      setFrontendError(
        getErrorMessage(
          error,
          'Unable to create the PDF download. Please try again.',
        ),
      )
    }
  }

  const pathwaysText = coachMessage || cachedPathwaysMessage
  const pathways = parsePathwayCards(pathwaysText)
  const stablePathways = pathways.length > 0 ? pathways : (sessionContent.pathways ?? [])
  const selectedPathway =
    selectedPathwayTitle === null
      ? null
      : (stablePathways.find((pathway) => pathway.title === selectedPathwayTitle) ?? null)

  function handleDownloadPathwaysPdf() {
    handleDownloadPdf({
      ...sessionContent,
      pathways,
      rawPathwaysText: pathwaysText,
    })
  }

  return {
    step,
    hasAcknowledgedPrivacy,
    setHasAcknowledgedPrivacy,
    sessionView,
    coachMessage,
    resolvedScreen,
    lastBackendPreviousScreen,
    lastBackendStayedInCoaching,
    synthesisMode,
    feedback,
    feedbackForm,
    selectedPathway,
    selectedPathwayTitle,
    setFeedback,
    frontendError,
    isInitialisingSession,
    isSubmittingProblem,
    pathways: stablePathways,
    pathwaysText,
    handleStartSession,
    handlePrivacyContinue,
    handleProblemContinue,
    handleCoachingContinue,
    handleSynthesisAccept,
    handleOpenSynthesisRefinement,
    handleSubmitSynthesisRefinement,
    handleContinueToPathways,
    handlePathwaysContinue,
    handleSelectedPathwayChange,
    handleFeedbackQueryAccept,
    handleFeedbackQuerySkip,
    handleFeedbackClose,
    handleStartNewSession,
    handleDownloadPathwaysPdf,
  }
}

export type GlimpseSessionFlow = ReturnType<typeof useGlimpseSession>
