"""
StarDict format partical description limited to perform full import.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum, IntFlag, StrEnum
from pathlib import PurePath
from typing import Literal, NamedTuple

# Stardict version
Version = Literal["2.4.2", "3.0.0"]
# Size of a offset entry in bits
OffsetBits = Literal[32, 64]

IFO_MAGIC_STRING = "StarDict's dict ifo file\n"
IFO_VERSION = "version"
IFO_BOOKNAME = "bookname"
IFO_WORDCOUNT = "wordcount"
IFO_SYNWORDCOUNT = "synwordcount"
IFO_IDXFILESIZE = "idxfilesize"
IFO_IDXOFFSETBITS = "idxoffsetbits"
IFO_AUTHOR = "author"
IFO_EMAIL = "email"
IFO_WEBSITE = "website"
IFO_DESCRIPTION = "description"
IFO_DATE = "date"
IFO_SAMETYPESEQUENCE = "sametypesequence"
IFO_DICTTYPE = "dicttype"
IFO_FIELDS = [
    IFO_VERSION,
    IFO_BOOKNAME,
    IFO_WORDCOUNT,
    IFO_SYNWORDCOUNT,
    IFO_IDXFILESIZE,
    IFO_IDXOFFSETBITS,
    IFO_AUTHOR,
    IFO_EMAIL,
    IFO_WEBSITE,
    IFO_DESCRIPTION,
    IFO_DATE,
    IFO_SAMETYPESEQUENCE,
    IFO_DICTTYPE,
]


class EntryDataType(StrEnum):
    MEANING = "m"
    MEANING_LOCALE = "l"
    PANGO = "g"
    PHONETIC = "t"
    XDXF = "x"
    YINBIAO_KANA = "y"
    POWERWORD = "k"
    MEDIAWIKI = "w"
    HTML = "h"
    WORDNET = "n"
    RESOURCES = "r"
    WAV = "W"
    PICTURE = "P"
    EXTENSION = "X"


@dataclass
class StarDictInfo:
    """Description on the dictionary."""

    version: Version
    bookname: str
    wordcount: int
    idxfilesize: int
    idxoffsetbits: OffsetBits
    synwordcount: int | None = None
    author: str | None = None
    email: str | None = None
    website: str | None = None
    description: str | None = None
    date: str | None = None
    sametypesequence: list[EntryDataType] | None = None
    dicttype: str | None = None


@dataclass
class IdxEntry:
    """Index for entry dict files (ungziped)."""

    word: str
    offset: int
    size: int


class GzipFlag(IntFlag):
    """Flags, indicating optional fields in the header of gz file."""

    TEXT = 0x01  # Text file
    HCRC = 0x02  # CRC16 value is present
    EXTRA = 0x04  # Extra fields is present
    NAME = 0x08  # Name is present
    COMMENT = 0x10  # Comment is present


class GzipExtraFlag(IntFlag):
    """Extra compression flags"""

    # compressor used maximum compression, slowest algorithm
    XFL_MAX_SLOW = 0x02

    # compressor used fastest algorithm
    XFL_FAST = 0x04


class OperatingSystemType(Enum):
    FAT_FILESYSTEM = 0
    AMIGA = 1
    VMS = 2
    UNIX = 3
    VM_CMS = 4
    ATARI_TOS = 5
    HPFS_FILESYSTEM = 6
    MACINTOSH = 7
    Z_SYSTEM = 8
    CP_M = 9
    TOPS_20 = 10
    NTFS_FILESYSTEM = 11
    QDOS = 12
    ACORN_RISCOS = 13
    UNKNOWN = 255


@dataclass
class RandomAccessInfo:
    chunk_length: int
    compressed_chunk_lengths: list[int]


@dataclass
class DzInfo:
    """Dz file info."""

    compression_method: int
    flags: GzipFlag
    modify_time: date
    extra_flags: GzipExtraFlag
    operating_system_type: OperatingSystemType
    random_access_info: RandomAccessInfo | None
    original_file_name: str | None
    comment: str | None
    crc16_value: int | None
    header_length: int


@dataclass
class DictEntry:
    dtype: EntryDataType
    data: bytes


class StarDictFiles(NamedTuple):
    ifo: str
    idx: str
    dict: str

    @property
    def filename(self) -> str:
        return PurePath(self.ifo).stem
