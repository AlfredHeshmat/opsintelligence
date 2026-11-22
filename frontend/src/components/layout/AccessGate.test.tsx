import { render,screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect,it,vi } from 'vitest'
import { AccessGate } from './AccessGate'

it('offers a no-login demo choice and explicit enterprise sign-in', async()=>{
 const onChoose=vi.fn()
 const user=userEvent.setup()
 render(<AccessGate onChoose={onChoose}/> )
 expect(screen.getByRole('heading',{name:/choose how to continue/i})).toBeInTheDocument()
 await user.click(screen.getByRole('button',{name:/enter demo workspace/i}))
 expect(onChoose).toHaveBeenCalledWith('demo')
 await user.click(screen.getByRole('button',{name:/continue to secure sign in/i}))
 expect(onChoose).toHaveBeenCalledWith('enterprise')
})

it('explains demo versus private enterprise access without promising unrestricted data',async()=>{
 const user=userEvent.setup()
 render(<AccessGate onChoose={()=>{}}/>)
 await user.click(screen.getByRole('button',{name:/what does each mode allow/i}))
 expect(screen.getByText(/no access to enterprise identities or credentials/i)).toBeInTheDocument()
})
