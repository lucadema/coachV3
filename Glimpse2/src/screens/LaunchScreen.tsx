import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function LaunchScreen({ flow }: ScreenProps) {
  return (
    <div className="screen-copy hero-copy">
      <p className="eyebrow">Aether Glimpse</p>
      <h2>A quiet space to think through a work challenge.</h2>
      <p>
        Move at a steady pace through a guided coaching process. Your current step stays clear,
        and earlier exchanges remain available when you need to look back.
      </p>
      <Button disabled={flow.navigation.isReviewingHistory} onClick={flow.enterExperience}>
        Begin
      </Button>
    </div>
  )
}
