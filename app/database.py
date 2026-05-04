"""
database.py — Connection pools for PostgreSQL primary and replica.

Key concept:
  - primary_pool  → all WRITE operations (INSERT, UPDATE, DELETE)
  - replica_pool  → all READ operations (SELECT)
  - the idea behind 2 database is to mimic method that big tech companies are implement, as users tend to read posts rather then post status
"""

import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

primary_pool: asyncpg.Pool | None = None
replica_pool: asyncpg.Pool | None = None


async def init_db():
    """Call this once at app startup to create both connection pools."""
    global primary_pool, replica_pool

    primary_pool = await asyncpg.create_pool(
        dsn=os.getenv("PRIMARY_DB_URL"),
        min_size=5,   # keep 5 connections warm and ready
        max_size=20,  # never open more than 20 connections
    )

    logger.info(" Database pools created primary" )

    replica_pool = await asyncpg.create_pool(
        dsn=os.getenv("REPLICA_DB_URL"),
        min_size=5,
        max_size=20,
    )

    logger.info(" Database pools created replica" )


async def close_db():
    """Call this at app shutdown to cleanly close all connections."""
    if primary_pool:
        await primary_pool.close()
    if replica_pool:
        await replica_pool.close()


def get_primary() -> asyncpg.Pool:
    """Use this for INSERT / UPDATE / DELETE."""
    return primary_pool


def get_replica() -> asyncpg.Pool:
    """Use this for SELECT queries."""
    return replica_pool