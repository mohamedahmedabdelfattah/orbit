#!/usr/bin/env python3
"""Repository-owned oracles for the feature-004 integration gates.

Run from the repository root:
    python specs/004-safe-upstream-merge/verify_candidate.py structural|tests|evidence|history

Each mode prints its success token only after all assertions pass. Standard library only.
"""
from __future__ import annotations

import ast
import glob
import json
import os
import re
import subprocess
import sys
import tempfile


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EVIDENCE = os.path.join(HERE, "evidence")
LOCAL = "366cf73e7e8f4e62e3604613097a00bafab087df"
UPSTREAM = "256ed1626941982d22c5aee7305f5ed3f9852dc4"
BASE = "500d772ae751651c5b6d1f0e2776e7dd5fd3d834"
REPLACED = "93773e055f31ce25bedc30cdc1fe3f73c541a0c7"
MODULES = ("test_core", "test_channels", "test_tools", "test_calls", "test_platforms", "test_mxc")
OVERLAPS = {
    "README.md", "SETUP.md", "core/engine.py", "core/guard/staff-guard/hooks/register.js",
    "core/onboard.py", "core/orders.py", "core/osinfo.py", "core/panel.py", "core/panel/app.js",
    "core/staffd.py", "core/team.py", "orbit", "tests/test_core.py", "tests/test_platforms.py",
}
RESOLUTIONS = {
    "R-ENGINE-COMMAND", "R-ENGINE-RUN", "R-OSINFO-NOTIFY", "R-README-COST",
    "R-INTERACTIVE-PLATFORM", "R-CLAUDE-DATA-ROOT", "R-UNREAD-SCOPE", "R-PROVIDER-COPY",
    "R-TEST-EVIDENCE", "R-CLEANUP", "R-RELEASE-STATUS",
}
INVARIANTS = {
    "BI-CONNECTION", "BI-SETTING-SOURCES", "BI-WINDOWS-MXC", "BI-WSL2-MODE", "BI-CLOUD-SHIFT",
    "BI-CONVERSATION", "BI-CONFIG-ROOT", "BI-ENTRY-MODE", "BI-TERMINAL", "BI-REPORT-DESK",
    "BI-UNREAD-SCOPE", "BI-NOTIFICATION", "BI-PROVIDER-COPY", "BI-TEST-CLEANUP", "BI-DATA",
    "BI-PLANNING-STATUS",
}


def run(*args, check=True, env=None):
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if check and proc.returncode:
        raise AssertionError("%s\n%s%s" % (" ".join(args), proc.stdout, proc.stderr))
    return proc


def git(*args, check=True):
    return run("git", *args, check=check).stdout.strip()


def read(path):
    with open(path, encoding="utf-8", errors="replace") as stream:
        return stream.read()


def tracked_paths():
    return [path for path in git("ls-files").splitlines() if path]


def changed_map(revision):
    rows = git("diff", "--name-status", BASE, revision).splitlines()
    return {row.split("\t", 1)[1]: row.split("\t", 1)[0] for row in rows}


def assert_no_markers(paths):
    marker = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.M)
    hits = [path for path in paths if marker.search(read(os.path.join(ROOT, path)))]
    assert not hits, "conflict markers: %s" % ", ".join(hits)


def assert_sources_parse(paths):
    python_paths = [path for path in paths if path.endswith(".py")] + ["orbit"]
    duplicates = []
    for path in python_paths:
        tree = ast.parse(read(os.path.join(ROOT, path)), filename=path)
        names = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        duplicates.extend("%s:%s" % (path, name) for name in set(names) if names.count(name) > 1)
    assert not duplicates, "duplicate top-level definitions: %s" % ", ".join(sorted(duplicates))


def assert_structured_files(paths):
    for path in paths:
        if path.endswith(".json"):
            json.loads(read(os.path.join(ROOT, path)))
    for path in ("core/panel/app.js", "core/guard/staff-guard/hooks/register.js"):
        run("node", "--check", path)


def assert_inventory():
    local, upstream = changed_map(LOCAL), changed_map(UPSTREAM)
    assert (len(local), len(upstream)) == (71, 35), (len(local), len(upstream))
    assert set(local) & set(upstream) == OVERLAPS
    assert len(set(local) | set(upstream)) == 92


def assert_expected_artifacts():
    expected = ("core/claudeapp.py", "core/desk.py", "core/desk.md", "core/jobs/claude_app.md",
                "core/mxc.py", "setup-windows.ps1", "specs/001-windows-mxc-sandbox/spec.md",
                "specs/002-claude-connection-pass-through/spec.md", "specs/003-close-containment-gaps/spec.md")
    missing = [path for path in expected if not os.path.isfile(os.path.join(ROOT, path))]
    assert not missing, "missing retained artifacts: %s" % ", ".join(missing)


def assert_guard_workflow():
    workflow = read(os.path.join(ROOT, ".github", "workflows", "tests.yml"))
    guard = read(os.path.join(ROOT, "core", "guard", "staff-guard", "tests", "guard.test.ts"))
    assert len(re.findall(r"^test\(", guard, re.M)) == 10
    assert "claude plugin test" in workflow
    assert workflow.index("curl -fsSL https://claude.ai/install.sh") < workflow.index("claude plugin test")


def structural():
    assert not git("diff", "--name-only", "--diff-filter=U"), "unmerged index paths remain"
    assert not git("ls-files", "-u"), "multi-stage index entries remain"
    run("git", "diff", "--check")
    run("git", "diff", "--cached", "--check")
    paths = [path for path in tracked_paths() if path.endswith((".py", ".js", ".ts", ".md", ".yml", ".yaml", ".json", ".sh", ".ps1", ".txt"))]
    assert_no_markers(paths)
    assert_sources_parse(tracked_paths())
    assert_structured_files(tracked_paths())
    assert read(os.path.join(ROOT, "VERSION")).strip() == "0.12.0"
    assert_inventory()
    assert_expected_artifacts()
    assert_guard_workflow()
    print("SAFE_MERGE_STRUCTURAL_OK")


def residue():
    patterns = ("staffroom-test-*", "orbit-platforms-test-*", "staff-channels-test-*",
                "staff-tools-test-*", "orbit-calls-test-*", "orbit-mxc-test-*", "fake-claude-*")
    return {os.path.realpath(path) for pattern in patterns for path in glob.glob(os.path.join(tempfile.gettempdir(), pattern))}


def tests():
    before, summaries = residue(), []
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", STAFF_TEST_OCR="0")
    for module in MODULES:
        proc = run(sys.executable, "-m", "unittest", "tests." + module, check=False, env=env)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode:
            raise AssertionError("tests.%s failed\n%s" % (module, output[-4000:]))
        match = re.search(r"Ran (\d+) tests?", output)
        assert match, "tests.%s produced no unittest count" % module
        summaries.append("%s=%s" % (module, match.group(1)))
    leaked = residue() - before
    assert not leaked, "test residue: %s" % ", ".join(sorted(leaked))
    print("SAFE_MERGE_TESTS_OK " + " ".join(summaries))


def table_rows(text, prefix):
    rows = []
    for line in text.splitlines():
        if line.startswith("| `%s" % prefix):
            rows.append([cell.strip().strip("`") for cell in line.strip().strip("|").split("|")])
    return rows


def assert_coverage(ledger):
    rows = table_rows(ledger, "C")
    assert len(rows) == 92
    assert len({row[0] for row in rows}) == 92
    assert len({row[1] for row in rows}) == 92
    assert sum(row[2] != "absent" for row in rows) == 71
    assert sum(row[3] != "absent" for row in rows) == 35
    assert sum(row[4] == "true" for row in rows) == 14
    assert not [row for row in rows if row[6] in ("pending", "approved_exclusion")]


def assert_resolution_status(ledger):
    found = set(re.findall(r"^### (R-[A-Z-]+)$", ledger, re.M))
    assert found == RESOLUTIONS, (found ^ RESOLUTIONS)
    blocks = re.split(r"^### ", ledger, flags=re.M)[1:]
    statuses = {block.splitlines()[0]: re.findall(r"\*\*Status:\*\* `([^`]+)`", block) for block in blocks}
    bad = {name: value for name, value in statuses.items() if name in RESOLUTIONS and value != ["verified"]}
    assert not bad, "unverified resolutions: %r" % bad


def assert_evidence_records(results):
    rows = table_rows(results, "E-")
    assert rows, "no validation evidence records"
    ids = [row[0] for row in rows]
    assert len(ids) == len(set(ids)), "duplicate evidence IDs"
    summary = {row[0]: row[1] for row in table_rows(results, "I") if row[0] in {"I0", "I1", "I2", "I3", "I4", "I5"}}
    assert summary == {gate: "pass" for gate in ("I0", "I1", "I2", "I3", "I4", "I5")}, summary
    assert "| `D1` | `pass` |" in results
    assert "| `REL1` | `blocked` |" in results
    assert "| `PUB1` | `pending` |" in results and "`hold_local`" in results


def evidence():
    ledger = read(os.path.join(EVIDENCE, "integration-ledger.md"))
    results = read(os.path.join(EVIDENCE, "validation-results.md"))
    assert_coverage(ledger)
    invariants = set(re.findall(r"^\| `(BI-[A-Z0-9-]+)` \|", ledger, re.M))
    assert invariants == INVARIANTS, (invariants ^ INVARIANTS)
    assert_resolution_status(ledger)
    assert_evidence_records(results)
    print("SAFE_MERGE_EVIDENCE_OK")


def history():
    merge = None
    for line in git("log", "--format=%H %P", "HEAD").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[1:] == [LOCAL, UPSTREAM]:
            merge = fields[0]
            break
    assert merge, "recorded merge with parents %s + %s is not on HEAD's ancestry" % (LOCAL, UPSTREAM)
    commit = merge
    fields = git("show", "-s", "--format=%H %T %P", commit).split()
    assert len(fields) == 4, fields
    assert fields[2:] == [LOCAL, UPSTREAM], fields
    assert git("rev-parse", "backup-before-sync") == LOCAL
    assert not git("replace", "-l"), "replacement refs remain"
    run("git", "merge-base", "--is-ancestor", LOCAL, commit)
    run("git", "merge-base", "--is-ancestor", UPSTREAM, commit)
    no_replace = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1")
    inspected = subprocess.run(["git", "show", "-s", "--format=%H %T %P", commit], cwd=ROOT,
                               env=no_replace, capture_output=True, text=True, check=True).stdout.split()
    assert inspected == fields
    assert REPLACED not in git("replace", "-l").splitlines()
    print("SAFE_MERGE_HISTORY_OK")


def main():
    modes = {"structural": structural, "tests": tests, "evidence": evidence, "history": history}
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode not in modes:
        raise SystemExit("usage: verify_candidate.py structural|tests|evidence|history")
    try:
        modes[mode]()
    except (AssertionError, OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit("%s verification failed: %s" % (mode, error))


if __name__ == "__main__":
    main()
