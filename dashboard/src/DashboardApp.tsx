import { useEffect, useState } from 'react'
import {
  fetchDashboardData,
  getDashboardToken,
  isDashboardTestMode,
} from './api/dashboardClient'
import { DashboardHeader } from './components/DashboardHeader'
import { EngagementHealthSection } from './components/EngagementHealthSection'
import { ErrorState } from './components/ErrorState'
import { LoadingState } from './components/LoadingState'
import { ProblemCategorySection } from './components/ProblemCategorySection'
import { UnavailableState } from './components/UnavailableState'
import { ValueUnlockedSection } from './components/ValueUnlockedSection'
import { createDashboardTestData } from './testData/dashboardTestData'
import type { DashboardLoadState } from './types'

const TEST_TOKEN_KEY = 'test-dashboard'

export function DashboardApp() {
  const [loadState, setLoadState] = useState<DashboardLoadState>(getInitialLoadState)

  useEffect(() => {
    if (loadState.status !== 'loading') {
      return
    }
    const token = getDashboardToken()
    if (!token) {
      return
    }

    let isMounted = true
    void fetchDashboardData(token)
      .then((data) => {
        if (!isMounted) {
          return
        }

        if (!data.available) {
          setLoadState({ status: 'unavailable' })
          return
        }

        setLoadState({
          status: 'ready',
          data,
          isTestMode: false,
          tokenKey: token,
        })
      })
      .catch(() => {
        if (isMounted) {
          setLoadState({ status: 'error' })
        }
      })

    return () => {
      isMounted = false
    }
  }, [loadState.status])

  if (loadState.status === 'loading') {
    return <LoadingState />
  }

  if (loadState.status === 'error') {
    return <ErrorState />
  }

  if (loadState.status === 'unavailable') {
    return <UnavailableState />
  }

  const { data, isTestMode, tokenKey } = loadState
  const enterpriseName = data.enterprise_name ?? 'Aether Glimpse'
  const pilotName = data.pilot_name ?? 'Pilot dashboard'

  return (
    <main className="dashboard-shell">
      <DashboardHeader
        enterpriseName={enterpriseName}
        isTestMode={isTestMode}
        pilotName={pilotName}
        pilotStatus={data.pilot_status}
      />
      <div className="section-stack">
        <ProblemCategorySection buckets={data.problem_categories} />
        <EngagementHealthSection buckets={data.engagement_signals} />
        <ValueUnlockedSection tokenKey={tokenKey} valueInputs={data.value_unlocked} />
      </div>
    </main>
  )
}

function getInitialLoadState(): DashboardLoadState {
  if (isDashboardTestMode()) {
    return {
      status: 'ready',
      data: createDashboardTestData(),
      isTestMode: true,
      tokenKey: TEST_TOKEN_KEY,
    }
  }

  if (!getDashboardToken()) {
    return { status: 'unavailable' }
  }

  return { status: 'loading' }
}
