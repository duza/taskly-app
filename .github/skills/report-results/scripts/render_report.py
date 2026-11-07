#!/usr/bin/env python3
"""Render .test-agent/report.md from decisions + real result files. Stdlib only."""
import argparse
import json
import os

D = ".test-agent"
ICON = {"create": "🆕", "update": "✏️", "skip": "⏭️"}


def load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def tests_line(t):
    if not t:
        return "no JUnit report"
    return f"{t['passed']} passed, {t['failures'] + t['errors']} failed, {t['skipped']} skipped"


def delta(now, before):
    if now is None:
        return "n/a"
    if before is None:
        return f"{now:.1f}%"
    d = now - before
    return f"{before:.1f}% → **{now:.1f}%** ({'+' if d >= 0 else ''}{d:.1f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", help="results.json produced on the PR base")
    ap.add_argument("--out", default=f"{D}/report.md")
    a = ap.parse_args()
    plan = load(f"{D}/plan.json", {"files": [], "mode": "?"})
    dec = load(f"{D}/decisions.json", {})
    res = load(f"{D}/results.json")
    muts = load(f"{D}/mutations.json", [])
    base = load(a.baseline) if a.baseline else None
    run_url = ""
    if os.getenv("GITHUB_RUN_ID"):
        run_url = f"{os.getenv('GITHUB_SERVER_URL')}/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"

    ok = bool(res and res.get("ok"))
    L = ["<!-- unit-test-agent-report -->",
         f"## 🧪 Unit Test Agent: {'✅ tests verified' if ok else '❌ verification failed or missing'}", ""]
    if dec.get("summary"):
        L += [dec["summary"], ""]

    by_path = {f["path"]: f for f in dec.get("files", [])}
    L += ["### Decisions", "| File | Action | Test file | Reason |", "|---|---|---|---|"]
    for e in plan.get("files", []):
        d = by_path.get(e["path"], {})
        action = d.get("action", "⚠️ undecided")
        L.append(f"| `{e['path']}` | {ICON.get(action, '')} {action} | "
                 f"{'`' + (d.get('test_path') or e.get('test_path') or '') + '`' if (d.get('test_path') or e.get('test_path')) else '—'} | "
                 f"{d.get('reason') or e.get('reason', '')} |")
    missing = [e["path"] for e in plan.get("files", []) if e["path"] not in by_path]
    if missing:
        L += ["", f"⚠️ No decision recorded for: {', '.join('`' + m + '`' for m in missing)}"]

    L += ["", "### Verification (actual test runs)"]
    if not res:
        L.append("❌ No `results.json`: the full test suites were not run.")
    else:
        b, f = res["backend"], res["frontend"]
        bb, fb = (base or {}).get("backend", {}), (base or {}).get("frontend", {})
        L += ["| Suite | Result | Coverage |", "|---|---|---|",
              f"| Backend (pytest) | {'✅' if b['exit_code'] == 0 else '❌'} {tests_line(b['tests'])} | "
              f"{delta(b.get('coverage_pct'), bb.get('coverage_pct'))} |",
              f"| Frontend (vitest) | {'✅' if f['exit_code'] == 0 else '❌'} {tests_line(f['tests'])} | "
              f"{delta(f.get('coverage_lines_pct'), fb.get('coverage_lines_pct'))} lines |",
              f"| Frontend typecheck / format | {'✅' if f['typecheck_ok'] else '❌'} / {'✅' if f['format_ok'] else '❌'} | |"]

    if muts:
        L += ["", "### Mutation check (do the new tests catch bugs?)", "| Source | Killed | Survived |",
              "|---|---|---|"]
        for m in muts:
            L.append(f"| `{m['source']}` | {m['killed']}/{m['tried']} | {m['survived']} |")

    if dec.get("findings"):
        L += ["", "### Findings"] + [f"- {x}" for x in dec["findings"]]

    L += ["", "<sub>Skills: " + ", ".join(f"`{s}`" for s in dec.get("skills_used", [])) +
          (f" · [workflow run]({run_url})" if run_url else "") +
          " · Generated from test result files, not model output. Review before merging.</sub>"]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(open(a.out).read())


if __name__ == "__main__":
    main()
