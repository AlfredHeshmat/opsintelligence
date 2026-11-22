import { render, screen } from '@testing-library/react'
import { expect,it } from 'vitest'
import { WorkflowGuide } from './WorkflowGuide'

it('links each stage and announces the active workflow stage',()=>{
 render(<WorkflowGuide activePage="optimization" />)
 expect(screen.getByRole('navigation',{name:/guided operational workflow/i})).toBeInTheDocument()
 expect(screen.getByRole('link',{name:/optimise/i})).toHaveAttribute('href','#optimization')
 expect(screen.getByRole('link',{name:/optimise/i})).toHaveAttribute('aria-current','step')
})
