import { describe, expect, it } from 'vitest'
import { buildApiUrl } from './coachClient'

describe('buildApiUrl', () => {
  it('joins base urls and paths without duplicate slashes', () => {
    expect(buildApiUrl('/user_message', 'http://127.0.0.1:8000/')).toBe(
      'http://127.0.0.1:8000/user_message',
    )
    expect(buildApiUrl('session_initialise', 'http://127.0.0.1:8000')).toBe(
      'http://127.0.0.1:8000/session_initialise',
    )
  })
})
