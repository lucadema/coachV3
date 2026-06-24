import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from '../components/Button'
import { ErrorNotice } from '../components/ErrorNotice'
import { MarkdownText } from '../components/MarkdownText'

type ScreenProps = {
  flow: GlimpseExperienceController
}

export function PathwaysScreen({ flow }: ScreenProps) {
  const disabled = flow.navigation.isReviewingHistory || flow.current.isSubmitting

  return (
    <div className="screen-copy">
      <ErrorNotice message={flow.current.frontendError} />
      {flow.pathways.length > 0 ? (
        <div className="pathway-grid">
          {flow.pathways.map((pathway) => {
            const selected = flow.current.selectedPathwayTitle === pathway.title
            return (
              <button
                className={selected ? 'pathway-card selected' : 'pathway-card'}
                disabled={disabled}
                key={pathway.title}
                onClick={() => flow.setSelectedPathway(pathway)}
                type="button"
              >
                <span>{pathway.title}</span>
                <MarkdownText text={pathway.body} />
              </button>
            )
          })}
        </div>
      ) : (
        <div className="coach-card">
          <MarkdownText text={flow.pathwaysText} />
        </div>
      )}
      <div className="split-actions">
        <Button disabled={disabled} onClick={flow.completePathways}>
          {flow.current.isSubmitting ? 'Closing...' : 'Continue'}
        </Button>
        <Button disabled={disabled} onClick={flow.downloadPdf} variant="secondary">
          Download PDF
        </Button>
      </div>
    </div>
  )
}
