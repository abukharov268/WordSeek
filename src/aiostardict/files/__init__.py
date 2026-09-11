from ._dict import iter_dict_entries, read_dict_entries, read_dz_info
from ._idx import read_indexes
from ._ifo import read_info
from ._paths import StarDictFileCollection

__all__ = [
    "StarDictFileCollection",
    "iter_dict_entries",
    "read_dict_entries",
    "read_dz_info",
    "read_indexes",
    "read_info",
]
