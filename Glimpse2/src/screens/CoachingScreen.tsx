import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { ErrorNotice } from '../components/ErrorNotice'
import { PromptForm } from '../components/Field'
import { MarkdownText } from '../components/MarkdownText'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function CoachingScreen({ flow }: ScreenProps) {
  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      {flow.current.coachMessage ? (
        <div className="coach-card">
          <MarkdownText text={flow.current.coachMessage} />
        </div>
      ) : null}
      <PromptForm
        buttonLabel={flow.current.isSubmitting ? 'Sending...' : 'Reply'}
        disabled={flow.navigation.isReviewingHistory || flow.current.isSubmitting}
        minRows={4}
        onSubmit={flow.submitCoachingMessage}
        placeholder="Write your response..."
      />
    </div>
  )
}
