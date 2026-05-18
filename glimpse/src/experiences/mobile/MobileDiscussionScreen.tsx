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

type MobileDiscussionScreenProps = {
  coachMessage: string
  error?: string | null
  isLoading?: boolean
  onContinue: (userMessage: string) => void | Promise<void>
}

export function MobileDiscussionScreen({
  coachMessage,
  error = null,
  isLoading = false,
  onContinue,
}: MobileDiscussionScreenProps) {
  const [userMessage, setUserMessage] = useState('')
  const trimmedUserMessage = userMessage.trim()
  const canContinue = trimmedUserMessage.length > 0 && !isLoading

  async function handleContinue() {
    if (!canContinue) {
      return
    }

    await onContinue(trimmedUserMessage)
    setUserMessage('')
  }

  return (
    <MobileFrame label="Aether Glimpse mobile discussion">
      <MobileWatermark />
      <MobileHalfCard top={80}>
        <MobilePrimaryIcon variant="aether" />
        <div className="absolute left-[21px] top-[95px] max-h-[236px] w-[310px] overflow-x-hidden overflow-y-auto">
          <p className="m-0 whitespace-pre-wrap text-center text-[16px] font-light leading-[18px] tracking-[-0.64px]">
            {coachMessage || 'Aether coaching response question here...'}
          </p>
        </div>
      </MobileHalfCard>
      <MobileHalfCard top={451}>
        <MobilePrimaryIcon variant="user" />
        <textarea
          aria-label="Reply to Aether"
          autoFocus
          disabled={isLoading}
          value={userMessage}
          onChange={(event) => {
            setUserMessage(event.target.value)
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
          void handleContinue()
        }}
      />
    </MobileFrame>
  )
}
