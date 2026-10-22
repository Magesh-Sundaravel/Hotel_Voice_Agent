import logging
import urllib.parse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.config import settings

logger = logging.getLogger(__name__)

_memory_checkpointer = MemorySaver()


def normalize_db_url(url: str) -> str:
    """Safely percent-encodes passwords with special characters (e.g. '@') in PostgreSQL connection strings."""
    if not url:
        return url
    if url.count("@") > 1 and "://" in url:
        prefix, rest = url.split("://", 1)
        creds, host_and_db = rest.rsplit("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
            encoded_password = urllib.parse.quote(
                urllib.parse.unquote(password), safe=""
            )
            return f"{prefix}://{user}:{encoded_password}@{host_and_db}"
    return url


def get_memory_checkpointer() -> MemorySaver:
    """Returns the singleton fallback in-memory checkpointer."""
    return _memory_checkpointer


@asynccontextmanager
async def get_checkpointer() -> AsyncIterator[BaseCheckpointSaver | Any]:
    """
    Initializes and yields the active checkpointer:
    - If DATABASE_URL or SUPABASE_DB_URL is configured:
      Connects to Supabase PostgreSQL using AsyncPostgresSaver and automatically runs .setup()
      to create the checkpointer tables (checkpoints, checkpoint_blobs, checkpoint_writes).
    - Otherwise:
      Yields an in-memory MemorySaver (ideal for offline tests and local prototyping).
    """
    raw_db_uri = settings.DATABASE_URL or settings.SUPABASE_DB_URL
    if raw_db_uri:
        db_uri = normalize_db_url(raw_db_uri)
        logger.info(
            "Initializing Supabase LangGraph AsyncPostgresSaver checkpointer..."
        )
        async with AsyncPostgresSaver.from_conn_string(db_uri) as postgres_saver:
            await postgres_saver.setup()
            yield postgres_saver
    else:
        yield _memory_checkpointer
