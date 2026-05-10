/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProblemInputScreen } from './ProblemInputScreen'

afterEach(() => {
  cleanup()
})

function getContinueButton() {
  return screen.getByRole('button', { name: /continue/i }) as HTMLButtonElement
}

function getProblemInput() {
  return screen.getByLabelText(/describe your professional challenge/i)
}

describe('ProblemInputScreen', () => {
  it('disables Continue when the input is empty', () => {
    render(<ProblemInputScreen onContinue={vi.fn()} />)

    expect(getContinueButton().disabled).toBe(true)
  })

  it('disables Continue when the input is whitespace only', async () => {
    const user = userEvent.setup()
    render(<ProblemInputScreen onContinue={vi.fn()} />)

    await user.type(getProblemInput(), '   ')

    expect(getContinueButton().disabled).toBe(true)
  })

  it('enables Continue when the user enters text', async () => {
    const user = userEvent.setup()
    render(<ProblemInputScreen onContinue={vi.fn()} />)

    await user.type(getProblemInput(), 'I need to reset expectations with my team')

    expect(getContinueButton().disabled).toBe(false)
  })

  it('calls onContinue with the entered text when Continue is clicked', async () => {
    const user = userEvent.setup()
    const onContinue = vi.fn()
    render(<ProblemInputScreen onContinue={onContinue} />)

    await user.type(getProblemInput(), 'I need to reset expectations with my team')
    await user.click(getContinueButton())

    expect(onContinue).toHaveBeenCalledTimes(1)
    expect(onContinue).toHaveBeenCalledWith('I need to reset expectations with my team')
  })

  it('disables Continue while loading', () => {
    render(
      <ProblemInputScreen
        initialValue="I need to reset expectations with my team"
        isLoading
        onContinue={vi.fn()}
      />,
    )

    expect(getContinueButton().disabled).toBe(true)
  })

  it('renders the error message when provided', () => {
    render(<ProblemInputScreen error="Something went wrong." onContinue={vi.fn()} />)

    expect(screen.getByRole('alert').textContent).toBe('Something went wrong.')
  })
})
