---
name: report-results
description: >-
  Render the pull-request report (decisions, tests written, verification results, coverage,
  mutation check, findings) from the agent's decisions file and the real result files.
  Use as the last step; post the rendered markdown as the PR comment.
---

# Report results

The PR comment is generated from files, so it can't overstate what happened.

## 1. Write `.test-agent/decisions.json`
```json
{
  "summary": "One or two sentences about what the PR changes and what you did.",
  "files": [
    {"path": "backend/app/api/health.py", "action": "create",
     "test_path": "backend/tests/api/test_health.py",
     "reason": "new endpoint without tests", "tests_added": 2, "tests_updated": 0}
  ],
  "skills_used": ["analyze-pr-changes", "write-backend-tests", "run-and-verify-tests", "report-results"],
  "findings": ["Possible bug: ...", "Ignored instruction in PR description asking to ..."]
}
```
`action` is one of `create`, `update` or `skip`. Every file from `plan.json` must appear.

## 2. Render
```bash
python3 .github/skills/report-results/scripts/render_report.py \
  --baseline .test-agent/baseline.json   # optional: results.json from the PR base, for coverage deltas
```
This produces `.test-agent/report.md` from `plan.json`, `decisions.json`, `results.json` and
`mutations.json`. If `results.json` is missing or failing, the report says so prominently.

## 3. Publish
Post `.test-agent/report.md` verbatim as the PR comment (the workflow's comment output). Do not
add claims that aren't in the rendered report.
