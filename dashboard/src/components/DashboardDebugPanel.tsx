type DashboardDebugPanelProps = {
  apiBaseUrl: string
  currentOrigin: string
  errorMessage?: string | null
  httpStatus?: number | null
  isOnline?: boolean | null
  isTestMode: boolean
  requestUrl: string | null
  state: string
  tokenPreview: string
}

export function DashboardDebugPanel({
  apiBaseUrl,
  currentOrigin,
  errorMessage,
  httpStatus,
  isOnline,
  isTestMode,
  requestUrl,
  state,
  tokenPreview,
}: DashboardDebugPanelProps) {
  return (
    <aside className="debug-panel" aria-label="Dashboard debug details">
      <div className="debug-panel-header">
        <p className="eyebrow">Debug mode</p>
        <span>Visible only with ?debug=true</span>
      </div>
      <dl className="debug-grid">
        <div>
          <dt>Load state</dt>
          <dd>{state}</dd>
        </div>
        <div>
          <dt>Dashboard origin</dt>
          <dd>{currentOrigin || 'unknown'}</dd>
        </div>
        <div>
          <dt>API base URL</dt>
          <dd>{apiBaseUrl}</dd>
        </div>
        <div>
          <dt>Request URL</dt>
          <dd>{requestUrl ?? 'not requested'}</dd>
        </div>
        <div>
          <dt>Token</dt>
          <dd>{tokenPreview}</dd>
        </div>
        <div>
          <dt>HTTP status</dt>
          <dd>{httpStatus ?? 'none'}</dd>
        </div>
        <div>
          <dt>Fetch error</dt>
          <dd>{errorMessage || 'none'}</dd>
        </div>
        <div>
          <dt>Browser online</dt>
          <dd>{typeof isOnline === 'boolean' ? String(isOnline) : 'unknown'}</dd>
        </div>
        <div>
          <dt>Test mode</dt>
          <dd>{String(isTestMode)}</dd>
        </div>
      </dl>
    </aside>
  )
}
