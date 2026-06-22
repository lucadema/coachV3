import { useState } from 'react'
import iconAetherCoach from '../assets/onboarding/icon-aether-coach.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import { ChevronIcon } from '../components/onboarding/UiIcons'
import type { FeedbackFormConfig } from '../types/feedback'
import type { PathwayCard } from '../types/session'

type FeedbackQueryScreenProps = {
  form: FeedbackFormConfig | null
  onSkip: () => void
  onTakeSurvey: () => void
  selectedPathway?: PathwayCard | null
}

const fallbackSurveyQuery = 'Would you be happy to answer a few quick questions about your experience?'

export function FeedbackQueryScreen({
  form,
  onSkip,
  onTakeSurvey,
  selectedPathway = null,
}: FeedbackQueryScreenProps) {
  const [isPathwayExpanded, setIsPathwayExpanded] = useState(false)
  const surveyQuery = form?.survey_query?.trim() || fallbackSurveyQuery

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <section
        aria-label="Aether Glimpse survey invitation"
        className="absolute left-[405px] top-[170px] h-[683px] w-[640px]"
      >
        <OnboardingCard className="inset-0" />
        <img
          src={iconAetherCoach}
          alt=""
          aria-hidden="true"
          className="absolute left-1/2 top-[45px] h-[42.53px] w-[42.523px] -translate-x-1/2"
        />

        <h1 className="absolute left-[58px] top-[128px] m-0 w-[524px] text-center text-[35px] font-light leading-[0.98] tracking-[-1.4px] text-[#294744]">
          You&apos;ve surfaced an effective way forward.
        </h1>

        {selectedPathway ? (
          <article
            className={[
              'absolute left-[64px] top-[250px] w-[512px] overflow-hidden rounded-[18px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)] transition-[height] duration-200',
              isPathwayExpanded ? 'h-[170px]' : 'h-[48px]',
            ].join(' ')}
          >
            <button
              type="button"
              aria-expanded={isPathwayExpanded}
              onClick={() => {
                setIsPathwayExpanded((currentValue) => !currentValue)
              }}
              className="relative h-[48px] w-full px-[48px] text-center text-[15px] font-bold leading-none text-[#294744]"
            >
              <span className="block truncate">{selectedPathway.title.toUpperCase()}</span>
              <span className="absolute right-[12px] top-[13px] flex size-[22px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b]">
                <ChevronIcon direction={isPathwayExpanded ? 'up' : 'down'} />
              </span>
            </button>
            {isPathwayExpanded ? (
              <p className="mx-[28px] mt-[12px] max-h-[94px] overflow-auto whitespace-pre-wrap text-center text-[14px] font-light leading-[1.22] tracking-[-0.42px] text-[#294744]">
                {selectedPathway.body || selectedPathway.title}
              </p>
            ) : null}
          </article>
        ) : null}

        <p
          className={[
            'absolute left-[72px] m-0 w-[496px] text-center text-[22px] font-light leading-[1.05] tracking-[-0.88px] text-[#294744]',
            selectedPathway ? 'top-[452px]' : 'top-[330px]',
          ].join(' ')}
        >
          {surveyQuery}
        </p>

        <div className="absolute left-[145px] top-[555px] flex gap-[60px]">
          <OnboardingButton label="Yes, sure" onClick={onTakeSurvey} />
          <OnboardingButton label="No thanks" onClick={onSkip} />
        </div>
      </section>
    </OnboardingFrame>
  )
}
