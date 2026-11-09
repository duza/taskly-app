from unittest.mock import Mock

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.core.database import (
    create_database_engine,
    create_session_factory,
    initialize,
)
from app.features.todos.models import Base


def test_engine_uses_the_postgresql_psycopg_driver():
    url = "postgresql+psycopg://taskly:taskly@localhost:5432/taskly"
    engine = create_database_engine(url)
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert engine.url.database == "taskly"
    finally:
        engine.dispose()


def test_engine_enables_pre_ping_and_a_connect_timeout(monkeypatch):
    create = Mock(return_value="engine")
    monkeypatch.setattr("app.core.database.create_engine", create)

    result = create_database_engine("postgresql+psycopg://u:p@h/db")

    assert result == "engine"
    create.assert_called_once_with(
        "postgresql+psycopg://u:p@h/db",
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )


def test_session_factory_binds_the_engine_and_keeps_objects_loaded_after_commit():
    engine = create_engine("sqlite://")
    try:
        factory = create_session_factory(engine)
        with factory() as session:
            assert isinstance(session, Session)
            assert session.get_bind() is engine
            assert session.expire_on_commit is False
    finally:
        engine.dispose()


def test_initialize_creates_all_model_tables():
    engine = create_engine("sqlite://")
    try:
        initialize(engine)

        assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables)
        assert Base.metadata.tables
    finally:
        engine.dispose()


def test_initialize_is_idempotent():
    engine = create_engine("sqlite://")
    try:
        initialize(engine)
        initialize(engine)

        assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables)
    finally:
        engine.dispose()
