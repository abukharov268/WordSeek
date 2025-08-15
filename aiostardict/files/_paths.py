from collections import defaultdict
from collections.abc import Iterable, Iterator
from os import PathLike

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

    def filter_path_in(self, path: str | PathLike[str]) -> bool:
        path = str(path)

        suffix = next(iter(suf for suf in SUFFIXES if path.endswith(suf)), None)
        if suffix is None:
            return False

        path_stem = path.removesuffix(suffix)
        self._file_grps[path_stem].add(path)
        return True
