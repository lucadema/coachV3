import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DashboardApp } from './DashboardApp'

describe('DashboardApp', () => {
  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
    window.history.pushState({}, '', '/')
  })

  it('renders deterministic test data without fetching real dashboard data', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    window.history.pushState({}, '', '/?test')

    render(<DashboardApp />)

    expect(await screen.findByText('Test data')).toBeTruthy()
    expect(screen.getByText('Aether Works')).toBeTruthy()
    expect(screen.getByText('Problem Categories')).toBeTruthy()
    expect(screen.getByText('Action Ownership')).toBeTruthy()
    expect(screen.getByText('Stuck Signal')).toBeTruthy()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('applies safe test-mode URL options to generated dashboard data', async () => {
    window.history.pushState(
      {},
      '',
      '/?test&testsessions=200&test_orgname=NHS&test_pilotname=Demo%20Pilot',
    )

    render(<DashboardApp />)

    expect(await screen.findByText('NHS')).toBeTruthy()
    expect(screen.getByText('Demo Pilot')).toBeTruthy()
    expect(screen.getByText('200 categorised sessions')).toBeTruthy()
    expect(screen.getByText('200 signal assessments')).toBeTruthy()
    expect(screen.getByText('200 responses included')).toBeTruthy()
    expect(screen.getByText('200 choices recorded')).toBeTruthy()
    expect(screen.getByText('200 sessions classified')).toBeTruthy()
  })

  it('does not render prototype-only sections for live dashboard data', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          available: true,
          enterprise_name: 'Live Enterprise',
          pilot_name: 'Live Pilot',
          pilot_status: 'active',
          problem_categories: [],
          engagement_signals: [],
          value_unlocked: {
            monthly_minutes: 0,
            qualifying_responses_count: 0,
            flag_to_organisation: {
              yes_count: 0,
              no_count: 0,
            },
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    window.history.pushState({}, '', '/?t=AbC_1234567890-token_value')

    render(<DashboardApp />)

    expect(await screen.findByText('Live Enterprise')).toBeTruthy()
    expect(screen.queryByText('Action Ownership')).toBeNull()
    expect(screen.queryByText('Stuck Signal')).toBeNull()
  })

  it('shows a safe unavailable state when no token is present', async () => {
    render(<DashboardApp />)

    await waitFor(() => {
      expect(screen.getByText('Dashboard unavailable')).toBeTruthy()
    })
    expect(screen.getByText('This dashboard is not currently available for this pilot.')).toBeTruthy()
  })
})
