/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { FeedbackScreen } from './FeedbackScreen'
import {
  createDefaultFeedbackState,
  type FeedbackFormConfig,
  type FeedbackState,
} from '../types/feedback'

const defaultFeedbackForm: FeedbackFormConfig = {
  show_feedback: true,
  feedback_pack_id: 'glimpse_default',
  title: 'Before you go, please tell us what you thought of the Aether Glimpse experience.',
  questions: [
    {
      id: 'helped_think_differently',
      type: 'boolean',
      text: 'Did Aether help you think about your challenge in a new way?',
      required: false,
    },
    {
      id: 'organisational_benefit',
      type: 'boolean',
      text: 'Can you see how access to this kind of thinking support could be benefical to a whole organisation',
      required: false,
    },
    {
      id: 'pilot_stage',
      type: 'single_select',
      text: 'Which stage are you in?',
      required: false,
      placeholder: 'CHOOSE AN OPTION',
      options: [
        {
          value: 'exploring',
          label: 'Exploring the idea',
        },
        {
          value: 'piloting',
          label: 'Piloting with a group',
        },
      ],
    },
    {
      id: 'valuable_moments',
      type: 'multi_select',
      text: 'What was the most valuable moment in this session for you?',
      required: false,
      options: [
        {
          value: 'being_asked_a_question',
          label: 'Being asked a question I hadn’t thought to ask myself',
        },
        {
          value: 'structured_pathways',
          label: 'Receiving structured pathways rather than a generic answer',
        },
        {
          value: 'guided_not_told',
          label: 'The feeling that I was being guided rather than just given information',
        },
        {
          value: 'confidential_space',
          label: 'Having a confidential space to think without judgement',
        },
      ],
    },
  ],
}

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

  return (
    <FeedbackScreen
      feedback={feedback}
      form={defaultFeedbackForm}
      onChange={setFeedback}
      onClose={onClose}
    />
  )
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
      name: /yes, did aether help you think/i,
    })
    const noButton = screen.getByRole('button', {
      name: /no, can you see how access/i,
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

  it('renders single-select options with the shared dropdown treatment', async () => {
    const user = userEvent.setup()
    render(<FeedbackHarness />)

    await user.click(screen.getByRole('button', { name: /^choose an option$/i }))

    expect(screen.getByText('Exploring the idea')).toBeTruthy()
    expect(screen.getByText('Piloting with a group')).toBeTruthy()
  })

  it('selecting a single-select option updates the local value', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<FeedbackHarness onClose={onClose} />)

    await user.click(screen.getByRole('button', { name: /^choose an option$/i }))
    await user.click(screen.getByRole('button', { name: /piloting with a group/i }))
    await user.click(screen.getByRole('button', { name: /^continue$/i }))

    expect(onClose).toHaveBeenCalledWith({
      pilot_stage: 'piloting',
    })
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

  it('Continue calls onClose with the current feedback data', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<FeedbackHarness onClose={onClose} />)

    await user.click(
      screen.getByRole('button', {
        name: /yes, did aether help you think/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    await user.click(
      screen.getByRole('button', {
        name: /receiving structured pathways rather than a generic answer/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /^continue$/i }))

    expect(onClose).toHaveBeenCalledWith({
      helped_think_differently: true,
      valuable_moments: ['structured_pathways'],
    })
  })

  it('does not call the backend while completing the local survey', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn<typeof fetch>()
    vi.stubGlobal('fetch', fetchMock)
    render(<FeedbackHarness />)

    await user.click(
      screen.getByRole('button', {
        name: /no, did aether help you think/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    await user.click(
      screen.getByRole('button', {
        name: /the feeling that i was being guided rather than just given information/i,
      }),
    )
    await user.click(screen.getByRole('button', { name: /^continue$/i }))

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
