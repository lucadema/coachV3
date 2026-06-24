import type {
  FeedbackFormConfig,
  FeedbackQuestion,
  FeedbackState,
  FeedbackValue,
} from '../../types/feedback'

type FeedbackFormProps = {
  feedback: FeedbackState
  form: FeedbackFormConfig
  onChange: (feedback: FeedbackState) => void
}

export function FeedbackForm({ feedback, form, onChange }: FeedbackFormProps) {
  function setQuestionValue(questionId: string, value: FeedbackValue) {
    onChange({
      ...feedback,
      [questionId]: value,
    })
  }

  return (
    <div className="feedback-form">
      {(form.questions ?? []).map((question) => (
        <FeedbackQuestionField
          key={question.id}
          onChange={setQuestionValue}
          question={question}
          value={feedback[question.id] ?? null}
        />
      ))}
    </div>
  )
}

function FeedbackQuestionField({
  onChange,
  question,
  value,
}: {
  onChange: (questionId: string, value: FeedbackValue) => void
  question: FeedbackQuestion
  value: FeedbackValue
}) {
  return (
    <fieldset className="feedback-question">
      <legend>
        {question.text}
        {question.required ? <span aria-label="required"> *</span> : null}
      </legend>
      {renderQuestion(question, value, onChange)}
    </fieldset>
  )
}

function renderQuestion(
  question: FeedbackQuestion,
  value: FeedbackValue,
  onChange: (questionId: string, value: FeedbackValue) => void,
) {
  switch (question.type) {
    case 'boolean':
      return (
        <div className="choice-row">
          <button
            className={value === true ? 'choice selected' : 'choice'}
            onClick={() => onChange(question.id, true)}
            type="button"
          >
            {question.true_label ?? 'Yes'}
          </button>
          <button
            className={value === false ? 'choice selected' : 'choice'}
            onClick={() => onChange(question.id, false)}
            type="button"
          >
            {question.false_label ?? 'No'}
          </button>
        </div>
      )
    case 'likert_1_5':
      return (
        <div className="choice-row compact">
          {[1, 2, 3, 4, 5].map((score) => (
            <button
              className={value === score ? 'choice selected' : 'choice'}
              key={score}
              onClick={() => onChange(question.id, score)}
              type="button"
            >
              {score}
            </button>
          ))}
        </div>
      )
    case 'single_select':
      return (
        <div className="choice-stack">
          {(question.options ?? []).map((option) => (
            <button
              className={value === option.value ? 'choice selected' : 'choice'}
              key={option.value}
              onClick={() => onChange(question.id, option.value)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
      )
    case 'multi_select': {
      const selectedValues = Array.isArray(value) ? value : []

      return (
        <div className="choice-stack">
          {(question.options ?? []).map((option) => {
            const selected = selectedValues.includes(option.value)
            return (
              <button
                className={selected ? 'choice selected' : 'choice'}
                key={option.value}
                onClick={() =>
                  onChange(
                    question.id,
                    selected
                      ? selectedValues.filter((item) => item !== option.value)
                      : [...selectedValues, option.value],
                  )
                }
                type="button"
              >
                {option.label}
              </button>
            )
          })}
        </div>
      )
    }
    case 'short_text':
      return (
        <input
          className="text-input"
          onChange={(event) => onChange(question.id, event.target.value)}
          placeholder={question.placeholder ?? ''}
          type="text"
          value={typeof value === 'string' ? value : ''}
        />
      )
    case 'free_text':
      return (
        <textarea
          className="text-area feedback-textarea"
          onChange={(event) => onChange(question.id, event.target.value)}
          placeholder={question.placeholder ?? ''}
          rows={5}
          value={typeof value === 'string' ? value : ''}
        />
      )
    default:
      return null
  }
}
