import { useState } from 'react'
import { ChevronIcon } from '../../../components/onboarding/UiIcons'
import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { QuestionWrapper } from './QuestionWrapper'
import { SelectionDot } from './SelectionDot'

type SelectDropdownQuestionProps = {
  error?: string | null
  mode: 'single' | 'multi'
  onChange: (questionId: string, value: FeedbackValue) => void
  onExpanded?: (questionId: string) => void
  question: FeedbackQuestion
  value: FeedbackValue
}

export function SelectDropdownQuestion({
  error = null,
  mode,
  onChange,
  onExpanded,
  question,
  value,
}: SelectDropdownQuestionProps) {
  const [isOpen, setIsOpen] = useState(false)
  const options = question.options ?? []
  const selectedValues =
    mode === 'multi'
      ? Array.isArray(value)
        ? value
        : []
      : typeof value === 'string'
        ? [value]
        : []
  const selectedOption = options.find((option) => option.value === selectedValues[0])
  const placeholder =
    question.placeholder ??
    (mode === 'multi' ? 'CHOOSE ALL OPTIONS THAT APPLY' : 'CHOOSE AN OPTION')
  const buttonLabel = mode === 'single' && selectedOption ? selectedOption.label : placeholder

  function handleOptionClick(optionValue: string) {
    if (mode === 'single') {
      onChange(question.id, optionValue)
      setIsOpen(false)
      return
    }

    const isSelected = selectedValues.includes(optionValue)
    onChange(
      question.id,
      isSelected
        ? selectedValues.filter((selectedValue) => selectedValue !== optionValue)
        : [...selectedValues, optionValue],
    )
  }

  return (
    <QuestionWrapper error={error} question={question}>
      <div
        className={[
          'mx-auto mt-[13px] w-[512px] max-w-full min-w-0 overflow-hidden rounded-[18px] bg-[linear-gradient(90deg,rgba(219,236,3,0.12)_0%,rgba(117,184,59,0.12)_100%)]',
          isOpen ? 'h-[174px] max-[767px]:h-[218px]' : 'h-[42px]',
        ].join(' ')}
      >
        <button
          type="button"
          aria-expanded={isOpen}
          aria-label={placeholder}
          onClick={() => {
            setIsOpen((currentValue) => {
              const nextValue = !currentValue

              if (nextValue) {
                onExpanded?.(question.id)
              }

              return nextValue
            })
          }}
          className="relative h-[42px] w-full px-[42px] text-center text-[14px] font-normal leading-none text-[#294744] max-[767px]:text-[13px]"
        >
          <span className="block truncate">{buttonLabel}</span>
          <span className="absolute right-[8px] top-[10px] flex size-[22px] items-center justify-center rounded-[8px] bg-[rgba(255,255,255,0.65)] text-[#75b83b]">
            <ChevronIcon direction={isOpen ? 'up' : 'down'} />
          </span>
        </button>

        {isOpen ? (
          <div className="max-h-[116px] overflow-x-hidden overflow-y-auto px-[14px] pb-[10px] pr-[22px] max-[767px]:max-h-[160px]">
            {options.map((option) => {
              const isSelected = selectedValues.includes(option.value)

              return (
                <button
                  type="button"
                  key={option.value}
                  aria-pressed={isSelected}
                  onClick={() => {
                    handleOptionClick(option.value)
                  }}
                  className="mt-[8px] flex w-full min-w-0 items-start gap-[8px] text-left text-[13px] font-normal leading-none text-[#294744] max-[767px]:text-[11px] max-[767px]:leading-tight"
                >
                  <SelectionDot selected={isSelected} />
                  <span className="min-w-0 flex-1 break-words">{option.label}</span>
                </button>
              )
            })}
          </div>
        ) : null}
      </div>
    </QuestionWrapper>
  )
}
