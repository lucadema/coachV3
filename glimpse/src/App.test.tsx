/* @vitest-environment jsdom */

import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { downloadSessionPdf } from './pdf/sessionPdfDownload'

vi.mock('./pdf/sessionPdfDownload', () => ({
  downloadSessionPdf: vi.fn(),
}))

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: {
      'Content-Type': 'application/json',
    },
    status: 200,
    ...init,
  })
}

const feedbackFormResponse = {
  show_feedback: true,
  feedback_pack_id: 'glimpse_default',
  title: 'Before you go, please tell us what you thought of the Aether Glimpse experience.',
  survey_query: 'Would you be happy to answer a few quick questions about your experience?',
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
      id: 'valuable_moments',
      type: 'multi_select',
      text: 'What was the most valuable moment in this session for you?',
      required: false,
      options: [
        {
          value: 'structured_pathways',
          label: 'Receiving structured pathways rather than a generic answer',
        },
      ],
    },
  ],
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  window.history.replaceState({}, '', '/')
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: undefined,
    writable: true,
  })
  vi.useRealTimers()
})

function stubMatchMedia(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: vi.fn((query: string): MediaQueryList => ({
      addEventListener: vi.fn(),
      addListener: vi.fn(),
      dispatchEvent: vi.fn(),
      matches,
      media: query,
      onchange: null,
      removeEventListener: vi.fn(),
      removeListener: vi.fn(),
    })),
    writable: true,
  })
}

async function advanceToInformationScreen() {
  await act(async () => {
    vi.advanceTimersByTime(3000)
  })
  await act(async () => {
    vi.advanceTimersByTime(4000)
  })

  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: /continue/i }))
}

async function flushPromises() {
  await act(async () => undefined)
}

function getLastContinueButton() {
  const buttons = screen.getAllByRole('button', { name: /continue/i })

  return buttons[buttons.length - 1]
}

describe('App experience mode', () => {
  it('defaults to the desktop experience when viewport detection is unavailable', () => {
    render(<App />)

    expect(screen.getByAltText('Aether')).toBeTruthy()
    expect(screen.queryByText('Aether Glimpse mobile experience')).toBeNull()
  })

  it('renders the mobile placeholder at the mobile breakpoint', () => {
    stubMatchMedia(true)

    render(<App />)

    expect(screen.getByTestId('mobile-experience')).toBeTruthy()
  })

  it.each([360, 375, 390, 414, 430])(
    'renders the mobile branch at %ipx viewport width',
    (width) => {
      Object.defineProperty(window, 'innerWidth', {
        configurable: true,
        value: width,
        writable: true,
      })
      stubMatchMedia(width <= 767)

      render(<App />)

      expect(screen.getByTestId('mobile-experience')).toBeTruthy()
    },
  )

  it('allows the desktop experience query override', () => {
    stubMatchMedia(true)
    window.history.replaceState({}, '', '/?experience=desktop')

    render(<App />)

    expect(screen.getByAltText('Aether')).toBeTruthy()
    expect(screen.queryByTestId('mobile-experience')).toBeNull()
  })

  it('allows the mobile experience query override', () => {
    stubMatchMedia(false)
    window.history.replaceState({}, '', '/?experience=mobile')

    render(<App />)

    expect(screen.getByTestId('mobile-experience')).toBeTruthy()
  })
})

describe('App backend connection flow', () => {
  it('shows a recoverable error if session initialisation fails', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse({ detail: 'Backend unavailable' }, { status: 500 }))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    await advanceToInformationScreen()
    fireEvent.click(screen.getByRole('button', { name: /start session/i }))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/session_initialise$/),
      expect.objectContaining({
        method: 'GET',
      }),
    )
    await act(async () => undefined)

    expect(screen.getByRole('alert').textContent).toBe('Backend unavailable')
  })

  it('shows the discussion screen when the first backend turn resolves to coaching', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(getLastContinueButton())
    await flushPromises()

    expect(screen.getByText('What feels most unresolved?')).toBeTruthy()
    expect(screen.getByLabelText(/reply to aether/i)).toBeTruthy()
  })

  it('shows synthesis review when coaching resolves to synthesis_review', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()

    expect(screen.getByText('Here is the synthesis.')).toBeTruthy()
    expect(screen.getByRole('button', { name: /that's it/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /not quite/i })).toBeTruthy()
  })

  it('shows pathways screen when accepted synthesis resolves to pathways', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: '## Pathway one\nDetails',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'presenting',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /that's it/i }))
    await flushPromises()

    expect(screen.getByText('PATHWAY ONE')).toBeTruthy()
    expect(screen.queryByText('Backend response placeholder')).toBeNull()

    const callsBeforeDownload = fetchMock.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /download session pdf/i }))

    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeDownload)
    expect(downloadSessionPdf).toHaveBeenCalledWith({
      pathways: [{ title: 'Pathway one', body: 'Details' }],
      problemStatement: 'I need to reset expectations with my team',
      synthesis: 'Here is the synthesis.',
    })
  })

  it('continues from pathways to local feedback, then closes locally', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: '## Pathway one\nDetails',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Closure text',
          session: {
            session_id: 'session-1',
            stage: 'closure',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(jsonResponse(feedbackFormResponse))
      .mockResolvedValueOnce(jsonResponse({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(getLastContinueButton())
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /that's it/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /heart pathway one/i }))
    fireEvent.click(getLastContinueButton())
    await flushPromises()

    const postBodies = fetchMock.mock.calls
      .map(([, options]) => options?.body)
      .filter((body): body is string => typeof body === 'string')

    expect(postBodies.some((body) => body.includes('"user_message":"continue"'))).toBe(true)
    expect(postBodies.every((body) => !body.includes('pathway_selected:'))).toBe(true)
    expect(
      screen.getByText('Would you be happy to answer a few quick questions about your experience?'),
    ).toBeTruthy()
    expect(screen.getByText('PATHWAY ONE')).toBeTruthy()
    expect(screen.queryByText('Closure text')).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: /yes, sure/i }))

    const callsBeforeClose = fetchMock.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /^continue$/i }))

    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeClose + 1)
    const closeBody = fetchMock.mock.calls.at(-1)?.[1]?.body
    expect(typeof closeBody === 'string' && closeBody.includes('"feedback_pack_id":"glimpse_default"')).toBe(true)
    expect(screen.getByText('We hope you’ve enjoyed this glimpse of Aether')).toBeTruthy()
  })

  it('keeps refined synthesis on synthesis review when backend returns pathways preparing', async () => {
    vi.useFakeTimers()

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the refined synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'preparing',
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /not quite/i }))
    fireEvent.change(screen.getByLabelText(/refinement feedback/i), {
      target: { value: 'Add the budget constraint' },
    })
    fireEvent.click(getLastContinueButton())
    await flushPromises()

    expect(screen.getByText('Here is the refined synthesis.')).toBeTruthy()
    expect(screen.getAllByRole('button', { name: /continue/i }).length).toBeGreaterThan(0)
    expect(screen.queryByRole('button', { name: /not quite/i })).toBeNull()
  })

  it('completes the backend-connected journey in the mobile experience', async () => {
    vi.useFakeTimers()
    stubMatchMedia(true)
    window.history.replaceState({}, '', '/?experience=mobile')

    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: 'session-1',
          stage: 'classification',
          state: 'evaluating',
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'What feels most unresolved?',
          session: {
            session_id: 'session-1',
            stage: 'coaching',
            state: 'guiding',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Here is the synthesis.',
          session: {
            session_id: 'session-1',
            stage: 'synthesis',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: '## Pathway one\nDetails',
          session: {
            session_id: 'session-1',
            stage: 'pathways',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          coach_message: 'Closure text',
          session: {
            session_id: 'session-1',
            stage: 'closure',
            state: 'presenting',
          },
        }),
      )
      .mockResolvedValueOnce(jsonResponse(feedbackFormResponse))
      .mockResolvedValueOnce(jsonResponse({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await advanceToInformationScreen()

    fireEvent.click(screen.getByRole('button', { name: /start session/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/describe your professional challenge/i), {
      target: { value: 'I need to reset expectations with my team' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.change(screen.getByLabelText(/reply to aether/i), {
      target: { value: 'The tradeoff is unclear' },
    })
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()
    fireEvent.click(screen.getByRole('button', { name: /that's it/i }))
    await flushPromises()

    expect(screen.getByText('PATHWAY ONE')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /expand pathway one/i }))
    expect(screen.getByText('Details')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /close expanded pathway/i }))
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await flushPromises()

    expect(
      screen.getByText('Would you be happy to answer a few quick questions about your experience?'),
    ).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /yes, sure/i }))
    fireEvent.click(
      screen.getByRole('button', {
        name: /yes, did aether help you think/i,
      }),
    )
    fireEvent.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    fireEvent.click(
      screen.getByRole('button', {
        name: /receiving structured pathways rather than a generic answer/i,
      }),
    )
    fireEvent.click(screen.getByRole('button', { name: /choose all options that apply/i }))
    fireEvent.click(screen.getByRole('button', { name: /^continue$/i }))

    expect(screen.getByText(/We hope/i)).toBeTruthy()
    expect(screen.queryByText('Closure text')).toBeNull()
  })
})
