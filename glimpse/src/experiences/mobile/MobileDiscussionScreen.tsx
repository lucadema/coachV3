import { useState } from 'react'
import {
  MobileButton,
  MobileError,
  MobileFrame,
  MobileHalfCard,
  MobilePrimaryIcon,
  MobileWatermark,
} from './MobilePrimitives'

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
        <div className="absolute left-[21px] top-[95px] max-h-[226px] w-[310px] overflow-auto">
          <p className="m-0 whitespace-pre-wrap text-center text-[16px] font-light leading-none tracking-[-0.64px]">
            {coachMessage || 'Aether coaching response question here...'}
          </p>
        </div>
      </MobileHalfCard>
      <MobileHalfCard top={455}>
        <MobilePrimaryIcon variant="user" />
        <textarea
          aria-label="Reply to Aether"
          disabled={isLoading}
          value={userMessage}
          onChange={(event) => {
            setUserMessage(event.target.value)
          }}
          placeholder="Your response here..."
          className="absolute left-[21px] top-[95px] h-[200px] w-[310px] resize-none bg-transparent text-center text-[16px] font-medium italic leading-[21px] text-[#294744] outline-none placeholder:text-[#294744] disabled:cursor-wait"
        />
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
