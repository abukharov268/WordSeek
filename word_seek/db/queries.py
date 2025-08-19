from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.sql import Delete, Select, Update
from sqlalchemy.sql.expression import null

from ..utils.models import range_lim
from ..utils.orm import sqlite
from .models import Article, Dictionary, Phrase, ViewLog

type Query[T] = Select[tuple[T]]
type ModifyQuery = Delete | Update


def find_checksum(checksum: str) -> Query[Dictionary]:
    return select(Dictionary).where(Dictionary.checksum == checksum).limit(1)


def find_phrase(phrase: str, limit: int = 16, offset: int = 0) -> Query[Phrase]:
    return (
        select(Phrase)
        .where(sqlite.instr(Phrase.text, phrase) > 0)
        .order_by(sqlite.instr(Phrase.text, phrase), Phrase.text)
        .offset(offset)
        .limit(limit)
    )


def find_articles(phrase: Phrase) -> Query[Article]:
    return (
        select(Article)
        .join(Dictionary)
        .where(Article.phrase_id == phrase.id)
        .order_by(Dictionary.sort_order == null(), Dictionary.sort_order)
    )


def list_dicts() -> Query[Dictionary]:
    return select(Dictionary).order_by(
        Dictionary.sort_order == null(), Dictionary.sort_order
    )


def list_view_logs(limit: int = 16, offset: int = 0) -> Query[ViewLog]:
    return (
        select(ViewLog)
        .order_by(ViewLog.shown_at_utc.desc())
        .offset(offset)
        .limit(limit)
    )


def delete_view_logs(
    *,
    items: ViewLog | int | list[ViewLog] | list[int] | None = None,
    shown_at_utc: range_lim[datetime] | datetime | None = None,
) -> ModifyQuery:
    query = delete(ViewLog)

    match items:
        case list():
            ids = [item if isinstance(item, int) else item.id for item in items]
            query = query.where(ViewLog.id.in_(ids))
        case int() as id:
            query = query.where(ViewLog.id == id)
        case ViewLog() as log:
            query = query.where(ViewLog.id == log.id)

    match shown_at_utc:
        case range_lim(start, end):
            query = query.where(ViewLog.shown_at_utc.between(start, end))
        case datetime() as moment:
            query = query.where(ViewLog.shown_at_utc == moment)

    return query
