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
import ipaddress
import json
import os
import re
import select
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse

import engine
import osinfo

CORE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(CORE)

# ------------------------------------------------------------------ constants
SCHEMA_VERSION = "1.0.0"                            # exact immutable stable contract shipped by MXC 1.0.1
SCHEMA_MAJOR = 1                                    # compatibility/reporting shorthand for doctor
EXECUTOR = "wxc-exec.exe"
EXECUTOR_FLAG_DEBUG = "--debug"
EXECUTOR_FLAG_AUDIT = "--audit"                     # doctor triage only — never on real commands
EXECUTOR_FLAG_PROBE = "--probe"
COMMAND_TIMEOUT_MS = 600000                         # a contained command dies after 10 min, no orphans

VENDOR_DIR = os.path.join(KIT, "vendor", "mxc")
VERSION_FILE = os.path.join(VENDOR_DIR, "version.txt")
SCHEMA_FILE = os.path.join(VENDOR_DIR, "schema-version.txt")

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
    """The installer-pinned runtime version. wxc-exec deliberately has no version-print flag."""
    return version_pinned()


def schema_pinned() -> str:
    """The schema recorded beside the installed executor, or Orbit's exact stable contract."""
    try:
        with open(SCHEMA_FILE, encoding="utf-8") as fh:
            return fh.read().strip() or SCHEMA_VERSION
    except OSError:
        return SCHEMA_VERSION


def discover() -> dict:
    """Is the ProcessContainer runtime present and capable of Orbit's deny paths and loopback proxy?
    This is still discovery, not proof: probe() runs positive and negative workloads (research D6)."""
    ex = executor_path()
    if not ex:
        return {"ok": False, "reason": "the MXC executor (%s) is missing: run the Windows installer "
                "(setup-windows.ps1) again" % EXECUTOR, "executor": None, "version": "",
                "schema_major": SCHEMA_MAJOR, "schema_version": SCHEMA_VERSION}
    pinned_schema = schema_pinned()
    if pinned_schema.split(".")[0] != SCHEMA_VERSION.split(".")[0]:
        return {"ok": False, "reason": "the installed MXC schema is v%s but Orbit emits v%s: run "
                "setup-windows.ps1 again" % (pinned_schema, SCHEMA_VERSION), "executor": ex,
                "version": version_pinned(), "schema_major": SCHEMA_MAJOR,
                "schema_version": SCHEMA_VERSION}
    rc, text, _ = ran([ex, EXECUTOR_FLAG_PROBE], timeout=30)
    try:
        report = json.loads(text) if rc == 0 else {}
    except ValueError:
        report = {}
    probes = report.get("probes") or {}
    missing = []
    for field, words in (("baseContainerApiPresent", "ProcessContainer support"),
                         ("baseContainerSupportsDenyPaths", "secret-path denial"),
                         ("baseContainerSupportsIdentitylessLoopbackProxy", "approved-site proxying")):
        if not probes.get(field):
            missing.append(words)
    if rc != 0 or not report or missing:
        detail = ", ".join(missing) or denial_summary(text) or "the host capability probe failed"
        return {"ok": False, "reason": "this Windows build cannot provide %s; install current Windows "
                "updates or use WSL2 mode" % detail, "executor": ex, "version": version_pinned(),
                "schema_major": SCHEMA_MAJOR, "schema_version": SCHEMA_VERSION}
    return {"ok": True, "reason": "", "executor": ex, "version": version_pinned(),
            "schema_major": SCHEMA_MAJOR, "schema_version": SCHEMA_VERSION, "capabilities": report}


def executor_argv(executor: str, request_file: str, command: str = None, debug=False) -> list:
    """The official one-shot CLI: wxc-exec [--debug] request.json.

    The command already lives in process.commandLine. Keeping it there makes the request independently
    valid and avoids the CLI's optional trailing `-- <COMMAND>...` override surface.
    """
    return [executor] + ([EXECUTOR_FLAG_DEBUG] if debug else []) + [request_file]


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
    return subprocess.run([a for a in args if a], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=timeout)


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
    team = os.path.join(engine.HOME, "team")
    return {
        "deny_read": sorted(set(_secret_paths() + others)),
        "allow_write": [emp["workspace"], team],
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


def _workload_command(command: str, tool_name: str = None) -> str:
    """Preserve the shell semantics of the tool whose command the hook received."""
    if tool_name == "PowerShell":
        return subprocess.list2cmdline(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                                       "-Command", command])
    if tool_name == "Bash":
        raise ValueError("Git Bash cannot initialize inside MXC 1.0; use Claude's PowerShell tool")
    return command


def _readonly_roots(paths) -> list:
    """Read parity with Orbit's old sandbox: host volumes are read-only except explicit write roots."""
    roots = set()
    for path in paths:
        if not path:
            continue
        drive, _tail = os.path.splitdrive(os.path.abspath(os.path.expanduser(path)))
        if drive:
            roots.add(drive + os.sep)
    return sorted(roots)


def build_request(emp, command: str, cwd: str = None, tool_name: str = None, temp_dir: str = None) -> dict:
    """One exact MXC stable-schema 1.0.0 request for one contained command.

    Domain names are deliberately not put in network.egress.allow: MXC 1.0 accepts CIDRs there, not
    DNS names. run_request() adds a deny-direct, loopback-only HTTP/S proxy for the policy's domains.
    """
    pol = emp if isinstance(emp, dict) and "deny_read" in emp else _policy(emp)
    workdir = os.path.abspath(cwd or os.getcwd())
    # ProcessContainer treats a nonexistent policy path as a configuration error. Omitting one is safe:
    # a command cannot create it because its parent is not writable, and the policy is rebuilt per command.
    denied = [p for p in pol["deny_read"] if os.path.lexists(p)]
    writable = [p for p in pol["allow_write"] if os.path.lexists(p)]
    if temp_dir and os.path.isdir(temp_dir):
        writable.append(temp_dir)
    process = {"commandLine": _workload_command(command, tool_name), "cwd": workdir,
               "inheritDefaultEnv": True, "timeout": pol.get("timeout_ms", COMMAND_TIMEOUT_MS)}
    if temp_dir:
        process["env"] = ["TEMP=%s" % temp_dir, "TMP=%s" % temp_dir]
    return {
        "version": SCHEMA_VERSION,
        "containment": "processcontainer",
        "lifecycle": {"destroyOnExit": True, "preservePolicy": False},
        "process": process,
        "filesystem": {"readwritePaths": writable,
                       "readonlyPaths": _readonly_roots([workdir, sys.executable, KIT] + writable + denied),
                       "deniedPaths": denied},
        "network": {"egress": {"default": "deny"},
                    "ingress": {"default": "deny", "hostLoopback": "deny"}},
        "ui": {"disable": False},                         # PowerShell/native CLI startup needs Win32k
        "telemetry": {"enabled": False},
        "fallback": {"allowDaclMutation": False},
    }


# ------------------------------------------------------------------ deny-direct domain proxy
def _host_allowed(host: str, domains) -> bool:
    """Exact domains and explicit `*.example.com` patterns only; never suffix-smuggle a hostname."""
    try:
        host = (host or "").strip().rstrip(".").encode("idna").decode("ascii").lower()
    except (UnicodeError, AttributeError):
        return False
    if not host:
        return False
    for raw in domains or []:
        try:
            pattern = str(raw).strip().rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError:
            continue
        if pattern.startswith("*."):
            base = pattern[2:]
            if base and host != base and host.endswith("." + base):
                return True
        elif host == pattern:
            return True
    return False


def _authority(value: str, default_port: int):
    """An HTTP authority → (host, port), including bracketed IPv6."""
    try:
        parsed = urllib.parse.urlsplit("//" + value)
        return parsed.hostname or "", parsed.port or default_port
    except ValueError:
        return "", 0


def _public_endpoints(host: str, port: int):
    """Resolve on the host; approved names never become local-network tunnels through the proxy."""
    try:
        found = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        return []
    public = []
    for family, socktype, proto, _canon, address in found:
        try:
            if ipaddress.ip_address(address[0].split("%", 1)[0]).is_global:
                public.append((family, socktype, proto, address))
        except ValueError:
            continue
    return sorted(public, key=lambda item: item[0] != socket.AF_INET)  # IPv4 first on ordinary Windows hosts


def _relay(left, right):
    """Copy a proxy tunnel in both directions until either side closes."""
    peers = [left, right]
    try:
        while peers:
            ready, _w, _x = select.select(peers, [], peers, 30)
            if not ready:
                break
            for source in ready:
                data = source.recv(65536)
                if not data:
                    return
                (right if source is left else left).sendall(data)
    except (OSError, ValueError):
        return


class _DomainProxyHandler(socketserver.StreamRequestHandler):
    """Small per-command HTTP/S CONNECT proxy. Direct container egress remains denied by MXC."""
    timeout = 30
    rbufsize = 0                                           # do not strand request-body/TLS bytes in a reader buffer

    def _reply(self, code, words):
        body = (words + "\n").encode("utf-8")
        self.wfile.write(("HTTP/1.1 %d %s\r\nConnection: close\r\nContent-Length: %d\r\n\r\n"
                          % (code, words, len(body))).encode("ascii") + body)

    def handle(self):
        first = self.rfile.readline(65537)
        if not first or len(first) > 65536:
            return
        try:
            method, target, version = first.decode("iso-8859-1").strip().split(" ", 2)
        except ValueError:
            self._reply(400, "Bad Request")
            return
        headers, total = [], 0
        while True:
            line = self.rfile.readline(65537)
            total += len(line)
            if not line or line in (b"\r\n", b"\n"):
                break
            if total > 65536:
                self._reply(431, "Headers Too Large")
                return
            headers.append(line)
        method = method.upper()
        if method == "CONNECT":
            host, port = _authority(target, 443)
            origin = None
        else:
            parsed = urllib.parse.urlsplit(target)
            if parsed.scheme not in ("", "http"):
                self._reply(400, "Bad Request")
                return
            host, port = parsed.hostname or "", parsed.port or 80
            if not host:
                host_header = next((h.split(b":", 1)[1].strip().decode("iso-8859-1") for h in headers
                                    if h.lower().startswith(b"host:")), "")
                host, port = _authority(host_header, 80)
                origin = target or "/"
            else:
                origin = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        if port not in (80, 443) or not _host_allowed(host, self.server.domains):
            self._reply(403, "Forbidden")
            return
        endpoints = _public_endpoints(host, port)
        if not endpoints:
            self._reply(502, "Bad Gateway")
            return
        upstream = None
        for family, socktype, proto, address in endpoints:
            candidate = socket.socket(family, socktype, proto)
            candidate.settimeout(15)
            try:
                candidate.connect(address)
                upstream = candidate
                break
            except OSError:
                candidate.close()
        if upstream is None:
            self._reply(502, "Bad Gateway")
            return
        with upstream:
            if method == "CONNECT":
                self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                self.wfile.flush()
            else:
                clean = [h for h in headers if not h.lower().startswith((b"proxy-connection:",
                                                                          b"proxy-authorization:"))]
                upstream.sendall(("%s %s %s\r\n" % (method, origin, version)).encode("iso-8859-1")
                                 + b"".join(clean) + b"\r\n")
            _relay(self.connection, upstream)


class _DomainProxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True

    def __init__(self, domains):
        self.domains = tuple(sorted(set(domains or [])))
        super().__init__(("127.0.0.1", 0), _DomainProxyHandler)


def _with_proxy(request: dict, port: int) -> dict:
    """Select MXC's recommended proxy-only model: no direct internet/private destination is allowed."""
    wire = copy.deepcopy(request)
    wire["processContainer"] = {"capabilities": ["internetClient"]}
    wire["network"] = {"egress": {"default": "deny"},
                       "ingress": {"default": "allow", "hostLoopback": "allow"}}
    wire["runtimeConfig"] = {"networkProxy": "http://127.0.0.1:%d" % port}
    wire.setdefault("process", {}).setdefault("env", []).extend(["NO_PROXY=", "no_proxy="])
    return wire


def _stream_executor(args, timeout=None):
    """Run the real workload with inherited stdio; tests still use the one executor seam."""
    if SPAWN is not None:
        return SPAWN(args=args, env=None, timeout=timeout)
    return subprocess.run(args, timeout=timeout)


def _remove_command_temp(path: str) -> None:
    """Delete only an Orbit-created per-command temp directory, never a sidecar-supplied arbitrary path."""
    if not path:
        return
    candidate = os.path.realpath(path)
    parent = os.path.dirname(candidate)
    runtime = os.path.realpath(os.path.join(engine.HOME, ".runtime"))
    try:
        inside = os.path.normcase(os.path.commonpath([runtime, candidate])) == os.path.normcase(runtime)
    except ValueError:
        inside = False
    if inside and os.path.basename(parent) == "tmp" and os.path.basename(os.path.dirname(parent)) == "mxc":
        shutil.rmtree(candidate, ignore_errors=True)


def run_request(request_file: str, domains_file: str) -> int:
    """Start the per-command allowlist proxy, then run one official MXC request with streaming stdio."""
    command_temp = None
    try:
        with open(request_file, encoding="utf-8") as fh:
            request = json.load(fh)
        with open(domains_file, encoding="utf-8") as fh:
            sidecar = json.load(fh)
        if isinstance(sidecar, list):                       # compatibility with early 0.8.0 request files
            domains = sidecar
        elif isinstance(sidecar, dict):
            domains, command_temp = sidecar.get("domains"), sidecar.get("temp_dir")
        else:
            domains = None
        if not isinstance(domains, list) or not all(isinstance(d, str) for d in domains):
            raise ValueError("invalid approved-domain policy")
        ex = executor_path()
        if not ex:
            raise OSError("wxc-exec.exe is missing; run setup-windows.ps1")
        proxy = _DomainProxy(domains)
        thread = threading.Thread(target=proxy.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        wire_file = None
        try:
            wire = _with_proxy(request, proxy.server_address[1])
            fd, wire_file = tempfile.mkstemp(prefix="mxc-wire-", suffix=".json", dir=os.path.dirname(request_file))
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(wire, fh)
            result = _stream_executor(executor_argv(ex, wire_file), timeout=None)
            return int(getattr(result, "returncode", 1))
        finally:
            proxy.shutdown()
            proxy.server_close()
            thread.join(timeout=2)
            if wire_file:
                try:
                    os.remove(wire_file)
                except OSError:
                    pass
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        sys.stderr.write("Orbit's sandbox could not start: %s\n" % _reason(e))
        return 126
    finally:
        _remove_command_temp(command_temp)


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
    return {"PreToolUse": [{"matcher": "Bash|PowerShell",
                            "hooks": [{"type": "command", "command": sys.executable,
                                       "args": [os.path.join(CORE, "mxc.py"), "--hook"], "timeout": 30}]}]}


def _log_decision(ws: str, rec: dict) -> None:
    """Diagnostics for support (R6.3) and the what-we-generated record (R2.5): <ws>/state/mxc.jsonl."""
    try:
        os.makedirs(os.path.join(ws, "state"), exist_ok=True)
        with open(os.path.join(ws, "state", "mxc.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def request_dir(emp_id: str) -> str:
    """Policy files live outside employee workspaces, so file tools cannot alter them after the hook."""
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "-", emp_id or "unknown")[:80] or "unknown"
    return os.path.join(engine.HOME, ".runtime", safe, "mxc", "requests")


def denials(limit=10) -> list:
    """Recent denials across the crew, in owner words (R6.3): who tried what, and why it was refused.
    Commands run outside the container on purpose (the gateways) don't appear. Empty = nothing denied."""
    out = []
    for f in sorted(glob.glob(os.path.join(engine.HOME, "employees", "*", "state", "mxc.jsonl"))):
        try:
            with open(f, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("decision") == "deny":
                out.append("/%s tried: %s — %s" % (rec.get("employee") or "?", rec.get("command", "?"),
                                                   rec.get("reason") or "the sandbox couldn't start"))
    return out[-limit:]


def support_bundle_paths() -> list:
    """The files support would ask for when something looks wrong (R6.3): the sandbox decision log, the
    generated requests, and the run logs. Only these — never an employee's own work or memory."""
    out = []
    for f in sorted(glob.glob(os.path.join(engine.HOME, "employees", "*", "state", "mxc.jsonl"))):
        out.append(f)
    out.extend(sorted(p for p in glob.glob(os.path.join(engine.HOME, ".runtime", "*", "mxc", "requests"))
                      if os.path.isdir(p)))
    out.extend(sorted(glob.glob(os.path.join(engine.HOME, "employees", "*", "state", "runs.jsonl"))))
    return out


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
    if payload.get("tool_name") == "Bash":
        why = ("native Windows uses Claude's PowerShell tool because Git Bash cannot initialize inside "
               "MXC 1.0; retry this command as PowerShell")
        _log_decision(ws, {**base, "decision": "deny", "reason": why})
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                        "permissionDecisionReason": why}}
    d = discover()
    req_dir = request_dir(emp_id)
    command_temp = None
    if d["ok"]:
        try:
            os.makedirs(req_dir, exist_ok=True)
            temp_root = os.path.join(os.path.dirname(req_dir), "tmp")
            os.makedirs(temp_root, exist_ok=True)
            command_temp = tempfile.mkdtemp(prefix="command-", dir=temp_root)
            policy = _policy(emp)
            req = build_request(policy, cmd, cwd or payload.get("cwd") or ws, payload.get("tool_name"), command_temp)
            domains = policy.get("domains") or []
        except Exception as e:  # noqa: BLE001
            _remove_command_temp(command_temp)
            d = {**d, "ok": False, "reason": "couldn't build the containment request: %s" % _reason(e)}
    if not d["ok"]:
        msg = "Orbit's sandbox couldn't start (%s); the command was denied rather than run unsandboxed." % d["reason"]
        _log_decision(ws, {**base, "decision": "deny", "reason": d["reason"]})
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": _reason(msg)}}
    try:
        os.makedirs(req_dir, exist_ok=True)
        policy_record = {"request": req, "allowed_domains": domains}
        h = hashlib.sha256(json.dumps(policy_record, sort_keys=True).encode("utf-8")).hexdigest()[:12]
        stamp = "%s-%09d-%d" % (time.strftime("%Y%m%d-%H%M%S"), time.time_ns() % 1000000000, os.getpid())
        stem = os.path.join(req_dir, "%s-%s" % (stamp, h))
        path, domains_path = stem + ".json", stem + ".domains.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(req, fh)
        with open(domains_path, "w", encoding="utf-8") as fh:
            json.dump({"domains": domains, "temp_dir": command_temp}, fh)
    except OSError as e:
        _remove_command_temp(command_temp)
        why = "couldn't write the containment request: %s" % _reason(e)
        _log_decision(ws, {**base, "decision": "deny", "reason": why})
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                        "permissionDecisionReason": _reason(why)}}
    contained = '& "%s" "%s" --run "%s" "%s"' % (sys.executable, os.path.join(CORE, "mxc.py"),
                                                       path, domains_path)
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
    tmp = tempfile.mkdtemp(prefix="mxc-probe-")
    builder = builder or (lambda cmd, cwd: build_request(emp, cmd, cwd, temp_dir=tmp))
    base, forged = _probe_reqs(builder)
    unique = "%s-%s" % (os.getpid(), time.time_ns())
    secret_file = os.path.join(tempfile.gettempdir(), "orbit-probe-secret-%s.txt" % unique)
    outside = os.path.join(os.path.expanduser("~"), "orbit-probe-should-fail-%s.tmp" % unique)
    try:
        with open(secret_file, "w", encoding="utf-8") as fh:
            fh.write("pretend credential\n")
    except OSError:
        pass
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
        # positive: write inside scope and read it back
        inside = os.path.join(tmp, "inside.txt")
        pos = subprocess.list2cmdline([sys.executable, "-c",
                                      "import pathlib; print(pathlib.Path(%r).write_text('ok'))" % inside])
        rc, txt, ms = case("probe-pos", base(pos, tmp), pos)
        out["positive"]["write_inside_scope"] = rc == 0
        out["capability_notes"]["startup_ms"] = ms                   # SC6: ~1 s per command budget
        # negative: a normally owner-writable file outside workspace/team/temp must still be refused
        neg = subprocess.list2cmdline([sys.executable, "-c",
                                      "import pathlib; pathlib.Path(%r).write_text('outside')" % outside])
        rc, txt, _ = case("probe-neg-write", base(neg, tmp), neg, timeout=30)
        out["negative"]["outside_write"] = rc != 0 or bool(PROBE_DENY_MARKERS.search(txt))
        # negative: read a file this request's own deny_read covers
        cmd = subprocess.list2cmdline([sys.executable, "-c", "print(open(%r).read())" % secret_file])
        req = forged(cmd, tmp, filesystem={"deniedPaths": [secret_file],
                                           "readonlyPaths": _readonly_roots([sys.executable, secret_file]),
                                           "readwritePaths": [tmp]})
        rc, txt, _ = case("probe-neg-read", req, cmd, timeout=30)
        out["negative"]["secret_read"] = rc != 0 or bool(PROBE_DENY_MARKERS.search(txt))
        # negative: a connect to a host that is not allowlisted (literal address; no DNS needed)
        net = subprocess.list2cmdline([sys.executable, "-c",
                                      "import socket; socket.create_connection(('198.51.100.1',443),3).close()"])
        req = forged(net, tmp, network={"egress": {"default": "deny"},
                                       "ingress": {"default": "deny", "hostLoopback": "deny"}})
        rc, txt, _ = case("probe-neg-net", req, net, timeout=30)
        out["negative"]["non_allowlisted_connect"] = rc != 0 or bool(PROBE_DENY_MARKERS.search(txt))
        # negative: a workload outliving its timeout is terminated (never orphaned)
        slow = subprocess.list2cmdline([sys.executable, "-c", "import time; time.sleep(30)"])
        req = forged(slow, tmp)
        req["process"]["timeout"] = 1500
        rc, txt, ms = case("probe-neg-timeout", req, slow, timeout=45)
        out["negative"]["timeout_termination"] = rc != 0 and ms < 15000
    finally:
        for planted in (secret_file, outside):
            try:
                os.remove(planted)                                   # no probe artifact survives success or failure
            except OSError:
                pass
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


def last_lines(path, limit=60) -> list:
    """A log's last lines anywhere (Windows has no tail; this is the same read everywhere)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()[-limit:]
    except OSError:
        return []


def audit(emp=None) -> str:
    """The executor's own audit report on a tiny test command — `orbit doctor --audit` triage only
    (T042). The executor never gets --audit on a real command (contracts/cc-hook.md)."""
    d = discover()
    if not d["ok"]:
        return "the MXC runtime isn't usable yet: %s" % d["reason"]
    tmp = tempfile.mkdtemp(prefix="mxc-audit-")
    try:
        req_f = os.path.join(tmp, "audit.json")
        with open(req_f, "w", encoding="utf-8") as fh:
            json.dump(build_request(emp or {"id": "audit", "workspace": tmp, "name": "audit"},
                                    "Write-Output audit-ok", tmp, "PowerShell", tmp), fh)
        rc, out, _ = ran([d["executor"], EXECUTOR_FLAG_AUDIT, req_f], timeout=60)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    body = denial_summary(out) if out.strip() else \
        "no audit details printed (exit %s). The runtime runs; ask support with the evidence files." % rc
    return ("The executor's own audit of a test command:\n" + body + "\nEvidence files to share "
            "(logs, not a crew member's work): " + ("\n  ".join(support_bundle_paths()) or "(none yet)"))


# ------------------------------------------------------------------ hook entry point
if __name__ == "__main__":
    if "--hook" in sys.argv:
        sys.exit(hook_main())
    if len(sys.argv) == 4 and sys.argv[1] == "--run":
        sys.exit(run_request(sys.argv[2], sys.argv[3]))
    print(__doc__)
