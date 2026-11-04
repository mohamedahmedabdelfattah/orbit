"""The MXC sandbox on native Windows, without MXC: the translation invariants, the hook decisions
and the probe verdicts all run through the executor seam (a stand-in for wxc-exec.exe).
Never records real audio, never launches a real container.  python3 -m unittest tests.test_mxc
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

TMP = tempfile.mkdtemp(prefix="orbit-mxc-test-")
os.environ["STAFFROOM_HOME"] = TMP
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "core"))
sys.path.insert(0, os.path.join(KIT, "core", "tools"))

import engine  # noqa: E402
import mxc  # noqa: E402
import osinfo  # noqa: E402


def set_kind(kind):
    old, osinfo.KIND = osinfo.KIND, kind
    return old


class StubResult:
    def __init__(self, rc=0, out=""):
        self.returncode, self.stdout, self.stderr = rc, out, ""


FAKE_EXECUTOR = os.path.join("C:" + os.sep, "fake", "wxc-exec.exe")


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
        self.kind = set_kind("windows")

    def tearDown(self):
        osinfo.KIND = self.kind

    def build(self, cmd="echo hi", emp=None):
        return mxc.build_request(emp or self.emp, cmd, self.ws)

    def test_fail_closed_defaults_hold_by_construction(self):
        r = self.build()
        self.assertEqual(r["network"]["egress"]["default"], "deny")
        self.assertIn("pypi.org", r["network"]["egress"]["allow"])
        self.assertTrue(r["filesystem"]["deny_read"])
        self.assertIn(os.path.join(engine.HOME, "team"), r["filesystem"]["allow_write"])
        self.assertGreater(r["timeout_ms"], 0)

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
            allow = self.build()["network"]["egress"]["allow"]
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
        # the employee's own workspace is never in deny_read, and the native secret set is
        deny = {os.path.normcase(p) for p in r["filesystem"]["deny_read"]}
        self.assertNotIn(os.path.normcase(self.ws), deny)
        self.assertTrue(any(d.endswith(".ssh") for d in deny))              # the native secret root is there

    def test_cache_roundtrip_is_the_same_policy(self):
        mxc.write_policy_cache(self.emp)
        self.assertEqual(mxc.read_policy_cache(self.emp), mxc.compute_policy(self.emp))


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
        mxc.set_executor_stub(lambda args, env=None, timeout=None: StubResult(0, "schema v1.0.0"))

    def tearDown(self):
        mxc._gateway_patterns, mxc.executor_path, mxc.version_pinned = self.pat, self.exPath, self.pin
        mxc.clear_executor_stub()
        os.environ.update(self.env)
        osinfo.KIND = self.kind

    def hook(self, cmd="echo hi"):
        return mxc.decision({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": self.ws})

    def test_an_excluded_command_passes_through_unwrapped(self):
        self.assertEqual(self.hook("staff-fetch --url x"), {})

    def test_a_contained_command_is_allowed_with_the_rewritten_input(self):
        r = self.hook("echo hi")
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"], "allow")
        contained = r["hookSpecificOutput"]["updatedInput"]["command"]
        self.assertIn("wxc-exec", contained)
        self.assertIn("echo hi", contained)                 # the agent's own command, inside the boundary
        tokens = contained.split(" ")
        req_f = tokens[1]                                   # executor, request path, then the command
        with open(req_f, encoding="utf-8") as fh:
            req = json.load(fh)
        self.assertEqual(req["network"]["egress"]["default"], "deny")
        self.assertEqual(req["command"], "echo hi")         # agent-flow neutrality: nothing Orbit-added

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
            if args[-1] == "--debug":
                return StubResult(0, "schema v1.0.0\n")
            name = os.path.splitext(os.path.basename(args[-2]))[0]
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
            if args[-1] == "--debug":
                return StubResult(0, "schema v1.0.0\n")
            cmd = args[-1]
            if "inside.txt" in cmd and "orbit-probe-secret" not in cmd:
                return StubResult(0, "ok\n")
            if "orbit-probe-secret" in cmd:
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


if __name__ == "__main__":
    unittest.main()
