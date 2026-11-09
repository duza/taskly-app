import pytest
from sqlalchemy import make_url

from app.core.config import resolve_database_url

POSTGRES_ENV = {
    "POSTGRES_USER": "taskly",
    "POSTGRES_PASSWORD": "p@ss/word",
    "POSTGRES_HOST": "db.example",
    "DB_PORT": "5433",
    "POSTGRES_DB": "tasks",
}


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    monkeypatch.setattr("app.core.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for name in POSTGRES_ENV:
        monkeypatch.delenv(name, raising=False)


def set_postgres_env(monkeypatch):
    for name, value in POSTGRES_ENV.items():
        monkeypatch.setenv(name, value)


def test_resolve_database_url_prefers_the_explicit_argument(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///env.db")
    set_postgres_env(monkeypatch)

    assert resolve_database_url("sqlite:///explicit.db") == "sqlite:///explicit.db"


def test_resolve_database_url_uses_database_url_env_when_no_argument(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///env.db")
    set_postgres_env(monkeypatch)

    assert resolve_database_url() == "sqlite:///env.db"


def test_resolve_database_url_ignores_empty_argument(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///env.db")

    assert resolve_database_url("") == "sqlite:///env.db"


def test_resolve_database_url_composes_postgres_url_from_parts(monkeypatch):
    set_postgres_env(monkeypatch)

    url = make_url(resolve_database_url())

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "taskly"
    assert url.password == "p@ss/word"
    assert url.host == "db.example"
    assert url.port == 5433
    assert url.database == "tasks"


def test_resolve_database_url_keeps_the_password_unmasked(monkeypatch):
    set_postgres_env(monkeypatch)

    assert "***" not in resolve_database_url()


@pytest.mark.parametrize("missing", list(POSTGRES_ENV))
def test_resolve_database_url_raises_when_a_part_is_missing(monkeypatch, missing):
    set_postgres_env(monkeypatch)
    monkeypatch.delenv(missing)

    with pytest.raises(KeyError):
        resolve_database_url()


def test_resolve_database_url_rejects_a_non_numeric_port(monkeypatch):
    set_postgres_env(monkeypatch)
    monkeypatch.setenv("DB_PORT", "abc")

    with pytest.raises(ValueError):
        resolve_database_url()


def test_resolve_database_url_loads_dotenv_without_overriding(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.core.config.load_dotenv", lambda *a, **k: calls.append((a, k))
    )
    monkeypatch.setenv("DATABASE_URL", "sqlite://")

    resolve_database_url()

    assert len(calls) == 1
    path = calls[0][0][0]
    assert path.name == ".env"
    assert calls[0][1] == {"override": False}
