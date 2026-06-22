import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  CoachApiError,
  getFeedbackForm,
  initialiseSession,
  recordSessionEvent,
  sendUserMessage,
  submitFeedback,
} from './coachClient'

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: {
      'Content-Type': 'application/json',
    },
    status: 200,
    ...init,
  })
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('coachClient', () => {
  it('calls GET /session_initialise and returns parsed JSON', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        session_id: 'session-1',
        stage: 'classification',
        state: 'awaiting_input',
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(initialiseSession({ baseUrl: 'http://api.test' })).resolves.toEqual({
      session_id: 'session-1',
      stage: 'classification',
      state: 'awaiting_input',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/session_initialise',
      expect.objectContaining({
        method: 'GET',
      }),
    )
  })

  it('calls POST /user_message with the expected payload and returns parsed JSON', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        coach_message: 'Tell me more.',
        session: {
          session_id: 'session-1',
          stage: 'coaching',
          state: 'guiding',
        },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      sendUserMessage('session-1', 'A challenge I am facing', { baseUrl: 'http://api.test' }),
    ).resolves.toEqual({
      coach_message: 'Tell me more.',
      session: {
        session_id: 'session-1',
        stage: 'coaching',
        state: 'guiding',
      },
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/user_message',
      expect.objectContaining({
        body: JSON.stringify({
          session_id: 'session-1',
          user_message: 'A challenge I am facing',
        }),
        method: 'POST',
      }),
    )
  })

  it('includes optional launch context metadata on user messages', async () => {
    vi.stubGlobal('window', {
      location: {
        search: '?session_label=Luca',
      },
    })
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        coach_message: 'Tell me more.',
        session: {
          session_id: 'session-1',
          stage: 'coaching',
          state: 'guiding',
        },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await sendUserMessage('session-1', 'A challenge I am facing', {
      baseUrl: 'http://api.test',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/user_message',
      expect.objectContaining({
        body: JSON.stringify({
          session_id: 'session-1',
          user_message: 'A challenge I am facing',
          client_context: {
            session_label: 'luca',
          },
        }),
      }),
    )
  })

  it('throws a CoachApiError when the backend cannot be reached', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockRejectedValue(new Error('Failed to fetch'))
    vi.stubGlobal('fetch', fetchMock)

    await expect(initialiseSession({ baseUrl: 'http://api.test' })).rejects.toMatchObject({
      message: 'Failed to fetch',
      status: null,
    })
  })

  it('marks 404 responses as missing session errors', async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ detail: 'Session not found' }, { status: 404 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      sendUserMessage('missing-session', 'A challenge I am facing', {
        baseUrl: 'http://api.test',
      }),
    ).rejects.toMatchObject({
      isMissingSession: true,
      message: 'Session not found',
      status: 404,
    } satisfies Partial<CoachApiError>)
  })

  it('records PDF download telemetry events', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    await recordSessionEvent('session-1', { event: 'pdf_downloaded' }, { baseUrl: 'http://api.test' })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/telemetry/session_event',
      expect.objectContaining({
        body: JSON.stringify({
          session_id: 'session-1',
          event: 'pdf_downloaded',
        }),
        method: 'POST',
      }),
    )
  })

  it('loads the active feedback form', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        show_feedback: true,
        feedback_pack_id: 'glimpse_default',
        survey_query: 'Would you be happy to answer a few quick questions?',
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getFeedbackForm('session-1', { baseUrl: 'http://api.test' })).resolves.toMatchObject({
      survey_query: 'Would you be happy to answer a few quick questions?',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/coach/v2/feedback-form?session_id=session-1',
      expect.objectContaining({
        method: 'GET',
      }),
    )
  })

  it('submits configurable feedback responses', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    await submitFeedback(
      'session-1',
      'glimpse_default',
      {
        helped_think_differently: true,
        valuable_moments: ['structured_pathways'],
      },
      { baseUrl: 'http://api.test' },
    )

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/coach/v2/feedback',
      expect.objectContaining({
        body: JSON.stringify({
          session_id: 'session-1',
          feedback_pack_id: 'glimpse_default',
          responses: {
            helped_think_differently: true,
            valuable_moments: ['structured_pathways'],
          },
        }),
        method: 'POST',
      }),
    )
  })
})
