---
name: analyze-pr-changes
description: >-
  Analyze the files changed in a pull request (or a backfill scope) and produce a per-file test plan:
  stack, expected test file, whether it exists, coverage-exclusion status, and a suggested action.
  Use this first, before writing any test.
---

# Analyze PR changes

Produces `.test-agent/plan.json` deterministically, so decisions start from facts, not guesses.

## Run

```bash
# Pull request mode: compare against the PR base
python3 .github/skills/analyze-pr-changes/scripts/plan_changes.py --base "origin/${BASE_REF:-main}"

# Backfill mode: plan for every source file (used to raise coverage across the repo)
python3 .github/skills/analyze-pr-changes/scripts/plan_changes.py --all
```

## Output (one entry per file)

```json
{"path": "backend/app/api/health.py", "status": "M", "stack": "backend",
 "test_path": "backend/tests/api/test_health.py", "test_exists": false,
 "coverage_excluded": false, "suggested": "create", "reason": "source without tests"}
```

`suggested` is a hint: `create`, `update`, `review` (the test exists, so check whether the change is covered)
or `skip` (with reason). Then:

1. Read the diff for every non-skip entry (`git diff <base>...HEAD -- <path>`) and the existing test
   file, if any.
2. Make the final decision per the agent's decision policy, and record it in `.test-agent/decisions.json`.
3. Files the project excludes from coverage (`pyproject.toml [tool.coverage.run] omit`,
   `vite.config.ts coverage.exclude`) default to `skip` unless they contain real logic.
