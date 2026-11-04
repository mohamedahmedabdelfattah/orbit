#!/usr/bin/env python3
"""The native-Windows sandbox: Orbit's ownership policy on Microsoft Execution Containers (MXC).

One job, three surfaces, in Orbit's words:
  * translate the one policy model (deny-read, allow-write, network allowlist) into an MXC
    stable-schema request, one per contained shell command — deterministic for a given
    registry + profile state, cached per run for speed (R2.5);
  * issue contained commands through Orbit's PreToolUse hook and probe the sandbox in both
    directions before a crew run;
  * refuse instead of unsandbox: a command that can't be contained is denied, never let
    through without the boundary (R2.4).

The agent itself is never wrapped: `claude` runs exactly as on macOS/Linux; only its
shell/PowerShell tool calls are rewritten into executor invocations by the hook
(contracts/cc-hook.md). Python 3.9 compatible; the executor is an external binary, not a lib.
"""
from __future__ import annotations

import copy
import fnmatch
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import engine
import osinfo

CORE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(CORE)

# ------------------------------------------------------------------ constants
SCHEMA_MAJOR = 1                                    # the MXC request schema major version Orbit emits
EXECUTOR = "wxc-exec.exe"
EXECUTOR_FLAG_DEBUG = "--debug"
EXECUTOR_FLAG_AUDIT = "--audit"                     # doctor triage only — never on real commands
COMMAND_TIMEOUT_MS = 600000                         # a contained command dies after 10 min, no orphans

VENDOR_DIR = os.path.join(KIT, "vendor", "mxc")
VERSION_FILE = os.path.join(VENDOR_DIR, "version.txt")

MODES = ("mxc", "wsl2")

PROBE_DENY_MARKERS = re.compile(r"denied|blocked|not allowed|refused|EACCES|EPERM|forbidden", re.I)


def _reason(msg):
    """Single-line, sanitized for the run log and hook reasons: no newlines, no control chars."""
    return re.sub(r"[\x00-\x1f]+", " ", " ".join(str(msg).split())) or "unknown reason"


# ------------------------------------------------------------------ executor discovery and seam
def executor_path():
    """The MXC executor binary: first the kit's vendored copy, then PATH. None when absent."""
    cand = os.path.join(VENDOR_DIR, EXECUTOR)
    if os.path.isfile(cand):
        return cand
    if osinfo.KIND == "windows":
        return osinfo.which(EXECUTOR)
    return None


def version_pinned() -> str:
    """The MXC runtime version the installer recorded (vendor/mxc/version.txt), or ''."""
    try:
        with open(VERSION_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def version_of(executor: str = None) -> str:
    """The runtime's own version, from the schema line of its --debug output. Never required."""
    try:
        r = _spawn_executor([executor or executor_path() or EXECUTOR, EXECUTOR_FLAG_DEBUG], timeout=30)
        m = re.search(r"schema[: ]+v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", (r.stdout or "") + (r.stderr or ""))
        return ".".join(g for g in m.groups() if g is not None) if m else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def discover() -> dict:
    """Is MXC usable on this machine? Files and schema only — only the probe can prove enforcement
    (research D6: discovery is never proof). → {ok, reason, executor, version, schema_major}"""
    ex = executor_path()
    if not ex:
        return {"ok": False, "reason": "the MXC executor (%s) is missing: run the Windows installer "
                "(setup-windows.ps1) again" % EXECUTOR, "executor": None, "version": "",
                "schema_major": SCHEMA_MAJOR}
    ver, pinned = version_of(ex), version_pinned()
    if pinned and ver and pinned.split(".")[0] != ver.split(".")[0]:
        return {"ok": False, "reason": "the installed MXC runtime is v%s but Orbit asks for schema "
                "v%d: run the Windows installer again" % (ver, SCHEMA_MAJOR), "executor": ex,
                "version": ver, "schema_major": SCHEMA_MAJOR}
    return {"ok": True, "reason": "", "executor": ex, "version": ver, "schema_major": SCHEMA_MAJOR}


def executor_argv(executor: str, request_file: str, command: str, debug=False) -> list:
    """The executor invocation: executor, request file, wrapped command (D1: the CLI shape — request
    path plus wrapped command argument — is verified against the current release at packaging time)."""
    return [executor] + ([EXECUTOR_FLAG_DEBUG] if debug else []) + [request_file, command]


SPAWN = None                                            # tests intercept here: set_executor_stub(fn)


def set_executor_stub(fn):
    """Point the executor seam at a fake for tests: fn(args=…, env=…, timeout=…) → returncode/stdout/stderr."""
    global SPAWN
    SPAWN = fn


def clear_executor_stub():
    global SPAWN
    SPAWN = None


def _spawn_executor(args, env=None, timeout=None):
    """The one place an executor launch happens (fakeable; T002). Never --audit/--debug on real runs."""
    if SPAWN is not None:
        return SPAWN(args=args, env=env, timeout=timeout)
    return subprocess.run([a for a in args if a], capture_output=True, text=True, env=env, timeout=timeout)


def ran(args, timeout=60):
    """→ (returncode, combined output, elapsed ms), for the probe and doctor triage."""
    t0 = time.time()
    try:
        r = _spawn_executor(args=args, timeout=timeout)
        rc = getattr(r, "returncode", 1)
        out = (getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        rc, out = 127, _reason(e)
    return rc, out, round((time.time() - t0) * 1000)


def denial_summary(text: str) -> str:
    """Executor failure/violation output → an owner-readable sentence (T035, feeds R6.3)."""
    t = " ".join((text or "").split())
    if not t:
        return "the sandbox reported no details (logged)."
    return t[:300]


# ------------------------------------------------------------------ mode storage (PlatformMode)
def mode() -> str:
    """The effective containment path on native Windows: "mxc" (default) or "wsl2" (fallback).
    Anywhere else the answer is "wsl2" — meaning: run Orbit inside WSL2 the way it always has."""
    m = (engine.registry().get("platform") or {}).get("sandbox_mode")
    if m in MODES:
        return m
    return "mxc" if osinfo.KIND == "windows" else "wsl2"


def mode_info(reg=None) -> dict:
    p = (reg if reg is not None else engine.registry()).get("platform") or {}
    m = p.get("sandbox_mode")
    if m not in MODES:
        m = "mxc" if osinfo.KIND == "windows" else "wsl2"
    return {"sandbox_mode": m, "decided_by": p.get("decided_by") or "",
            "decided_at": p.get("decided_at") or "", "mxc_unavailable_reason": p.get("mxc_unavailable_reason")}


def set_mode(m, decided_by="owner", reason=""):
    """A mode change needs an owner decision, or a recorded unavailability reason — nothing else (R4.1)."""
    if m not in MODES:
        raise ValueError("unknown sandbox mode: %s" % m)
    if decided_by not in ("owner", "unavailable"):
        raise ValueError("a mode decision is made by the owner or by detected unavailability")
    if decided_by == "unavailable" and not reason:
        raise ValueError("an unavailability decision needs the reason recorded")
    reg = engine.registry()
    reg["platform"] = {"sandbox_mode": m, "decided_by": decided_by,
                       "decided_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "mxc_unavailable_reason": _reason(reason) if reason else None}
    engine.save_registry(reg, "sandbox mode: %s (%s)" % (m, decided_by))


def record_unavailable(reason):
    """MXC turned out unusable on this machine: fall back to WSL2 with the reason recorded. Setup and
    doctor only — nothing switches a run's mode mid-flight (SC3)."""
    set_mode("wsl2", "unavailable", reason)


def unavailable_reason() -> str:
    return (engine.registry().get("platform") or {}).get("mxc_unavailable_reason") or ""


# ------------------------------------------------------------------ policy translation (ContainmentPolicy)
def _secret_paths() -> list:
    """The deny-read set in this machine's native paths (engine.SECRET_PATHS is already shaped so)."""
    return sorted({os.path.abspath(os.path.expanduser(p)) for p in engine.SECRET_PATHS})


def compute_policy(emp: dict) -> dict:
    """The one policy model, once, for this employee and this registry state (deterministic; R2.5).
    Colleagues' workspaces are unreadable, exactly as the built-in sandbox does it. Gateway commands
    never appear here: they run unwrapped, where their own hosts/limits live (excludedCommands parity)."""
    others = [os.path.realpath(p) for p in glob.glob(os.path.join(engine.HOME, "employees", "*"))
              if os.path.realpath(p) != os.path.realpath(emp["workspace"])]
    if osinfo.KIND == "windows":
        temp_dir = tempfile.gettempdir()
        team = os.path.join(engine.HOME, "team")
    else:
        temp_dir, team = tempfile.gettempdir(), os.path.join(engine.HOME, "team")
    return {
        "deny_read": sorted(set(_secret_paths() + others)),
        "allow_write": [emp["workspace"], team, temp_dir],
        "domains": sorted(set(engine.BASE_DOMAINS
                              + engine.registry().get("network_domains", [])
                              + emp.get("network_domains", []))),
        "timeout_ms": COMMAND_TIMEOUT_MS,
    }


def cache_file(emp: dict) -> str:
    return os.path.join(emp["workspace"], "state", "mxc-policy.json")


def read_policy_cache(emp: dict):
    try:
        with open(cache_file(emp), encoding="utf-8") as fh:
            pol = json.load(fh)
        return pol if pol.get("deny_read") and pol.get("allow_write") else None
    except (OSError, ValueError):
        return None


def write_policy_cache(emp: dict) -> str:
    """The policy, precomputed by engine.run before the agent starts: each hook call (a fresh process
    per tool call) then only stamps a request, without re-reading the whole registry."""
    pol = compute_policy(emp)
    f = cache_file(emp)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(pol, fh)
    os.replace(tmp, f)
    return f


def _policy(emp):
    return read_policy_cache(emp) or compute_policy(emp)


def build_request(emp, command: str, cwd: str = None) -> dict:
    """One MXC request for one contained command, per contracts/mxc-request.md. Invariants 1–3
    (fail-closed defaults, no silent loosening, agent-flow neutrality) hold by construction."""
    pol = emp if isinstance(emp, dict) and "deny_read" in emp else _policy(emp)
    return {
        "command": command,
        "working_directory": os.path.abspath(cwd or os.getcwd()),
        "filesystem": {"deny_read": pol["deny_read"], "allow_write": pol["allow_write"]},
        "network": {"egress": {"default": "deny", "allow": pol["domains"]}},
        "timeout_ms": pol.get("timeout_ms", COMMAND_TIMEOUT_MS),
    }


# ------------------------------------------------------------------ the hook (PreToolUse)
def _gateway_patterns(emp_id: str) -> list:
    try:
        import abilities
        return abilities.commands(emp_id)
    except Exception:  # noqa: BLE001  (an ability hiccup must never make a command uncontainable)
        return []


def _excluded(command: str, patterns=None) -> bool:
    """Gateway commands (staff-fetch …) run unwrapped: their own limits stay in force, exactly like the
    built-in sandbox's excludedCommands."""
    pats = patterns if patterns is not None else _gateway_patterns(os.environ.get("STAFF_EMPLOYEE") or "")
    return any(fnmatch.fnmatch(command, p) for p in pats)


def hook_settings() -> dict:
    """The hooks block Orbit adds to the settings blob on native Windows: a PreToolUse hook matching
    Bash|PowerShell that rewrites each shell command into an MXC executor invocation (T033)."""
    cmd = '"%s" "%s" --hook' % (sys.executable, os.path.join(CORE, "mxc.py"))
    return {"PreToolUse": [{"matcher": "Bash|PowerShell",
                            "hooks": [{"type": "command", "command": cmd, "timeout": 30}]}]}


def _log_decision(ws: str, rec: dict) -> None:
    """Diagnostics for support (R6.3) and the what-we-generated record (R2.5): <ws>/state/mxc.jsonl."""
    try:
        os.makedirs(os.path.join(ws, "state"), exist_ok=True)
        with open(os.path.join(ws, "state", "mxc.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def decision(payload: dict, cwd=None, now=None) -> dict:
    """One PreToolUse hook call → the hook's answer, per contracts/cc-hook.md.
    payload: {tool_name, tool_input:{command}} as Claude sends it."""
    payload = payload or {}
    cmd = ((payload.get("tool_input") or {}).get("command") or "").strip()
    if not cmd:
        return {}
    emp_id = os.environ.get("STAFF_EMPLOYEE") or ""
    if emp_id:
        emp = engine.employee(emp_id)
    else:
        emp = {"id": "unknown", "name": "?",
               "workspace": cwd or payload.get("cwd") or os.getcwd()}
    ws = emp["workspace"]
    base = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now or time.time())),
            "employee": emp_id or "unknown", "tool": payload.get("tool_name"), "command": cmd[:200]}
    if _excluded(cmd):
        _log_decision(ws, {**base, "decision": "pass-through"})
        return {}                                        # no decision: Claude's own rules apply, unwrapped
    d = discover()
    if d["ok"]:
        try:
            req = build_request(emp, cmd, cwd or payload.get("cwd") or ws)
        except Exception as e:  # noqa: BLE001
            d = {**d, "ok": False, "reason": "couldn't build the containment request: %s" % _reason(e)}
    if not d["ok"]:
        msg = "Orbit's sandbox couldn't start (%s); the command was denied rather than run unsandboxed." % d["reason"]
        _log_decision(ws, {**base, "decision": "deny", "reason": d["reason"]})
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": _reason(msg)}}
    req_dir = os.path.join(ws, "state", "requests")
    os.makedirs(req_dir, exist_ok=True)
    h = hashlib.sha256(json.dumps(req, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    path = os.path.join(req_dir, "%s-%s.json" % (time.strftime("%Y%m%d-%H%M%S"), h))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(req, fh)
    contained = " ".join(('"%s"' % a) if re.search(r"\s", a) else a
                         for a in executor_argv(d["executor"], path, cmd))
    _log_decision(ws, {**base, "decision": "allow", "request_hash": h, "request": os.path.basename(path),
                       "executor": os.path.basename(d["executor"])})
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                   "permissionDecisionReason": "contained by Orbit's sandbox (MXC)",
                                   "updatedInput": {**(payload.get("tool_input") or {}), "command": contained}}}


def hook_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}


def hook_main() -> int:
    """stdin hook JSON → decision JSON on stdout, exit 0 always (a crashed hook must not widen
    anything: Claude falls back to its own permission rules)."""
    try:
        r = decision(hook_payload())
    except Exception as e:  # noqa: BLE001
        r = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
             "permissionDecisionReason": _reason("Orbit's sandbox hook failed: %s" % e)}}
    print(json.dumps(r))
    return 0


# ------------------------------------------------------------------ the probe (ProbeResult, data-model §3)
def _probe_reqs(builder):
    """The request factory for probe cases: the caller's builder, with family-specific tweaks applied
    to a copy (never to the real policy)."""
    def base(cmd, cwd):
        return builder(cmd, cwd)

    def forged(cmd, cwd, **tweaks):
        req = copy.deepcopy(builder(cmd, cwd))
        for k, v in tweaks.items():
            req[k] = v
        return req
    return base, forged


def probe(emp=None, builder=None, on_cmd=None) -> dict:
    """Prove both directions before a crew run (R6.1): allowed work succeeds; an out-of-scope write,
    a secret read, a non-allowlisted connect each fail; a workload outliving the timeout is killed
    (no orphans). Discovery alone is never proof (research D6). → ProbeResult per data-model §3."""
    emp = emp or {"id": "probe", "workspace": os.path.join(engine.HOME, "employees", "probe"),
                  "name": "probe"}
    out = {"mode": "mxc", "positive": {}, "negative": {}, "capability_notes": {}, "verdict": "unknown"}
    d = discover()
    if not d["ok"]:
        return {**out, "verdict": "unusable-with-reason", "capability_notes": {"discovery": d["reason"]}}
    ex = d["executor"]
    builder = builder or (lambda cmd, cwd: build_request(emp, cmd, cwd))
    base, forged = _probe_reqs(builder)
    secret_file = os.path.join(tempfile.gettempdir(), "orbit-probe-secret.txt")
    try:
        with open(secret_file, "w", encoding="utf-8") as fh:
            fh.write("pretend credential\n")
    except OSError:
        pass
    tmp = tempfile.mkdtemp(prefix="mxc-probe-")

    def case(name, req, cmd, timeout=45):
        req_f = os.path.join(tmp, name + ".json")
        try:
            with open(req_f, "w", encoding="utf-8") as fh:
                json.dump(req, fh)
        except OSError as e:
            rc, txt, ms = 127, _reason(e), 0
        else:
            rc, txt, ms = ran(executor_argv(ex, req_f, cmd), timeout=timeout)
        if on_cmd:
            on_cmd(name, rc, txt)
        return rc, txt, ms

    try:
        is_win = osinfo.KIND == "windows"
        # positive: write inside scope and read it back
        pos = 'python -c "import pathlib; print(pathlib.Path(r\'%s\').write_text(\'ok\'))"' % \
            os.path.join(tmp, "inside.txt") if is_win else "echo ok > inside.txt && cat inside.txt"
        rc, txt, ms = case("probe-pos", base(pos, tmp), pos)
        out["positive"]["write_inside_scope"] = rc == 0
        out["capability_notes"]["startup_ms"] = ms                   # SC6: ~1 s per command budget
        # negative: a write outside allow_write (the team folder's git area is deliberately not writable)
        neg = "echo outside > %s" % os.path.join(tmp, "..", "mxc-probe-should-fail.txt")
        rc, txt, _ = case("probe-neg-write", base(neg, tmp), neg, timeout=30)
        out["negative"]["outside_write"] = rc != 0 or bool(PROBE_DENY_MARKERS.search(txt))
        # negative: read a file this request's own deny_read covers
        req = forged("type secret" if is_win else "cat secret", tmp,
                     filesystem={"deny_read": [secret_file],
                                 "allow_write": [tmp, tempfile.gettempdir()]})
        cmd = "type \"%s\"" % secret_file if is_win else "cat %s" % secret_file
        rc, txt, _ = case("probe-neg-read", req, cmd, timeout=30)
        out["negative"]["secret_read"] = rc != 0 or bool(PROBE_DENY_MARKERS.search(txt))
        # negative: a connect to a host that is not allowlisted (literal address; no DNS needed)
        req = forged("curl -m 4 -s 198.51.100.1 -o nul", tmp, network={"egress": {"default": "deny", "allow": []}})
        rc, txt, _ = case("probe-neg-net", req, "curl -m 4 -s 198.51.100.1 -o nul" if is_win
                          else "curl -m 4 -s 198.51.100.1 -o probe-net.txt", timeout=30)
        out["negative"]["non_allowlisted_connect"] = rc != 0 or bool(PROBE_DENY_MARKERS.search(txt))
        # negative: a workload outliving its timeout is terminated (never orphaned)
        slow = "ping -n 30 127.0.0.1" if is_win else "sleep 30"
        req = forged(slow, tmp, timeout_ms=1500)
        rc, txt, ms = case("probe-neg-timeout", req, slow, timeout=45)
        out["negative"]["timeout_termination"] = rc != 0 or ms < 15000
        if os.path.exists(secret_file):
            os.remove(secret_file)                                   # nothing sensitive sits around
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [k for k, ok in out["negative"].items() if not ok]
    if all(out["positive"].values()) and not bad:
        out["verdict"] = "usable"
    else:
        out["verdict"] = "unusable-with-reason"
        out["capability_notes"]["failed"] = ", ".join(bad) or "the positive test failed"
    return out


def probe_summary(res: dict) -> str:
    """A ProbeResult in owner language for doctor/run output (R6.2/R6.3)."""
    if res.get("verdict") == "usable":
        return "the sandbox proved both directions: allowed work succeeds and every denial held."
    notes = "; ".join("%s: %s" % (k, v) for k, v in (res.get("capability_notes") or {}).items() if v)
    rows = [k for grp in ("positive", "negative")
            for k, ok in (res.get(grp) or {}).items() if ok is False]
    return "the sandbox couldn't be trusted yet%s. What failed: %s." % (
        (" (%s)" % notes) if notes else "", ", ".join(rows) or "unknown")


# ------------------------------------------------------------------ hook entry point
if __name__ == "__main__":
    if "--hook" in sys.argv:
        sys.exit(hook_main())
    print(__doc__)
