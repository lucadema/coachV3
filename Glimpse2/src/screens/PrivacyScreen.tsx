import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function PrivacyScreen({ flow }: ScreenProps) {
  const disabled = flow.navigation.isReviewingHistory

  return (
    <div className="screen-copy">
      <h2>Before we start</h2>
      <p>
        This experience is designed for reflective work. Please avoid entering personal,
        confidential, or highly sensitive information.
      </p>
      <label className="checkbox-line">
        <input
          checked={flow.current.privacyAccepted}
          disabled={disabled}
          onChange={(event) => flow.setPrivacyAccepted(event.target.checked)}
          type="checkbox"
        />
        <span>I understand and want to continue.</span>
      </label>
      <Button
        disabled={disabled || !flow.current.privacyAccepted}
        onClick={flow.continueFromPrivacy}
      >
        Continue
      </Button>
    </div>
  )
}
