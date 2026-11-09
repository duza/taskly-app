---
name: write-frontend-tests
description: >-
  Conventions and recipes for Vitest + React Testing Library unit tests in the Taskly frontend
  (components, hooks, API client, utilities). Use when creating or updating *.test.ts(x) files
  under frontend/src/.
---

# Write frontend tests (Vitest + Testing Library)

## Layout and naming
- Colocate tests: `Foo.tsx` gets `Foo.test.tsx`, and `useBar.ts` gets `useBar.test.ts(x)`.
- Import test APIs explicitly: `import { describe, expect, it, vi } from 'vitest'`.
- `src/test/setup.ts` already registers jest-dom matchers and `cleanup`.

## Reuse what exists
- **Design system:** mock it the way existing tests do (the factory must be async, because `vi.mock` is
  hoisted):
  `vi.mock('../../../design-system', () => import('../../../design-system/mocks'))`
  (adjust the relative path).
- **Fixtures:** `src/test/todoFixture.ts`.
- **Interaction:** `const user = userEvent.setup()`, then `await user.click/type/selectOptions`.
- **Queries:** prefer accessible queries: `getByRole`, `getByLabelText`, `getByText`.

## Recipes
- **Components:** render with props, interact, assert visible output and callback calls
  (`vi.fn()`). Cover empty, loading, error and edge states that the component branches on.
- **React Query hooks** (`features/todos/hooks/*`): create a fresh client per test:
  `new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })`,
  wrap `renderHook` in `QueryClientProvider`, and mock `todosApi` with
  `vi.mock('../api/todos', ...)` or `vi.spyOn(todosApi, 'create')`. Assert cache effects with
  `queryClient.getQueryData(todoKeys.list)` (for example, a saved item is prepended and deduplicated),
  and wait with `await waitFor(...)`.
- **`lib/http.ts` / API client:** stub `fetch` with `vi.stubGlobal('fetch', vi.fn())` and restore
  it in `afterEach(() => vi.unstubAllGlobals())`. Cover OK JSON, 204, 422 message, `detail` string,
  a non-JSON error body, network failure, and an aborted signal that rethrows.
- **Utilities:** table-driven with `it.each`.
- **Time:** `vi.useFakeTimers()` and `vi.setSystemTime(...)`; restore with `vi.useRealTimers()`.

## Never
- Real network or timers; snapshots of whole component trees; testing CSS or styled-components
  internals; `it.only` or `it.skip`; editing non-test files.

## Run
```bash
cd frontend && npx vitest run src/path/Foo.test.tsx && npm run typecheck
```
New test files must pass `npm run typecheck` and `npm run format:check`
(`npx prettier --write <file>` fixes formatting).
