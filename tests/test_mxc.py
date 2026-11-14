"""The MXC sandbox on native Windows, without MXC: the translation invariants, the hook decisions
and the probe verdicts all run through the executor seam (a stand-in for wxc-exec.exe).
Never records real audio, never launches a real container.  python3 -m unittest tests.test_mxc
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import unittest

TMP = tempfile.mkdtemp(prefix="orbit-mxc-test-")
os.environ["STAFFROOM_HOME"] = TMP
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "core"))
sys.path.insert(0, os.path.join(KIT, "core", "tools"))

import _cleanup  # noqa: E402
import engine  # noqa: E402
import mxc  # noqa: E402
import osinfo  # noqa: E402

_cleanup.home(TMP)                          # now too: named-class loads skip load_tests
_cleanup.on_exit(TMP)


def load_tests(loader, tests, pattern):
    return _cleanup.home_suite(tests, TMP)


def set_kind(kind):
    old, osinfo.KIND = osinfo.KIND, kind
    return old


class StubResult:
    def __init__(self, rc=0, out=""):
        self.returncode, self.stdout, self.stderr = rc, out, ""


FAKE_EXECUTOR = os.path.join("C:" + os.sep, "fake", "wxc-exec.exe")
PROBE_REPORT = json.dumps({"tier": "base-container", "needsDaclAugmentation": False, "probes": {
    "baseContainerApiPresent": True,
    "baseContainerSupportsDenyPaths": True,
    "baseContainerSupportsIdentitylessLoopbackProxy": True,
}})


class Seam(unittest.TestCase):
    """The executor seam itself (T002): exactly one launch path, never --audit on real runs."""

    def test_all_launches_go_through_the_seam(self):
        seen = []
        mxc.set_executor_stub(lambda args, env=None, timeout=None: seen.append(args) or StubResult(0, "rc"))
        try:
            rc, out, _ = mxc.ran(["anything"])
            self.assertEqual(rc, 0)
            self.assertEqual(seen, [["anything"]])
        finally:
            mxc.clear_executor_stub()

    def test_without_a_stub_a_wrong_executor_is_a_failure(self):
        mxc.clear_executor_stub()
        rc, out, _ = mxc.ran(["definitely-not-a-real-executable-xyz"])
        self.assertNotEqual(rc, 0)


class Request(unittest.TestCase):
    """Policy translation (T030) and its invariants (T031), per contracts/mxc-request.md."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(dir=TMP)
        self.emp = {"id": "sara", "workspace": self.ws, "name": "Sara"}
        os.makedirs(os.path.join(engine.HOME, "team"), exist_ok=True)
        self.kind = set_kind("windows")

    def tearDown(self):
        osinfo.KIND = self.kind

    def build(self, cmd="echo hi", emp=None):
        return mxc.build_request(emp or self.emp, cmd, self.ws)

    def test_fail_closed_defaults_hold_by_construction(self):
        r = self.build()
        self.assertEqual(r["version"], "1.0.0")
        self.assertEqual(r["containment"], "processcontainer")
        self.assertEqual(r["network"]["egress"]["default"], "deny")
        self.assertNotIn("allow", r["network"]["egress"])  # domains go through the deny-direct proxy, never CIDR fields
        self.assertTrue(r["filesystem"]["deniedPaths"])
        self.assertIn(os.path.join(engine.HOME, "team"), r["filesystem"]["readwritePaths"])
        self.assertGreater(r["process"]["timeout"], 0)
        self.assertEqual(r["ui"], {"disable": False})       # native shells initialize Win32k even without windows
        self.assertFalse(r["telemetry"]["enabled"])
        self.assertFalse(r["fallback"]["allowDaclMutation"])

    def test_deny_and_allow_are_disjoint(self):
        pol = mxc.compute_policy(self.emp)
        secrets = {os.path.normcase(p) for p in pol["deny_read"]}
        writes = {os.path.normcase(p) for p in pol["allow_write"]}
        self.assertFalse(secrets & writes)              # deny paths and write roots are different trees

    def test_no_silent_loosening_owner_domains_only(self):
        reg = engine.registry()
        reg["network_domains"] = ["example.com"]
        engine.save_registry(reg)
        try:
            allow = mxc.compute_policy(self.emp)["domains"]
            self.assertIn("example.com", allow)             # an owner choice widens it
            self.assertIn("pypi.org", allow)                # the base set is always there
        finally:
            reg["network_domains"] = []
            engine.save_registry(reg)

    def test_deterministic_for_the_same_policy_state(self):
        a = json.dumps(self.build(), sort_keys=True)
        b = json.dumps(self.build(), sort_keys=True)
        self.assertEqual(a, b)                              # R2.5: same state → same request

    def test_deny_read_narrows_to_the_machine_s_native_secrets(self):
        r = self.build()
        # the employee's own workspace is never denied, and the source policy carries native secrets;
        # the wire request omits only paths that do not exist (MXC rejects nonexistent policy paths).
        deny = {os.path.normcase(p) for p in r["filesystem"]["deniedPaths"]}
        self.assertNotIn(os.path.normcase(self.ws), deny)
        policy_deny = {os.path.normcase(p) for p in mxc.compute_policy(self.emp)["deny_read"]}
        self.assertTrue(any(d.endswith(".ssh") for d in policy_deny))       # the native secret root is sourced

    def test_the_agent_command_is_the_stable_schema_process_command(self):
        r = mxc.build_request(self.emp, "echo one && echo two", self.ws, "PowerShell")
        self.assertIn("powershell.exe", r["process"]["commandLine"].lower())
        self.assertIn("echo one && echo two", r["process"]["commandLine"])
        self.assertNotIn("command", r)                         # old Orbit-only pseudo-schema is gone
        self.assertNotIn("timeout_ms", r)

    def test_cache_roundtrip_is_the_same_policy(self):
        mxc.write_policy_cache(self.emp)
        self.assertEqual(mxc.read_policy_cache(self.emp), mxc.compute_policy(self.emp))


class DomainProxy(unittest.TestCase):
    """MXC accepts CIDRs, not durable DNS rules: Orbit's per-command proxy enforces owner domains."""

    def test_exact_and_explicit_wildcard_domains_only(self):
        self.assertTrue(mxc._host_allowed("pypi.org", ["pypi.org"]))
        self.assertFalse(mxc._host_allowed("evilpypi.org", ["pypi.org"]))
        self.assertFalse(mxc._host_allowed("files.pypi.org", ["pypi.org"]))
        self.assertTrue(mxc._host_allowed("files.example.com", ["*.example.com"]))
        self.assertFalse(mxc._host_allowed("example.com", ["*.example.com"]))

    def test_approved_names_still_cannot_rebind_to_the_owners_machine(self):
        original = mxc.socket.getaddrinfo
        mxc.socket.getaddrinfo = lambda *_a, **_k: [(mxc.socket.AF_INET, mxc.socket.SOCK_STREAM, 6, "",
                                                     ("127.0.0.1", 443))]
        try:
            self.assertEqual(mxc._public_endpoints("approved.example", 443), [])
        finally:
            mxc.socket.getaddrinfo = original

    def test_proxy_mode_keeps_direct_egress_denied(self):
        req = {"network": {"egress": {"default": "deny"},
                           "ingress": {"default": "deny", "hostLoopback": "deny"}}}
        wire = mxc._with_proxy(req, 43123)
        self.assertEqual(wire["network"]["egress"], {"default": "deny"})
        self.assertEqual(wire["network"]["ingress"], {"default": "allow", "hostLoopback": "allow"})
        self.assertEqual(wire["processContainer"]["capabilities"], ["internetClient"])
        self.assertEqual(wire["runtimeConfig"]["networkProxy"], "http://127.0.0.1:43123")
        self.assertEqual(wire["process"]["env"], ["NO_PROXY=", "no_proxy="])
        self.assertNotIn("runtimeConfig", req)               # per-command mutation never changes the audit record


class Hook(unittest.TestCase):
    """The PreToolUse decision matrix (T032/T034), per contracts/cc-hook.md."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(dir=TMP)
        self.emp = {"id": "sara", "workspace": self.ws, "name": "Sara"}
        self.kind = set_kind("windows")
        self.pat = mxc._gateway_patterns
        mxc._gateway_patterns = lambda eid: ["staff-fetch *"]
        self.exPath = mxc.executor_path
        mxc.executor_path = lambda: FAKE_EXECUTOR
        self.pin = mxc.version_pinned
        mxc.version_pinned = lambda: ""
        self.env = {k: os.environ.pop(k) for k in ("STAFF_EMPLOYEE",) if k in os.environ}
        mxc.set_executor_stub(lambda args, env=None, timeout=None: StubResult(0, PROBE_REPORT))

    def tearDown(self):
        mxc._gateway_patterns, mxc.executor_path, mxc.version_pinned = self.pat, self.exPath, self.pin
        mxc.clear_executor_stub()
        os.environ.update(self.env)
        osinfo.KIND = self.kind

    def hook(self, cmd="Write-Output hi", tool="PowerShell"):
        return mxc.decision({"tool_name": tool, "tool_input": {"command": cmd}, "cwd": self.ws})

    def test_an_excluded_command_passes_through_unwrapped(self):
        self.assertEqual(self.hook("staff-fetch --url x", "Bash"), {})

    def test_a_contained_command_is_allowed_with_the_rewritten_input(self):
        r = self.hook("Write-Output hi")
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"], "allow")
        contained = r["hookSpecificOutput"]["updatedInput"]["command"]
        self.assertIn("mxc.py", contained)
        self.assertIn("--run", contained)                   # helper owns the short-lived domain proxy + executor
        self.assertTrue(contained.startswith('& "'))        # PowerShell invokes a quoted Python path with call operator
        quoted = re.findall(r'"([^"]+)"', contained)
        req_f, domains_f = quoted[-2:]
        with open(req_f, encoding="utf-8") as fh:
            req = json.load(fh)
        self.assertEqual(req["network"]["egress"]["default"], "deny")
        self.assertIn("Write-Output hi", req["process"]["commandLine"])  # agent-flow neutrality: command is inside
        with open(domains_f, encoding="utf-8") as fh:
            sidecar = json.load(fh)
        self.assertIn("pypi.org", sidecar["domains"])        # approved domains are enforced by the host proxy
        self.assertIn(sidecar["temp_dir"], req["filesystem"]["readwritePaths"])  # one command, one temp grant
        self.assertIn("TEMP=" + sidecar["temp_dir"], req["process"]["env"])
        mxc._remove_command_temp(sidecar["temp_dir"])

    def test_git_bash_is_denied_with_a_powershell_retry_not_run_on_the_host(self):
        r = self.hook("echo hi", "Bash")
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("retry this command as PowerShell", r["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNone(r["hookSpecificOutput"].get("updatedInput"))

    def test_missing_executor_denies_rather_than_running_unsandboxed(self):
        mxc.executor_path = lambda: None
        saved_stub = mxc.SPAWN
        mxc.clear_executor_stub()
        mxc.set_executor_stub(lambda args, env=None, timeout=None: StubResult(1, ""))
        try:
            r = self.hook("echo hi")
        finally:
            mxc.set_executor_stub(saved_stub)
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertTrue(r["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(r["hookSpecificOutput"].get("updatedInput"), None)

    def test_the_decision_log_records_what_was_generated(self):
        self.hook("echo hi")
        with open(os.path.join(self.ws, "state", "mxc.jsonl"), encoding="utf-8") as fh:
            rec = json.loads(fh.read().splitlines()[-1])
        self.assertEqual(rec["decision"], "allow")
        self.assertTrue(rec["request_hash"])                # R2.5: what Orbit generated, logged

    def test_an_empty_or_nonshell_payload_decides_nothing(self):
        self.assertEqual(mxc.decision({}), {})
        self.assertEqual(mxc.decision({"tool_name": "Bash", "tool_input": {}}), {})
        self.assertEqual(mxc.decision({"tool_name": "Bash", "tool_input": {"command": "  "}}), {})

    def test_hook_payload_tolerates_junk_input(self):
        class FakeStdin:
            def read(self):
                return "not json at all"
        real_in, sys.stdin = sys.stdin, FakeStdin()
        try:
            self.assertEqual(mxc.hook_payload(), {})
        finally:
            sys.stdin = real_in


class Probe(unittest.TestCase):
    """The probe verdict matrix (T040/T043): positives pass, each negative failure is one verdict."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(dir=TMP)
        self.emp = {"id": "sara", "workspace": self.ws, "name": "Sara"}
        self.kind = set_kind("windows")
        self.exPath = mxc.executor_path
        mxc.executor_path = lambda: FAKE_EXECUTOR

    def tearDown(self):
        mxc.executor_path = self.exPath
        osinfo.KIND = self.kind

    def _probe(self, stub):
        mxc.set_executor_stub(stub)
        try:
            return mxc.probe(self.emp)
        finally:
            mxc.clear_executor_stub()

    def _simulating_stub(self, cfg=None):
        """A stand-in for wxc-exec.exe that simulates containment per probe case: each case file
        records what a real container would decide for it (allow work, refuse every violation)."""
        decisions = {
            "probe-pos": (0, "ok\n"),
            "probe-neg-write": (1, "denied: outside the writable set"),
            "probe-neg-read": (1, "denied: reading a denied path"),
            "probe-neg-net": (1, "blocked: egress denied"),
            "probe-neg-timeout": (1, "terminated: outlived the timeout"),
        }

        def stub(args, env=None, timeout=None):
            if args[-1] == "--probe":
                return StubResult(0, PROBE_REPORT)
            name = os.path.splitext(os.path.basename(args[-1]))[0]
            return StubResult(*decisions[name])
        return stub

    def test_everything_holding_verdicts_usable(self):
        r = self._probe(self._simulating_stub())
        self.assertEqual(r["verdict"], "usable", r)
        self.assertTrue(all(r["negative"].values()), r["negative"])
        self.assertTrue(r["positive"]["write_inside_scope"])
        self.assertIsInstance(r["capability_notes"]["startup_ms"], int)   # SC6: the budget is measured

    def test_a_secret_read_that_leaks_verdicts_unusable(self):
        def stub(args, env=None, timeout=None):
            if args[-1] == "--probe":
                return StubResult(0, PROBE_REPORT)
            name = os.path.splitext(os.path.basename(args[-1]))[0]
            if name == "probe-pos":
                return StubResult(0, "ok\n")
            if name == "probe-neg-read":
                return StubResult(0, "pretend credential\n")   # the leak: the read succeeded
            return StubResult(1, "denied")
        r = self._probe(stub)
        self.assertEqual(r["verdict"], "unusable-with-reason")
        self.assertIn("secret_read", r["capability_notes"]["failed"])

    def test_discovery_failure_is_unusable_with_reason(self):
        mxc.executor_path = lambda: None
        r = self._probe(lambda args, env=None, timeout=None: StubResult(1, ""))
        self.assertEqual(r["verdict"], "unusable-with-reason")
        self.assertIn("missing", r["capability_notes"]["discovery"])

    def test_the_summary_names_what_failed_in_owner_language(self):
        r = {"verdict": "unusable-with-reason", "positive": {"write_inside_scope": True},
             "negative": {"outside_write": True, "secret_read": False},
             "capability_notes": {"failed": "secret_read"}}
        self.assertIn("secret_read", mxc.probe_summary(r))
        r["verdict"] = "usable"
        self.assertIn("proved both directions", mxc.probe_summary(r))


class Audit(unittest.TestCase):
    """orbit doctor --audit (T042/US6): the executor's own report on a tiny command — triage only,
    and the audit flag never touches a real contained command."""

    def setUp(self):
        self.kind = set_kind("windows")
        self.exPath = mxc.executor_path
        self.pin = mxc.version_pinned
        mxc.executor_path = lambda: FAKE_EXECUTOR
        mxc.version_pinned = lambda: ""

    def tearDown(self):
        mxc.clear_executor_stub()
        mxc.executor_path, mxc.version_pinned = self.exPath, self.pin
        osinfo.KIND = self.kind

    def test_the_audit_probe_runs_through_the_seam_and_reports_in_owner_words(self):
        seen = []
        def stub(args, env=None, timeout=None):
            seen.append(args)
            return StubResult(0, PROBE_REPORT) if args[-1] == "--probe" else \
                StubResult(1, "violation: reading a denied path")
        mxc.set_executor_stub(stub)
        text = mxc.audit()
        self.assertTrue(any(s and s[1] == mxc.EXECUTOR_FLAG_AUDIT for s in seen), seen)   # the triage mode
        self.assertNotIn(mxc.EXECUTOR_FLAG_AUDIT,               # and never on a real contained command
                         mxc.executor_argv(mxc.EXECUTOR, "req.json", "echo hi"))
        self.assertIn("The executor's own audit", text)
        self.assertIn("reading a denied path", text)            # T035's owner-language rendering

    def test_without_a_runtime_the_audit_names_the_prerequisite(self):
        mxc.executor_path = lambda: None
        text = mxc.audit()
        self.assertIn("runtime isn't usable", text)
        self.assertIn("setup-windows.ps1", text)                # the fix, not a stack trace (SC5)


class Registry(unittest.TestCase):
    """The PlatformMode store as data (T071/A1): the four fields set exactly, unrelated registry keys
    untouched, and the store reloads in both modes (kind is a per-call switch)."""

    def setUp(self):
        self.kind = set_kind("windows")
        reg = engine.registry()
        self.before = json.loads(json.dumps(reg))            # a deep snapshot: neighbors must survive
        reg["owner"] = {"name": "Test Owner"}                # an unrelated key, on purpose
        reg["employees"] = {}
        engine.save_registry(reg)

    def tearDown(self):
        engine.save_registry(self.before)
        osinfo.KIND = self.kind

    def test_set_mode_writes_exactly_the_four_fields(self):
        mxc.set_mode("wsl2", decided_by="owner")
        reg = engine.registry()
        self.assertEqual(set(reg["platform"]),
                         {"sandbox_mode", "decided_by", "decided_at", "mxc_unavailable_reason"})
        self.assertEqual(reg["platform"]["sandbox_mode"], "wsl2")
        self.assertEqual(reg["platform"]["decided_by"], "owner")
        self.assertTrue(reg["platform"]["decided_at"])       # timestamped (A1)
        self.assertIsNone(reg["platform"]["mxc_unavailable_reason"])   # no reason: an owner choice
        self.assertEqual(reg["owner"], {"name": "Test Owner"})         # nothing else moved
        self.assertEqual(reg.get("network_domains"), self.before.get("network_domains"))

    def test_record_unavailable_puts_the_reason_where_a_reload_finds_it(self):
        mxc.record_unavailable("the sandbox proof failed: outside_write realized a stray write")
        reg = engine.registry()
        self.assertEqual(reg["platform"]["decided_by"], "unavailable")
        info = mxc.mode_info()                               # reloaded from disk
        self.assertEqual(info["sandbox_mode"], "wsl2")
        self.assertEqual(info["decided_by"], "unavailable")
        self.assertIn("proof failed", mxc.unavailable_reason())

    def test_an_owner_switch_back_clears_the_unavailability_story(self):
        mxc.record_unavailable("runtime missing")
        osinfo.KIND = "windows"                              # KIND switches per call in mxc.py
        mxc.set_mode("mxc", decided_by="owner")
        self.assertEqual(mxc.unavailable_reason(), "")       # repaired: the old reason stops guiding
        self.assertEqual(mxc.mode_info()["decided_by"], "owner")

    def test_an_unknown_mode_or_maker_is_refused(self):
        with self.assertRaises(ValueError):
            mxc.set_mode("bubblewrap")                       # not a mode
        with self.assertRaises(ValueError):
            mxc.set_mode("wsl2", decided_by="wizard")        # not a decision maker (R4.1)
        with self.assertRaises(ValueError):
            mxc.set_mode("wsl2", decided_by="unavailable")   # a machine decision needs its reason


class Support(unittest.TestCase):
    """Denial surfacing for support (T035/R6.3): owner words in orbit logs; a bundle of evidence paths.
    The files are planted where the kit itself looks (engine.HOME), so this works in any test process."""

    def plant(self, eid="sara") -> str:
        ws = os.path.join(engine.HOME, "employees", eid, "state")
        os.makedirs(ws, exist_ok=True)
        return ws

    def test_refusals_come_out_in_owner_words_without_pass_throughs(self):
        ws = self.plant()
        with open(os.path.join(ws, "mxc.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"decision": "pass-through", "employee": "sara", "command": "staff-fetch x"}) + "\n")
            fh.write(json.dumps({"decision": "allow", "employee": "sara", "command": "echo hi",
                                 "request_hash": "abc"}) + "\n")
            fh.write(json.dumps({"decision": "deny", "employee": "sara", "command": "cat .netrc",
                                 "reason": "reading a denied path"}) + "\n")
        rows = mxc.denials()
        self.assertEqual(len(rows), 1, rows)
        self.assertIn("sara", rows[0])
        self.assertIn("cat .netrc", rows[0])
        self.assertIn("reading a denied path", rows[0])

    def test_the_bundle_is_evidence_files_not_private_work(self):
        ws = self.plant()
        os.makedirs(mxc.request_dir("sara"), exist_ok=True)
        paths = mxc.support_bundle_paths()
        text = " | ".join(paths)
        self.assertIn("mxc.jsonl", text)
        self.assertIn("requests", text)
        self.assertFalse(any(p.endswith("CLAUDE.md") or "employees/sara/plan" in os.path.normcase(p)
                             for p in paths))                     # never the work itself (R6.3)


if __name__ == "__main__":
    unittest.main()
