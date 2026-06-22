/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { FeedbackQueryScreen } from './FeedbackQueryScreen'
import type { FeedbackFormConfig } from '../types/feedback'

const form: FeedbackFormConfig = {
  show_feedback: true,
  feedback_pack_id: 'glimpse_default',
  survey_query: 'Would you be happy to answer a few quick questions?',
}

afterEach(() => {
  cleanup()
})

describe('FeedbackQueryScreen', () => {
  it('renders the configured survey query', () => {
    render(<FeedbackQueryScreen form={form} onSkip={vi.fn()} onTakeSurvey={vi.fn()} />)

    expect(screen.getByText('Would you be happy to answer a few quick questions?')).toBeTruthy()
  })

  it('falls back only when the configured survey query is blank', () => {
    render(
      <FeedbackQueryScreen
        form={{ ...form, survey_query: '   ' }}
        onSkip={vi.fn()}
        onTakeSurvey={vi.fn()}
      />,
    )

    expect(
      screen.getByText('Would you be happy to answer a few quick questions about your experience?'),
    ).toBeTruthy()
  })

  it('renders and expands the selected pathway when provided', async () => {
    const user = userEvent.setup()
    render(
      <FeedbackQueryScreen
        form={form}
        onSkip={vi.fn()}
        onTakeSurvey={vi.fn()}
        selectedPathway={{
          title: 'Build the evidence first',
          body: 'Full pathway details.',
        }}
      />,
    )

    await user.click(screen.getByRole('button', { name: /build the evidence first/i }))

    expect(screen.getByText('Full pathway details.')).toBeTruthy()
  })

  it('calls the selected action', async () => {
    const user = userEvent.setup()
    const onSkip = vi.fn()
    const onTakeSurvey = vi.fn()
    render(<FeedbackQueryScreen form={form} onSkip={onSkip} onTakeSurvey={onTakeSurvey} />)

    await user.click(screen.getByRole('button', { name: /yes, sure/i }))
    await user.click(screen.getByRole('button', { name: /no thanks/i }))

    expect(onTakeSurvey).toHaveBeenCalledTimes(1)
    expect(onSkip).toHaveBeenCalledTimes(1)
  })
})
