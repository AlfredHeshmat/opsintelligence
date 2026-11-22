import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it } from 'vitest'
import { WorkspaceHelp } from './WorkspaceHelp'

it('reveals contextual guidance on demand with accessible expanded state',async()=>{
 const user=userEvent.setup()
 render(<WorkspaceHelp title="How does it work?">This is model guidance.</WorkspaceHelp>)
 const toggle=screen.getByRole('button',{name:/how does it work/i})
 expect(toggle).toHaveAttribute('aria-expanded','false')
 expect(screen.queryByText('This is model guidance.')).not.toBeInTheDocument()
 await user.click(toggle)
 expect(toggle).toHaveAttribute('aria-expanded','true')
 expect(screen.getByText('This is model guidance.')).toBeInTheDocument()
})
