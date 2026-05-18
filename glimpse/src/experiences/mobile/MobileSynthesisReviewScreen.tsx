import { useState } from 'react'
import type { SynthesisReviewMode } from '../../types/synthesis'
import {
  MobileButton,
  MobileError,
  MobileFrame,
  MobileFullCard,
  MobileHalfCard,
  MobilePrimaryIcon,
  MobileWatermark,
} from './MobilePrimitives'
import { ProcessingIndicator } from '../../components/onboarding/ProcessingIndicator'

type MobileSynthesisReviewScreenProps = {
  error?: string | null
  isLoading?: boolean
  mode: SynthesisReviewMode
  onAccept: () => void | Promise<void>
  onContinueToPathways: () => void | Promise<void>
  onOpenRefinement: () => void
  onSubmitRefinement: (feedback: string) => void | Promise<void>
  synthesisText: string
}

export function MobileSynthesisReviewScreen({
  error = null,
  isLoading = false,
  mode,
  onAccept,
  onContinueToPathways,
  onOpenRefinement,
  onSubmitRefinement,
  synthesisText,
}: MobileSynthesisReviewScreenProps) {
  const [refinementText, setRefinementText] = useState('')
  const trimmedRefinementText = refinementText.trim()
  const canSubmitRefinement = trimmedRefinementText.length > 0 && !isLoading
  const isRefinementOpen = mode === 'refinement_open'
  const isAwaitingPathways = mode === 'awaiting_pathways_after_refinement'

  async function handleSubmitRefinement() {
    if (!canSubmitRefinement) {
      return
    }

    await onSubmitRefinement(trimmedRefinementText)
    setRefinementText('')
  }

  return (
    <MobileFrame label="Aether Glimpse mobile problem statement">
      <MobileWatermark />
      <MobileFullCard>
        <MobilePrimaryIcon variant="aether" />
        <p className="absolute left-[21px] top-[99px] m-0 w-[310px] text-center text-[16px] font-light leading-none tracking-[-0.64px]">
          We’ve made considerable progress, and based on the reflective conversation, the challenge you are navigating is:
        </p>
        <div className="absolute left-[21px] top-[205px] max-h-[275px] w-[310px] overflow-auto">
          <p className="m-0 whitespace-pre-wrap text-center text-[16px] font-medium leading-none tracking-[-0.64px]">
            {synthesisText || 'No synthesis is available yet.'}
          </p>
        </div>
        <p className="absolute left-[21px] top-[579px] m-0 w-[310px] text-center text-[16px] font-light leading-none tracking-[-0.64px]">
          {isAwaitingPathways
            ? 'Your refinement has been applied. Continue to see the pathways.'
            : 'Have we captured this accurately?'}
        </p>
      </MobileFullCard>
      {isRefinementOpen ? null : (
        <>
          <MobileButton
            disabled={isLoading}
            label={isAwaitingPathways ? 'Continue' : "That's it"}
            onClick={() => {
              void (isAwaitingPathways ? onContinueToPathways() : onAccept())
            }}
            top={698}
          />
          {isAwaitingPathways ? null : (
            <MobileButton
              disabled={isLoading}
              label="Not quite"
              onClick={onOpenRefinement}
              top={762}
            />
          )}
        </>
      )}

      {isRefinementOpen ? (
        <>
          <MobileHalfCard top={451}>
            <MobilePrimaryIcon variant="user" />
            <textarea
              aria-label="Refinement feedback"
              autoFocus
              disabled={isLoading}
              value={refinementText}
              onChange={(event) => {
                setRefinementText(event.target.value)
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
          <MobileButton
            disabled={!canSubmitRefinement}
            label="Continue"
            onClick={() => {
              void handleSubmitRefinement()
            }}
          />
        </>
      ) : null}
      <MobileError>{error}</MobileError>
    </MobileFrame>
  )
}
