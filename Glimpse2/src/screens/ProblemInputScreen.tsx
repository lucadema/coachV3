import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { ErrorNotice } from '../components/ErrorNotice'
import { PromptForm } from '../components/Field'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function ProblemInputScreen({ flow }: ScreenProps) {
  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      <h2>What would you like to think through?</h2>
      <p>
        A few sentences are enough. Focus on the situation, decision, tension, or work challenge
        that would be useful to clarify.
      </p>
      <PromptForm
        buttonLabel={flow.current.isSubmitting ? 'Sending...' : 'Continue'}
        disabled={flow.navigation.isReviewingHistory || flow.current.isSubmitting}
        onSubmit={flow.submitProblem}
        placeholder="Describe the challenge you want to work through..."
      />
    </div>
  )
}
