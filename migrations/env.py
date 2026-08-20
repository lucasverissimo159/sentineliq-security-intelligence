"""Alembic environment: wires migrations to SentinelIQ's settings and models.

The database URL is pulled from `Settings` (i.e. from the environment
/ .env) rather than hardcoded in alembic.ini, so migrations always run
against whichever database the app itself is configured for.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine

from sentineliq.infrastructure.config.settings import get_settings

# Import models so they register on Base.metadata before autogenerate runs.
from sentineliq.infrastructure.persistence import models  # noqa: F401
from sentineliq.infrastructure.persistence.database import Base, create_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable: AsyncEngine = create_engine()
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
