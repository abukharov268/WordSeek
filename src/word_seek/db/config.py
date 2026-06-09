from pathlib import PurePath

from platformdirs import user_data_dir

_AUTHOR = "io.github.abukharov268"
APP_ID = f"{_AUTHOR}.WordSeek"


def get_db_path() -> PurePath:
    return PurePath(user_data_dir(APP_ID, _AUTHOR)).joinpath("database.db")


def get_db_connection_url(no_async: bool = False) -> str:
    if no_async:
        return f"sqlite:///{get_db_path()}"
    return f"sqlite+aiosqlite:///{get_db_path()}"
