import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

type ClosedScreenProps = {
  onStartNewSession: () => void
}

export function ClosedScreen({ onStartNewSession }: ClosedScreenProps) {
  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
      <section aria-label="Aether session closed">
        <h1 className="absolute left-[157px] top-[407px] m-0 w-[1130px] text-center text-[95px] font-thin leading-[95px] tracking-[-3.8px] text-[#294744]">
          We hope you’ve enjoyed this glimpse of Aether
        </h1>
        <div className="absolute left-[640px] top-[703px]">
          <OnboardingButton
            label="Start a New Session"
            onClick={onStartNewSession}
            tone="filled"
          />
        </div>
      </section>
    </OnboardingFrame>
  )
}
