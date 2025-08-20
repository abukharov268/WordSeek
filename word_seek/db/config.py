import os
from functools import partial
from pathlib import PurePath
from typing import Final

from anyio import Path, to_thread
from platformdirs import user_data_dir
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base

_AUTHOR = "abukharov268"
_DATA_PATH = PurePath(user_data_dir("word_seek", _AUTHOR))
DB_PATH: Final = _DATA_PATH.joinpath("database.db")
_db_initialized = False

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False, future=True)


async def wipeout() -> None:
    path = Path(DB_PATH)
    if await path.exists():
        await to_thread.run_sync(partial(os.remove, DB_PATH))


async def _ensure_dir() -> None:
    path = Path(DB_PATH.parent)
    await path.mkdir(parents=True, exist_ok=True)


async def ensure_db() -> None:
    global _db_initialized

    if not _db_initialized:
        await _ensure_dir()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()

        _db_initialized = True


def new_session() -> AsyncSession:
    return async_sessionmaker(engine)()
