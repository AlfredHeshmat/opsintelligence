import { render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { AccessGate } from './AccessGate'

it('public deployment only offers the synthetic demo, never enterprise sign-in', () => {
  render(<AccessGate onChoose={vi.fn()} publicDemoOnly />)
  expect(screen.getByRole('button', { name: /enter demo workspace/i })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /sign in or create account/i })).not.toBeInTheDocument()
  expect(screen.getByText(/interactive public demonstration uses synthetic/i)).toBeInTheDocument()
})
