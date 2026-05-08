import iconAetherCoach from '../assets/onboarding/icon-aether-coach.svg'
import iconUserCloud from '../assets/onboarding/icon-user-cloud.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

const informationIntroMessage = `This is a space to explore one professional
challenge with clarity and depth.

Aether will ask you questions that help
you understand your problem more fully
before presenting a set of resolution
pathways you can take away and act on.`

const informationIconMessage = `Throughout the session,
the thinking cloud icon represents you.
The green ‘a’ icon represents Aether.`

type InformationScreenProps = {
  onStartSession: () => void
}

export function InformationScreen({ onStartSession }: InformationScreenProps) {
  return (
    <OnboardingFrame>
      <OnboardingCard className="inset-[16.7%_26.46%_16.6%_26.46%]" />
      <p className="absolute inset-[24.9%_36.8%_58.01%_36.8%] m-0 whitespace-pre-line text-center text-[20px] font-light leading-[1.18] tracking-[-0.8px] text-[#294744]">
        {informationIntroMessage}
      </p>
      <img
        src={iconUserCloud}
        alt=""
        aria-hidden="true"
        className="absolute inset-[45.8%_51.38%_50.05%_45.69%] h-[42.53px] w-[42.523px]"
      />
      <img
        src={iconAetherCoach}
        alt=""
        aria-hidden="true"
        className="absolute inset-[45.8%_45.66%_50.05%_51.41%] h-[42.53px] w-[42.523px]"
      />
      <p className="absolute inset-[54.1%_36.8%_37.79%_36.8%] m-0 whitespace-pre-line text-center text-[20px] font-light leading-[1.18] tracking-[-0.8px] text-[#294744]">
        {informationIconMessage}
      </p>
      <div className="absolute inset-[75.29%_44.11%_20.61%_44.18%]">
        <OnboardingButton label="Start Session" onClick={onStartSession} tone="outline" />
      </div>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />
    </OnboardingFrame>
  )
}
