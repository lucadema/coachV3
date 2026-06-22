import type { PilotStatus } from '../types'

type DashboardHeaderProps = {
  enterpriseName: string
  pilotName: string
  pilotStatus: PilotStatus | null
  isTestMode: boolean
}

export function DashboardHeader({
  enterpriseName,
  pilotName,
  pilotStatus,
  isTestMode,
}: DashboardHeaderProps) {
  return (
    <header className="dashboard-header">
      <div>
        <p className="eyebrow">Aether Glimpse pilot dashboard</p>
        <h1>{enterpriseName}</h1>
        <p className="pilot-name">{pilotName}</p>
      </div>
      <div className="header-badges">
        {pilotStatus ? <span className={`status status-${pilotStatus}`}>{pilotStatus}</span> : null}
        {isTestMode ? <span className="test-badge">Test data</span> : null}
      </div>
    </header>
  )
}
