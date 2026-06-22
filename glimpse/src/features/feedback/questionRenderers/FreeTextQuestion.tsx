import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { QuestionWrapper } from './QuestionWrapper'

export function FreeTextQuestion({
  error = null,
  onChange,
  question,
  value,
}: {
  error?: string | null
  onChange: (questionId: string, value: FeedbackValue) => void
  question: FeedbackQuestion
  value: FeedbackValue
}) {
  return (
    <QuestionWrapper error={error} question={question}>
      <textarea
        value={typeof value === 'string' ? value : ''}
        onChange={(event) => {
          onChange(question.id, event.target.value)
        }}
        className="mt-[13px] min-h-[96px] w-full min-w-0 resize-none rounded-[18px] bg-[rgba(255,255,255,0.65)] px-[16px] py-[12px] text-[14px] text-[#294744] outline-none"
      />
    </QuestionWrapper>
  )
}
