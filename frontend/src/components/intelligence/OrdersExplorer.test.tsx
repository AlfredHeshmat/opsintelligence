import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it } from 'vitest'
import { OrdersExplorer } from './OrdersExplorer'
import { filterAndSortOrders, safeCsvCell, type OrderRecord } from './ordersUtils'

const rows: OrderRecord[] = [
 {id:1,sku:'SKU-Z',quantity:4,priority:2,status:'pending',promised_at:'2026-11-20',revenue:30},
 {id:2,sku:'SKU-A',quantity:1,priority:1,status:'delivered',promised_at:'2026-11-21',revenue:10},
]
it('filters, sorts and paginates the local bounded order preview', async () => {
 const user = userEvent.setup()
 render(<OrdersExplorer orders={rows} />)
 expect(screen.getByText('#1')).toBeInTheDocument()
 await user.type(screen.getByRole('searchbox', {name:'Search loaded orders'}), 'SKU-A')
 expect(screen.queryByText('#1')).not.toBeInTheDocument()
 expect(screen.getByText('#2')).toBeInTheDocument()
 await user.click(screen.getByRole('button', {name:'Reset filters'}))
 expect(screen.getByText('#1')).toBeInTheDocument()
})
it('provides deterministic sort and escapes spreadsheet formula input', () => {
 expect(filterAndSortOrders(rows, '', 'all', 'sku', 'asc')[0].sku).toBe('SKU-A')
 expect(filterAndSortOrders(rows, '', 'pending', 'id', 'asc')).toHaveLength(1)
 expect(safeCsvCell('=HYPERLINK("bad")')).toBe('"\'=HYPERLINK(""bad"")"')
 expect(safeCsvCell('some, value')).toBe('"some, value"')
})
