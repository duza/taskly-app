---
name: run-and-verify-tests
description: >-
  Verify unit tests by running them: targeted run, a flake re-run, the full backend/frontend suites
  with coverage, and a mutation sanity check showing the new tests fail when the code under test is
  broken. Produces machine-readable results for the report. Use after writing or updating tests.
---

# Run and verify tests

Tests only count when this skill says they passed. Never report results you did not run.

## 1. Targeted, twice (flake check)
```bash
bash .github/skills/run-and-verify-tests/scripts/verify.sh targeted \
  backend/tests/api/test_health.py frontend/src/lib/http.test.ts
```
Runs each given test file twice. A test that passes once and fails once is **flaky**: fix it.

## 2. Mutation sanity check (do the tests catch bugs?)
```bash
python3 .github/skills/run-and-verify-tests/scripts/mutation_check.py \
  --source backend/app/api/health.py --test backend/tests/api/test_health.py
```
Applies small mutations to the source one at a time (`==`/`!=`, `<`/`>=`, `True`/`False`,
`&&`/`||`, `return x` to `return None`, and so on), runs the test file, and restores the source.
"Killed" means a test failed, which is good. Survivors point to missing assertions: strengthen the tests,
then re-run. The source file is always restored, and `git diff --exit-code -- <source>` is checked
at the end.

## 3. Full suites with coverage
```bash
bash .github/skills/run-and-verify-tests/scripts/verify.sh full
```
Writes `.test-agent/results.json`: pass/fail/skip counts from JUnit XML and coverage totals for
backend and frontend, plus typecheck and format status for the frontend.

## Rules
- A failing test you wrote: fix the test, or remove it and record why in `decisions.json`.
- A failing **existing** test: do not edit it to pass unless the intended behaviour changed. Otherwise report
  it as a finding.
- Do not raise timeouts, add retries or skip tests to get green.
