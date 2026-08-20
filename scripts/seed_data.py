"""Convenience script: seed the local database with a handful of sample logs.

Usage:
    python scripts/seed_data.py

Requires DATABASE_URL to point at a running PostgreSQL instance with
migrations already applied (`alembic upgrade head`).
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.value_objects.severity import Severity
from sentineliq.infrastructure.persistence.database import get_session_factory
from sentineliq.infrastructure.persistence.repositories.postgres_log_repository import (
    PostgresLogRepository,
)

SAMPLE_EVENTS = [
    ("firewall-edge-01", "Blocked inbound connection from 203.0.113.4:443", Severity.MEDIUM),
    ("auth-service", "Failed login for user 'admin' (5th attempt in 2 minutes)", Severity.HIGH),
    ("vpn-gateway", "New VPN session established from 198.51.100.22", Severity.INFO),
    ("firewall-edge-01", "Blocked inbound connection from 203.0.113.4:8080", Severity.MEDIUM),
    ("ids-sensor", "Port scan detected from 203.0.113.4 across 40 ports", Severity.CRITICAL),
]


async def main() -> None:
    session_factory = get_session_factory()
    now = datetime.now(UTC)

    async with session_factory() as session:
        repository = PostgresLogRepository(session)
        entries = [
            LogEntry.new(
                source=source,
                raw_message=message,
                severity=severity,
                occurred_at=now - timedelta(minutes=i),
            )
            for i, (source, message, severity) in enumerate(SAMPLE_EVENTS)
        ]
        await repository.save_many(entries)
        await session.commit()

    print(f"Seeded {len(SAMPLE_EVENTS)} sample log entries.")


if __name__ == "__main__":
    asyncio.run(main())
