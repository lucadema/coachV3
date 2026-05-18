import { useState } from 'react'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import { ChevronIcon } from '../components/onboarding/UiIcons'
import {
  type FeedbackState,
  type ValuableMomentOption,
  valuableMomentOptions,
} from '../types/feedback'

type FeedbackScreenProps = {
  error?: string | null
  feedback: FeedbackState
  onChange: (feedback: FeedbackState) => void
  onClose: (feedback: FeedbackState) => void
}

type YesNoQuestionProps = {
  name: keyof Pick<FeedbackState, 'helpedThinkDifferently' | 'organisationalBenefit'>
  onChange: (feedback: FeedbackState) => void
  question: string
  value: FeedbackState
  yesLabel: string
  noLabel: string
}

function SelectionDot({ selected }: { selected: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={[
        'inline-block size-[18px] shrink-0 rounded-full border-[1.5px] border-[#75b83b] bg-white shadow-[0_0_0_2px_rgba(255,255,255,0.65)]',
        selected ? 'bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]' : 'bg-white',
      ].join(' ')}
    />
  )
}

function YesNoQuestion({
  name,
  noLabel,
  onChange,
  question,
  value,
  yesLabel,
}: YesNoQuestionProps) {
  function setValue(nextValue: boolean) {
    onChange({
      ...value,
      [name]: nextValue,
    })
  }

  return (
    <fieldset className="m-0 border-0 p-0 text-center">
      <legend className="m-0 w-full text-center text-[18px] font-light leading-none tracking-[-0.72px] text-[#294744]">
        {question}
      </legend>
      <div className="mt-[13px] flex justify-center gap-[50px]">
        <button
          type="button"
          aria-pressed={value[name] === true}
          aria-label={yesLabel}
          onClick={() => {
            setValue(true)
          }}
          className="flex items-center gap-[8px] text-[14px] font-normal leading-none text-[#294744]"
        >
          <SelectionDot selected={value[name] === true} />
          YES
        </button>
        <button
          type="button"
          aria-pressed={value[name] === false}
          aria-label={noLabel}
          onClick={() => {
            setValue(false)
          }}
          className="flex items-center gap-[8px] text-[14px] font-normal leading-none text-[#294744]"
        >
          <SelectionDot selected={value[name] === false} />
          NO
        </button>
      </div>
    </fieldset>
  )
}

function ValuableMomentsDropdown({
  feedback,
  isOpen,
  onChange,
  onToggle,
}: {
  feedback: FeedbackState
  isOpen: boolean
  onChange: (feedback: FeedbackState) => void
  onToggle: () => void
}) {
  function toggleOption(option: ValuableMomentOption) {
    const isSelected = feedback.valuableMoments.includes(option)
    const valuableMoments = isSelected
      ? feedback.valuableMoments.filter((selectedOption) => selectedOption !== option)
      : [...feedback.valuableMoments, option]

    onChange({
      ...feedback,
      valuableMoments,
    })
  }

  return (
    <div
      className={[
        'absolute left-[64px] top-[452px] w-[512px] overflow-hidden rounded-[18px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]',
        isOpen ? 'h-[154px]' : 'h-[42px]',
      ].join(' ')}
    >
      <button
        type="button"
        aria-expanded={isOpen}
        aria-label="Choose all options that apply"
        onClick={onToggle}
        className="relative h-[42px] w-full text-center text-[14px] font-normal leading-none text-[#294744]"
      >
        CHOOSE ALL OPTIONS THAT APPLY
        <span className="absolute right-[8px] top-[10px] flex size-[22px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b]">
          <ChevronIcon direction={isOpen ? 'up' : 'down'} />
        </span>
      </button>

      {isOpen ? (
        <div className="absolute left-[14px] top-[52px] flex max-h-[92px] w-[484px] flex-col gap-[8px] overflow-y-auto pr-[8px]">
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
                className="flex items-center gap-[8px] text-left text-[13px] font-normal leading-none text-[#294744]"
              >
                <SelectionDot selected={isSelected} />
                <span>{option}</span>
              </button>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}

export function FeedbackScreen({
  error = null,
  feedback,
  onChange,
  onClose,
}: FeedbackScreenProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <section
        aria-label="Aether Glimpse feedback survey"
        className="absolute left-[405px] top-[150px] h-[718px] w-[640px]"
      >
        <OnboardingCard className="inset-0" />
        <h1 className="absolute left-[20px] top-[38px] m-0 w-[600px] text-center text-[29px] font-light leading-none tracking-[-1.16px] text-[#294744]">
          Before you go, please tell us what you thought of the Aether Glimpse experience.
        </h1>

        <div className="absolute left-[20px] top-[163px] w-[600px]">
          <YesNoQuestion
            name="helpedThinkDifferently"
            noLabel="No, Aether did not help me think about my challenge in a new way"
            onChange={onChange}
            question="Did Aether help you think about your challenge in a new way?"
            value={feedback}
            yesLabel="Yes, Aether helped me think about my challenge in a new way"
          />
        </div>

        <div className="absolute left-[20px] top-[290px] w-[600px]">
          <YesNoQuestion
            name="organisationalBenefit"
            noLabel="No, I cannot see organisational benefit"
            onChange={onChange}
            question="Can you see how access to this kind of thinking support could be benefical to a whole organisation"
            value={feedback}
            yesLabel="Yes, I can see organisational benefit"
          />
        </div>

        <p className="absolute left-[20px] top-[414px] m-0 w-[600px] text-center text-[18px] font-light leading-none tracking-[-0.72px] text-[#294744]">
          What was the most valuable moment in this session for you?
        </p>

        <ValuableMomentsDropdown
          feedback={feedback}
          isOpen={isDropdownOpen}
          onChange={onChange}
          onToggle={() => {
            setIsDropdownOpen((currentValue) => !currentValue)
          }}
        />

        {error ? (
          <p
            role="alert"
            className="absolute left-[70px] top-[662px] m-0 w-[500px] text-center text-[13px] font-light leading-[1.2] text-[#294744]"
          >
            {error}
          </p>
        ) : null}

        <div className="absolute left-[235px] top-[636px]">
          <OnboardingButton
            label="Close"
            onClick={() => {
              onClose(feedback)
            }}
          />
        </div>
      </section>
    </OnboardingFrame>
  )
}
