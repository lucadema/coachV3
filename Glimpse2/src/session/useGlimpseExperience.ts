import { useMemo, useState } from 'react'
import {
  CoachApiError,
  getFeedbackForm,
  initialiseSession,
  recordSessionEvent,
  sendUserMessage,
  submitFeedback,
} from '../api/coachClient'
import { downloadSessionPdf } from '../pdf/sessionPdfDownload'
import { buildSessionPdfData } from '../pdf/sessionPdfLayout'
import type { SessionPdfSourceData } from '../pdf/sessionPdfTypes'
import { createDefaultFeedbackState, type FeedbackState } from '../types/feedback'
import type { ExperienceSnapshot, NavigationState } from '../types/experience'
import type {
  BackendSessionView,
  BackendTurnResponse,
  ConversationExchange,
  ExperienceStep,
  PathwayCard,
} from '../types/session'
import {
  isRefinedSynthesisWaitingForPathways,
  parsePathwayCards,
  stepFromBackendSession,
} from '../flow/stages'

const MISSING_SESSION_NOTICE =
  'Your previous session is no longer available, likely because the backend restarted or was redeployed. Please start a new session.'

function makeId(prefix: string): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `${prefix}-${crypto.randomUUID()}`
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function createSnapshot(
  overrides: Partial<ExperienceSnapshot> = {},
): ExperienceSnapshot {
  return {
    id: makeId('snapshot'),
    step: 'launch',
    privacyAccepted: false,
    sessionId: null,
    sessionView: null,
    coachMessage: '',
    cachedPathwaysMessage: '',
    synthesisMode: 'review',
    selectedPathwayTitle: null,
    feedback: createDefaultFeedbackState(),
    feedbackForm: null,
    sessionContent: {},
    frontendError: null,
    isInitialisingSession: false,
    isSubmitting: false,
    exchanges: [],
    ...overrides,
  }
}

function getErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallbackMessage
}

function buildCachedPathwaysMessage(
  session: BackendSessionView,
  coachMessage: string,
  currentCachedPathwaysMessage: string,
): string {
  if (session.stage === 'pathways' && coachMessage) {
    return coachMessage
  }

  return currentCachedPathwaysMessage
}

function buildExchange(
  step: ExperienceStep,
  userMessage: string,
  coachMessage: string,
): ConversationExchange {
  return {
    id: makeId('exchange'),
    step,
    userMessage,
    coachMessage,
    createdAt: new Date().toISOString(),
  }
}

function buildTurnSnapshot({
  base,
  response,
  userMessage,
}: {
  base: ExperienceSnapshot
  response: BackendTurnResponse
  userMessage?: string
}): ExperienceSnapshot {
  const session = response.session ?? {}
  const coachMessage = response.coach_message ?? ''
  const cachedPathwaysMessage = buildCachedPathwaysMessage(
    session,
    coachMessage,
    base.cachedPathwaysMessage,
  )
  const nextStep = stepFromBackendSession(session)
  const pathwaysText = coachMessage || cachedPathwaysMessage
  const parsedPathways = parsePathwayCards(pathwaysText)
  const nextContent: SessionPdfSourceData = {
    ...base.sessionContent,
  }

  if (nextStep === 'synthesis_review' && coachMessage) {
    nextContent.synthesis = coachMessage
  }

  if (nextStep === 'pathways') {
    nextContent.pathways =
      parsedPathways.length > 0 ? parsedPathways : base.sessionContent.pathways
    nextContent.rawPathwaysText = pathwaysText
  }

  return createSnapshot({
    ...base,
    step: nextStep,
    sessionId: session.session_id ?? base.sessionId,
    sessionView: session,
    coachMessage,
    cachedPathwaysMessage,
    selectedPathwayTitle: nextStep === 'pathways' ? base.selectedPathwayTitle : null,
    sessionContent: nextContent,
    frontendError: null,
    isInitialisingSession: false,
    isSubmitting: false,
    exchanges:
      userMessage && userMessage.trim()
        ? [...base.exchanges, buildExchange(base.step, userMessage.trim(), coachMessage)]
        : base.exchanges,
  })
}

export function useGlimpseExperience() {
  const [snapshots, setSnapshots] = useState<ExperienceSnapshot[]>(() => [createSnapshot()])
  const [snapshotIndex, setSnapshotIndex] = useState(0)
  const current = snapshots[snapshotIndex] ?? snapshots[0]
  const latestIndex = snapshots.length - 1
  const isReviewingHistory = snapshotIndex < latestIndex

  function replaceCurrent(partial: Partial<ExperienceSnapshot>) {
    setSnapshots((existingSnapshots) =>
      existingSnapshots.map((snapshot, index) =>
        index === snapshotIndex
          ? createSnapshot({
              ...snapshot,
              ...partial,
              id: snapshot.id,
            })
          : snapshot,
      ),
    )
  }

  function commitSnapshot(snapshot: ExperienceSnapshot) {
    setSnapshots((existingSnapshots) => {
      const base = existingSnapshots.slice(0, snapshotIndex + 1)
      return [...base, createSnapshot(snapshot)]
    })
    setSnapshotIndex(snapshotIndex + 1)
  }

  function commitPartial(partial: Partial<ExperienceSnapshot>) {
    commitSnapshot(createSnapshot({ ...current, ...partial }))
  }

  async function ensureSessionId(base: ExperienceSnapshot): Promise<{
    sessionId: string
    sessionView: BackendSessionView
  }> {
    if (base.sessionId && base.sessionView) {
      return {
        sessionId: base.sessionId,
        sessionView: base.sessionView,
      }
    }

    const session = await initialiseSession()

    if (!session.session_id) {
      throw new CoachApiError('The backend did not return a session id.')
    }

    return {
      sessionId: session.session_id,
      sessionView: session,
    }
  }

  async function applyFeedbackGate(snapshot: ExperienceSnapshot): Promise<ExperienceSnapshot> {
    if (snapshot.step !== 'feedback_query' || !snapshot.sessionId) {
      return snapshot
    }

    try {
      const form = await getFeedbackForm(snapshot.sessionId)

      if (!form.show_feedback) {
        return createSnapshot({
          ...snapshot,
          step: 'closed',
          feedbackForm: null,
        })
      }

      return createSnapshot({
        ...snapshot,
        feedbackForm: form,
      })
    } catch {
      return createSnapshot({
        ...snapshot,
        step: 'closed',
        feedbackForm: null,
      })
    }
  }

  async function commitBackendResponse(
    base: ExperienceSnapshot,
    response: BackendTurnResponse,
    userMessage?: string,
  ) {
    const nextSnapshot = buildTurnSnapshot({ base, response, userMessage })
    const gatedSnapshot = await applyFeedbackGate(nextSnapshot)
    commitSnapshot(gatedSnapshot)
  }

  function guardLatest(): boolean {
    return !isReviewingHistory
  }

  function enterExperience() {
    if (!guardLatest()) {
      return
    }

    commitPartial({
      step: 'privacy',
      frontendError: null,
    })
  }

  function setPrivacyAccepted(privacyAccepted: boolean) {
    replaceCurrent({ privacyAccepted })
  }

  function continueFromPrivacy() {
    if (!guardLatest() || !current.privacyAccepted) {
      return
    }

    commitPartial({
      step: 'intro',
      frontendError: null,
    })
  }

  async function startSession() {
    if (!guardLatest()) {
      return
    }

    replaceCurrent({
      frontendError: null,
      isInitialisingSession: true,
    })

    try {
      const { sessionId, sessionView } = await ensureSessionId(current)
      commitSnapshot(
        createSnapshot({
          ...current,
          step: 'problem_input',
          sessionId,
          sessionView,
          frontendError: null,
          isInitialisingSession: false,
        }),
      )
    } catch (error) {
      replaceCurrent({
        frontendError: getErrorMessage(
          error,
          'Unable to start a backend session. Please check that the API is running and try again.',
        ),
        isInitialisingSession: false,
      })
    }
  }

  function resetAfterMissingSession() {
    commitSnapshot(
      createSnapshot({
        step: 'intro',
        frontendError: MISSING_SESSION_NOTICE,
      }),
    )
  }

  async function submitUserText(userMessage: string, options: { asProblem?: boolean } = {}) {
    if (!guardLatest()) {
      return
    }

    const trimmedMessage = userMessage.trim()
    if (!trimmedMessage) {
      return
    }

    replaceCurrent({
      frontendError: null,
      isSubmitting: true,
    })

    try {
      const { sessionId, sessionView } = await ensureSessionId(current)
      const base = createSnapshot({
        ...current,
        sessionId,
        sessionView,
        sessionContent: options.asProblem
          ? {
              ...current.sessionContent,
              problemStatement: trimmedMessage,
            }
          : current.sessionContent,
      })
      const response = await sendUserMessage(sessionId, trimmedMessage)

      await commitBackendResponse(base, response, trimmedMessage)
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      replaceCurrent({
        frontendError: getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
        isSubmitting: false,
      })
    }
  }

  async function submitControlMessage(userMessage: string) {
    if (!guardLatest()) {
      return
    }

    replaceCurrent({
      frontendError: null,
      isSubmitting: true,
    })

    try {
      const { sessionId, sessionView } = await ensureSessionId(current)
      const base = createSnapshot({
        ...current,
        sessionId,
        sessionView,
      })
      const response = await sendUserMessage(sessionId, userMessage)

      await commitBackendResponse(base, response)
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      replaceCurrent({
        frontendError: getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
        isSubmitting: false,
      })
    }
  }

  async function acceptSynthesis() {
    await submitControlMessage('yes')
  }

  function openSynthesisRefinement() {
    if (!guardLatest()) {
      return
    }

    replaceCurrent({
      frontendError: null,
      synthesisMode: 'refinement_open',
    })
  }

  async function submitSynthesisRefinement(feedbackText: string) {
    if (!guardLatest()) {
      return
    }

    const trimmedFeedback = feedbackText.trim()
    if (!trimmedFeedback) {
      return
    }

    replaceCurrent({
      frontendError: null,
      isSubmitting: true,
    })

    try {
      const { sessionId, sessionView } = await ensureSessionId(current)
      const base = createSnapshot({
        ...current,
        sessionId,
        sessionView,
      })
      const response = await sendUserMessage(sessionId, trimmedFeedback)
      const nextSnapshot = buildTurnSnapshot({
        base,
        response,
        userMessage: trimmedFeedback,
      })

      if (isRefinedSynthesisWaitingForPathways(nextSnapshot.sessionView)) {
        commitSnapshot(
          createSnapshot({
            ...nextSnapshot,
            step: 'synthesis_review',
            synthesisMode: 'awaiting_pathways_after_refinement',
            sessionContent: {
              ...nextSnapshot.sessionContent,
              synthesis: nextSnapshot.coachMessage,
            },
          }),
        )
        return
      }

      const gatedSnapshot = await applyFeedbackGate(nextSnapshot)
      commitSnapshot(gatedSnapshot)
    } catch (error) {
      if (error instanceof CoachApiError && error.isMissingSession) {
        resetAfterMissingSession()
        return
      }

      replaceCurrent({
        frontendError: getErrorMessage(
          error,
          'Unable to submit your response. Please check that the API is running and try again.',
        ),
        isSubmitting: false,
      })
    }
  }

  async function continueToPathways() {
    await submitControlMessage('continue')
  }

  async function completePathways() {
    await submitControlMessage('continue')
  }

  function setSelectedPathway(pathway: PathwayCard) {
    if (!guardLatest()) {
      return
    }

    replaceCurrent({
      selectedPathwayTitle:
        current.selectedPathwayTitle === pathway.title ? null : pathway.title,
    })
  }

  function takeFeedbackSurvey() {
    if (!guardLatest()) {
      return
    }

    commitPartial({
      step: 'feedback',
      frontendError: null,
    })
  }

  function skipFeedbackSurvey() {
    if (!guardLatest()) {
      return
    }

    commitPartial({
      step: 'closed',
      frontendError: null,
    })
  }

  function setFeedback(feedback: FeedbackState) {
    replaceCurrent({ feedback })
  }

  function closeFeedback(feedback: FeedbackState) {
    if (!guardLatest()) {
      return
    }

    const next = createSnapshot({
      ...current,
      step: 'closed',
      feedback,
      frontendError: null,
    })

    commitSnapshot(next)

    if (current.sessionId && current.feedbackForm?.feedback_pack_id) {
      void submitFeedback(
        current.sessionId,
        current.feedbackForm.feedback_pack_id,
        feedback,
      ).catch(() => undefined)
    }
  }

  function startNewSession() {
    if (!guardLatest()) {
      return
    }

    commitSnapshot(
      createSnapshot({
        step: 'intro',
        privacyAccepted: true,
      }),
    )
  }

  async function downloadPdf() {
    replaceCurrent({ frontendError: null })

    try {
      const pathwaysText = current.coachMessage || current.cachedPathwaysMessage
      const sourcePathways = parsePathwayCards(pathwaysText)
      const pdfSource: SessionPdfSourceData = {
        ...current.sessionContent,
        pathways:
          sourcePathways.length > 0
            ? sourcePathways
            : current.sessionContent.pathways,
        rawPathwaysText: current.sessionContent.rawPathwaysText ?? pathwaysText,
      }

      await downloadSessionPdf(buildSessionPdfData(pdfSource))
      if (current.sessionId) {
        void recordSessionEvent(current.sessionId, { event: 'pdf_downloaded' }).catch(
          () => undefined,
        )
      }
    } catch (error) {
      replaceCurrent({
        frontendError: getErrorMessage(
          error,
          'Unable to create the PDF download. Please try again.',
        ),
      })
    }
  }

  function goBack() {
    setSnapshotIndex((index) => Math.max(0, index - 1))
  }

  function goForward() {
    setSnapshotIndex((index) => Math.min(snapshots.length - 1, index + 1))
  }

  function returnToLatest() {
    setSnapshotIndex(snapshots.length - 1)
  }

  const pathwaysText = current.coachMessage || current.cachedPathwaysMessage
  const pathways = useMemo(() => {
    const parsedPathways = parsePathwayCards(pathwaysText)
    return parsedPathways.length > 0 ? parsedPathways : current.sessionContent.pathways ?? []
  }, [current.sessionContent.pathways, pathwaysText])
  const selectedPathway = useMemo(
    () =>
      current.selectedPathwayTitle === null
        ? null
        : pathways.find((pathway) => pathway.title === current.selectedPathwayTitle) ?? null,
    [current.selectedPathwayTitle, pathways],
  )

  const navigation: NavigationState = {
    canGoBack: snapshotIndex > 0,
    canGoForward: snapshotIndex < snapshots.length - 1,
    isReviewingHistory,
    currentIndex: snapshotIndex,
    total: snapshots.length,
  }

  return {
    current,
    navigation,
    pathways,
    pathwaysText,
    selectedPathway,
    enterExperience,
    setPrivacyAccepted,
    continueFromPrivacy,
    startSession,
    submitProblem: (problemText: string) => submitUserText(problemText, { asProblem: true }),
    submitCoachingMessage: (userMessage: string) => submitUserText(userMessage),
    acceptSynthesis,
    openSynthesisRefinement,
    submitSynthesisRefinement,
    continueToPathways,
    completePathways,
    setSelectedPathway,
    takeFeedbackSurvey,
    skipFeedbackSurvey,
    setFeedback,
    closeFeedback,
    startNewSession,
    downloadPdf,
    goBack,
    goForward,
    returnToLatest,
  }
}

export type GlimpseExperienceController = ReturnType<typeof useGlimpseExperience>
