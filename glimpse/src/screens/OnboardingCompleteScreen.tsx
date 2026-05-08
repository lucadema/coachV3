import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

export function OnboardingCompleteScreen() {
  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
      <div className="absolute inset-0 flex items-center justify-center">
        <p className="m-0 text-center text-[29px] font-light leading-[1.2] tracking-[-1.16px] text-[#294744]">
          Onboarding flow complete.
        </p>
      </div>
    </OnboardingFrame>
  )
}
