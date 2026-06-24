import type { AccessLink, Enterprise, FeedbackPackOption, Pilot, PilotSummary } from '../types'

const DEFAULT_ADMIN_API_BASE_URL = 'http://127.0.0.1:8010'

export type AdminClientOptions = {
  authToken: string
  baseUrl?: string
}

type RequestJsonOptions = AdminClientOptions & {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  payload?: unknown
}

export class AdminApiError extends Error {
  readonly status: number | null
  readonly responseBody: unknown

  constructor(message: string, status: number | null = null, responseBody: unknown = null) {
    super(message)
    this.name = 'AdminApiError'
    this.status = status
    this.responseBody = responseBody
  }
}

export function getAdminApiBaseUrl(): string {
  return (import.meta.env.VITE_ADMIN_API_BASE_URL || DEFAULT_ADMIN_API_BASE_URL).replace(/\/+$/, '')
}

export function buildAdminApiUrl(path: string, baseUrl = getAdminApiBaseUrl()): string {
  const normalisedPath = path.startsWith('/') ? path : `/${path}`
  return `${baseUrl.replace(/\/+$/, '')}${normalisedPath}`
}

async function readResponseBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function detailFromBody(body: unknown): string | null {
  if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
    return body.detail
  }

  return typeof body === 'string' && body ? body : null
}

async function requestJson<T>(path: string, options: RequestJsonOptions): Promise<T> {
  const method = options.method ?? 'GET'
  const response = await fetch(buildAdminApiUrl(path, options.baseUrl), {
    body: options.payload === undefined ? undefined : JSON.stringify(options.payload),
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${options.authToken}`,
      ...(options.payload === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    method,
  }).catch((error: unknown) => {
    throw new AdminApiError(
      error instanceof Error ? error.message : 'The admin API could not be reached.',
    )
  })

  const responseBody = await readResponseBody(response)
  if (!response.ok) {
    throw new AdminApiError(
      detailFromBody(responseBody) ?? `Admin API request failed with HTTP ${response.status}.`,
      response.status,
      responseBody,
    )
  }

  return responseBody as T
}

export function listEnterprises(options: AdminClientOptions): Promise<Enterprise[]> {
  return requestJson<Enterprise[]>('/admin/enterprises', options)
}

export function createEnterprise(
  payload: { name: string; notes?: string },
  options: AdminClientOptions,
): Promise<Enterprise> {
  return requestJson<Enterprise>('/admin/enterprises', {
    ...options,
    method: 'POST',
    payload,
  })
}

export function updateEnterprise(
  enterpriseId: string,
  payload: { name?: string; status?: string; notes?: string },
  options: AdminClientOptions,
): Promise<Enterprise> {
  return requestJson<Enterprise>(`/admin/enterprises/${encodeURIComponent(enterpriseId)}`, {
    ...options,
    method: 'PATCH',
    payload,
  })
}

export function deleteEnterprise(enterpriseId: string, options: AdminClientOptions): Promise<void> {
  return requestJson<void>(`/admin/enterprises/${encodeURIComponent(enterpriseId)}`, {
    ...options,
    method: 'DELETE',
  })
}

export function listPilots(enterpriseId: string, options: AdminClientOptions): Promise<Pilot[]> {
  return requestJson<Pilot[]>(
    `/admin/enterprises/${encodeURIComponent(enterpriseId)}/pilots`,
    options,
  )
}

export function createPilot(
  payload: { enterprise_id: string; name: string; notes?: string; feedback_pack_id?: string | null },
  options: AdminClientOptions,
): Promise<Pilot> {
  return requestJson<Pilot>('/admin/pilots', {
    ...options,
    method: 'POST',
    payload,
  })
}

export function updatePilot(
  pilotId: string,
  payload: { name?: string; status?: string; notes?: string; feedback_pack_id?: string | null },
  options: AdminClientOptions,
): Promise<Pilot> {
  return requestJson<Pilot>(`/admin/pilots/${encodeURIComponent(pilotId)}`, {
    ...options,
    method: 'PATCH',
    payload,
  })
}

export function deletePilot(pilotId: string, options: AdminClientOptions): Promise<void> {
  return requestJson<void>(`/admin/pilots/${encodeURIComponent(pilotId)}`, {
    ...options,
    method: 'DELETE',
  })
}

export function listFeedbackPacks(options: AdminClientOptions): Promise<FeedbackPackOption[]> {
  return requestJson<FeedbackPackOption[]>('/admin/feedback-packs', options)
}

export function getPilotSummary(pilotId: string, options: AdminClientOptions): Promise<PilotSummary> {
  return requestJson<PilotSummary>(`/admin/pilots/${encodeURIComponent(pilotId)}/summary`, options)
}

export function listLinks(pilotId: string, options: AdminClientOptions): Promise<AccessLink[]> {
  return requestJson<AccessLink[]>(`/admin/pilots/${encodeURIComponent(pilotId)}/links`, options)
}

export function generateLink(
  pilotId: string,
  type: 'glimpse' | 'dashboard',
  options: AdminClientOptions,
): Promise<AccessLink> {
  return requestJson<AccessLink>(
    `/admin/pilots/${encodeURIComponent(pilotId)}/links/${type}`,
    {
      ...options,
      method: 'POST',
    },
  )
}

export function rotateLink(tokenId: string, options: AdminClientOptions): Promise<AccessLink> {
  return requestJson<AccessLink>(`/admin/tokens/${encodeURIComponent(tokenId)}/rotate`, {
    ...options,
    method: 'POST',
  })
}

export function revokeLink(tokenId: string, options: AdminClientOptions): Promise<AccessLink> {
  return requestJson<AccessLink>(`/admin/tokens/${encodeURIComponent(tokenId)}/revoke`, {
    ...options,
    method: 'POST',
  })
}
