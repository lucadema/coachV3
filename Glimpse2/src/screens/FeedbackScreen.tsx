import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'
import { FeedbackForm } from '../features/feedback/FeedbackForm'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function FeedbackScreen({ flow }: ScreenProps) {
  const form = flow.current.feedbackForm

  if (!form) {
    return (
      <div className="screen-copy">
        <h2>Thank you.</h2>
        <Button onClick={flow.skipFeedbackSurvey}>Close</Button>
      </div>
    )
  }

  return (
    <div className="screen-copy">
      <h2>{form.title ?? 'Feedback'}</h2>
      {form.description ? <p>{form.description}</p> : null}
      <FeedbackForm feedback={flow.current.feedback} form={form} onChange={flow.setFeedback} />
      <Button
        disabled={flow.navigation.isReviewingHistory}
        onClick={() => flow.closeFeedback(flow.current.feedback)}
      >
        Submit feedback
      </Button>
    </div>
  )
}
