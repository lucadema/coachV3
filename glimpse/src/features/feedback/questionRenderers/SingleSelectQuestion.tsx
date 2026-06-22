import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { SelectDropdownQuestion } from './SelectDropdownQuestion'

export function SingleSelectQuestion({
  error = null,
  onChange,
  onExpanded,
  question,
  value,
}: {
  error?: string | null
  onChange: (questionId: string, value: FeedbackValue) => void
  onExpanded?: (questionId: string) => void
  question: FeedbackQuestion
  value: FeedbackValue
}) {
  return (
    <SelectDropdownQuestion
      error={error}
      mode="single"
      onChange={onChange}
      onExpanded={onExpanded}
      question={question}
      value={value}
    />
  )
}
