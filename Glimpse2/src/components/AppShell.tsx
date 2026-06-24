import type { ReactNode } from 'react'
import { STAGE_DEFINITIONS } from '../flow/stages'
import type { GlimpseExperienceController } from '../session/useGlimpseExperience'
import { Button } from './Button'
import { MessageHistory } from './MessageHistory'
import { ProgressBar } from './ProgressBar'

type AppShellProps = {
  children: ReactNode
  flow: GlimpseExperienceController
}

export function AppShell({ children, flow }: AppShellProps) {
  const { current, navigation } = flow
  const definition = STAGE_DEFINITIONS[current.step]

  return (
    <div className="app-background">
      <div className="app-shell">
        <header className="topbar">
          <div className="brand-mark">
            <img alt="" src="/aether-logo.png" />
          </div>
          <div className="history-nav" aria-label="History navigation">
            <Button
              aria-label="Go back"
              disabled={!navigation.canGoBack}
              onClick={flow.goBack}
              variant="quiet"
            >
              Back
            </Button>
            <span className="history-count">
              {navigation.currentIndex + 1}/{navigation.total}
            </span>
            <Button
              aria-label="Go forward"
              disabled={!navigation.canGoForward}
              onClick={flow.goForward}
              variant="quiet"
            >
              Forward
            </Button>
          </div>
        </header>

        <ProgressBar step={current.step} />

        {navigation.isReviewingHistory ? (
          <div className="history-review-banner" role="status">
            <span>You are reviewing an earlier point in this session.</span>
            <Button onClick={flow.returnToLatest} variant="secondary">
              Return to latest
            </Button>
          </div>
        ) : null}

        <main className="workspace">
          <section className="stage-panel" aria-labelledby="stage-title">
            <div className="stage-heading">
              <p className="stage-phase">{definition.phase}</p>
              <h1 id="stage-title">{definition.label}</h1>
            </div>
            {children}
          </section>
          <MessageHistory exchanges={current.exchanges} />
        </main>
      </div>
    </div>
  )
}
