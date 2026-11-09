#!/usr/bin/env python3
"""Tiny mutation check: do the tests fail when the code under test is broken?

Applies one simple mutation at a time to --source, runs --test, and restores the file.
Results are appended to .test-agent/mutations.json. Stdlib only.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# Comparisons require surrounding spaces, so JSX tags and generics are never touched.
# "return X" is only mutated when X is complete on one line (no trailing "(", "[", "{", "\").
PY_MUTATIONS = [(r" == ", " != "), (r" != ", " == "), (r" < ", " >= "), (r" > ", " <= "),
                (r" <= ", " > "), (r" >= ", " < "),
                (r"\bTrue\b", "False"), (r"\bFalse\b", "True"), (r" and ", " or "), (r" or ", " and "),
                (r"\bis None\b", "is not None"), (r"\bis not None\b", "is None"),
                (r"^(\s*)return (?!None\b)(.*[^(\[{\\\s])\s*$", r"\1return None")]
TS_MUTATIONS = [(r" === ", " !== "), (r" !== ", " === "), (r" && ", " || "), (r" \|\| ", " && "),
                (r" < ", " >= "), (r" > ", " <= "), (r" <= ", " > "), (r" >= ", " < "),
                (r"\btrue\b", "false"), (r"\bfalse\b", "true"),
                (r"^(\s*)return (?!undefined\b)(.*[^(\[{\s])\s*$", r"\1return undefined")]
SKIP_LINE = re.compile(r"^\s*(#|//|import |from \S+ import|export \* from|\*|/\*|@)")
STRING = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`")


def mask_strings(line):
    """Blank out string literal contents so mutations never land inside text."""
    return STRING.sub(lambda m: m.group(0)[0] + "x" * (len(m.group(0)) - 2) + m.group(0)[-1], line)


def run_test(test, root, timeout):
    if test.startswith("backend/"):
        py = os.path.join(root, "backend/.venv/bin/python")
        py = py if os.path.exists(py) else sys.executable
        cmd, cwd = [py, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", test[len("backend/"):]], "backend"
    else:
        cmd, cwd = ["npx", "vitest", "run", test[len("frontend/"):]], "frontend"
    try:
        return subprocess.run(cmd, cwd=os.path.join(root, cwd), capture_output=True, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        return 124


def candidates(lines, rules, limit):
    out = []
    in_doc = False
    for i, line in enumerate(lines):
        s = line.strip()
        # Skip Python docstrings / multi-line strings.
        quotes = s.count('"""') + s.count("'''")
        if in_doc or (quotes and s.startswith(('"""', "'''"))):
            if quotes % 2 == 1:
                in_doc = not in_doc
            continue
        if SKIP_LINE.match(line) or not s or s.startswith(("<", "/>", "{/*")):
            continue
        masked = mask_strings(line)
        for pat, rep in rules:
            m = re.search(pat, masked)
            if not m:
                continue
            # Apply the substitution at the same span of the original line.
            new = line[:m.start()] + re.sub(pat, rep, line[m.start():m.end()], count=1) + line[m.end():]
            if new != line:
                out.append((i, pat, line, new))
                break
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--max", type=int, default=8, help="max mutations to try")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                          check=True).stdout.strip()
    os.chdir(root)
    if run_test(a.test, root, a.timeout) != 0:
        print("baseline test run fails: fix the tests before mutation checking")
        return 2
    rules = PY_MUTATIONS if a.source.endswith(".py") else TS_MUTATIONS
    original = open(a.source).read()
    lines = original.split("\n")
    backup = a.source + ".mutation-backup"
    shutil.copyfile(a.source, backup)
    results = []
    try:
        for i, pat, old, new in candidates(lines, rules, a.max):
            mutated = lines.copy()
            mutated[i] = new
            open(a.source, "w").write("\n".join(mutated))
            rc = run_test(a.test, root, a.timeout)
            killed = rc != 0
            results.append({"line": i + 1, "from": old.strip(), "to": new.strip(), "killed": killed})
            print(f"{'KILLED  ' if killed else 'SURVIVED'} line {i + 1}: {old.strip()!r} -> {new.strip()!r}")
    finally:
        shutil.move(backup, a.source)
    clean = subprocess.run(["git", "diff", "--quiet", "--", a.source]).returncode == 0 or \
        open(a.source).read() == original
    killed = sum(r["killed"] for r in results)
    summary = {"source": a.source, "test": a.test, "tried": len(results), "killed": killed,
               "survived": len(results) - killed, "restored": clean, "mutations": results}
    os.makedirs(".test-agent", exist_ok=True)
    path = ".test-agent/mutations.json"
    data = json.load(open(path)) if os.path.exists(path) else []
    data = [d for d in data if d["source"] != a.source] + [summary]
    json.dump(data, open(path, "w"), indent=2)
    print(f"{killed}/{len(results)} mutations killed; source restored: {clean}")
    return 0 if clean else 3


if __name__ == "__main__":
    sys.exit(main())
