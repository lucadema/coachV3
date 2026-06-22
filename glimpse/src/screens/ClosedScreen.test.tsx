/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ClosedScreen } from './ClosedScreen'

afterEach(() => {
  cleanup()
})

describe('ClosedScreen', () => {
  it('renders the final close message', () => {
    render(<ClosedScreen onDownloadPdf={vi.fn()} onStartNewSession={vi.fn()} />)

    expect(screen.getByText('We hope you’ve enjoyed this glimpse of Aether')).toBeTruthy()
    expect(
      screen.getByText('Feel free to download a copy of your session and to start a new one.'),
    ).toBeTruthy()
  })

  it('moves the PDF download control to the closed screen', async () => {
    const onDownloadPdf = vi.fn()
    render(<ClosedScreen onDownloadPdf={onDownloadPdf} onStartNewSession={vi.fn()} />)

    screen.getByText(
      'Keep a record by downloading the problem statement and resolution pathways from this session. The download does not include the coaching conversation that produced them.',
    )
    screen.getByRole('button', { name: /download session pdf/i }).click()

    expect(onDownloadPdf).toHaveBeenCalledTimes(1)
  })
})
