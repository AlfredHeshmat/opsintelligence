import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { it, expect } from 'vitest'
import { OrganisationWorkspace } from './OrganisationWorkspace'

it('offers invitation acceptance to a new employee without requiring public company signup', async () => {
 const user = userEvent.setup()
 render(<OrganisationWorkspace />)
 expect(screen.getByRole('button', {name: /have an employee invitation code/i})).toBeInTheDocument()
 await user.click(screen.getByRole('button', {name: /have an employee invitation code/i}))
 expect(screen.getByLabelText(/invitation code/i)).toBeInTheDocument()
 expect(screen.getByLabelText(/invited email/i)).toBeInTheDocument()
 expect(screen.getByLabelText(/create employee password/i)).toBeInTheDocument()
 expect(screen.getByRole('button', {name: /accept invitation and create account/i})).toBeInTheDocument()
})
