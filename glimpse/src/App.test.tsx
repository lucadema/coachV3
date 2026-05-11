/* @vitest-environment jsdom */

import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { downloadSessionPdf } from './pdf/sessionPdfDownload'

vi.mock('./pdf/sessionPdfDownload', () => ({
  downloadSessionPdf: vi.fn(),
}))

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
  cleanup()
  vi.clearAllMocks()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

async function advanceToInformationScreen() {
  await act(async () => {
    vi.advanceTimersByTime(3000)
  })
  await act(async () => {
    vi.advanceTimersByTime(4000)
  })

  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: /next/i }))
}

async function flushPromises() {
  await act(async () => undefined)
}

describe('App backend connection flow', () => {
  it('shows a recoverable error if session initialisation fails', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ detail: 'Backend unavailable' }, { status: 500 }))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    await advanceToInformationScreen()
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/session_initialise$/),
      expect.objectContaining({
        method: 'GET',
      }),
    )
    await act(async () => undefined)

    expect(screen.getByRole('alert').textContent).toBe('Backend unavailable')
  })

  it('shows the discussion screen when the first backend turn resolves to coaching', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()

    expect(screen.getByText('What feels most unresolved?')).toBeTruthy()
    expect(screen.getByLabelText(/reply to aether/i)).toBeTruthy()
  })

  it('shows synthesis review when coaching resolves to synthesis_review', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()

    expect(screen.getByText('Here is the synthesis.')).toBeTruthy()
    expect(screen.getByRole('button', { name: /that’s it/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /not quite/i })).toBeTruthy()
  })

  it('shows pathways screen when accepted synthesis resolves to pathways', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: '## Pathway one\nDetails',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'presenting',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /that’s it/i }))
    await flushPromises()

    expect(screen.getByText('PATHWAY ONE')).toBeTruthy()
    expect(screen.queryByText('Backend response placeholder')).toBeNull()

    const callsBeforeDownload = fetchMock.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /download session pdf/i }))

    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeDownload)
    expect(downloadSessionPdf).toHaveBeenCalledWith({
      pathways: [{ title: 'Pathway one', body: 'Details' }],
      problemStatement: 'I need to reset expectations with my team',
      synthesis: 'Here is the synthesis.',
    })
  })

  it('continues from pathways to local feedback, then closes locally', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: '## Pathway one\nDetails',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Closure text',
          session: {
            session_id: 'session-1',
            stage: 'closure',
            state: 'presenting',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /that’s it/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()

    const postBodies = fetchMock.mock.calls
      .map(([, options]) => options?.body)
      .filter((body): body is string => typeof body === 'string')

    expect(postBodies.some((body) => body.includes('"user_message":"continue"'))).toBe(true)
    expect(postBodies.every((body) => !body.includes('pathway_selected:'))).toBe(true)
    expect(
      screen.getByText('Before you go, please tell us what you thought of the Aether Glimpse experience.'),
    ).toBeTruthy()
    expect(screen.queryByText('Closure text')).toBeNull()

    const callsBeforeClose = fetchMock.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /^close$/i }))

    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeClose)
    expect(screen.getByText('We hope you’ve enjoyed this glimpse of Aether')).toBeTruthy()
  })

  it('keeps refined synthesis on synthesis review when backend returns pathways preparing', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the refined synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'preparing',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /not quite/i }))
    fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
      target: { value: 'Add the budget constraint' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()

    expect(screen.getByText('Here is the refined synthesis.')).toBeTruthy()
    expect(screen.getByRole('button', { name: /continue/i })).toBeTruthy()
    expect(screen.queryByRole('button', { name: /not quite/i })).toBeNull()
  })
})
