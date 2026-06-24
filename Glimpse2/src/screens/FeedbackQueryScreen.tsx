import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function FeedbackQueryScreen({ flow }: ScreenProps) {
  const disabled = flow.navigation.isReviewingHistory
  const query = flow.current.feedbackForm?.survey_query ?? 'Would you like to share feedback?'

  return (
    <div className="screen-copy">
      <h2>{query}</h2>
      {flow.selectedPathway ? (
        <p className="muted-copy">Selected pathway: {flow.selectedPathway.title}</p>
      ) : null}
      <div className="split-actions">
        <Button disabled={disabled} onClick={flow.takeFeedbackSurvey}>
          Take survey
        </Button>
        <Button disabled={disabled} onClick={flow.skipFeedbackSurvey} variant="secondary">
          Skip
        </Button>
      </div>
    </div>
  )
}
