import { useRef } from 'react'
import type {
  FeedbackFormConfig,
  FeedbackQuestion,
  FeedbackState,
  FeedbackValue,
} from '../../types/feedback'
import { BooleanQuestion } from './questionRenderers/BooleanQuestion'
import { FreeTextQuestion } from './questionRenderers/FreeTextQuestion'
import { LikertQuestion } from './questionRenderers/LikertQuestion'
import { MultiSelectQuestion } from './questionRenderers/MultiSelectQuestion'
import { ShortTextQuestion } from './questionRenderers/ShortTextQuestion'
import { SingleSelectQuestion } from './questionRenderers/SingleSelectQuestion'

type FeedbackFormProps = {
  feedback: FeedbackState
  form: FeedbackFormConfig
  onChange: (feedback: FeedbackState) => void
  onQuestionExpanded?: (questionElement: HTMLDivElement | null) => void
}

export function FeedbackForm({
  feedback,
  form,
  onChange,
  onQuestionExpanded,
}: FeedbackFormProps) {
  const questionRefs = useRef<Record<string, HTMLDivElement | null>>({})

  function setQuestionValue(questionId: string, value: FeedbackValue) {
    onChange({
      ...feedback,
      [questionId]: value,
    })
  }

  function handleQuestionExpanded(questionId: string) {
    onQuestionExpanded?.(questionRefs.current[questionId] ?? null)
  }

  return (
    <>
      {(form.questions ?? []).map((question) => (
        <div
          key={question.id}
          ref={(element) => {
            questionRefs.current[question.id] = element
          }}
          className="feedback-question"
        >
          {renderQuestion(
            question,
            feedback[question.id] ?? null,
            setQuestionValue,
            handleQuestionExpanded,
          )}
        </div>
      ))}
    </>
  )
}

function renderQuestion(
  question: FeedbackQuestion,
  value: FeedbackValue,
  onChange: (questionId: string, value: FeedbackValue) => void,
  onQuestionExpanded: (questionId: string) => void,
) {
  switch (question.type) {
    case 'boolean':
      return <BooleanQuestion onChange={onChange} question={question} value={value} />
    case 'likert_1_5':
      return <LikertQuestion onChange={onChange} question={question} value={value} />
    case 'single_select':
      return (
        <SingleSelectQuestion
          onChange={onChange}
          onExpanded={onQuestionExpanded}
          question={question}
          value={value}
        />
      )
    case 'multi_select':
      return (
        <MultiSelectQuestion
          onChange={onChange}
          onExpanded={onQuestionExpanded}
          question={question}
          value={value}
        />
      )
    case 'short_text':
      return <ShortTextQuestion onChange={onChange} question={question} value={value} />
    case 'free_text':
      return <FreeTextQuestion onChange={onChange} question={question} value={value} />
    default:
      return null
  }
}
