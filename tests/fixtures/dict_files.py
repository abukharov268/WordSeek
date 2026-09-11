import pathlib
import subprocess
from dataclasses import dataclass
from os import environ

import pytest

TABFILE_PATH = environ.get("TABFILE_PATH", "/usr/lib/stardict-tools/tabfile")
DICTZIP_PATH = environ.get("DICTZIP_PATH", "dictzip")


@dataclass
class DictionaryFiles:
    ifo_path: str
    idx_path: str
    dict_path: str


@pytest.fixture
def simple_dict_file() -> DictionaryFiles:
    dir = pathlib.Path(__file__).parent
    tab_path = dir / "simple.tab"
    ifo_path = dir / "simple.ifo"
    idx_path = dir / "simple.idx"
    dict_path = dir / "simple.dict.dz"

    if not (ifo_path.exists() and idx_path.exists() and dict_path.exists()):
        subprocess.run([TABFILE_PATH, tab_path.name], check=True, cwd=tab_path.parent)

    return DictionaryFiles(
        ifo_path=str(ifo_path), idx_path=str(idx_path), dict_path=str(dict_path)
    )
