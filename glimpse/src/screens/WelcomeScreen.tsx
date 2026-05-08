import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

export function WelcomeScreen() {
  return (
    <OnboardingFrame>
      <div className="absolute inset-[43.95%_11.3%_47.36%_11.3%]">
        <h1 className="m-0 whitespace-nowrap text-center text-[95px] font-thin leading-[95px] tracking-[-3.8px] text-[#294744]">
          Welcome to Aether Glimpse
        </h1>
      </div>
      <div className="absolute inset-[54.98%_11.3%_36.33%_11.3%] flex flex-col items-center text-center text-[29px] font-light leading-[1.18] tracking-[-1.16px] text-[#294744]">
        <p className="m-0">Together we’ll explore a challenge you’re facing at work.</p>
        <p className="m-0">
          Before we get stuck in, there’s a few things we need to agree on.
        </p>
      </div>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
    </OnboardingFrame>
  )
}
