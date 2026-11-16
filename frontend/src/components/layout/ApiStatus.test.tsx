import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'

import { ApiStatus } from './ApiStatus'

function healthyResponse() {
  return {
    ok: true,
    json: async () => ({ status: 'healthy' }),
  }
}

it('shows a connected status when the API is healthy', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(healthyResponse()))

  render(<ApiStatus />)

  expect(await screen.findByText('Backend connected')).toBeInTheDocument()

  expect(screen.getByRole('button', { name: 'Check again' })).toBeEnabled()
})

it('shows an unavailable status when the network request fails', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
  )

  render(<ApiStatus />)

  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()
})

it('reconnects when the user retries after a failure', async () => {
  const user = userEvent.setup()

  const fetchMock = vi
    .fn()
    .mockRejectedValueOnce(new TypeError('Failed to fetch'))
    .mockResolvedValueOnce(healthyResponse())

  vi.stubGlobal('fetch', fetchMock)

  render(<ApiStatus />)

  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Check again' }))

  expect(await screen.findByText('Backend connected')).toBeInTheDocument()

  expect(fetchMock).toHaveBeenCalledTimes(2)
})

it('shows unavailable when the API returns an HTTP error', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
    }),
  )

  render(<ApiStatus />)

  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()
})

it('rejects an unexpected health response', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'unexpected' }),
    }),
  )

  render(<ApiStatus />)

  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()
})
