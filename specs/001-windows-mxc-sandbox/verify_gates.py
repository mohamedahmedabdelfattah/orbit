#!/usr/bin/env python3
"""Gate oracles for GATES.md (feature 001-windows-mxc-sandbox).

Run from this directory:  python verify_gates.py <command>

Each command performs all its assertions and prints its success marker
("... verification passed") only after every assertion holds; it exits
nonzero with bounded diagnostics otherwise.  Stdlib only.
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # feature dir -> specs -> kit root
WF = os.path.join(REPO, ".github", "workflows", "tests.yml")

ALL_MODULES = ["tests.test_core", "tests.test_channels", "tests.test_tools",
               "tests.test_calls", "tests.test_platforms", "tests.test_mxc"]

# (module, ["-k" substring filters]) pairs per phase command: each filtered
# run must select at least one test and end OK.
PHASE_RUNS = {
    "phase2":  [("tests.test_platforms", ["windows"]), ("tests.test_platforms", ["mode"])],
    "phase4":  [("tests.test_mxc", ["request", "hook"])],
    "phase5":  [("tests.test_mxc", ["probe"])],
    "phase57": [("tests.test_platforms", ["switch", "wsl2"])],
    "phase39": [("tests.test_platforms", ["task"]), ("tests.test_platforms", ["doctor"])],
}

RAN = re.compile(r"Ran (\d+) tests? ")


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def run_unittest(module, kf=None):
    """Run one unittest module from the repo root; return (ok, selected, tail)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", STAFF_TEST_OCR="0")
    cmd = [sys.executable, "-m", "unittest", module]
    if kf:
        for pat in kf:
            cmd += ["-k", pat]
    proc = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, timeout=1100,
                          encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    m = RAN.search(out)
    sel = int(m.group(1)) if m else None
    ok = proc.returncode == 0 and sel is not None and sel > 0
    return ok, sel, out[-2500:]


def fail(diag):
    for d in diag:
        sys.stdout.write(d.rstrip() + "\n")
    sys.exit(1)


def cmd_phase(name):
    ok, diag = True, []
    for module, kf in PHASE_RUNS[name]:
        g, sel, tail = run_unittest(module, kf)
        if not g:
            ok = False
            diag.append("%s -k %r: selected=%s\n%s" % (module, kf, sel, tail))
    if not ok:
        fail(diag)
    print("%s verification passed" % name)
    sys.exit(0)


def cmd_full():
    env = dict(os.environ, PYTHONIOENCODING="utf-8", STAFF_TEST_OCR="0")
    proc = subprocess.run([sys.executable, "-m", "unittest"] + ALL_MODULES,
                          cwd=REPO, env=env, capture_output=True, timeout=1100,
                          encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    m = RAN.search(out)
    sel = int(m.group(1)) if m else None
    if proc.returncode == 0 and sel and sel > 0 and "FAILED" not in out:
        print("full-suite verification passed")
        sys.exit(0)
    fail(["full suite: exit=%s selected=%s\n%s" % (proc.returncode, sel, out[-2500:])])


def cmd_ci():
    problems = []
    if not os.path.isfile(WF):
        fail(["workflow missing: .github/workflows/tests.yml"])
    text = read(WF)
    if "windows-latest" not in text:
        problems.append("no windows-latest job in tests.yml")
    hint = "MXC containment itself is not part of automated testing"
    if hint not in text:
        problems.append("no MXC-not-automated hint comment in tests.yml")
    elif "specs/001-windows-mxc-sandbox/quickstart.md" not in text:
        problems.append("hint does not point to quickstart.md")
    if problems:
        fail(problems)
    print("ci verification passed")
    sys.exit(0)


def cmd_planning():
    docs = ["spec.md", "plan.md", "tasks.md", "research.md", "data-model.md",
            "quickstart.md",
            os.path.join("contracts", "mxc-request.md"),
            os.path.join("contracts", "cc-hook.md"),
            os.path.join("contracts", "service-task.md"),
            os.path.join("checklists", "requirements.md"),
            "GATES.md"]
    problems = ["missing artifact: %s" % d for d in docs
                if not os.path.isfile(os.path.join(HERE, d))]
    if problems:
        fail(problems)

    tasks = read(os.path.join(HERE, "tasks.md"))
    plan = read(os.path.join(HERE, "plan.md"))
    spec = read(os.path.join(HERE, "spec.md"))
    qs = read(os.path.join(HERE, "quickstart.md"))
    research = read(os.path.join(HERE, "research.md"))

    defined = set(re.findall(r"^- \[.\] (T\d{3})", tasks, re.M))
    if not defined:
        problems.append("tasks.md defines no tasks")
    for name, text in (("plan.md", plan), ("tasks.md", tasks), ("spec.md", spec),
                       ("research.md", research), ("quickstart.md", qs)):
        for ref in re.findall(r"\b(T\d{3})\b", text):
            if ref not in defined:
                problems.append("dangling task reference %s in %s" % (ref, name))

    # stale per-run containment / release-gate artifacts must be gone
    for fname, text in (("plan.md", plan), ("tasks.md", tasks), ("spec.md", spec),
                        ("research.md", research), ("quickstart.md", qs)):
        if "SE-1" in text:
            problems.append("stale 'SE-1' label in %s" % fname)
        if "manual release gate" in text:
            problems.append("'manual release gate' wording survives in %s" % fname)
    if "Why CI can't run real MXC probes" in plan:
        problems.append("plan.md references old CI section title")
    if "Why CI doesn't test real MXC" not in plan:
        problems.append("plan.md missing updated CI note title")
    if "report from T034" in tasks or "report from T035" not in tasks:
        problems.append("T042 triage reference not on T035")
    if "one per employee run" in spec:
        problems.append("spec.md still says one container per employee run")
    if "one per contained command" not in spec:
        problems.append("spec.md missing per-command containment wording")
    for s in "ABCDEF":
        if "Scenario %s" % s not in qs:
            problems.append("quickstart.md missing Scenario %s" % s)
    if "PreToolUse" not in tasks:
        problems.append("tasks.md lost the PreToolUse hook wording")

    if problems:
        fail(problems)
    print("planning verification passed")
    sys.exit(0)


def main():
    cmds = {"planning": cmd_planning, "ci": cmd_ci,
            "full": cmd_full}
    for _k in PHASE_RUNS:
        cmds[_k] = (lambda k: lambda: cmd_phase(k))(_k)
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c not in cmds:
        sys.stdout.write("usage: verify_gates.py (%s)\n" % " | ".join(sorted(cmds)))
        sys.exit(2)
    cmds[c]()


if __name__ == "__main__":
    main()
