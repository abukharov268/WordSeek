from .errors import StarDictError
from .files._dict import iter_dict_entries, read_dict_entries, read_dz_info
from .files._idx import read_indexes
from .files._ifo import read_info
from .files._paths import StarDictFileCollection
from .models import (
    DzInfo,
    GzipExtraFlag,
    GzipFlag,
    IdxEntry,
    OffsetBits,
    OperatingSystemType,
    RandomAccessInfo,
    StarDictFiles,
    StarDictInfo,
    Version,
)

__all__ = [
    "DzInfo",
    "GzipExtraFlag",
    "GzipFlag",
    "IdxEntry",
    "OffsetBits",
    "OperatingSystemType",
    "RandomAccessInfo",
    "StarDictError",
    "StarDictFileCollection",
    "StarDictFiles",
    "StarDictInfo",
    "Version",
    "iter_dict_entries",
    "read_dict_entries",
    "read_dz_info",
    "read_indexes",
    "read_info",
]
