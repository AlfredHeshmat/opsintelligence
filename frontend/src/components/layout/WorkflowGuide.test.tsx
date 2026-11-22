import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect,it } from 'vitest'
import { WorkflowGuide } from './WorkflowGuide'

it('links each stage and announces the active workflow stage',async()=>{
 const user=userEvent.setup()
 render(<WorkflowGuide activePage="optimization" />)
 expect(screen.getByRole('navigation',{name:/guided operational workflow/i})).toBeInTheDocument()
 expect(screen.getByText(/step 3 of 5/i)).toBeInTheDocument()
 const toggle=screen.getByRole('button',{name:/show all steps/i})
 expect(toggle).toHaveAttribute('aria-expanded','false')
 await user.click(toggle)
 expect(toggle).toHaveAttribute('aria-expanded','true')
 expect(screen.getByRole('link',{name:/optimise/i})).toHaveAttribute('href','#optimization')
 expect(screen.getByRole('link',{name:/optimise/i})).toHaveAttribute('aria-current','step')
})
