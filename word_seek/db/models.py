from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Dictionary(Base):
    __tablename__ = "dictionary"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    title: Mapped[str]
    checksum: Mapped[str]
    sort_order: Mapped[int | None] = mapped_column(default=None)


class Phrase(Base):
    __tablename__ = "phrase"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    text: Mapped[str] = mapped_column(index=True, unique=True)


class ArticleFormat(StrEnum):
    TEXT = "text"
    XDXF = "xdxf"


class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrase.id"), index=True)
    phrase: Mapped[Phrase] = relationship(Phrase, init=False)
    dictionary_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"))
    dictionary: Mapped[Dictionary] = relationship(Dictionary, init=False, lazy="joined")
    index: Mapped[int]
    dtype: Mapped[ArticleFormat]
    text: Mapped[str]


class ViewLog(Base):
    __tablename__ = "view_log"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrase.id"), index=True)
    phrase: Mapped[Phrase] = relationship(Phrase, init=False, lazy="joined")
    shown_at_utc: Mapped[datetime]


@dataclass
class ArticleImportItem:
    phrase: str
    index: int
    format: ArticleFormat
    text: str
