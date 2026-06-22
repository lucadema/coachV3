import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { QuestionWrapper } from './QuestionWrapper'

export function LikertQuestion({
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
      <div className="mt-[13px] flex justify-center gap-[10px]">
        {[1, 2, 3, 4, 5].map((rating) => (
          <button
            type="button"
            key={rating}
            aria-pressed={value === rating}
            onClick={() => {
              onChange(question.id, rating)
            }}
            className={[
              'size-[36px] rounded-full text-[14px] text-[#294744]',
              value === rating
                ? 'bg-[linear-gradient(180deg,#dbec03_0%,#75b83b_100%)]'
                : 'bg-[rgba(255,255,255,0.65)]',
            ].join(' ')}
          >
            {rating}
          </button>
        ))}
      </div>
    </QuestionWrapper>
  )
}
