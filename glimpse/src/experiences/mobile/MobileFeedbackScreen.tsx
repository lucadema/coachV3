import { useState } from 'react'
import {
  MobileButton,
  MobileFrame,
  MobileFullCard,
  MobilePrimaryIcon,
  MobileSelectionDot,
  MobileWatermark,
} from './MobilePrimitives'
import {
  type FeedbackState,
  type ValuableMomentOption,
  valuableMomentOptions,
} from '../../types/feedback'

type MobileFeedbackScreenProps = {
  feedback: FeedbackState
  onChange: (feedback: FeedbackState) => void
  onClose: (feedback: FeedbackState) => void
}

export function MobileFeedbackScreen({
  feedback,
  onChange,
  onClose,
}: MobileFeedbackScreenProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  function setBoolean(name: 'helpedThinkDifferently' | 'organisationalBenefit', value: boolean) {
    onChange({ ...feedback, [name]: value })
  }

  function toggleOption(option: ValuableMomentOption) {
    const isSelected = feedback.valuableMoments.includes(option)
    onChange({
      ...feedback,
      valuableMoments: isSelected
        ? feedback.valuableMoments.filter((selectedOption) => selectedOption !== option)
        : [...feedback.valuableMoments, option],
    })
  }

  return (
    <MobileFrame label="Aether Glimpse mobile survey">
      <MobileWatermark />
      <MobileFullCard>
        <MobilePrimaryIcon variant="aether" />
        <p className="absolute left-[22px] top-[99px] m-0 w-[310px] text-center text-[16px] font-medium leading-none tracking-[-0.64px]">
          Thank you. We’ve now completed the session. You’ve clarified the core tension well, and have several resolution pathways you can action.
        </p>
        <p className="absolute left-[22px] top-[186px] m-0 w-[310px] text-center text-[16px] font-medium leading-none tracking-[-0.64px]">
          Before you go, please tell us what you thought of the Aether Glimpse experience.
        </p>
        <SurveyQuestion
          noLabel="No, Aether did not help me think about my challenge in a new way"
          onNo={() => {
            setBoolean('helpedThinkDifferently', false)
          }}
          onYes={() => {
            setBoolean('helpedThinkDifferently', true)
          }}
          question="Did Aether help you think about your challenge in a new way?"
          top={281}
          value={feedback.helpedThinkDifferently}
          yesLabel="Yes, Aether helped me think about my challenge in a new way"
        />
        <SurveyQuestion
          noLabel="No, I cannot see organisational benefit"
          onNo={() => {
            setBoolean('organisationalBenefit', false)
          }}
          onYes={() => {
            setBoolean('organisationalBenefit', true)
          }}
          question="Can you see how access to this kind of thinking support could be benefical to a whole organisation"
          top={393}
          value={feedback.organisationalBenefit}
          yesLabel="Yes, I can see organisational benefit"
        />
        <p className="absolute left-[22px] top-[489px] m-0 w-[310px] text-center text-[16px] font-light leading-none tracking-[-0.64px]">
          What was the most valuable moment in this session for you?
        </p>
        <div className="absolute left-[7px] top-[543px] w-[340px] rounded-[24px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]">
          <button
            type="button"
            aria-expanded={isDropdownOpen}
            aria-label="Choose all options that apply"
            onClick={() => {
              setIsDropdownOpen((currentValue) => !currentValue)
            }}
            className="relative h-[42px] w-full text-center text-[13px] font-normal leading-none"
          >
            CHOOSE ALL OPTIONS THAT APPLY
            <span className="absolute right-[10px] top-[10px] flex size-[22px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.5)] text-[#75b83b]">
              {isDropdownOpen ? '^' : 'v'}
            </span>
          </button>
          {isDropdownOpen ? (
            <div className="px-[14px] pb-[14px]">
              {valuableMomentOptions.map((option) => {
                const isSelected = feedback.valuableMoments.includes(option)

                return (
                  <button
                    type="button"
                    key={option}
                    aria-pressed={isSelected}
                    onClick={() => {
                      toggleOption(option)
                    }}
                    className="mt-[10px] flex items-center gap-[8px] text-left text-[12px] leading-none"
                  >
                    <MobileSelectionDot selected={isSelected} />
                    <span>{option}</span>
                  </button>
                )
              })}
            </div>
          ) : null}
        </div>
      </MobileFullCard>
      <MobileButton
        label="Close"
        onClick={() => {
          onClose(feedback)
        }}
      />
    </MobileFrame>
  )
}

function SurveyQuestion({
  noLabel,
  onNo,
  onYes,
  question,
  top,
  value,
  yesLabel,
}: {
  noLabel: string
  onNo: () => void
  onYes: () => void
  question: string
  top: number
  value: boolean | null
  yesLabel: string
}) {
  return (
    <fieldset className="absolute left-[22px] m-0 w-[310px] border-0 p-0 text-center" style={{ top }}>
      <legend className="m-0 w-full text-[16px] font-light leading-none tracking-[-0.64px]">
        {question}
      </legend>
      <div className="mt-[13px] flex justify-center gap-[56px] text-[13px]">
        <button type="button" aria-pressed={value === true} aria-label={yesLabel} onClick={onYes} className="flex items-center gap-[8px]">
          <MobileSelectionDot selected={value === true} />
          YES
        </button>
        <button type="button" aria-pressed={value === false} aria-label={noLabel} onClick={onNo} className="flex items-center gap-[8px]">
          <MobileSelectionDot selected={value === false} />
          NO
        </button>
      </div>
    </fieldset>
  )
}
