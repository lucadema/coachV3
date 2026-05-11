/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SynthesisReviewScreen, type SynthesisReviewMode } from './SynthesisReviewScreen'

afterEach(() => {
  cleanup()
})

function renderScreen(overrides: Partial<Parameters<typeof SynthesisReviewScreen>[0]> = {}) {
  return render(
    <SynthesisReviewScreen
      mode="review"
      onAccept={vi.fn()}
      onContinueToPathways={vi.fn()}
      onOpenRefinement={vi.fn()}
      onSubmitRefinement={vi.fn()}
      synthesisText="This is the current synthesis."
      {...overrides}
    />,
  )
}

function getRefinementInput() {
  return screen.getByLabelText(/refinement feedback/i)
}

function getContinueButton() {
  return screen.getByRole('button', { name: /continue/i }) as HTMLButtonElement
}

describe('SynthesisReviewScreen', () => {
  it('renders the synthesis text', () => {
    renderScreen()

    expect(screen.getByText('This is the current synthesis.')).toBeTruthy()
  })

  it('calls onAccept when That’s it is clicked', async () => {
    const user = userEvent.setup()
    const onAccept = vi.fn()
    renderScreen({ onAccept })

    await user.click(screen.getByRole('button', { name: /that’s it/i }))

    expect(onAccept).toHaveBeenCalledTimes(1)
  })

  it('calls onOpenRefinement when Not quite is clicked', async () => {
    const user = userEvent.setup()
    const onOpenRefinement = vi.fn()
    renderScreen({ onOpenRefinement })

    await user.click(screen.getByRole('button', { name: /not quite/i }))

    expect(onOpenRefinement).toHaveBeenCalledTimes(1)
  })

  it('shows refinement textarea in refinement mode', () => {
    renderScreen({ mode: 'refinement_open' })

    expect(getRefinementInput()).toBeTruthy()
  })

  it('disables Submit when refinement text is empty', () => {
    renderScreen({ mode: 'refinement_open' })

    expect(getContinueButton().disabled).toBe(true)
  })

  it('disables Submit when refinement text is whitespace only', async () => {
    const user = userEvent.setup()
    renderScreen({ mode: 'refinement_open' })

    await user.type(getRefinementInput(), '   ')

    expect(getContinueButton().disabled).toBe(true)
  })

  it('enables Submit when refinement text has content', async () => {
    const user = userEvent.setup()
    renderScreen({ mode: 'refinement_open' })

    await user.type(getRefinementInput(), 'Add the market capacity constraint')

    expect(getContinueButton().disabled).toBe(false)
  })

  it('submits refinement text', async () => {
    const user = userEvent.setup()
    const onSubmitRefinement = vi.fn()
    renderScreen({ mode: 'refinement_open', onSubmitRefinement })

    await user.type(getRefinementInput(), 'Add the market capacity constraint')
    await user.click(getContinueButton())

    expect(onSubmitRefinement).toHaveBeenCalledTimes(1)
    expect(onSubmitRefinement).toHaveBeenCalledWith('Add the market capacity constraint')
  })

  it('disables controls while loading', () => {
    renderScreen({ isLoading: true, mode: 'refinement_open' })

    expect((screen.getByRole('button', { name: /that’s it/i }) as HTMLButtonElement).disabled).toBe(
      true,
    )
    expect((screen.getByRole('button', { name: /not quite/i }) as HTMLButtonElement).disabled).toBe(
      true,
    )
    expect((getRefinementInput() as HTMLTextAreaElement).disabled).toBe(true)
    expect(getContinueButton().disabled).toBe(true)
  })

  it('renders the error message when provided', () => {
    renderScreen({ error: 'Unable to update synthesis.' })

    expect(screen.getByRole('alert').textContent).toBe('Unable to update synthesis.')
  })

  it.each<SynthesisReviewMode>(['awaiting_pathways_after_refinement'])(
    'renders continue-to-pathways action in %s mode',
    (mode) => {
      renderScreen({ mode })

      expect(screen.getByRole('button', { name: /continue/i })).toBeTruthy()
      expect(screen.queryByRole('button', { name: /not quite/i })).toBeNull()
    },
  )
})
