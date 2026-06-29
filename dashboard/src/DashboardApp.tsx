import { useEffect, useState } from 'react'
import {
  buildRedactedDashboardApiUrl,
  DashboardApiError,
  fetchDashboardData,
  getDashboardApiBaseUrl,
  getDashboardTestOptions,
  getDashboardToken,
  isDashboardDebugMode,
  isDashboardTestMode,
  redactDashboardToken,
} from './api/dashboardClient'
import { ActionOwnershipSection } from './components/ActionOwnershipSection'
import { DashboardDebugPanel } from './components/DashboardDebugPanel'
import { DashboardHeader } from './components/DashboardHeader'
import { EngagementHealthSection } from './components/EngagementHealthSection'
import { ErrorState } from './components/ErrorState'
import { LoadingState } from './components/LoadingState'
import { ProblemCategorySection } from './components/ProblemCategorySection'
import { StuckSignalSection } from './components/StuckSignalSection'
import { UnavailableState } from './components/UnavailableState'
import { ValueUnlockedSection } from './components/ValueUnlockedSection'
import { createDashboardTestData } from './testData/dashboardTestData'
import type { DashboardLoadState } from './types'

const TEST_TOKEN_KEY = 'test-dashboard'

export function DashboardApp() {
  const [loadState, setLoadState] = useState<DashboardLoadState>(getInitialLoadState)
  const debugPanel = buildDebugPanel(loadState)

  useEffect(() => {
    if (loadState.status !== 'loading') {
      return
    }
    const token = getDashboardToken()
    if (!token) {
      return
    }

    let isMounted = true
    const redactedRequestUrl = buildRedactedDashboardApiUrl(token)
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
      .catch((error: unknown) => {
        if (isMounted) {
          const apiError = error instanceof DashboardApiError ? error : null
          setLoadState({
            status: 'error',
            errorMessage:
              error instanceof Error ? error.message : 'Dashboard data could not be loaded.',
            httpStatus: apiError?.status ?? null,
            requestUrl: redactedRequestUrl,
          })
        }
      })

    return () => {
      isMounted = false
    }
  }, [loadState.status])

  if (loadState.status === 'loading') {
    return <LoadingState>{debugPanel}</LoadingState>
  }

  if (loadState.status === 'error') {
    return <ErrorState>{debugPanel}</ErrorState>
  }

  if (loadState.status === 'unavailable') {
    return <UnavailableState>{debugPanel}</UnavailableState>
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
      {debugPanel}
      <div className="section-stack">
        <ProblemCategorySection buckets={data.problem_categories} />
        <EngagementHealthSection buckets={data.engagement_signals} />
        <ValueUnlockedSection tokenKey={tokenKey} valueInputs={data.value_unlocked} />
        {isTestMode && data.action_ownership ? (
          <ActionOwnershipSection data={data.action_ownership} />
        ) : null}
        {isTestMode && data.stuck_signal ? (
          <StuckSignalSection data={data.stuck_signal} />
        ) : null}
      </div>
    </main>
  )
}

function getInitialLoadState(): DashboardLoadState {
  if (isDashboardTestMode()) {
    return {
      status: 'ready',
      data: createDashboardTestData(getDashboardTestOptions()),
      isTestMode: true,
      tokenKey: TEST_TOKEN_KEY,
    }
  }

  if (!getDashboardToken()) {
    return { status: 'unavailable' }
  }

  return { status: 'loading' }
}

function buildDebugPanel(loadState: DashboardLoadState) {
  if (!isDashboardDebugMode()) {
    return null
  }

  const token = getDashboardToken()
  const isTestMode = isDashboardTestMode()
  const currentOrigin = typeof window === 'undefined' ? '' : window.location.origin
  const isOnline = typeof navigator === 'undefined' ? null : navigator.onLine
  const requestUrl =
    loadState.status === 'error' && loadState.requestUrl
      ? loadState.requestUrl
      : buildRedactedDashboardApiUrl(token)

  return (
    <DashboardDebugPanel
      apiBaseUrl={getDashboardApiBaseUrl()}
      currentOrigin={currentOrigin}
      errorMessage={loadState.status === 'error' ? loadState.errorMessage : null}
      httpStatus={loadState.status === 'error' ? loadState.httpStatus : null}
      isOnline={isOnline}
      isTestMode={isTestMode}
      requestUrl={requestUrl}
      state={loadState.status}
      tokenPreview={token ? redactDashboardToken(token) : 'missing or invalid'}
    />
  )
}
