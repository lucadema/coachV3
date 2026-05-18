import { useState } from 'react'
import {
  MobileButton,
  MobileError,
  MobileFrame,
  MobileHalfCard,
  MobilePrimaryIcon,
  MobileWatermark,
} from './MobilePrimitives'
import { ProcessingIndicator } from '../../components/onboarding/ProcessingIndicator'

type MobileProblemInputScreenProps = {
  error?: string | null
  isLoading?: boolean
  onContinue: (problemText: string) => void | Promise<void>
}

const problemPrompt =
  'Let’s think this through together.\nIn the field below, describe a\nprofessional challenge, or unresolved\nissue you are currently facing.'

export function MobileProblemInputScreen({
  error = null,
  isLoading = false,
  onContinue,
}: MobileProblemInputScreenProps) {
  const [problemText, setProblemText] = useState('')
  const trimmedProblemText = problemText.trim()
  const canContinue = trimmedProblemText.length > 0 && !isLoading

  return (
    <MobileFrame label="Aether Glimpse mobile problem input">
      <MobileWatermark />
      <MobileHalfCard top={80}>
        <MobilePrimaryIcon variant="aether" />
        <p className="absolute left-[21px] top-[93px] m-0 w-[310px] whitespace-pre-line text-center text-[16px] font-light leading-none tracking-[-0.64px]">
          {problemPrompt}
        </p>
      </MobileHalfCard>
      <MobileHalfCard top={451}>
        <MobilePrimaryIcon variant="user" />
        <textarea
          aria-label="Describe your professional challenge"
          autoFocus
          disabled={isLoading}
          value={problemText}
          onChange={(event) => {
            setProblemText(event.target.value)
          }}
          placeholder=""
          className="absolute left-[21px] top-[95px] h-[200px] w-[310px] resize-none bg-transparent text-center text-[16px] font-medium italic leading-[21px] text-[#294744] outline-none placeholder:text-[#294744] disabled:cursor-wait"
        />
        {isLoading ? (
          <div className="absolute left-[27px] top-[298px] w-[300px]">
            <ProcessingIndicator />
          </div>
        ) : null}
      </MobileHalfCard>
      <MobileError>{error}</MobileError>
      <MobileButton
        disabled={!canContinue}
        label="Continue"
        onClick={() => {
          void onContinue(trimmedProblemText)
        }}
      />
    </MobileFrame>
  )
}
