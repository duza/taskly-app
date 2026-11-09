#!/usr/bin/env python3
"""Build a per-file unit-test plan for changed (or all) source files. Stdlib only."""
import argparse
import fnmatch
import json
import os
import subprocess
import sys

BACKEND_SRC = "backend/app/"
FRONTEND_SRC = "frontend/src/"
# Mirrors pyproject.toml [tool.coverage.run] omit and vite.config.ts coverage.exclude.
BACKEND_EXCLUDED = ["*/__init__.py", "backend/app/main.py", "*/schemas.py", "*/models.py", "*/types.py",
                    "*/constants.py"]
FRONTEND_EXCLUDED = ["frontend/src/main.tsx", "frontend/src/test/*", "frontend/src/design-system/*",
                     "*/types.ts", "*.types.ts", "*/index.ts", "*/constants.ts", "*/constants.tsx",
                     "*.constants.ts", "frontend/src/features/todos/api/queryKeys.ts",
                     "frontend/src/lib/queryClient.ts", "*.stories.tsx", "*.styles.ts", "*.d.ts"]


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def changed_files(base):
    out = git("diff", "--name-status", "--find-renames", f"{base}...HEAD")
    files = []
    for line in out.splitlines():
        parts = line.split("\t")
        status, path = parts[0][0], parts[-1]
        files.append((status, path))
    return files


def all_files():
    return [("A", p) for p in git("ls-files", BACKEND_SRC, FRONTEND_SRC).splitlines()]


def matches(path, patterns):
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def classify(status, path):
    entry = {"path": path, "status": status, "stack": None, "test_path": None, "test_exists": False,
             "coverage_excluded": False, "suggested": "skip", "reason": ""}
    if status == "D":
        entry["reason"] = "file deleted"
        return entry
    if path.startswith(BACKEND_SRC) and path.endswith(".py"):
        entry["stack"] = "backend"
        rel = path[len(BACKEND_SRC):]
        d, name = os.path.split(rel)
        entry["test_path"] = os.path.join("backend/tests", d, f"test_{name}")
        entry["coverage_excluded"] = matches(path, BACKEND_EXCLUDED)
    elif path.startswith(FRONTEND_SRC) and path.endswith((".ts", ".tsx")):
        if ".test." in path:
            entry["stack"] = "frontend"
            entry["reason"] = "test file (changed by the PR author)"
            return entry
        entry["stack"] = "frontend"
        base, ext = os.path.splitext(path)
        entry["test_path"] = f"{base}.test{ext}"
        entry["coverage_excluded"] = matches(path, FRONTEND_EXCLUDED)
    elif path.startswith("backend/tests/"):
        entry["stack"] = "backend"
        entry["reason"] = "test file (changed by the PR author)"
        return entry
    else:
        entry["reason"] = "not application source (docs, config, CI, assets)"
        return entry

    entry["test_exists"] = os.path.exists(entry["test_path"])
    if entry["coverage_excluded"]:
        entry["reason"] = "excluded from coverage by project config; test only if it holds real logic"
    elif not entry["test_exists"]:
        entry["suggested"], entry["reason"] = "create", "source without a test file"
    else:
        entry["suggested"], entry["reason"] = "review", "test exists; check that the change is covered"
    return entry


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--base", help="git ref of the PR base, e.g. origin/main")
    g.add_argument("--all", action="store_true", help="plan every source file (backfill mode)")
    ap.add_argument("--out", default=".test-agent/plan.json")
    a = ap.parse_args()
    files = all_files() if a.all else changed_files(a.base)
    plan = [classify(s, p) for s, p in files]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"mode": "all" if a.all else f"diff:{a.base}", "files": plan}, f, indent=2)
    counts = {}
    for e in plan:
        counts[e["suggested"]] = counts.get(e["suggested"], 0) + 1
    print(f"wrote {a.out}: {len(plan)} files {counts}")
    for e in plan:
        if e["suggested"] != "skip":
            print(f"  {e['suggested']:7} {e['path']} -> {e['test_path']}")


if __name__ == "__main__":
    sys.exit(main())
