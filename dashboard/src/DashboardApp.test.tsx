import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DashboardApp } from './DashboardApp'

describe('DashboardApp', () => {
  afterEach(() => {
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
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('shows a safe unavailable state when no token is present', async () => {
    render(<DashboardApp />)

    await waitFor(() => {
      expect(screen.getByText('Dashboard unavailable')).toBeTruthy()
    })
    expect(screen.getByText('This dashboard is not currently available for this pilot.')).toBeTruthy()
  })
})
