/* @vitest-environment jsdom */

import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

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

  it('routes away from discussion to the placeholder when coaching resolves to another screen', async () => {
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

    expect(screen.getByText('Backend response placeholder')).toBeTruthy()
    expect(screen.getByText('synthesis_review')).toBeTruthy()
    expect(screen.getByText('synthesis')).toBeTruthy()
    expect(screen.getByText('presenting')).toBeTruthy()
    expect(screen.getByText('No')).toBeTruthy()
  })
})
