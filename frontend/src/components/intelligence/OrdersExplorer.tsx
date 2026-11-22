import { useMemo, useState } from 'react'
import { safeCsvCell, filterAndSortOrders } from './ordersUtils'
import type { OrderRecord, SortKey } from './ordersUtils'

const PAGE_SIZE = 10
const columns: { key: SortKey; title: string }[] = [
  { key: 'id', title: 'Order ID' }, { key: 'sku', title: 'SKU' },
  { key: 'quantity', title: 'Units' }, { key: 'priority', title: 'Priority' },
  { key: 'status', title: 'Status' }, { key: 'promised_at', title: 'Promised date' },
]

export function OrdersExplorer({ orders }: { orders: OrderRecord[] }) {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [sortKey, setSortKey] = useState<SortKey>('id')
  const [direction, setDirection] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)
  const statuses = useMemo(() => [...new Set(orders.map(item => item.status))].sort(), [orders])
  const filtered = useMemo(() => filterAndSortOrders(orders, query, status, sortKey, direction), [orders, query, status, sortKey, direction])
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, pages)
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  function updateSort(key: SortKey) {
    setSortKey(key)
    setDirection(previous => sortKey === key && previous === 'asc' ? 'desc' : 'asc')
    setPage(1)
  }
  function exportCsv() {
    const header = columns.map(col => safeCsvCell(col.title)).join(',')
    const records = filtered.map(item => columns.map(col => safeCsvCell(item[col.key])).join(','))
    const blob = new Blob([[header, ...records].join('\r\n')], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'opsintelligence-synthetic-orders.csv'
    document.body.append(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return <section id="orders" aria-labelledby="orders-heading" className="enterprise-panel mt-6 scroll-mt-24 p-5 sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><p className="eyebrow">Operations / source records</p><h2 id="orders-heading" className="mt-2 text-xl font-semibold">Operational orders explorer</h2><p className="mt-2 max-w-3xl text-sm text-muted">Search, filter, sort and export the <strong>first {orders.length} records returned by the API</strong>. This is a bounded synthetic-data preview, not a complete database-wide search.</p></div>
      <button type="button" className="secondary-action" onClick={exportCsv} disabled={!filtered.length}>Export filtered CSV</button>
    </div>
    <div className="mt-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_220px_auto] sm:items-end">
      <label className="field-label">Search loaded orders<input aria-label="Search loaded orders" type="search" placeholder="Order ID, SKU, date or status" className="field-control" value={query} onChange={event => { setQuery(event.target.value); setPage(1) }} /></label>
      <label className="field-label">Status<select aria-label="Filter order status" className="field-control" value={status} onChange={event => { setStatus(event.target.value); setPage(1) }}><option value="all">All statuses</option>{statuses.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
      <button type="button" className="secondary-action" onClick={() => { setQuery(''); setStatus('all'); setSortKey('id'); setDirection('asc'); setPage(1) }}>Reset filters</button>
    </div>
    <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted"><span role="status">Showing {visible.length ? (currentPage - 1) * PAGE_SIZE + 1 : 0}–{(currentPage - 1) * PAGE_SIZE + visible.length} of {filtered.length} matching loaded records</span><span>Local browser filters · Synthetic records</span></div>
    <div className="mt-3 overflow-x-auto rounded-xl border border-line"><table className="data-grid w-full min-w-[670px] text-left text-sm"><thead><tr>{columns.map(col => <th scope="col" key={col.key} aria-sort={sortKey === col.key ? (direction === 'asc' ? 'ascending' : 'descending') : 'none'}><button type="button" className="sort-button" onClick={() => updateSort(col.key)} aria-label={`Sort by ${col.title}`}>{col.title}<span aria-hidden="true" className="ml-2 text-brand">{sortKey === col.key ? direction === 'asc' ? '↑' : '↓' : '↕'}</span></button></th>)}</tr></thead><tbody>{visible.map(order => <tr key={order.id}><td className="font-semibold">#{order.id}</td><td>{order.sku}</td><td>{order.quantity.toLocaleString()}</td><td>{order.priority}</td><td><span className={`status-chip ${order.status.toLowerCase().includes('deliver') ? 'status-good' : 'status-neutral'}`}>{order.status}</span></td><td>{order.promised_at.slice(0, 10)}</td></tr>)}{!visible.length && <tr><td colSpan={columns.length} className="py-10 text-center text-muted">No loaded records match these filters. Reset the filters to explore again.</td></tr>}</tbody></table></div>
    <div className="mt-4 flex items-center justify-between gap-3"><span className="text-xs text-muted">Page {currentPage} of {pages}</span><div className="flex gap-2"><button type="button" className="secondary-action" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>Previous</button><button type="button" className="secondary-action" disabled={currentPage === pages} onClick={() => setPage(currentPage + 1)}>Next</button></div></div>
    <p className="mt-4 text-xs leading-6 text-muted"><strong>Data notes:</strong> Changing filters does not change the database, solver inputs or optimisation results. For a full company-wide search, the backend will require authorised paginated queries and tenant-scoped access checks.</p>
  </section>
}
