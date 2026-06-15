import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { App } from './App'

describe('App', () => {
  it('shows the admin token gate before authentication', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: /admin control panel/i })).toBeTruthy()
    expect(screen.getByLabelText(/admin api token/i)).toBeTruthy()
  })
})
