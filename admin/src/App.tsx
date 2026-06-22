import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AdminApiError,
  createEnterprise,
  createPilot,
  deleteEnterprise,
  deletePilot,
  generateLink,
  getPilotSummary,
  listEnterprises,
  listLinks,
  listPilots,
  revokeLink,
  rotateLink,
  updateEnterprise,
  updatePilot,
} from './api/adminClient'
import type { AccessLink, Enterprise, Pilot, PilotStatus, PilotSummary } from './types'

const ADMIN_TOKEN_STORAGE_KEY = 'aether_glimpse_admin_token'

type AsyncStatus = {
  message: string | null
  tone: 'info' | 'error' | 'success'
}

function getInitialAdminToken(): string {
  try {
    return window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return 'Not set'
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function linkTitle(link: AccessLink): string {
  return link.token_type === 'glimpse_app' ? 'Glimpse participant' : 'Organisation dashboard'
}

function statusClass(status: string): string {
  return `status status-${status}`
}

function getErrorMessage(error: unknown): string {
  if (error instanceof AdminApiError) {
    return error.message
  }

  return error instanceof Error ? error.message : 'Unexpected admin operation failure.'
}

export function App() {
  const [authToken, setAuthToken] = useState(getInitialAdminToken)

  if (!authToken) {
    return (
      <LoginScreen
        onLogin={(token) => {
          try {
            window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token)
          } catch {
            // Session storage is only a convenience; the in-memory state is enough.
          }
          setAuthToken(token)
        }}
      />
    )
  }

  return (
    <AdminWorkspace
      authToken={authToken}
      onLogout={() => {
        try {
          window.sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY)
        } catch {
          // Ignore storage failures.
        }
        setAuthToken('')
      }}
    />
  )
}

function LoginScreen({ onLogin }: { onLogin: (token: string) => void }) {
  const [token, setToken] = useState('')
  const trimmedToken = token.trim()

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (trimmedToken) {
      onLogin(trimmedToken)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <p className="eyebrow">Aether Glimpse</p>
        <h1 id="login-title">Admin Control Panel</h1>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Admin API token
            <input
              autoFocus
              type="password"
              value={token}
              onChange={(event) => setToken(event.target.value)}
            />
          </label>
          <button type="submit" disabled={!trimmedToken}>
            Enter admin
          </button>
        </form>
      </section>
    </main>
  )
}

function AdminWorkspace({
  authToken,
  onLogout,
}: {
  authToken: string
  onLogout: () => void
}) {
  const [enterprises, setEnterprises] = useState<Enterprise[]>([])
  const [pilots, setPilots] = useState<Pilot[]>([])
  const [links, setLinks] = useState<AccessLink[]>([])
  const [summary, setSummary] = useState<PilotSummary | null>(null)
  const [selectedEnterpriseId, setSelectedEnterpriseId] = useState<string | null>(null)
  const [selectedPilotId, setSelectedPilotId] = useState<string | null>(null)
  const [status, setStatus] = useState<AsyncStatus>({ message: null, tone: 'info' })
  const [isLoading, setIsLoading] = useState(false)

  const requestOptions = useMemo(() => ({ authToken }), [authToken])
  const selectedEnterprise = enterprises.find((item) => item.id === selectedEnterpriseId) ?? null
  const selectedPilot = pilots.find((item) => item.id === selectedPilotId) ?? null

  async function refreshEnterprises() {
    setIsLoading(true)
    setStatus({ message: null, tone: 'info' })
    try {
      const rows = await listEnterprises(requestOptions)
      setEnterprises(rows)
      setSelectedEnterpriseId((current) => current ?? rows[0]?.id ?? null)
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    } finally {
      setIsLoading(false)
    }
  }

  async function refreshPilots(enterpriseId: string) {
    setIsLoading(true)
    setStatus({ message: null, tone: 'info' })
    try {
      const rows = await listPilots(enterpriseId, requestOptions)
      setPilots(rows)
      setSelectedPilotId((current) => {
        if (current && rows.some((pilot) => pilot.id === current)) {
          return current
        }
        return rows[0]?.id ?? null
      })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    } finally {
      setIsLoading(false)
    }
  }

  async function refreshPilotOperations(pilotId: string) {
    setIsLoading(true)
    setStatus({ message: null, tone: 'info' })
    setLinks([])
    setSummary(null)

    const errors: string[] = []

    try {
      const nextLinks = await listLinks(pilotId, requestOptions)
      setLinks(nextLinks)
    } catch (error) {
      errors.push(getErrorMessage(error))
    }

    try {
      const nextSummary = await getPilotSummary(pilotId, requestOptions)
      setSummary(nextSummary)
    } catch (error) {
      errors.push(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }

    if (errors.length > 0) {
      setStatus({ message: errors[0], tone: 'error' })
    }
  }

  useEffect(() => {
    void refreshEnterprises()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestOptions])

  useEffect(() => {
    if (selectedEnterpriseId) {
      void refreshPilots(selectedEnterpriseId)
    } else {
      setPilots([])
      setSelectedPilotId(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedEnterpriseId])

  useEffect(() => {
    if (selectedPilotId) {
      void refreshPilotOperations(selectedPilotId)
    } else {
      setLinks([])
      setSummary(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPilotId])

  async function handleCreateEnterprise(name: string, notes: string) {
    try {
      const enterprise = await createEnterprise({ name, notes }, requestOptions)
      setEnterprises((current) => [enterprise, ...current])
      setSelectedEnterpriseId(enterprise.id)
      setStatus({ message: 'Enterprise created.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleCreatePilot(name: string, notes: string) {
    if (!selectedEnterprise) {
      return
    }

    try {
      const pilot = await createPilot(
        {
          enterprise_id: selectedEnterprise.id,
          name,
          notes,
        },
        requestOptions,
      )
      setPilots((current) => [pilot, ...current])
      setSelectedPilotId(pilot.id)
      setStatus({ message: 'Pilot created.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleEnterpriseStatusChange(enterprise: Enterprise, statusValue: string) {
    try {
      const updated = await updateEnterprise(
        enterprise.id,
        { status: statusValue },
        requestOptions,
      )
      setEnterprises((current) => current.map((item) => (item.id === updated.id ? updated : item)))
      setStatus({ message: 'Enterprise updated.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handlePilotStatusChange(pilot: Pilot, statusValue: PilotStatus) {
    try {
      const updated = await updatePilot(pilot.id, { status: statusValue }, requestOptions)
      setPilots((current) => current.map((item) => (item.id === updated.id ? updated : item)))
      setStatus({ message: 'Pilot updated.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleDeleteEnterprise(enterprise: Enterprise) {
    const confirmed = window.confirm(
      `Delete ${enterprise.name}? This also deletes its pilots and access links.`,
    )
    if (!confirmed) {
      return
    }

    try {
      await deleteEnterprise(enterprise.id, requestOptions)
      setEnterprises((current) => current.filter((item) => item.id !== enterprise.id))
      setPilots([])
      setLinks([])
      setSummary(null)
      setSelectedEnterpriseId((current) => (current === enterprise.id ? null : current))
      setSelectedPilotId(null)
      setStatus({ message: 'Enterprise deleted.', tone: 'success' })
      await refreshEnterprises()
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleDeletePilot(pilot: Pilot) {
    const confirmed = window.confirm(`Delete ${pilot.name}? This also deletes its access links.`)
    if (!confirmed) {
      return
    }

    try {
      await deletePilot(pilot.id, requestOptions)
      setPilots((current) => current.filter((item) => item.id !== pilot.id))
      setLinks([])
      setSummary(null)
      setSelectedPilotId((current) => (current === pilot.id ? null : current))
      setStatus({ message: 'Pilot deleted.', tone: 'success' })
      if (selectedEnterpriseId) {
        await refreshPilots(selectedEnterpriseId)
      }
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleGenerateLink(type: 'glimpse' | 'dashboard') {
    if (!selectedPilot) {
      return
    }

    try {
      await generateLink(selectedPilot.id, type, requestOptions)
      await refreshPilotOperations(selectedPilot.id)
      setStatus({ message: 'Link ready.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleRotateLink(link: AccessLink) {
    if (!selectedPilot) {
      return
    }

    try {
      await rotateLink(link.token_id, requestOptions)
      await refreshPilotOperations(selectedPilot.id)
      setStatus({ message: 'Link rotated.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleRevokeLink(link: AccessLink) {
    if (!selectedPilot) {
      return
    }

    try {
      await revokeLink(link.token_id, requestOptions)
      await refreshPilotOperations(selectedPilot.id)
      setStatus({ message: 'Link revoked.', tone: 'success' })
    } catch (error) {
      setStatus({ message: getErrorMessage(error), tone: 'error' })
    }
  }

  async function handleCopy(link: AccessLink) {
    if (!link.full_access_link) {
      return
    }

    try {
      await navigator.clipboard.writeText(link.full_access_link)
      setStatus({ message: 'Link copied.', tone: 'success' })
    } catch {
      setStatus({ message: 'Copy failed. Select and copy the link manually.', tone: 'error' })
    }
  }

  return (
    <main className="admin-shell">
      <header className="admin-header">
        <div>
          <p className="eyebrow">Aether Glimpse</p>
          <h1>Admin Control Panel</h1>
        </div>
        <nav aria-label="Admin sections">
          <a href="#enterprises">Enterprises</a>
          <a href="#pilots">Pilots</a>
          <a href="#links">Access links</a>
          <a href="#dashboard">Dashboard</a>
        </nav>
        <button type="button" className="ghost-button" onClick={onLogout}>
          Sign out
        </button>
      </header>

      {status.message ? (
        <p role={status.tone === 'error' ? 'alert' : 'status'} className={`notice ${status.tone}`}>
          {status.message}
        </p>
      ) : null}

      <div className="workspace-grid" aria-busy={isLoading}>
        <section id="enterprises" className="panel">
          <PanelHeader title="Enterprises" count={enterprises.length} />
          <CreateForm
            nameLabel="Enterprise name"
            notesLabel="Enterprise notes"
            buttonLabel="Create enterprise"
            onSubmit={handleCreateEnterprise}
          />
          <div className="list-stack">
            {enterprises.map((enterprise) => (
              <button
                type="button"
                key={enterprise.id}
                className={`list-row ${enterprise.id === selectedEnterpriseId ? 'selected' : ''}`}
                onClick={() => setSelectedEnterpriseId(enterprise.id)}
              >
                <span>
                  <strong>{enterprise.name}</strong>
                  <small>{enterprise.id}</small>
                </span>
                <span className={statusClass(enterprise.status)}>{enterprise.status}</span>
              </button>
            ))}
          </div>
        </section>

        <section id="pilots" className="panel">
          <PanelHeader title="Pilots" count={pilots.length} />
          {selectedEnterprise ? (
            <>
              <div className="detail-strip">
                <strong>{selectedEnterprise.name}</strong>
                <div className="compact-actions">
                  <select
                    value={selectedEnterprise.status}
                    onChange={(event) => {
                      void handleEnterpriseStatusChange(selectedEnterprise, event.target.value)
                    }}
                  >
                    <option value="active">active</option>
                    <option value="paused">paused</option>
                    <option value="closed">closed</option>
                  </select>
                  <button
                    type="button"
                    className="danger-button"
                    disabled={selectedEnterprise.status !== 'closed'}
                    title={
                      selectedEnterprise.status === 'closed'
                        ? 'Delete closed enterprise'
                        : 'Enterprise must be closed before it can be deleted'
                    }
                    onClick={() => void handleDeleteEnterprise(selectedEnterprise)}
                  >
                    Delete
                  </button>
                </div>
              </div>
              <CreateForm
                nameLabel="Pilot name"
                notesLabel="Pilot notes"
                buttonLabel="Create pilot"
                onSubmit={handleCreatePilot}
              />
            </>
          ) : (
            <p className="empty-state">Create or select an enterprise.</p>
          )}
          <div className="list-stack">
            {pilots.map((pilot) => (
              <button
                type="button"
                key={pilot.id}
                className={`list-row ${pilot.id === selectedPilotId ? 'selected' : ''}`}
                onClick={() => {
                  if (pilot.id === selectedPilotId) {
                    void refreshPilotOperations(pilot.id)
                    return
                  }

                  setLinks([])
                  setSummary(null)
                  setSelectedPilotId(pilot.id)
                }}
              >
                <span>
                  <strong>{pilot.name}</strong>
                  <small>{pilot.id}</small>
                </span>
                <span className={statusClass(pilot.status)}>{pilot.status}</span>
              </button>
            ))}
          </div>
        </section>

        <section id="links" className="panel panel-wide">
          <PanelHeader title="Pilot operations" count={links.length} />
          {selectedPilot ? (
            <>
              <div className="detail-strip">
                <div>
                  <strong>{selectedPilot.name}</strong>
                  <small>{selectedPilot.id}</small>
                </div>
                <div className="compact-actions">
                  <select
                    value={selectedPilot.status}
                    onChange={(event) => {
                      void handlePilotStatusChange(selectedPilot, event.target.value as PilotStatus)
                    }}
                  >
                    <option value="draft">draft</option>
                    <option value="active">active</option>
                    <option value="paused">paused</option>
                    <option value="closed">closed</option>
                  </select>
                  <button
                    type="button"
                    className="danger-button"
                    disabled={selectedPilot.status !== 'closed'}
                    title={
                      selectedPilot.status === 'closed'
                        ? 'Delete closed pilot'
                        : 'Pilot must be closed before it can be deleted'
                    }
                    onClick={() => void handleDeletePilot(selectedPilot)}
                  >
                    Delete
                  </button>
                </div>
              </div>
              <SummaryGrid summary={summary} />
              <div className="action-row">
                <button type="button" onClick={() => void handleGenerateLink('glimpse')}>
                  Generate Glimpse link
                </button>
                <button type="button" onClick={() => void handleGenerateLink('dashboard')}>
                  Generate dashboard link
                </button>
              </div>
              <div className="link-stack">
                {links.map((link) => (
                  <article key={link.token_id} className="link-card">
                    <header>
                      <div>
                        <strong>{linkTitle(link)}</strong>
                        <small>prefix {link.token_prefix}</small>
                      </div>
                      <span className={statusClass(link.status)}>{link.status}</span>
                    </header>
                    <input readOnly value={link.full_access_link ?? 'No active link'} />
                    <dl>
                      <div>
                        <dt>Created</dt>
                        <dd>{formatDate(link.created_at)}</dd>
                      </div>
                      <div>
                        <dt>Last used</dt>
                        <dd>{formatDate(link.last_used_at)}</dd>
                      </div>
                    </dl>
                    <div className="action-row">
                      <button
                        type="button"
                        disabled={!link.full_access_link}
                        onClick={() => void handleCopy(link)}
                      >
                        Copy
                      </button>
                      <button type="button" onClick={() => void handleRotateLink(link)}>
                        Rotate
                      </button>
                      <button type="button" onClick={() => void handleRevokeLink(link)}>
                        Revoke
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </>
          ) : (
            <p className="empty-state">Create or select a pilot.</p>
          )}
        </section>

        <section id="dashboard" className="panel dashboard-panel">
          <PanelHeader title="Admin dashboard" />
          <div className="dashboard-placeholder">
            <span className="watermark">Aether</span>
            <strong>Reserved dashboard surface</strong>
            <p>Pilot-level metrics are available above; broader admin reporting can plug in here.</p>
          </div>
        </section>
      </div>
    </main>
  )
}

function PanelHeader({ title, count }: { title: string; count?: number }) {
  return (
    <header className="panel-header">
      <h2>{title}</h2>
      {typeof count === 'number' ? <span>{count}</span> : null}
    </header>
  )
}

function CreateForm({
  nameLabel,
  notesLabel,
  buttonLabel,
  onSubmit,
}: {
  nameLabel: string
  notesLabel: string
  buttonLabel: string
  onSubmit: (name: string, notes: string) => void | Promise<void>
}) {
  const [name, setName] = useState('')
  const [notes, setNotes] = useState('')
  const trimmedName = name.trim()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!trimmedName) {
      return
    }

    await onSubmit(trimmedName, notes)
    setName('')
    setNotes('')
  }

  return (
    <form className="create-form" onSubmit={(event) => void handleSubmit(event)}>
      <label>
        {nameLabel}
        <input value={name} onChange={(event) => setName(event.target.value)} />
      </label>
      <label>
        {notesLabel}
        <textarea value={notes} onChange={(event) => setNotes(event.target.value)} />
      </label>
      <button type="submit" disabled={!trimmedName}>
        {buttonLabel}
      </button>
    </form>
  )
}

function SummaryGrid({ summary }: { summary: PilotSummary | null }) {
  return (
    <div className="summary-grid">
      <Metric label="Sessions" value={summary?.sessions_count ?? 0} />
      <Metric label="Feedback" value={summary?.feedback_records_count ?? 0} />
      <Metric label="Last activity" value={formatDate(summary?.last_activity_at)} />
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
