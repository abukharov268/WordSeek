import pathlib
from collections import defaultdict
from collections.abc import Iterable, Iterator

import anyio

from ..models import StarDictFiles

SUFFIXES = [".ifo", ".idx.gz", ".idx", ".dict.dz", ".dict"]


class StarDictFileCollection(Iterable[StarDictFiles]):
    def __init__(self) -> None:
        self._file_grps = defaultdict[str, set[str]](set)

    def bundles(self) -> Iterable[StarDictFiles]:
        for grp in self._file_grps.values():
            ifo, idx, dct = None, None, None
            for f in grp:
                if f.endswith(".ifo"):
                    ifo = f
                elif f.endswith((".idx", ".idx.gz")):
                    idx = f
                elif f.endswith((".dict", ".dict.dz")):
                    dct = f

            if ifo and idx and dct:
                yield StarDictFiles(ifo, idx, dct)

    def __iter__(self) -> Iterator[StarDictFiles]:
        return iter(self.bundles())

    def append_relevant(self, path: pathlib.Path) -> bool:
        return path.is_file() and self._append_relevant_file(str(path))

    async def aappend_relevant(self, path: anyio.Path) -> bool:
        return await path.is_file() and self._append_relevant_file(str(path))

    def _append_relevant_file(self, path: str) -> bool:
        suffix = next(iter(suf for suf in SUFFIXES if path.endswith(suf)), None)
        if suffix is None:
            return False

        path_stem = path.removesuffix(suffix)
        self._file_grps[path_stem].add(path)
        return True
