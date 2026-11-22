export type OrderRecord = { id:number; sku:string; quantity:number; priority:number; status:string; promised_at:string; revenue:number }
export type SortKey = 'id' | 'sku' | 'quantity' | 'priority' | 'status' | 'promised_at'

// Prefix dangerous spreadsheet formulas. All CSV output is derived from the displayed synthetic records.
export function safeCsvCell(value: string | number): string {
  const text = String(value)
  const safe = /^[\s]*[=+@\-\t\r]/.test(text) ? `'${text}` : text
  return `"${safe.replace(/"/g, '""')}"`
}

export function filterAndSortOrders(orders: OrderRecord[], query: string, status: string, key: SortKey, direction: 'asc' | 'desc'): OrderRecord[] {
  const normalized = query.trim().toLowerCase()
  return orders.filter(order => {
    const matchesQuery = !normalized || `${order.id} ${order.sku} ${order.status} ${order.promised_at}`.toLowerCase().includes(normalized)
    return matchesQuery && (status === 'all' || order.status === status)
  }).sort((a, b) => {
    const left = a[key]
    const right = b[key]
    const comparison = typeof left === 'number' && typeof right === 'number' ? left - right : String(left).localeCompare(String(right), undefined, { numeric: true })
    return direction === 'asc' ? comparison : -comparison
  })
}

