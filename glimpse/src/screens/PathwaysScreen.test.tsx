/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PathwaysScreen } from './PathwaysScreen'
import type { PathwayCard } from '../types/session'

const pathways: PathwayCard[] = [
  {
    title: 'Build the evidence first',
    body: 'Full evidence pathway body with orientation and conditions.',
  },
  {
    title: 'Reframe the business case',
    body: 'Full business case pathway body with risks and constraints.',
  },
]

afterEach(() => {
  cleanup()
})

function renderScreen(overrides: Partial<Parameters<typeof PathwaysScreen>[0]> = {}) {
  return render(
    <PathwaysScreen
      onContinue={vi.fn()}
      onDownloadPdf={vi.fn()}
      pathways={pathways}
      rawPathwaysText="## Build the evidence first"
      {...overrides}
    />,
  )
}

describe('PathwaysScreen', () => {
  it('renders pathway titles', () => {
    renderScreen()

    expect(screen.getByText('BUILD THE EVIDENCE FIRST')).toBeTruthy()
    expect(screen.getByText('REFRAME THE BUSINESS CASE')).toBeTruthy()
  })

  it('hides pathway bodies in the collapsed card view', () => {
    renderScreen()

    expect(screen.queryByText('Full evidence pathway body with orientation and conditions.')).toBeNull()
  })

  it('expands the selected pathway when plus is pressed', async () => {
    const user = userEvent.setup()
    renderScreen()

    await user.click(screen.getByRole('button', { name: /expand build the evidence first/i }))

    expect(screen.getByText('Full evidence pathway body with orientation and conditions.')).toBeTruthy()
  })

  it('closes expanded view and returns to collapsed options', async () => {
    const user = userEvent.setup()
    renderScreen()

    await user.click(screen.getByRole('button', { name: /expand build the evidence first/i }))
    await user.click(screen.getByRole('button', { name: /close expanded pathway/i }))

    expect(screen.getByText('BUILD THE EVIDENCE FIRST')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /close expanded pathway/i })).toBeNull()
  })

  it('does not call onContinue when expanding or closing a pathway', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    renderScreen({ onContinue })

    await user.click(screen.getByRole('button', { name: /expand build the evidence first/i }))
    await user.click(screen.getByRole('button', { name: /close expanded pathway/i }))

    expect(onContinue).not.toHaveBeenCalled()
  })

  it('calls onDownloadPdf when the download button is clicked', async () => {
    const user = userEvent.setup()
    const onDownloadPdf = vi.fn()
    renderScreen({ onDownloadPdf })

    await user.click(screen.getByRole('button', { name: /download session pdf/i }))

    expect(onDownloadPdf).toHaveBeenCalledTimes(1)
  })

  it('does not trigger PDF generation when expanding or closing a pathway', async () => {
    const user = userEvent.setup()
    const onDownloadPdf = vi.fn()
    renderScreen({ onDownloadPdf })

    await user.click(screen.getByRole('button', { name: /expand build the evidence first/i }))
    await user.click(screen.getByRole('button', { name: /close expanded pathway/i }))

    expect(onDownloadPdf).not.toHaveBeenCalled()
  })

  it('calls onContinue when Continue is clicked', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    renderScreen({ onContinue })

    await user.click(screen.getByRole('button', { name: /continue/i }))

    expect(onContinue).toHaveBeenCalledTimes(1)
  })

  it('disables Continue while loading', () => {
    renderScreen({ isLoading: true })

    expect((screen.getByRole('button', { name: /continue/i }) as HTMLButtonElement).disabled).toBe(
      true,
    )
  })

  it('renders the error message when provided', () => {
    renderScreen({ error: 'Unable to continue.' })

    expect(screen.getByRole('alert').textContent).toBe('Unable to continue.')
  })

  it('renders raw text fallback when no pathway cards are available', () => {
    renderScreen({
      pathways: [],
      rawPathwaysText: 'Unstructured pathway response from the backend.',
    })

    expect(screen.getByText('Unstructured pathway response from the backend.')).toBeTruthy()
  })
})
