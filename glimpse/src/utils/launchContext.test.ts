import { afterEach, describe, expect, it, vi } from 'vitest'
import { getLaunchContext, sanitizeAccessToken, sanitizeSessionLabel } from './launchContext'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('launchContext', () => {
  it('returns an empty context when no session_label is present', () => {
    expect(getLaunchContext()).toEqual({})
  })

  it('sanitises a valid session_label from the URL', () => {
    vi.stubGlobal('window', {
      location: {
        search: '?session_label=%20Luca.Test-1_%20',
      },
    })

    expect(getLaunchContext()).toEqual({ sessionLabel: 'luca.test-1_' })
  })

  it('sanitises a valid pilot token from the URL', () => {
    vi.stubGlobal('window', {
      location: {
        search: '?t=AbC_1234567890-token_value',
      },
    })

    expect(getLaunchContext()).toEqual({ accessToken: 'AbC_1234567890-token_value' })
  })

  it('supports token as a readable alias for t', () => {
    vi.stubGlobal('window', {
      location: {
        search: '?token=XyZ_1234567890-token_value&session_label=Pilot.One',
      },
    })

    expect(getLaunchContext()).toEqual({
      accessToken: 'XyZ_1234567890-token_value',
      sessionLabel: 'pilot.one',
    })
  })

  it('ignores invalid labels', () => {
    expect(sanitizeSessionLabel('this is invalid')).toBeUndefined()
    expect(sanitizeSessionLabel('luca@example.com')).toBeUndefined()
    expect(sanitizeSessionLabel('a'.repeat(65))).toBeUndefined()
    expect(sanitizeSessionLabel('')).toBeUndefined()
  })

  it('ignores invalid access tokens', () => {
    expect(sanitizeAccessToken('short')).toBeUndefined()
    expect(sanitizeAccessToken('has spaces in token')).toBeUndefined()
    expect(sanitizeAccessToken('x'.repeat(257))).toBeUndefined()
    expect(sanitizeAccessToken('')).toBeUndefined()
  })
})
