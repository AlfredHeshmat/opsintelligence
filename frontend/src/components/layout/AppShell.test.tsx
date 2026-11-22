import { render, screen } from '@testing-library/react'
import { act } from 'react'
import { afterEach, expect, it } from 'vitest'
import { AppShell } from './AppShell'

afterEach(() => { window.location.hash = '#workspace' })

it('groups the navigation and marks the active destination', () => {
 window.location.hash = '#industry-pilots'
 render(<AppShell><p>Page content</p></AppShell>)
 expect(screen.getByText('Page content')).toBeInTheDocument()
 const links = screen.getAllByRole('link', { name: /industry solver lab/i })
 expect(links[0]).toHaveAttribute('aria-current', 'page')
 expect(screen.getAllByText('DECISION INTELLIGENCE').length).toBeGreaterThan(0)
})

it('updates the active navigation state when the URL hash changes', () => {
 window.location.hash = '#workspace'
 render(<AppShell><p>Page content</p></AppShell>)
 act(() => { window.location.hash = '#optimization'; window.dispatchEvent(new HashChangeEvent('hashchange')) })
 expect(screen.getAllByRole('link', { name: /^optimisation$/i })[0]).toHaveAttribute('aria-current','page')
})

