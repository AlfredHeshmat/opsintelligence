import { useMemo, useState } from 'react'

type Point = { date: string; orders: number; delayed: number }
const formatter = new Intl.DateTimeFormat('en-AU', { day: 'numeric', month: 'short', timeZone: 'UTC' })
function dateLabel(value: string) {
 const parsed = new Date(`${value.slice(0, 10)}T00:00:00Z`)
 return Number.isNaN(parsed.getTime()) ? value : formatter.format(parsed)
}

export function TrendExplorer({ trend }: { trend: Point[] }) {
 const [metric, setMetric] = useState<'orders' | 'delayed'>('orders')
 const [windowSize, setWindowSize] = useState(30)
 const [selectedDate, setSelectedDate] = useState<string | null>(null)
 const points = useMemo(() => trend.slice(-windowSize), [trend, windowSize])
 const maximum = Math.max(1, ...points.map(point => point[metric]))
 const total = points.reduce((sum, item) => sum + item[metric], 0)
 const peak = points.reduce<Point | null>((best, item) => !best || item[metric] > best[metric] ? item : best, null)
 const chosen = points.find(item => item.date === selectedDate) ?? points.at(-1)
 return <section aria-labelledby="trend-heading" className="enterprise-panel p-5 sm:p-6">
  <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="eyebrow">Demand intelligence</p><h2 id="trend-heading" className="mt-1 text-lg font-semibold">Operational activity over time</h2><p className="mt-1 text-xs text-muted">Daily counts from locally stored synthetic order records</p></div><span className="status-chip status-neutral">Database-derived</span></div>
  <div className="mt-5 flex flex-wrap items-end justify-between gap-4"><div className="flex flex-wrap gap-3"><label className="field-label">Measure<select aria-label="Chart measure" className="field-control" value={metric} onChange={event => { setMetric(event.target.value as 'orders' | 'delayed'); setSelectedDate(null) }}><option value="orders">Orders</option><option value="delayed">Recorded delays</option></select></label><label className="field-label">Period<select aria-label="Chart period" className="field-control" value={windowSize} onChange={event => { setWindowSize(Number(event.target.value)); setSelectedDate(null) }}><option value={7}>Last 7 available days</option><option value={14}>Last 14 available days</option><option value={30}>Last 30 available days</option></select></label></div><div className="flex gap-5"><div><p className="text-xs text-muted">Period total</p><p className="text-2xl font-bold tabular-nums">{total.toLocaleString()}</p></div><div><p className="text-xs text-muted">Peak day</p><p className="text-2xl font-bold tabular-nums">{peak?.[metric] ?? '—'}</p></div></div></div>
  {points.length ? <><div className="mt-6 flex h-48 items-end gap-[3px]" role="group" aria-label={`Daily ${metric} bar chart, each bar selectable for details`}>
   {points.map(point => <button type="button" key={point.date} className={`trend-bar group relative min-w-0 flex-1 rounded-t-md ${chosen?.date === point.date ? 'bg-brand' : 'bg-teal-500/75 hover:bg-teal-700'}`} style={{ height: `${Math.max(3, point[metric] / maximum * 100)}%` }} title={`${point.date}: ${point[metric]} ${metric}`} aria-label={`${point.date}: ${point[metric]} ${metric}`} aria-pressed={chosen?.date === point.date} onClick={() => setSelectedDate(point.date)}><span className="sr-only">{point[metric]}</span></button>)}
  </div><div className="mt-2 flex justify-between text-xs text-muted"><span>{dateLabel(points[0].date)}</span><span>{dateLabel(points.at(-1)!.date)}</span></div><div aria-live="polite" className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-canvas p-4"><div><p className="text-xs font-medium text-muted">Selected day · {chosen?.date}</p><p className="mt-1 text-lg font-semibold tabular-nums">{chosen?.[metric].toLocaleString()} {metric === 'orders' ? 'orders' : 'recorded delays'}</p></div><p className="max-w-xs text-xs leading-5 text-muted">Use the metric and period filters to change the chart. Select a bar to inspect a specific day.</p></div></> : <p className="mt-6 rounded-xl bg-canvas p-5 text-sm text-muted">No daily data available. Generate a synthetic dataset from the Overview page.</p>}
 </section>
}
