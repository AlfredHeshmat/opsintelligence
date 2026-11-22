"""Strict, bounded CSV parsing for fictional logistics order data.

No AI parsing, no arbitrary file types, no formula evaluation, no raw file persistence.
"""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
import re
from app.models.project_data import ProjectOrder

MAX_BYTES = 2_000_000
MAX_ROWS = 2_000
FIELDS = ('order_id', 'order_date', 'warehouse_id', 'sku', 'quantity', 'priority',
          'promised_date', 'shipped_date', 'status', 'unit_price_aud', 'unit_cost_aud',
          'shipping_cost_aud', 'destination_region')
REGIONS = {'NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT'}
STATUSES = {'pending', 'shipped', 'delivered', 'cancelled'}
PRIORITIES = {'standard', 'priority', 'express'}
IDENTIFIER = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


class ImportValidationError(ValueError):
    pass


def _identifier(value: str, col: str, maxlen: int):
    cleaned = value.strip()
    if not cleaned or len(cleaned) > maxlen or not IDENTIFIER.fullmatch(cleaned):
        raise ValueError(f'{col} must be a short alphanumeric identifier')
    return cleaned


def _amount(raw: str, column: str):
    try:
        result = Decimal(raw).quantize(Decimal('0.01'))
        if not result.is_finite() or result < 0 or result >= 1_000_000_000:
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise ValueError(f'{column} must be a non-negative amount') from None
    return result


def parse_project_orders(raw: bytes, org_id: int, project_id: int) -> list[ProjectOrder]:
    if not raw or len(raw) > MAX_BYTES:
        raise ImportValidationError('CSV must be nonempty and at most 2 MB')
    try:
        contents = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ImportValidationError('CSV must use UTF-8 encoding') from None
    if '\x00' in contents:
        raise ImportValidationError('CSV contains an invalid character')
    reader = csv.DictReader(StringIO(contents, newline=''), restkey='__extra__', strict=True)
    if reader.fieldnames != list(FIELDS):
        raise ImportValidationError('CSV columns must exactly match: ' + ', '.join(FIELDS))
    orders: list[ProjectOrder] = []
    seen: set[str] = set()
    try:
        for line, record in enumerate(reader, start=2):
            if line > MAX_ROWS + 1:
                raise ImportValidationError(f'Too many orders (limit {MAX_ROWS})')
            try:
                if None in record.values() or '__extra__' in record:
                    raise ValueError('incorrect number of columns')
                oid = _identifier(record['order_id'], 'order_id', 64)
                if oid in seen:
                    raise ValueError('duplicate order_id')
                seen.add(oid)
                qty = int(record['quantity'])
                if qty < 1 or qty > 100_000 or str(qty) != record['quantity'].strip():
                    raise ValueError('quantity must be an integer between 1 and 100000')
                order_date = date.fromisoformat(record['order_date'])
                promised = date.fromisoformat(record['promised_date'])
                shipped = date.fromisoformat(record['shipped_date']) if record['shipped_date'] else None
                if promised < order_date or (shipped is not None and shipped < order_date):
                    raise ValueError('dates are inconsistent')
                status = record['status'].lower().strip()
                if status not in STATUSES:
                    raise ValueError('unsupported order status')
                if status in {'delivered','shipped'} and shipped is None:
                    raise ValueError('shipped_date required for shipped/delivered')
                if status in {'pending','cancelled'} and shipped is not None:
                    raise ValueError('shipped_date must be blank for pending/cancelled')
                priority = record['priority'].lower().strip()
                if priority not in PRIORITIES:
                    raise ValueError('unsupported priority')
                region = record['destination_region'].strip().upper()
                if region not in REGIONS:
                    raise ValueError('unsupported destination_region')
                orders.append(ProjectOrder(organisation_id=org_id, project_id=project_id,
                    order_id=oid, order_date=order_date, warehouse_id=_identifier(record['warehouse_id'],'warehouse_id',40),
                    sku=_identifier(record['sku'],'sku',64), quantity=qty, priority=priority,
                    promised_date=promised, shipped_date=shipped, status=status,
                    unit_price_aud=_amount(record['unit_price_aud'],'unit_price_aud'),
                    unit_cost_aud=_amount(record['unit_cost_aud'],'unit_cost_aud'),
                    shipping_cost_aud=_amount(record['shipping_cost_aud'],'shipping_cost_aud'),
                    destination_region=region))
            except (ValueError, TypeError, OverflowError) as exc:
                raise ImportValidationError(f'CSV row {line}: {exc}') from None
    except csv.Error as exc:
        raise ImportValidationError(f'Malformed CSV: {exc}') from None
    if not orders:
        raise ImportValidationError('CSV must contain at least one order')
    return orders
