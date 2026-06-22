import { useState } from 'react'
import { ChevronIcon } from '../../components/onboarding/UiIcons'
import type { FeedbackFormConfig } from '../../types/feedback'
import type { PathwayCard } from '../../types/session'
import {
  MobileButton,
  MobileFrame,
  MobileFullCard,
  MobilePrimaryIcon,
  MobileWatermark,
} from './MobilePrimitives'

type MobileFeedbackQueryScreenProps = {
  form: FeedbackFormConfig | null
  onSkip: () => void
  onTakeSurvey: () => void
  selectedPathway?: PathwayCard | null
}

const fallbackSurveyQuery = 'Would you be happy to answer a few quick questions about your experience?'

export function MobileFeedbackQueryScreen({
  form,
  onSkip,
  onTakeSurvey,
  selectedPathway = null,
}: MobileFeedbackQueryScreenProps) {
  const [isPathwayExpanded, setIsPathwayExpanded] = useState(false)
  const surveyQuery = form?.survey_query?.trim() || fallbackSurveyQuery

  return (
    <MobileFrame label="Aether Glimpse mobile survey invitation">
      <MobileWatermark />
      <MobileFullCard>
        <MobilePrimaryIcon variant="aether" />
        <h1 className="absolute inset-x-[22px] top-[110px] m-0 text-center text-[29px] font-light leading-[0.98] tracking-[-1.16px] break-words">
          You&apos;ve surfaced an effective way forward.
        </h1>

        {selectedPathway ? (
          <article
            className={[
              'absolute inset-x-[22px] top-[250px] overflow-hidden rounded-[24px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)] transition-[height] duration-200',
              isPathwayExpanded ? 'h-[188px]' : 'h-[54px]',
            ].join(' ')}
          >
            <button
              type="button"
              aria-expanded={isPathwayExpanded}
              onClick={() => {
                setIsPathwayExpanded((currentValue) => !currentValue)
              }}
              className="relative h-[54px] w-full min-w-0 px-[42px] text-center text-[14px] font-bold leading-none"
            >
              <span className="block truncate">{selectedPathway.title.toUpperCase()}</span>
              <span className="absolute right-[12px] top-[15px] flex size-[24px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b]">
                <ChevronIcon direction={isPathwayExpanded ? 'up' : 'down'} />
              </span>
            </button>
            {isPathwayExpanded ? (
              <p className="mx-[18px] mt-[12px] max-h-[108px] overflow-x-hidden overflow-y-auto whitespace-pre-wrap break-words text-center text-[12px] font-light leading-[1.22] tracking-[-0.36px]">
                {selectedPathway.body || selectedPathway.title}
              </p>
            ) : null}
          </article>
        ) : null}

        <p
          className={[
            'absolute inset-x-[36px] m-0 text-center text-[18px] font-light leading-[1.08] tracking-[-0.72px] break-words',
            selectedPathway ? 'top-[500px]' : 'top-[355px]',
          ].join(' ')}
        >
          {surveyQuery}
        </p>
      </MobileFullCard>

      <div className="absolute inset-x-[40px] top-[702px]">
        <MobileButton label="Yes, sure" onClick={onTakeSurvey} top={0} />
        <MobileButton label="No thanks" onClick={onSkip} top={60} />
      </div>
    </MobileFrame>
  )
}
