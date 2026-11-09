from unittest.mock import Mock, call

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import lifespan as lifespan_module


@pytest.fixture
def patched(monkeypatch):
    engine = Mock(name="engine")
    factory = Mock(name="session_factory")
    manager = Mock()
    manager.create_engine.return_value = engine
    manager.create_factory.return_value = factory
    monkeypatch.setattr(lifespan_module, "create_database_engine", manager.create_engine)
    monkeypatch.setattr(lifespan_module, "create_session_factory", manager.create_factory)
    monkeypatch.setattr(lifespan_module, "initialize", manager.initialize)
    return manager, engine, factory


def make_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan_module.lifespan)
    app.state.database_url = "sqlite://"
    return app


def test_lifespan_sets_up_the_session_factory_and_disposes_the_engine(patched):
    manager, engine, factory = patched
    app = make_app()

    with TestClient(app):
        assert app.state.session_factory is factory
        engine.dispose.assert_not_called()

    assert manager.mock_calls == [
        call.create_engine("sqlite://"),
        call.initialize(engine),
        call.create_factory(engine),
    ]
    engine.dispose.assert_called_once_with()


def test_lifespan_disposes_the_engine_when_initialization_fails(patched):
    manager, engine, _ = patched
    manager.initialize.side_effect = RuntimeError("boom")
    app = make_app()

    with pytest.raises(RuntimeError, match="boom"):
        with TestClient(app):
            pass

    engine.dispose.assert_called_once_with()
    manager.create_factory.assert_not_called()
    assert not hasattr(app.state, "session_factory")
