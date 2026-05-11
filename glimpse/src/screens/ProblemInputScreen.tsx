import { useState } from 'react'
import iconAetherCoach from '../assets/onboarding/icon-aether-coach.svg'
import iconUserCloud from '../assets/onboarding/icon-user-cloud.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'

const problemPrompt =
  'Let’s think this through together. In the field below, describe a professional challenge, or unresolved issue you are currently facing.'

type ProblemInputScreenProps = {
  error?: string | null
  initialValue?: string
  isLoading?: boolean
  onContinue: (problemText: string) => void
}

export function ProblemInputScreen({
  error = null,
  initialValue = '',
  isLoading = false,
  onContinue,
}: ProblemInputScreenProps) {
  const [problemText, setProblemText] = useState(initialValue)
  const trimmedProblemText = problemText.trim()
  const canContinue = trimmedProblemText.length > 0 && !isLoading

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <section
        aria-labelledby="problem-input-prompt"
        className="absolute left-[384px] top-[170px] h-[338px] w-[683px]"
      >
        <OnboardingCard className="inset-0" />
        <img
          src={iconAetherCoach}
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-[46px] h-[42.53px] w-[42.523px] -translate-x-1/2"
        />
        <p
          id="problem-input-prompt"
          className="absolute left-[37px] top-[124px] m-0 w-[608px] text-center text-[20px] font-light leading-none tracking-[-0.8px] text-[#294744]"
        >
          {problemPrompt}
        </p>
      </section>

      <section
        aria-busy={isLoading}
        aria-label="Your response"
        className="absolute left-[383px] top-[514px] h-[338px] w-[683px]"
      >
        <OnboardingCard className="inset-0" />
        <img
          src={iconUserCloud}
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-[43px] h-[42.53px] w-[42.523px] -translate-x-1/2"
        />
        <textarea
          aria-label="Describe your professional challenge"
          disabled={isLoading}
          value={problemText}
          onChange={(event) => {
            setProblemText(event.target.value)
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
              if (!canContinue) {
                return
              }

              onContinue(trimmedProblemText)
            }}
            tone={canContinue ? 'filled' : 'outline'}
          />
        </div>
      </section>
    </OnboardingFrame>
  )
}
