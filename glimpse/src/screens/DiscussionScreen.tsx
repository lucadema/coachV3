import { useState } from 'react'
import iconAetherCoach from '../assets/onboarding/icon-aether-coach.svg'
import iconUserCloud from '../assets/onboarding/icon-user-cloud.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

type DiscussionScreenProps = {
  coachMessage: string
  error?: string | null
  isLoading?: boolean
  onContinue: (userMessage: string) => void | Promise<void>
}

export function DiscussionScreen({
  coachMessage,
  error = null,
  isLoading = false,
  onContinue,
}: DiscussionScreenProps) {
  const [userMessage, setUserMessage] = useState('')
  const trimmedUserMessage = userMessage.trim()
  const canContinue = trimmedUserMessage.length > 0 && !isLoading

  async function handleContinue() {
    if (!canContinue) {
      return
    }

    await onContinue(trimmedUserMessage)
    setUserMessage('')
  }

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <section
        aria-labelledby="discussion-coach-message"
        className="absolute left-[384px] top-[170px] h-[338px] w-[683px]"
      >
        <OnboardingCard className="inset-0" />
        <img
          src={iconAetherCoach}
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-[43px] h-[42.53px] w-[42.523px] -translate-x-1/2"
        />
        <div className="absolute left-[38px] top-[118px] h-[178px] w-[608px] overflow-auto">
          <p
            id="discussion-coach-message"
            className="m-0 whitespace-pre-wrap text-center text-[20px] font-light leading-none tracking-[-0.8px] text-[#294744]"
          >
            {coachMessage || 'Aether coaching response question here...'}
          </p>
        </div>
      </section>

      <section
        aria-busy={isLoading}
        aria-label="Your coaching reply"
        className="absolute left-[384px] top-[515px] h-[338px] w-[683px]"
      >
        <OnboardingCard className="inset-0" />
        <img
          src={iconUserCloud}
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-[43px] h-[42.53px] w-[42.523px] -translate-x-1/2"
        />
        <textarea
          aria-label="Reply to Aether"
          disabled={isLoading}
          value={userMessage}
          onChange={(event) => {
            setUserMessage(event.target.value)
          }}
          placeholder="Your response here..."
          className="absolute left-[38px] top-[111px] h-[115px] w-[608px] resize-none bg-transparent text-center text-[20px] font-medium leading-[22px] text-[#294744] italic outline-none placeholder:text-[rgba(41,71,68,0.25)] disabled:cursor-wait"
        />
        {error ? (
          <p
            role="alert"
            className="absolute left-[92px] top-[226px] m-0 w-[500px] text-center text-[13px] font-light leading-[1.2] text-[#294744]"
          >
            {error}
          </p>
        ) : null}
        <div className="absolute left-[255px] top-[263px]">
          <OnboardingButton
            disabled={!canContinue}
            label="Continue"
            onClick={() => {
              void handleContinue()
            }}
            tone={canContinue ? 'filled' : 'outline'}
          />
        </div>
      </section>
    </OnboardingFrame>
  )
}
