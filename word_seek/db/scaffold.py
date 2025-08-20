import os
from functools import partial

from anyio import Path, to_thread

from .config import get_db_path
from .exec import engine
from .models import Base

_db_initialized = False


async def wipeout() -> None:
    path = Path(get_db_path())
    if await path.exists():
        await to_thread.run_sync(partial(os.remove, get_db_path()))


async def _ensure_dir() -> None:
    path = Path(get_db_path().parent)
    await path.mkdir(parents=True, exist_ok=True)


async def ensure_db() -> None:
    global _db_initialized

    if not _db_initialized:
        await _ensure_dir()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()

        _db_initialized = True
