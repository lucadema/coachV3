import { PROGRESS_MILESTONES, STAGE_DEFINITIONS } from '../flow/stages'
import type { ExperienceStep } from '../types/session'

type ProgressBarProps = {
  step: ExperienceStep
}

export function ProgressBar({ step }: ProgressBarProps) {
  const definition = STAGE_DEFINITIONS[step]

  return (
    <div className="progress-shell" aria-label="Experience progress">
      <div className="progress-topline">
        <span>{definition.label}</span>
        <span>{definition.progress}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${definition.progress}%` }} />
      </div>
      <div className="progress-milestones" aria-hidden="true">
        {PROGRESS_MILESTONES.map((milestone) => (
          <span
            className={
              STAGE_DEFINITIONS[milestone].progress <= definition.progress ? 'is-reached' : ''
            }
            key={milestone}
          />
        ))}
      </div>
    </div>
  )
}
