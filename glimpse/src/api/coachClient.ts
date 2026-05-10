import type { BackendSessionView, BackendTurnResponse } from '../types/session'

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

type CoachClientOptions = {
  baseUrl?: string
}

type RequestJsonOptions = CoachClientOptions & {
  method?: 'GET' | 'POST'
  payload?: unknown
}

type CoachApiErrorOptions = {
  responseBody?: unknown
  status?: number | null
}

export class CoachApiError extends Error {
  readonly isMissingSession: boolean
  readonly responseBody: unknown
  readonly status: number | null

  constructor(message: string, options: CoachApiErrorOptions = {}) {
    super(message)
    this.name = 'CoachApiError'
    this.status = options.status ?? null
    this.responseBody = options.responseBody
    this.isMissingSession = this.status === 404
  }
}

function getApiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, '')
}

function buildApiUrl(path: string, baseUrl = getApiBaseUrl()): string {
  const normalisedBaseUrl = baseUrl.replace(/\/+$/, '')
  const normalisedPath = path.startsWith('/') ? path : `/${path}`

  return `${normalisedBaseUrl}${normalisedPath}`
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

function getErrorDetail(responseBody: unknown): string | null {
  if (
    responseBody &&
    typeof responseBody === 'object' &&
    'detail' in responseBody &&
    typeof responseBody.detail === 'string'
  ) {
    return responseBody.detail
  }

  if (typeof responseBody === 'string' && responseBody.trim()) {
    return responseBody
  }

  return null
}

async function requestJson<T>(path: string, options: RequestJsonOptions = {}): Promise<T> {
  const method = options.method ?? 'GET'
  const response = await fetch(buildApiUrl(path, options.baseUrl), {
    body: options.payload === undefined ? undefined : JSON.stringify(options.payload),
    headers: {
      Accept: 'application/json',
      ...(options.payload === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    method,
  }).catch((error: unknown) => {
    const message =
      error instanceof Error
        ? error.message
        : 'The backend could not be reached. Please check that the API is running.'

    throw new CoachApiError(message)
  })

  const responseBody = await readResponseBody(response)

  if (!response.ok) {
    const detail = getErrorDetail(responseBody)
    const message = detail ?? `Backend request failed with HTTP ${response.status}.`

    throw new CoachApiError(message, {
      responseBody,
      status: response.status,
    })
  }

  return responseBody as T
}

export async function initialiseSession(
  options: CoachClientOptions = {},
): Promise<BackendSessionView> {
  return requestJson<BackendSessionView>('/session_initialise', options)
}

export async function sendUserMessage(
  sessionId: string,
  userMessage: string,
  options: CoachClientOptions = {},
): Promise<BackendTurnResponse> {
  return requestJson<BackendTurnResponse>('/user_message', {
    ...options,
    method: 'POST',
    payload: {
      session_id: sessionId,
      user_message: userMessage,
    },
  })
}

export async function getDebugTrace(
  sessionId: string,
  options: CoachClientOptions = {},
): Promise<unknown> {
  return requestJson<unknown>(`/debug_trace/${encodeURIComponent(sessionId)}`, options)
}
