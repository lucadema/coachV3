import { MobileClosedScreen } from './mobile/MobileClosedScreen'
import { MobileFeedbackQueryScreen } from './mobile/MobileFeedbackQueryScreen'
import { MobileFeedbackScreen } from './mobile/MobileFeedbackScreen'
import { MobileInformationScreen } from './mobile/MobileInformationScreen'
import { MobileLaunchScreen } from './mobile/MobileLaunchScreen'
import { MobilePathwaysScreen } from './mobile/MobilePathwaysScreen'
import { MobilePrivacyScreen } from './mobile/MobilePrivacyScreen'
import { MobileProblemInputScreen } from './mobile/MobileProblemInputScreen'
import { MobileSynthesisReviewScreen } from './mobile/MobileSynthesisReviewScreen'
import { MobileDiscussionScreen } from './mobile/MobileDiscussionScreen'
import { MobileWelcomeScreen } from './mobile/MobileWelcomeScreen'
import type { GlimpseSessionFlow } from '../flow/useGlimpseSession'

type MobileExperienceProps = {
  flow: GlimpseSessionFlow
}

export function MobileExperience({ flow }: MobileExperienceProps) {
  if (flow.step === 'launch') {
    return <MobileLaunchScreen />
  }

  if (flow.step === 'welcome') {
    return <MobileWelcomeScreen />
  }

  if (flow.step === 'privacy') {
    return (
      <MobilePrivacyScreen
        hasAcknowledged={flow.hasAcknowledgedPrivacy}
        onAcknowledgedChange={flow.setHasAcknowledgedPrivacy}
        onContinue={flow.handlePrivacyContinue}
      />
    )
  }

  if (flow.step === 'information') {
    return (
      <MobileInformationScreen
        error={flow.frontendError}
        isLoading={flow.isInitialisingSession}
        onStartSession={flow.handleStartSession}
      />
    )
  }

  if (flow.step === 'problem_input') {
    return (
      <MobileProblemInputScreen
        error={flow.frontendError}
        isLoading={flow.isInitialisingSession || flow.isSubmittingProblem}
        onContinue={flow.handleProblemContinue}
      />
    )
  }

  if (flow.step === 'coaching') {
    return (
      <MobileDiscussionScreen
        coachMessage={flow.coachMessage}
        error={flow.frontendError}
        isLoading={flow.isSubmittingProblem}
        onContinue={flow.handleCoachingContinue}
      />
    )
  }

  if (flow.step === 'synthesis_review') {
    return (
      <MobileSynthesisReviewScreen
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
      <MobilePathwaysScreen
        error={flow.frontendError}
        isLoading={flow.isSubmittingProblem}
        onContinue={flow.handlePathwaysContinue}
        onSelectPathway={flow.handleSelectedPathwayChange}
        pathways={flow.pathways}
        rawPathwaysText={flow.pathwaysText}
        selectedPathwayTitle={flow.selectedPathwayTitle}
      />
    )
  }

  if (flow.step === 'feedback_query') {
    return (
      <MobileFeedbackQueryScreen
        form={flow.feedbackForm}
        onSkip={flow.handleFeedbackQuerySkip}
        onTakeSurvey={flow.handleFeedbackQueryAccept}
        selectedPathway={flow.selectedPathway}
      />
    )
  }

  if (flow.step === 'feedback') {
    return (
      <MobileFeedbackScreen
        feedback={flow.feedback}
        form={flow.feedbackForm}
        onChange={flow.setFeedback}
        onClose={flow.handleFeedbackClose}
      />
    )
  }

  return (
    <MobileClosedScreen
      onDownloadPdf={flow.handleDownloadPathwaysPdf}
      onStartNewSession={flow.handleStartNewSession}
    />
  )
}
