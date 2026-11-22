import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it } from 'vitest'
import { TrendExplorer } from './TrendExplorer'

it('lets analysts explore daily order and delay measures without changing backend data', async () => {
 const user=userEvent.setup()
 render(<TrendExplorer trend={[{date:'2026-11-20',orders:8,delayed:2},{date:'2026-11-21',orders:12,delayed:3}]} />)
 expect(screen.getByText('20')).toBeInTheDocument()
 await user.selectOptions(screen.getByRole('combobox',{name:'Chart measure'}),'delayed')
 expect(screen.getByText('5')).toBeInTheDocument()
 await user.click(screen.getByRole('button',{name:/2026-11-20: 2 delayed/}))
 expect(screen.getByText('2 recorded delays')).toBeInTheDocument()
})
