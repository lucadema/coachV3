import { describe, expect, it } from 'vitest'
import { sanitizeAccessToken, sanitizeSessionLabel } from './launchContext'

describe('launch context sanitizers', () => {
  it('normalises valid session labels', () => {
    expect(sanitizeSessionLabel(' Pilot-Group_1 ')).toBe('pilot-group_1')
  })

  it('rejects unsafe session labels', () => {
    expect(sanitizeSessionLabel('../pilot')).toBeUndefined()
  })

  it('accepts long opaque access tokens', () => {
    expect(sanitizeAccessToken('abcDEF_1234567890-token')).toBe('abcDEF_1234567890-token')
  })

  it('rejects short access tokens', () => {
    expect(sanitizeAccessToken('short')).toBeUndefined()
  })
})
