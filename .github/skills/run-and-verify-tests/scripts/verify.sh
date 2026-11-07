#!/usr/bin/env bash
# verify.sh targeted <test files...>  -> run each test file twice (flake check)
# verify.sh full                      -> full suites + coverage -> .test-agent/results.json
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
OUT=.test-agent; mkdir -p "$OUT"
PY="${PYTHON:-python3}"; [[ -x backend/.venv/bin/python ]] && PY="$ROOT/backend/.venv/bin/python"

run_one() {  # file -> exit code
  case $1 in
    backend/*)  (cd backend && "$PY" -m pytest -q -p no:cacheprovider "${1#backend/}") ;;
    frontend/*) (cd frontend && npx vitest run "${1#frontend/}") ;;
    *) echo "unknown test path: $1" >&2; return 2 ;;
  esac
}

targeted() {
  local f rc1 rc2 status=0
  for f in "$@"; do
    run_one "$f" >"$OUT/run1.log" 2>&1; rc1=$?
    run_one "$f" >"$OUT/run2.log" 2>&1; rc2=$?
    if [[ $rc1 == 0 && $rc2 == 0 ]]; then echo "PASS   $f (2/2)"
    elif [[ $rc1 != "$rc2" ]]; then echo "FLAKY  $f (run1=$rc1 run2=$rc2)"; status=1
    else echo "FAIL   $f"; tail -40 "$OUT/run1.log"; status=1; fi
  done
  return $status
}

full() {
  local be fe tc fmt
  (cd backend && "$PY" -m pytest -q -p no:cacheprovider --cov=app --cov-report=json \
     --junitxml=../$OUT/backend-junit.xml) >"$OUT/backend.log" 2>&1; be=$?
  (cd frontend && npx vitest run --coverage --reporter=default --reporter=junit \
     --outputFile.junit=../$OUT/frontend-junit.xml) >"$OUT/frontend.log" 2>&1; fe=$?
  (cd frontend && npm run -s typecheck) >"$OUT/typecheck.log" 2>&1; tc=$?
  (cd frontend && npm run -s format:check) >"$OUT/format.log" 2>&1; fmt=$?
  "$PY" - "$be" "$fe" "$tc" "$fmt" <<'EOF'
import json, sys, xml.etree.ElementTree as ET
be, fe, tc, fmt = map(int, sys.argv[1:5])
def junit(p):
    try:
        r = ET.parse(p).getroot()
    except Exception:
        return None
    suites = [r] if r.tag == "testsuite" else list(r.iter("testsuite"))
    t = {k: sum(int(s.get(k, 0) or 0) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    t["passed"] = t["tests"] - t["failures"] - t["errors"] - t["skipped"]
    return t
def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None
bc = load("backend/coverage.json") or load("backend/coverage/coverage.json")
fc = load("frontend/coverage/coverage-summary.json")
res = {
  "backend": {"exit_code": be, "tests": junit(".test-agent/backend-junit.xml"),
              "coverage_pct": round(bc["totals"]["percent_covered"], 2) if bc else None},
  "frontend": {"exit_code": fe, "tests": junit(".test-agent/frontend-junit.xml"),
               "coverage_lines_pct": fc["total"]["lines"]["pct"] if fc else None,
               "typecheck_ok": tc == 0, "format_ok": fmt == 0},
}
res["ok"] = be == 0 and fe == 0 and tc == 0 and fmt == 0
json.dump(res, open(".test-agent/results.json", "w"), indent=2)
print(json.dumps(res, indent=2))
sys.exit(0 if res["ok"] else 1)
EOF
}

case ${1:-} in
  targeted) shift; targeted "$@" ;;
  full) full ;;
  *) echo "usage: verify.sh targeted <files...> | full" >&2; exit 2 ;;
esac
