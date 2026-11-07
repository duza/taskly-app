---
name: write-backend-tests
description: >-
  Conventions and recipes for writing pytest unit tests for the Taskly FastAPI backend
  (routers, repositories, validators, mappers, config, app factory, lifespan, health).
  Use when creating or updating files under backend/tests/.
---

# Write backend tests (pytest)

## Layout and naming
- Mirror the source tree: `backend/app/x/y.py` maps to `backend/tests/x/test_y.py`. Every new
  test directory needs an empty `__init__.py`, like the existing ones.
- Test names describe behaviour: `test_<unit>_<does_what>_<when>`.
- Run from `backend/` (`pythonpath = ["."]` is configured, so `from app... import ...` works).

## Reuse what exists
- `tests/conftest.py`: `client` (FastAPI `TestClient` mounting only the todos router, with the
  repository overridden), `repository_mock`, `todo_values`, `todo`, `model_factory`.
- `tests/mocks.py`: `make_repository_mock()`, a `create_autospec(TodoRepository)` mock. Prefer it
  over a hand-rolled `Mock()`, so calls are checked against the real interface.

## Recipes
- **Router:** use `client`, set `repository_mock.<method>.return_value`, assert the status code and
  JSON body, and `assert_called_once_with(...)` using schema objects (`TodoCreate(...)`). Cover
  success, not-found (`None` or `False` from the repository gives a 404), and 422 validation without
  calling the repository.
- **Repository:** `session = Mock(spec=Session)`. Assert `add/commit/refresh/delete` calls and their
  order where it matters, and the returned mapped `Todo`. For queries, compare statements with
  `statement.compare(expected)`. Freeze time by patching `app.features.todos.repository.datetime`,
  or assert `created_at == updated_at` and a tz-aware value instead of comparing to "now".
- **Config (`resolve_database_url`):** use `monkeypatch.setenv/delenv`. Patch `load_dotenv` (for
  example `monkeypatch.setattr("app.core.config.load_dotenv", lambda *a, **k: None)`) so a developer's
  `.env` can't leak into the test. Cover explicit argument > `DATABASE_URL` > composed URL.
- **App factory / lifespan / health:** build the app with `create_app("sqlite://")` or patch
  `create_database_engine`, `initialize` and `create_session_factory` in `app.core.lifespan`. Use
  `with TestClient(app):` to drive the lifespan, and assert `engine.dispose()` runs even on error.
  For health, override the `get_repository` dependency with a mock whose `session.execute` is checked.
- Parametrize input variations with `@pytest.mark.parametrize` instead of copy-pasted tests.

## Never
- Connect to Postgres or the network; rely on test order; use `time.sleep`; mark tests
  skip/xfail to hide failures; change anything under `backend/app/`.

## Run
```bash
cd backend && python -m pytest -q tests/path/test_file.py
```
