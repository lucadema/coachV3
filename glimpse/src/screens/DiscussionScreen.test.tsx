/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DiscussionScreen } from './DiscussionScreen'

afterEach(() => {
  cleanup()
})

function getContinueButton() {
  return screen.getByRole('button', { name: /continue/i }) as HTMLButtonElement
}

function getReplyInput() {
  return screen.getByLabelText(/reply to aether/i)
}

describe('DiscussionScreen', () => {
  it('renders the coach message', () => {
    render(<DiscussionScreen coachMessage="What feels most unresolved?" onContinue={vi.fn()} />)

    expect(screen.getByText('What feels most unresolved?')).toBeTruthy()
  })

  it('disables Continue when input is empty', () => {
    render(<DiscussionScreen coachMessage="What feels most unresolved?" onContinue={vi.fn()} />)

    expect(getContinueButton().disabled).toBe(true)
  })

  it('disables Continue when input is whitespace only', async () => {
    const user = userEvent.setup()
    render(<DiscussionScreen coachMessage="What feels most unresolved?" onContinue={vi.fn()} />)

    await user.type(getReplyInput(), '   ')

    expect(getContinueButton().disabled).toBe(true)
  })

  it('enables Continue when the user enters text', async () => {
    const user = userEvent.setup()
    render(<DiscussionScreen coachMessage="What feels most unresolved?" onContinue={vi.fn()} />)

    await user.type(getReplyInput(), 'The tradeoff is unclear')

    expect(getContinueButton().disabled).toBe(false)
  })

  it('calls onContinue with the entered text', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    render(<DiscussionScreen coachMessage="What feels most unresolved?" onContinue={onContinue} />)

    await user.type(getReplyInput(), 'The tradeoff is unclear')
    await user.click(getContinueButton())

    expect(onContinue).toHaveBeenCalledTimes(1)
    expect(onContinue).toHaveBeenCalledWith('The tradeoff is unclear')
  })

  it('disables input and Continue while loading', () => {
    render(
      <DiscussionScreen
        coachMessage="What feels most unresolved?"
        isLoading
        onContinue={vi.fn()}
      />,
    )

    expect((getReplyInput() as HTMLTextAreaElement).disabled).toBe(true)
    expect(getContinueButton().disabled).toBe(true)
  })

  it('renders the error message when provided', () => {
    render(
      <DiscussionScreen
        coachMessage="What feels most unresolved?"
        error="Unable to send reply."
        onContinue={vi.fn()}
      />,
    )

    expect(screen.getByRole('alert').textContent).toBe('Unable to send reply.')
  })
})
