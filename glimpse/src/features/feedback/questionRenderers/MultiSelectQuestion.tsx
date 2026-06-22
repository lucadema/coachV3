import type { FeedbackQuestion, FeedbackValue } from '../../../types/feedback'
import { SelectDropdownQuestion } from './SelectDropdownQuestion'

type MultiSelectQuestionProps = {
  error?: string | null
  onChange: (questionId: string, value: FeedbackValue) => void
  onExpanded?: (questionId: string) => void
  question: FeedbackQuestion
  value: FeedbackValue
}

export function MultiSelectQuestion({
  error = null,
  onChange,
  onExpanded,
  question,
  value,
}: MultiSelectQuestionProps) {
  return (
    <SelectDropdownQuestion
      error={error}
      mode="multi"
      onChange={onChange}
      onExpanded={onExpanded}
      question={question}
      value={value}
    />
  )
}
