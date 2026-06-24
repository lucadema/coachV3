import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'
import { ErrorNotice } from '../components/ErrorNotice'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function IntroScreen({ flow }: ScreenProps) {
  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      <h2>Set down the challenge in your own words.</h2>
      <p>
        You will be asked a small number of focused questions, then invited to review a synthesis
        and consider possible pathways forward.
      </p>
      <Button
        disabled={flow.navigation.isReviewingHistory || flow.current.isInitialisingSession}
        onClick={flow.startSession}
      >
        {flow.current.isInitialisingSession ? 'Starting...' : 'Start session'}
      </Button>
    </div>
  )
}
