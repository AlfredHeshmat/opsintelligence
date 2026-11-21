import { useEffect, useState } from 'react'

type Status = 'checking' | 'connected' | 'unavailable'

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
).replace(/\/$/, '')

const messages = {
  checking: {
    title: 'Checking connection',
    description: 'Contacting the operations API.',
    colour: 'bg-warning',
  },
  connected: {
    title: 'Backend connected',
    description:
      'The API is responding normally. Database readiness is checked separately.',
    colour: 'bg-success',
  },
  unavailable: {
    title: 'Backend unavailable',
    description:
      'We could not reach a healthy API. Check that FastAPI is running and try again.',
    colour: 'bg-danger',
  },
}

export function ApiStatus() {
  const [status, setStatus] = useState<Status>('checking')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    const timeout = window.setTimeout(() => controller.abort(), 5000)

    async function checkHealth() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/health`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Health request failed')
        }

        const data: unknown = await response.json()

        if (
          typeof data !== 'object' ||
          data === null ||
          !('status' in data) ||
          data.status !== 'healthy'
        ) {
          throw new Error('Unexpected health response')
        }

        if (active) setStatus('connected')
      } catch {
        if (active) setStatus('unavailable')
      } finally {
        window.clearTimeout(timeout)
      }
    }

    void checkHealth()

    return () => {
      active = false
      controller.abort()
      window.clearTimeout(timeout)
    }
  }, [attempt])

  const message = messages[status]

  function retry() {
    setStatus('checking')
    setAttempt((value) => value + 1)
  }

  return (
    <section
      id="connection"
      aria-labelledby="connection-title"
      className="scroll-mt-24 rounded-2xl border border-line bg-surface p-6 shadow-panel"
    >
      <h2 id="connection-title" className="text-base font-semibold">
        API connection
      </h2>

      <div role="status" aria-live="polite" className="mt-6">
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className={`size-2.5 shrink-0 rounded-full ${message.colour}`}
          />
          <p className="font-semibold">{message.title}</p>
        </div>

        <p className="mt-3 text-sm leading-6 text-muted">
          {message.description}
        </p>
      </div>

      <div className="mt-6 border-t border-line pt-5">
        <button
          type="button"
          onClick={retry}
          disabled={status === 'checking'}
          className="rounded-lg border border-line px-4 py-2.5 text-sm font-semibold transition-colors hover:bg-canvas disabled:opacity-50"
        >
          {status === 'checking' ? 'Checking…' : 'Check again'}
        </button>
      </div>
    </section>
  )
}
