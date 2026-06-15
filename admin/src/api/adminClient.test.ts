import { describe, expect, it } from 'vitest'
import { buildAdminApiUrl } from './adminClient'

describe('adminClient', () => {
  it('builds API URLs without double slashes', () => {
    expect(buildAdminApiUrl('/admin/enterprises', 'http://127.0.0.1:8010/')).toBe(
      'http://127.0.0.1:8010/admin/enterprises',
    )
  })
})
