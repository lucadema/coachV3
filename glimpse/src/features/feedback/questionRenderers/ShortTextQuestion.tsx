import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { QuestionWrapper } from './QuestionWrapper'

export function ShortTextQuestion({
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
      <input
        value={typeof value === 'string' ? value : ''}
        onChange={(event) => {
          onChange(question.id, event.target.value)
        }}
        className="mt-[13px] h-[42px] w-full min-w-0 rounded-[18px] bg-[rgba(255,255,255,0.65)] px-[16px] text-[14px] text-[#294744] outline-none"
      />
    </QuestionWrapper>
  )
}
