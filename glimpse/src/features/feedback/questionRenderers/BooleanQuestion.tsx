import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { QuestionWrapper } from './QuestionWrapper'
import { SelectionDot } from './SelectionDot'

type BooleanQuestionProps = {
  error?: string | null
  onChange: (questionId: string, value: FeedbackValue) => void
  question: FeedbackQuestion
  value: FeedbackValue
}

export function BooleanQuestion({
  error = null,
  onChange,
  question,
  value,
}: BooleanQuestionProps) {
  return (
    <QuestionWrapper error={error} question={question}>
      <div className="mt-[13px] flex justify-center gap-[50px] max-[767px]:gap-[48px]">
        <button
          type="button"
          aria-pressed={value === true}
          aria-label={`Yes, ${question.text}`}
          onClick={() => {
            onChange(question.id, true)
          }}
          className="flex items-center gap-[8px] text-[14px] font-normal leading-none text-[#294744] max-[767px]:text-[13px]"
        >
          <SelectionDot selected={value === true} />
          YES
        </button>
        <button
          type="button"
          aria-pressed={value === false}
          aria-label={`No, ${question.text}`}
          onClick={() => {
            onChange(question.id, false)
          }}
          className="flex items-center gap-[8px] text-[14px] font-normal leading-none text-[#294744] max-[767px]:text-[13px]"
        >
          <SelectionDot selected={value === false} />
          NO
        </button>
      </div>
    </QuestionWrapper>
  )
}
