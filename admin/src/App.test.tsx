import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

const ADMIN_TOKEN_STORAGE_KEY = 'aether_glimpse_admin_token'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
    status,
  })
}

beforeEach(() => {
  window.sessionStorage.clear()
})

afterEach(() => {
  vi.unstubAllGlobals()
  window.sessionStorage.clear()
})

describe('App', () => {
  it('shows the admin token gate before authentication', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: /admin control panel/i })).toBeTruthy()
    expect(screen.getByLabelText(/admin api token/i)).toBeTruthy()
  })

  it('shows selected pilot links even when summary loading fails', async () => {
    window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, 'test-admin-token')
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)

      if (url.endsWith('/admin/enterprises')) {
        return jsonResponse([
          {
            created_at: '2026-06-22T10:00:00Z',
            id: 'enterprise-1',
            name: 'Test Enterprise',
            notes: '',
            status: 'active',
            updated_at: '2026-06-22T10:00:00Z',
          },
        ])
      }

      if (url.endsWith('/admin/enterprises/enterprise-1/pilots')) {
        return jsonResponse([
          {
            created_at: '2026-06-22T10:00:00Z',
            end_at: null,
            enterprise_id: 'enterprise-1',
            feedback_pack_id: null,
            id: 'pilot-1',
            name: 'Pilot One',
            notes: '',
            start_at: null,
            status: 'paused',
            updated_at: '2026-06-22T10:00:00Z',
          },
          {
            created_at: '2026-06-22T10:00:00Z',
            end_at: null,
            enterprise_id: 'enterprise-1',
            feedback_pack_id: null,
            id: 'pilot-2',
            name: 'Pilot Two',
            notes: '',
            start_at: null,
            status: 'active',
            updated_at: '2026-06-22T10:00:00Z',
          },
        ])
      }

      if (url.endsWith('/admin/pilots/pilot-1/links')) {
        return jsonResponse([])
      }

      if (url.endsWith('/admin/pilots/pilot-1/summary')) {
        return jsonResponse({
          feedback_records_count: 0,
          last_activity_at: null,
          link_statuses: {},
          pilot_id: 'pilot-1',
          pilot_status: 'paused',
          sessions_count: 0,
        })
      }

      if (url.endsWith('/admin/pilots/pilot-2/links')) {
        return jsonResponse([
          {
            created_at: '2026-06-22T10:00:00Z',
            expires_at: null,
            full_access_link: 'https://pilot.example/start?t=pilot-two-token',
            last_used_at: null,
            pilot_id: 'pilot-2',
            revoked_at: null,
            status: 'active',
            token_id: 'token-2',
            token_prefix: 'pilot-tw',
            token_type: 'glimpse_app',
          },
        ])
      }

      if (url.endsWith('/admin/pilots/pilot-2/summary')) {
        return jsonResponse({ detail: 'Summary query failed.' }, 500)
      }

      return jsonResponse({ detail: `Unhandled URL ${url}` }, 404)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Pilot Two/i })).toBeTruthy()
    })

    fireEvent.click(screen.getByRole('button', { name: /Pilot Two/i }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('https://pilot.example/start?t=pilot-two-token')).toBeTruthy()
    })
    expect(screen.getByRole('alert')).toBeTruthy()
  })
})
