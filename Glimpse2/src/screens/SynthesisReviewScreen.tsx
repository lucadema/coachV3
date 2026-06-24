import { useState } from 'react'
import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'
import { ErrorNotice } from '../components/ErrorNotice'
import { MarkdownText } from '../components/MarkdownText'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function SynthesisReviewScreen({ flow }: ScreenProps) {
  const [feedbackText, setFeedbackText] = useState('')
  const disabled = flow.navigation.isReviewingHistory || flow.current.isSubmitting
  const mode = flow.current.synthesisMode

  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      <div className="coach-card synthesis-card">
        <MarkdownText text={flow.current.coachMessage} />
      </div>

      {mode === 'awaiting_pathways_after_refinement' ? (
        <div className="action-cluster">
          <p className="muted-copy">The synthesis has been updated.</p>
          <Button disabled={disabled} onClick={flow.continueToPathways}>
            {flow.current.isSubmitting ? 'Preparing...' : 'Continue to pathways'}
          </Button>
        </div>
      ) : null}

      {mode === 'refinement_open' ? (
        <form
          className="prompt-form"
          onSubmit={(event) => {
            event.preventDefault()
            flow.submitSynthesisRefinement(feedbackText)
          }}
        >
          <textarea
            className="text-area"
            disabled={disabled}
            onChange={(event) => setFeedbackText(event.target.value)}
            placeholder="What should be adjusted in this synthesis?"
            rows={5}
            value={feedbackText}
          />
          <div className="form-actions">
            <Button disabled={disabled || !feedbackText.trim()} type="submit">
              {flow.current.isSubmitting ? 'Updating...' : 'Submit refinement'}
            </Button>
          </div>
        </form>
      ) : null}

      {mode === 'review' ? (
        <div className="split-actions">
          <Button disabled={disabled} onClick={flow.acceptSynthesis}>
            {flow.current.isSubmitting ? 'Continuing...' : 'Accept synthesis'}
          </Button>
          <Button disabled={disabled} onClick={flow.openSynthesisRefinement} variant="secondary">
            Refine it
          </Button>
        </div>
      ) : null}
    </div>
  )
}
