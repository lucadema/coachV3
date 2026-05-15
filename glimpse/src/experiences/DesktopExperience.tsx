import { BackendResponsePlaceholder } from '../screens/BackendResponsePlaceholder'
import { ClosedScreen } from '../screens/ClosedScreen'
import { DiscussionScreen } from '../screens/DiscussionScreen'
import { FeedbackScreen } from '../screens/FeedbackScreen'
import { InformationScreen } from '../screens/InformationScreen'
import { LaunchScreen } from '../screens/LaunchScreen'
import { OnboardingCompleteScreen } from '../screens/OnboardingCompleteScreen'
import { PathwaysScreen } from '../screens/PathwaysScreen'
import { PrivacyScreen } from '../screens/PrivacyScreen'
import { ProblemInputScreen } from '../screens/ProblemInputScreen'
import { SynthesisReviewScreen } from '../screens/SynthesisReviewScreen'
import { WelcomeScreen } from '../screens/WelcomeScreen'
import type { GlimpseSessionFlow } from '../flow/useGlimpseSession'

type DesktopExperienceProps = {
  flow: GlimpseSessionFlow
}

export function DesktopExperience({ flow }: DesktopExperienceProps) {
  if (flow.step === 'launch') {
    return <LaunchScreen />
  }

  if (flow.step === 'welcome') {
    return <WelcomeScreen />
  }

  if (flow.step === 'privacy') {
    return (
      <PrivacyScreen
        hasAcknowledged={flow.hasAcknowledgedPrivacy}
        onAcknowledgedChange={flow.setHasAcknowledgedPrivacy}
        onContinue={flow.handlePrivacyContinue}
      />
    )
  }

  if (flow.step === 'information') {
    return (
      <InformationScreen
        error={flow.frontendError}
        isLoading={flow.isInitialisingSession}
        onStartSession={flow.handleStartSession}
      />
    )
  }

  if (flow.step === 'problem_input') {
    return (
      <ProblemInputScreen
        error={flow.frontendError}
        isLoading={flow.isInitialisingSession || flow.isSubmittingProblem}
        onContinue={flow.handleProblemContinue}
      />
    )
  }

  if (flow.step === 'coaching') {
    return (
      <DiscussionScreen
        coachMessage={flow.coachMessage}
        error={flow.frontendError}
        isLoading={flow.isSubmittingProblem}
        onContinue={flow.handleCoachingContinue}
      />
    )
  }

  if (flow.step === 'synthesis_review') {
    return (
      <SynthesisReviewScreen
        error={flow.frontendError}
        isLoading={flow.isSubmittingProblem}
        mode={flow.synthesisMode}
        onAccept={flow.handleSynthesisAccept}
        onContinueToPathways={flow.handleContinueToPathways}
        onOpenRefinement={flow.handleOpenSynthesisRefinement}
        onSubmitRefinement={flow.handleSubmitSynthesisRefinement}
        synthesisText={flow.coachMessage}
      />
    )
  }

  if (flow.step === 'pathways') {
    return (
      <PathwaysScreen
        error={flow.frontendError}
        isLoading={flow.isSubmittingProblem}
        onContinue={flow.handlePathwaysContinue}
        onDownloadPdf={flow.handleDownloadPathwaysPdf}
        pathways={flow.pathways}
        rawPathwaysText={flow.pathwaysText}
      />
    )
  }

  if (flow.step === 'feedback') {
    return (
      <FeedbackScreen
        feedback={flow.feedback}
        onChange={flow.setFeedback}
        onClose={flow.handleFeedbackClose}
      />
    )
  }

  if (flow.step === 'closed') {
    return <ClosedScreen onStartNewSession={flow.handleStartNewSession} />
  }

  if (flow.step === 'backend_response') {
    return (
      <BackendResponsePlaceholder
        coachMessage={flow.coachMessage}
        error={flow.frontendError}
        previousScreen={flow.lastBackendPreviousScreen}
        resolvedScreen={flow.resolvedScreen}
        sessionView={flow.sessionView}
        stayedInCoaching={flow.lastBackendStayedInCoaching}
      />
    )
  }

  return <OnboardingCompleteScreen />
}
