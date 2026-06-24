import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'
import { ErrorNotice } from '../components/ErrorNotice'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function ClosedScreen({ flow }: ScreenProps) {
  const disabled = flow.navigation.isReviewingHistory

  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      <h2>Your Glimpse session is complete.</h2>
      <p>
        You can download a summary of the synthesis and pathways, or begin a new session when you
        are ready.
      </p>
      <div className="split-actions">
        <Button disabled={disabled} onClick={flow.downloadPdf}>
          Download PDF
        </Button>
        <Button disabled={disabled} onClick={flow.startNewSession} variant="secondary">
          New session
        </Button>
      </div>
    </div>
  )
}
