import logging
from importlib import resources

import alembic.runtime.migration
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection

from .config import get_db_connection_url
from .exec import engine

alembic.runtime.migration.log.addFilter(lambda rec: rec.levelno >= logging.ERROR)


async def run_async_upgrade() -> None:
    with resources.path("word_seek", "alembic.ini") as config_path:
        config = Config(config_path)
    config.set_main_option("sqlalchemy.url", get_db_connection_url())

    async with engine.begin() as conn:
        await conn.run_sync(_run_upgrade, config)


def _run_upgrade(connection: Connection, config: Config) -> None:
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
