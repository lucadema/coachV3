/* @vitest-environment jsdom */

import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { ClosedScreen } from './ClosedScreen'

afterEach(() => {
  cleanup()
})

describe('ClosedScreen', () => {
  it('renders the final close message', () => {
    render(<ClosedScreen />)

    expect(screen.getByText('We hope you’ve enjoyed this glimpse of Aether')).toBeTruthy()
  })
})
