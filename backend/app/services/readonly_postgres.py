"""Opt-in, narrowly scoped PostgreSQL preview for synthetic test datasets.

Connections are provisioned out-of-band by the operator. Never accept connection
strings, hostnames, table lists, or SQL from the browser. Disabled by default.
"""
import json
import os
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import sql


class ConnectorUnavailable(Exception):
    """Missing/invalid provisioning or deliberately disabled connector."""


class ConnectorExecutionError(Exception):
    """Execution failure; internal driver details must not reach API callers."""


@dataclass(frozen=True)
class Profile:
    dsn: str
    tables: tuple[str, ...]


def provisioned_profile(org_id: int, connector_id: int) -> Profile | None:
    if os.getenv('OPS_READONLY_CONNECTORS_ENABLED', '').lower() != 'true':
        return None
    try:
        config: Any = json.loads(os.getenv('OPS_PG_CONNECTOR_BINDINGS_JSON', '{}'))
        profile = config[str(org_id)][str(connector_id)]
        dsn = profile['dsn']
        tables = profile['tables']
        if (not isinstance(dsn, str) or not dsn.startswith(('postgresql://', 'postgres://'))
                or not isinstance(tables, list) or not tables or len(tables) > 10):
            return None
        if any(not isinstance(t, str) or not _valid_table(t) for t in tables):
            return None
        return Profile(dsn=dsn, tables=tuple(tables))
    except (KeyError, ValueError, TypeError, IndexError, AttributeError):
        return None


def _valid_table(value: str) -> bool:
    parts = value.split('.')
    return len(parts) == 2 and all(part.isidentifier() and part.isascii() and len(part) <= 63 for part in parts)


def _connect(profile: Profile):
    return psycopg.connect(profile.dsn, connect_timeout=3, options='-c default_transaction_read_only=on')


def check_connection(profile: Profile) -> dict:
    """Only static SELECT, read-only transaction, no schema discovery."""
    try:
        with _connect(profile) as conn:
            with conn.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                cur.execute('SET LOCAL statement_timeout = 2000')
                cur.execute('SELECT current_setting(\'transaction_read_only\')')
                if cur.fetchone()[0] != 'on':
                    raise ConnectorExecutionError('Read-only transaction could not be verified')
        return {'status': 'reachable', 'read_only': True, 'allowed_tables': list(profile.tables)}
    except (psycopg.Error, OSError) as exc:
        raise ConnectorExecutionError('Read-only connection check failed') from exc


def preview_table(profile: Profile, table: str) -> dict:
    """Static allowlisted table SELECT. Bounded rows and SQL execution time."""
    if table not in profile.tables:
        raise ConnectorUnavailable('Table is not in the operator allowlist')
    schema, name = table.split('.')
    try:
        with _connect(profile) as conn:
            with conn.cursor() as cur:
                cur.execute('SET TRANSACTION READ ONLY')
                cur.execute('SET LOCAL statement_timeout = 2000')
                cur.execute(sql.SQL('SELECT * FROM {}.{} LIMIT 25').format(
                    sql.Identifier(schema), sql.Identifier(name)))
                fields = [col.name for col in cur.description]
                if len(fields) > 50:
                    raise ConnectorUnavailable('Configured table has too many columns for a safe preview')
                rows = [dict(zip(fields, (str(v)[:500] if v is not None else None for v in row)))
                        for row in cur.fetchall()]
        return {'table': table, 'columns': fields, 'rows': rows, 'row_limit': 25,
                'source': 'operator_provisioned_read_only_postgresql', 'sample_only': True}
    except (psycopg.Error, OSError) as exc:
        raise ConnectorExecutionError('Read-only table preview failed') from exc
