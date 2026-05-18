import { afterEach, describe, expect, it, vi } from 'vitest'
import { getLaunchContext, sanitizeSessionLabel } from './launchContext'

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

  it('ignores invalid labels', () => {
    expect(sanitizeSessionLabel('this is invalid')).toBeUndefined()
    expect(sanitizeSessionLabel('luca@example.com')).toBeUndefined()
    expect(sanitizeSessionLabel('a'.repeat(65))).toBeUndefined()
    expect(sanitizeSessionLabel('')).toBeUndefined()
  })
})
