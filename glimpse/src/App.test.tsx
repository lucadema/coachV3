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

describe('App backend connection flow', () => {
  it('shows a recoverable error if session initialisation fails', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ detail: 'Backend unavailable' }, { status: 500 }))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    await act(async () => {
      vi.advanceTimersByTime(3000)
    })
    await act(async () => {
      vi.advanceTimersByTime(4000)
    })

    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
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
})
