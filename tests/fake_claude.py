"""One deterministic fake Claude Code executable for every story and platform test (T001).

No real inference, credentials or network. `install()` writes a driver script plus a tiny
launcher, configures its behavior through `control.json`, and returns the launcher path to
assign to `engine.resolve_claude`. Every call is recorded to `calls.jsonl` — argv, the full
environment snapshot and stdin — and nothing about that recording is ever written to stdout,
so tests can prove Orbit doesn't copy inherited values EVEN WHEN the environment carries them.

The driver deliberately never echoes an inherited sentinel back, while a separate harmless
marker can be emitted on stderr to prove Claude-output handling itself is unchanged.
"""
import json
import os
import tempfile

try:                                                     # test modules import this both ways
    from . import _cleanup
except ImportError:
    import _cleanup

DRIVER = r'''# the fake Claude Code: records, then answers only what control.json allows
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
rec = {"argv": argv, "cwd": os.getcwd(), "env": dict(os.environ), "stdin": ""}
try:
    if not sys.stdin.isatty():
        rec["stdin"] = sys.stdin.read()
except Exception:
    pass
with open(os.path.join(HERE, "calls.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def out(d):
    print(json.dumps(d), flush=True)


cfg = {}
ctl = os.path.join(HERE, "control.json")
if os.path.exists(ctl):
    with open(ctl, encoding="utf-8") as fh:
        cfg = json.load(fh)

if "--version" in argv or "-v" in argv:
    v = cfg.get("version", {})
    if v.get("stderr"):
        sys.stderr.write(v["stderr"])
    out_text = v.get("out", "fake-claude 0.0.1")
    if v.get("out_marker"):
        sys.stderr.write(v["out_marker"] + "\n")
    print(out_text)
    sys.exit(v.get("exit", 0))

if argv[:2] == ["auth", "status"]:
    a = cfg.get("auth", {})
    print(json.dumps({"loggedIn": a.get("loggedIn", False),
                      "authMethod": a.get("authMethod", "none")}), flush=True)
    if a.get("stderr"):
        sys.stderr.write(a["stderr"])
    sys.exit(a.get("exit", 0))

if argv[:1] == ["plugin"]:
    a = cfg.get("admin", {})                           # plugin administration (marketplace/install/update)
    sys.stdout.write((a.get("out") or "already installed") + "\n")
    if a.get("stderr"):
        sys.stderr.write(a["stderr"])
    sys.exit(a.get("exit", 0))

if "-p" in argv or "--print" in argv:
    p = cfg.get("prompt", {})
    if p.get("stderr_marker"):
        sys.stderr.write(p["stderr_marker"] + "\n")
    if p.get("fail_resume") and "--resume" in argv:
        out({"type": "result", "subtype": "error_during_execution", "is_error": True,
             "result": p["fail_resume"], "num_turns": 0, "total_cost_usd": 0.0})
        sys.exit(p.get("exit", 1))
    if p.get("error"):
        out({"type": "result", "subtype": "error_during_execution", "is_error": True,
             "result": p["error"], "num_turns": 0, "total_cost_usd": 0.0})
        sys.exit(p.get("exit", 1))
    fmt = argv[argv.index("--output-format") + 1] if "--output-format" in argv and \
        argv.index("--output-format") + 1 < len(argv) else "stream"
    if fmt == "json":
        out({"type": "result", "subtype": "success", "is_error": False,
             "result": p.get("result", ""), "structured_output": p.get("structured") or {},
             "num_turns": 1, "total_cost_usd": 0.0})
    else:
        out({"type": "system", "subtype": "init", "session_id": "fake-session"})
        out({"type": "assistant", "message": {"content": [{"type": "text", "text": p.get("result") or "Done."}]}})
        out({"type": "result", "subtype": "success", "is_error": False,
             "result": p.get("result") or "Done.", "num_turns": 1, "total_cost_usd": 0.0})
    sys.exit(p.get("exit", 0))

sys.stderr.write("fake-claude: unsupported invocation %r\n" % (argv,))
sys.exit(2)
'''

LAUNCHER_BAT = '@echo off\r\nset PYTHONUTF8=1\r\n"{py}" "{driver}" %*\r\n'
LAUNCHER_SH = '#!/bin/sh\nexec "{py}" "{driver}" "$@"\n'


def install(directory=None, version=None, auth=None, prompt=None, admin=None):
    """Write the fake into `directory` (or a fresh temp dir) and return the launcher path.
    `version`, `auth`, `prompt` and `admin` are control.json sections; anything left out keeps
    harmless defaults (`--version` succeeds, account status says signed out, `-p` succeeds,
    `plugin` administration reports already-installed)."""
    d = directory or tempfile.mkdtemp(prefix="fake-claude-")
    _cleanup.on_exit(d)                                 # never leave a full-environment recorder behind
    os.makedirs(d, exist_ok=True)
    driver = os.path.join(d, "fake_claude.py")
    with open(driver, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(DRIVER)
    import sys
    py = sys.executable
    drv = os.path.abspath(driver)
    if os.name == "nt":
        launcher = os.path.join(d, "claude.bat")
        with open(launcher, "w", encoding="utf-8") as fh:
            fh.write(LAUNCHER_BAT.format(py=py, driver=drv))
    else:
        launcher = os.path.join(d, "claude")
        with open(launcher, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(LAUNCHER_SH.format(py=py, driver=drv))
        os.chmod(launcher, 0o755)
    configure(d, version=version, auth=auth, prompt=prompt, admin=admin)
    return launcher


def configure(directory, version=None, auth=None, prompt=None, admin=None):
    """Merge control sections into control.json. Sections below are optional dicts; pass a
    full `cfg` key/value for top-level extras."""
    ctl = os.path.join(directory, "control.json")
    cfg = {}
    if os.path.exists(ctl):
        with open(ctl, encoding="utf-8") as fh:
            cfg = json.load(fh)
    for name, val in (("version", version), ("auth", auth), ("prompt", prompt), ("admin", admin)):
        if val is not None:
            cfg[name] = val
    with open(ctl, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=1)


def calls(directory):
    """Every recorded invocation: list of {argv, cwd, env, stdin}, oldest first."""
    path = os.path.join(directory, "calls.jsonl")
    try:
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    except OSError:
        return []
