from collections.abc import AsyncGenerator

import pytest
from faker import Faker
from pytest import FixtureRequest, MonkeyPatch

import word_seek.db.config
from word_seek.db import migrating, repo
from word_seek.db.exec import new_session
from word_seek.db.models import Phrase

fake = Faker()


@pytest.fixture(autouse=True)
async def inmemory_sqlite(monkeypatch: MonkeyPatch) -> AsyncGenerator:
    monkeypatch.setattr(
        word_seek.db.config,
        "get_db_path",
        lambda: "file:memdb1?mode=memory&cache=shared&uri=true",
    )

    async with new_session():
        await migrating.run_async_upgrade()
        yield


@pytest.fixture
async def hello_phrases() -> AsyncGenerator:
    async with new_session() as session:
        phrases = [
            Phrase("hi"),
            Phrase("Hello"),
            Phrase("Привет"),
            Phrase("Hello!"),
            Phrase("Привет!"),
            Phrase("hey"),
            Phrase("hello"),
            Phrase("привет"),
            Phrase("Hello World"),
            Phrase("Привет Мир"),
            Phrase("Othello"),
            Phrase("приветствие"),
            Phrase("morning"),
        ]
        shuffled_phrases = fake.random_elements(
            phrases, length=len(phrases), unique=True
        )
        session.add_all(shuffled_phrases)
        await session.commit()

        yield

        for phrase in phrases:
            await session.delete(phrase)
        await session.commit()


@pytest.fixture(
    params=["hello", "Hello", "привет", "Привет"],
    ids=["en-hello", "en-Hello", "ru-privet", "ru-Privet"],
)
def hello_phrase(request: FixtureRequest) -> str:
    return request.param


@pytest.fixture
def expected_hello_match(hello_phrase: str, hello_phrases: None) -> list[str]:
    match hello_phrase:
        case "hello":
            return [
                "hello",
                "Hello",
                "Hello!",
                "Othello",
                "Hello World",
            ]
        case "Hello":
            return [
                "Hello",
                "hello",
                "Hello!",
                "Othello",
                "Hello World",
            ]
        case "привет":
            return [
                "привет",
                "Привет",
                "Привет!",
                "Привет Мир",
                "приветствие",
            ]
        case "Привет":
            return [
                "Привет",
                "привет",
                "Привет!",
                "Привет Мир",
                "приветствие",
            ]
        case _:
            assert None, "Unexpected phrase"


async def test_find_phrases(hello_phrase: str, expected_hello_match: list[str]) -> None:
    result = await repo.find_phrases(hello_phrase)

    assert [p.text for p in result] == expected_hello_match
