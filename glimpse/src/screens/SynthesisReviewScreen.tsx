import { useState } from 'react'
import iconAetherCoach from '../assets/onboarding/icon-aether-coach.svg'
import iconUserCloud from '../assets/onboarding/icon-user-cloud.svg'
import { AetherWatermark } from '../components/onboarding/AetherWatermark'
import { OnboardingButton } from '../components/onboarding/OnboardingButton'
import { OnboardingCard } from '../components/onboarding/OnboardingCard'
import { OnboardingFrame } from '../components/onboarding/OnboardingFrame'
import { ProcessingIndicator } from '../components/onboarding/ProcessingIndicator'
import type { SynthesisReviewMode } from '../types/synthesis'

export type { SynthesisReviewMode }

type SynthesisReviewScreenProps = {
  error?: string | null
  isLoading?: boolean
  mode: SynthesisReviewMode
  onAccept: () => void | Promise<void>
  onContinueToPathways: () => void | Promise<void>
  onOpenRefinement: () => void
  onSubmitRefinement: (feedback: string) => void | Promise<void>
  synthesisText: string
}

const reviewIntro =
  'We’ve made considerable progress, and based on the reflective conversation, the challenge you are navigating is:'

function SynthesisCard({
  isCompact = false,
  isLoading,
  mode,
  onAccept,
  onContinueToPathways,
  onOpenRefinement,
  synthesisText,
}: {
  isCompact?: boolean
  isLoading: boolean
  mode: SynthesisReviewMode
  onAccept: () => void | Promise<void>
  onContinueToPathways: () => void | Promise<void>
  onOpenRefinement: () => void
  synthesisText: string
}) {
  const isAwaitingPathways = mode === 'awaiting_pathways_after_refinement'

  return (
    <section
      aria-labelledby="synthesis-review-heading"
      className={[
        'absolute left-[384px] h-[683px] w-[683px]',
        isCompact ? 'top-[-174px]' : 'top-[170px]',
      ].join(' ')}
    >
      <OnboardingCard className="inset-0" />
      <img
        src={iconAetherCoach}
        alt=""
        aria-hidden="true"
        className="absolute left-1/2 top-[45px] h-[42.53px] w-[42.523px] -translate-x-1/2"
      />
      <p
        id="synthesis-review-heading"
        className="absolute left-[42px] top-[120px] m-0 w-[600px] text-center text-[20px] font-light leading-none tracking-[-0.8px] text-[#294744]"
      >
        {reviewIntro}
      </p>
      <div className="absolute left-[42px] top-[214px] max-h-[260px] w-[600px] overflow-x-hidden overflow-y-auto">
        <p className="m-0 whitespace-pre-wrap text-center text-[20px] font-medium leading-[22px] tracking-[-0.8px] text-[#294744]">
          {synthesisText || 'No synthesis is available yet.'}
        </p>
      </div>
      <p className="absolute left-[42px] top-[496px] m-0 w-[600px] text-center text-[20px] font-light leading-none tracking-[-0.8px] text-[#294744]">
        {isAwaitingPathways
          ? 'Your refinement has been applied. Review the updated synthesis and continue to see the pathways.'
          : 'Have we captured this accurately?'}
      </p>
      <div className="absolute left-[151px] top-[602px]">
        <OnboardingButton
          disabled={isLoading}
          label={isAwaitingPathways ? 'Continue to pathways' : "That’s it"}
          onClick={() => {
            void (isAwaitingPathways ? onContinueToPathways() : onAccept())
          }}
          tone={isLoading ? 'outline' : 'filled'}
        />
      </div>
      {isAwaitingPathways ? null : (
        <div className="absolute left-[372px] top-[602px]">
          <OnboardingButton
            disabled={isLoading}
            label="Not quite"
            onClick={onOpenRefinement}
            tone={isLoading ? 'outline' : 'filled'}
          />
        </div>
      )}
    </section>
  )
}

export function SynthesisReviewScreen({
  error = null,
  isLoading = false,
  mode,
  onAccept,
  onContinueToPathways,
  onOpenRefinement,
  onSubmitRefinement,
  synthesisText,
}: SynthesisReviewScreenProps) {
  const [refinementText, setRefinementText] = useState('')
  const trimmedRefinementText = refinementText.trim()
  const canSubmitRefinement = trimmedRefinementText.length > 0 && !isLoading
  const isRefinementOpen = mode === 'refinement_open'

  async function handleSubmitRefinement() {
    if (!canSubmitRefinement) {
      return
    }

    await onSubmitRefinement(trimmedRefinementText)
    setRefinementText('')
  }

  return (
    <OnboardingFrame>
      <AetherWatermark className="absolute left-1/2 top-[4.3%] -translate-x-1/2" />

      <SynthesisCard
        isCompact={isRefinementOpen}
        isLoading={isLoading}
        mode={mode}
        onAccept={onAccept}
        onContinueToPathways={onContinueToPathways}
        onOpenRefinement={onOpenRefinement}
        synthesisText={synthesisText}
      />

      {isRefinementOpen ? (
        <section
          aria-busy={isLoading}
          aria-label="Refinement response card"
          className="absolute left-[384px] top-[515px] h-[338px] w-[683px]"
        >
          <OnboardingCard className="inset-0" />
          <img
            src={iconUserCloud}
            alt=""
            aria-hidden="true"
            className="absolute left-1/2 top-[43px] h-[42.53px] w-[42.523px] -translate-x-1/2"
          />
          <textarea
            aria-label="Refinement feedback"
            autoFocus
            disabled={isLoading}
            value={refinementText}
            onChange={(event) => {
              setRefinementText(event.target.value)
            }}
            placeholder=""
            className="absolute left-[38px] top-[111px] h-[115px] w-[608px] resize-none bg-transparent text-center text-[20px] font-medium leading-[22px] text-[#294744] italic outline-none placeholder:text-[rgba(41,71,68,0.25)] disabled:cursor-wait"
          />
          {isLoading ? (
            <div className="absolute left-[92px] top-[226px] w-[500px]">
              <ProcessingIndicator />
            </div>
          ) : null}
          <div className="absolute left-[255px] top-[263px]">
            <OnboardingButton
              disabled={!canSubmitRefinement}
              label="Continue"
              onClick={() => {
                void handleSubmitRefinement()
              }}
              tone={canSubmitRefinement ? 'filled' : 'outline'}
            />
          </div>
        </section>
      ) : null}

      {error ? (
        <p
          role="alert"
          className="absolute left-[475px] top-[870px] m-0 w-[500px] text-center text-[13px] font-light leading-[1.2] text-[#294744]"
        >
          {error}
        </p>
      ) : null}
    </OnboardingFrame>
  )
}
