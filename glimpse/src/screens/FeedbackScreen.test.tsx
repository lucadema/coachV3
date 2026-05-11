/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { FeedbackScreen } from './FeedbackScreen'
import { createDefaultFeedbackState, type FeedbackState } from '../types/feedback'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function FeedbackHarness({
  initialFeedback = createDefaultFeedbackState(),
  onClose = vi.fn(),
}: {
  initialFeedback?: FeedbackState
  onClose?: (feedback: FeedbackState) => void
}) {
  const [feedback, setFeedback] = useState(initialFeedback)

  return <FeedbackScreen feedback={feedback} onChange={setFeedback} onClose={onClose} />
}

describe('FeedbackScreen', () => {
  it('renders both yes/no questions', () => {
    render(<FeedbackHarness />)

    expect(
      screen.getByText('Did Aether help you think about your challenge in a new way?'),
    ).toBeTruthy()
    expect(
      screen.getByText(
        'Can you see how access to this kind of thinking support could be benefical to a whole organisation',
      ),
    ).toBeTruthy()
  })

  it('selecting Yes and No updates the local values', async () => {
    const user = userEvent.setup()
    render(<FeedbackHarness />)

    const yesButton = screen.getByRole('button', {
      name: /yes, aether helped me think about my challenge/i,
    })
    const noButton = screen.getByRole('button', {
      name: /no, i cannot see organisational benefit/i,
    })

    await user.click(yesButton)
    await user.click(noButton)

    expect(yesButton.getAttribute('aria-pressed')).toBe('true')
    expect(noButton.getAttribute('aria-pressed')).toBe('true')
  })

  it('renders multi-select options when the dropdown opens', async () => {
    const user = userEvent.setup()
    render(<FeedbackHarness />)

    await user.click(screen.getByRole('button', { name: /choose all options that apply/i }))

    expect(screen.getByText('Being asked a question I hadn’t thought to ask myself')).toBeTruthy()
    expect(
      screen.getByText('Having a confidential space to think without judgement'),
    ).toBeTruthy()
  })

  it('selecting multiple valuable moments updates the local list', async () => {
    const user = userEvent.setup()
    render(<FeedbackHarness />)

    await user.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    const questionOption = screen.getByRole('button', {
      name: /being asked a question i hadn’t thought to ask myself/i,
    })
    const confidentialOption = screen.getByRole('button', {
      name: /having a confidential space to think without judgement/i,
    })

    await user.click(questionOption)
    await user.click(confidentialOption)

    expect(questionOption.getAttribute('aria-pressed')).toBe('true')
    expect(confidentialOption.getAttribute('aria-pressed')).toBe('true')
  })

  it('Close calls onClose with the current feedback data', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<FeedbackHarness onClose={onClose} />)

    await user.click(
      screen.getByRole('button', {
        name: /yes, aether helped me think about my challenge/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    await user.click(
      screen.getByRole('button', {
        name: /receiving structured pathways rather than a generic answer/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /^close$/i }))

    expect(onClose).toHaveBeenCalledWith({
      helpedThinkDifferently: true,
      organisationalBenefit: null,
      valuableMoments: ['Receiving structured pathways rather than a generic answer'],
    })
  })

  it('does not call the backend while completing the local survey', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn<typeof fetch>()
    vi.stubGlobal('fetch', fetchMock)
    render(<FeedbackHarness />)

    await user.click(
      screen.getByRole('button', {
        name: /no, aether did not help me think about my challenge/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    await user.click(
      screen.getByRole('button', {
        name: /the feeling that i was being guided rather than just given information/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /^close$/i }))

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
