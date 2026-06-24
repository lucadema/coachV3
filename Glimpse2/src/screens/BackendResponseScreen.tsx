import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { ErrorNotice } from '../components/ErrorNotice'
import { MarkdownText } from '../components/MarkdownText'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function BackendResponseScreen({ flow }: ScreenProps) {
  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      <h2>Backend response</h2>
      <div className="coach-card">
        <MarkdownText text={flow.current.coachMessage} />
      </div>
    </div>
  )
}
