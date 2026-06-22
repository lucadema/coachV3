import type { ReactNode } from 'react'
import type { FeedbackQuestion } from '../../../types/feedback'

type QuestionWrapperProps = {
  children: ReactNode
  className?: string
  error?: string | null
  question: FeedbackQuestion
}

export function QuestionWrapper({
  children,
  className = '',
  error = null,
  question,
}: QuestionWrapperProps) {
  return (
    <fieldset className={['m-0 min-w-0 border-0 p-0 text-center', className].join(' ')}>
      <legend className="m-0 w-full min-w-0 break-words text-center text-[18px] font-light leading-none tracking-[-0.72px] text-[#294744] max-[767px]:text-[16px] max-[767px]:leading-[1.05] max-[767px]:tracking-[-0.64px]">
        {question.text}
      </legend>
      {children}
      {error ? (
        <p role="alert" className="mt-[10px] text-[13px] font-light leading-[1.2] text-[#294744]">
          {error}
        </p>
      ) : null}
    </fieldset>
  )
}
