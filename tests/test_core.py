"""Core tests: abilities, hiring, orders, the engine's command line, the control panel's locks.
Runs against a throwaway team folder; never calls Claude.  python3 -m unittest tests.test_core
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import subprocess
import threading
import time
import unittest
import urllib.error
import urllib.request

TMP = tempfile.mkdtemp(prefix="staffroom-test-")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cleanup  # noqa: E402
_cleanup.on_exit(TMP)                      # nothing left behind: temp folders, transcripts
os.environ["STAFFROOM_HOME"] = TMP
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "core"))
sys.path.insert(0, os.path.join(KIT, "core", "tools"))
sys.path.insert(0, os.path.join(KIT, "tests"))

import abilities  # noqa: E402
import engine  # noqa: E402
import fake_claude  # noqa: E402
import hire  # noqa: E402
import orders  # noqa: E402
import osinfo  # noqa: E402
import team  # noqa: E402

RUNS = []                                  # employee runs the code asked for; tests never start Claude
team.run_async = lambda *a, **k: RUNS.append((a, k))


def fresh_team():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(os.path.join(TMP, "team"))
    engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex", "aliases": ["B"]}}, "employees": {},
                          "defaults": {"model": "sonnet"}, "panel": {"port": 7398}})


class Abilities(unittest.TestCase):
    def setUp(self):
        fresh_team()

    def test_presets(self):
        cat = abilities.by_id()
        default, sup = set(abilities.preset("default")), set(abilities.preset("super"))
        self.assertTrue(default < sup)
        self.assertNotIn("apify", default)                      # paid: never on by default
        self.assertEqual(sup, {k for k, a in cat.items() if not a.get("locked") and not a.get("consent")})   # consent: only its own switch
        self.assertTrue(all(cat[k].get("default") for k in default))

    def test_validate_drops_locked_and_unknown(self):
        self.assertEqual(abilities.validate(["memory", "web", "bogus", "apify"]), ["apify", "web"])

    def test_tools_and_gateways_follow_ticks(self):
        hire.hire("Tess", "Research", supervisor="Alex", picked=["web", "fetch"])
        allow, block = abilities.tools("tess")
        self.assertIn("WebSearch", allow)
        self.assertIn("Bash(staff-apify *)", block)
        self.assertIn("Bash(staff-browse *)", block)
        self.assertEqual(abilities.commands("tess"), ["staff-connectors", "staff-fetch", "staff-video"])   # web research: videos, connectors
        self.assertIn("research-playbook", abilities.skills("tess"))
        self.assertNotIn("social-media", abilities.skills("tess"))
        self.assertTrue(abilities.has("tess", "safety"))        # locked: always on


class Hiring(unittest.TestCase):
    def setUp(self):
        fresh_team()

    def test_hire_creates_a_folder_from_templates(self):
        h = hire.hire("Sara Ali", "Market researcher", "Competitors", supervisor="b")
        self.assertEqual(h, "sara-ali")
        ws = os.path.join(TMP, "employees", h)
        for f in ("CLAUDE.md", "STATE.md", "TASKS.md", "LESSONS.md", "GOALS.md", "profile.json", "evals/cases.md"):
            self.assertTrue(os.path.exists(os.path.join(ws, f)), f)
        with open(os.path.join(ws, "CLAUDE.md")) as fh:
            text = fh.read()
        self.assertIn("Sara Ali", text)
        self.assertIn(engine.KIT + "/core/handbook.md", text)
        self.assertNotIn("{", text)
        e = engine.registry()["employees"][h]
        self.assertEqual(e["supervisor"], "Alex")                # alias resolved to the owner
        self.assertEqual(sorted(e["abilities"]), sorted(abilities.preset("default")))
        with open(os.path.join(TMP, "team", "DIRECTORY.md")) as fh:
            self.assertIn("sara-ali", fh.read())

    def test_hire_refuses_bad_input(self):
        with self.assertRaises(hire.HireError):
            hire.hire("Sara", "Role", supervisor="Stranger")
        with self.assertRaises(hire.HireError):
            hire.hire("سارة", "Role", supervisor="Alex")           # needs a Latin handle
        self.assertEqual(hire.hire("سارة", "Role", supervisor="Alex", emp_id="sara"), "sara")
        with self.assertRaises(hire.HireError):
            hire.hire("Sara", "Role", supervisor="Alex")           # already works here
        with self.assertRaises(hire.HireError):
            hire.hire("Team", "Role", supervisor="Alex")           # reserved handle

    def test_status_and_fields(self):
        hire.hire("Tess", "Research", supervisor="Alex")
        hire.set_status("tess", "paused")
        self.assertNotIn("tess", team.active())
        hire.set_status("tess", "active")
        hire.set_field("tess", "model", "haiku")
        self.assertEqual(engine.employee("tess")["model"], "haiku")
        with self.assertRaises(hire.HireError):
            hire.set_field("tess", "model", "gpt-5")
        with self.assertRaises(hire.HireError):
            hire.set_field("tess", "network_domains", ["*"])     # not owner-editable from orders


class Orders(unittest.TestCase):
    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")

    def test_super_agent_and_back(self):
        out = orders.execute("Alex", "set_abilities", {"employee_id": "tess", "preset": "super"})
        self.assertIn("(super agent)", out)
        self.assertIn("+Apify scrapers", out)
        self.assertEqual(abilities.effective("tess"), {k for k, a in abilities.by_id().items() if not a.get("consent")})
        out = orders.execute("Alex", "set_abilities", {"employee_id": "tess", "preset": "default"})
        self.assertIn("−Apify scrapers", out)
        rows = team.tail(team.ORDERS)
        self.assertEqual([r["status"] for r in rows], ["done", "done"])

    def test_bad_orders_are_logged_and_refused(self):
        with self.assertRaises(orders.OrderError):
            orders.execute("Alex", "pause", {"employee_id": "nobody"})
        with self.assertRaises(orders.OrderError):
            orders.execute("Alex", "run_job", {"employee_id": "tess", "job": "rm -rf"})
        with self.assertRaises(orders.OrderError):
            orders.execute("Alex", "delete_everything", {})
        self.assertEqual(team.tail(team.ORDERS)[-1]["status"], "failed")

    def test_hire_from_the_panel(self):
        out = orders.execute("Alex", "hire", {"name": "Omar", "role": "Social media", "scope": "x", "preset": "super"})
        self.assertIn("/omar", out)
        self.assertEqual(abilities.effective("omar"), {k for k, a in abilities.by_id().items() if not a.get("consent")})


class Engine(unittest.TestCase):
    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex", picked=["web", "fetch", "browser"], domains=["api.example.com"])
        hire.hire("Omar", "Social", supervisor="Alex")

    def test_command_line(self):
        emp = engine.employee("tess")
        cmd = engine.command(emp, "sonnet")
        s = json.loads(cmd[cmd.index("--settings") + 1])
        self.assertFalse(engine.sandboxed())                               # the 0.13 team sandbox is off by default
        if osinfo.KIND == "windows" and engine.recorded_sandbox_mode() == "mxc":
            self.assertTrue(s["sandbox"]["enabled"])                     # native MXC containment remains mandatory
            self.assertTrue(s.get("hooks", {}).get("PreToolUse"))
        else:
            self.assertEqual(s["sandbox"], {"enabled": False})
        self.assertNotIn("--chrome", cmd)                                 # the owner's own Chrome is never theirs
        reg = engine.registry()
        reg["sandbox"] = True
        engine.save_registry(reg)
        cmd = engine.command(emp, "sonnet")
        s = json.loads(cmd[cmd.index("--settings") + 1])
        sb = s["sandbox"]
        self.assertTrue(sb["enabled"] and not sb["allowUnsandboxedCommands"])
        if osinfo.KIND == "windows":                       # MXC is the boundary: its PreToolUse hook, not the built-in sandbox
            self.assertNotIn("failIfUnavailable", sb)
            self.assertTrue(s.get("hooks", {}).get("PreToolUse"))
        else:
            self.assertTrue(sb["failIfUnavailable"])
        self.assertTrue(sb["network"]["strictAllowlist"])
        self.assertIn("api.example.com", sb["network"]["allowedDomains"])
        self.assertEqual(sorted(sb["excludedCommands"]), ["staff-browse *", "staff-connectors *", "staff-fetch *", "staff-video *"])
        self.assertIn(os.path.join(TMP, "employees", "omar"), sb["filesystem"]["denyRead"])   # colleagues' folders
        self.assertIn(engine.SECRETS, sb["filesystem"]["denyRead"])
        self.assertIn("--strict-mcp-config", cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "user,project")   # pass-through mode: the owner's user+project sources
        dirs = [cmd[i + 1] for i, x in enumerate(cmd) if x == "--plugin-dir"]
        self.assertEqual(dirs[0], engine.GUARD)
        self.assertTrue(dirs[1].startswith(os.path.join(TMP, ".runtime", "tess")))
        denied = cmd[cmd.index("--disallowedTools") + 1:]
        self.assertIn("Bash(staff-apify *)", denied)
        self.assertIn("Bash(git push *)", denied)
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "dontAsk")
        win = engine.command(emp, "opus", interactive=True)                 # the owner's own window: no -p, asks
        self.assertNotIn("-p", win)
        self.assertNotIn("--output-format", win)
        self.assertEqual(win[win.index("--permission-mode") + 1], "default")
        self.assertEqual(win[win.index("--settings") + 1], cmd[cmd.index("--settings") + 1])   # same locks


SENTINEL_ENV = {"CLAUDECODE": "1", "ANTHROPIC_BASE_URL": "http://inherited:4000",
                "ANTHROPIC_API_KEY": "sk-inherited-not-orbits", "FUTURE_PROVIDER_TOKEN": "sentinel-future"}

# The .bat shim cannot carry the real employee argv through cmd.exe's quote reparse; these
# run-through-engine tests are CI coverage for the macOS, Linux and WSL2 jobs.
POSIX_FAKE_RUN = unittest.skipIf(
    osinfo.KIND == "windows",
    "fake .bat shim vs. cmd.exe quoting: the full run matrix runs in the CI POSIX jobs")


class ProviderNeutralRun(unittest.TestCase):
    """T017 (FR-013, FR-014, FR-016, SC-003): ordinary work never probes or waits for
    `api.anthropic.com` before invoking Claude, starts the fake immediately, keeps only the
    resume/new-session safeguards, and never routes work anywhere else."""

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex", picked=["fetch"])
        self.real = engine.resolve_claude

    def tearDown(self):
        engine.resolve_claude = self.real

    def fake(self, **cfg):
        self.dir = _cleanup.temp("fake-claude-")
        engine.resolve_claude = lambda: fake_claude.install(self.dir, **cfg)

    @POSIX_FAKE_RUN
    def test_no_api_probe_and_no_wait_before_work(self):
        import socket
        import time
        self.fake(prompt={"result": "Done."})
        probes = []
        real_conn = socket.create_connection
        socket.create_connection = lambda *a, **k: probes.append(a) or (_ for _ in ()).throw(
            OSError("socket access blocked"))
        try:
            t0 = time.time()
            out = engine.run(engine.employee("tess"), "Write the brief.")
            elapsed = time.time() - t0
        finally:
            socket.create_connection = real_conn
        self.assertTrue(out["ok"], out)
        self.assertEqual(probes, [])                       # no reachability probe of the provider endpoint
        self.assertFalse(hasattr(engine, "online"))        # the process-wide reachability gate is gone
        self.assertFalse(hasattr(engine, "wait_online"))
        self.assertLess(elapsed, 60)
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 1)                     # Claude started immediately, exactly once
        self.assertEqual(out["model"], "sonnet")           # the same provider/model Orbit chose

    @POSIX_FAKE_RUN
    def test_resume_then_new_session_retry_is_unchanged(self):
        self.fake(prompt={"result": "first"})
        emp = engine.employee("tess")
        out = engine.run(emp, "one", session_key="room:1")
        self.assertTrue(out["ok"], out)
        fake_claude.configure(self.dir, prompt={"result": "second", "fail_resume": "resume unavailable"})
        out2 = engine.run(emp, "two", session_key="room:1")
        self.assertTrue(out2["ok"], out2)
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 3)
        self.assertIn("--resume", recs[1]["argv"])         # the saved session was tried first...
        self.assertTrue("--session-id" in recs[2]["argv"]) # ...and a fresh session followed, same provider
        sid = recs[2]["argv"][recs[2]["argv"].index("--session-id") + 1]
        with open(os.path.join(emp["workspace"], "state", "sessions.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["room:1"], sid)


class Diagnostics(unittest.TestCase):
    """T018 (FR-015, FR-016, FR-020, SC-009): every real Claude failure class keeps its own process
    result and classification while owner-facing wording stays provider-neutral — no generic
    account-login prescription, no guessed provider details."""

    CASES = {
        "rate-limit": "Claude AI usage limit reached. Please try again later.",
        "authentication": "OAuth token has expired; please log in again.",
        "connection": "connection refused while contacting the API",
        "network": "getaddrinfo ENOTFOUND api.anthropic.com",
        "provider": "API Error 500: upstream provider failed",
        "unknown": "kaboom",
    }

    def test_owner_wording_is_provider_neutral_for_every_failure_class(self):
        for name, err in self.CASES.items():
            for text in (engine.friendly_error(err), engine.why_failed(err)):
                low = text.lower()
                for banned in ("auth login", "log in", "login", "sign in", "anthropic", "api key",
                               "subscription", "api.anthropic.com"):
                    self.assertNotIn(banned, low, "%s wording: %r" % (name, text))
                self.assertTrue(text.strip(), name)

    def test_failure_classes_keep_their_distinct_plain_reason(self):
        self.assertIn("usage limit", engine.friendly_error(self.CASES["rate-limit"]))
        self.assertIn("usage limit", engine.why_failed(self.CASES["rate-limit"]))
        self.assertIn("authenticate", engine.friendly_error(self.CASES["authentication"]).lower())
        self.assertIn("authenticate", engine.why_failed(self.CASES["authentication"]).lower())
        self.assertIn("reach claude", engine.friendly_error(self.CASES["network"]).lower())
        self.assertIn("offline", engine.why_failed(self.CASES["network"]).lower())
        self.assertIn("asleep", engine.friendly_error(self.CASES["connection"]).lower())
        self.assertIn("ran out of time", engine.why_failed("request timed out"))


class DiagnosticProvenance(unittest.TestCase):
    """T018 run-level: the fake's actual error text survives into the run result untouched, the
    transient classification keeps driving retries, and no inherited sentinel is copied into any
    Orbit-persisted record — even on the failure path (FR-015, FR-020)."""

    BAN = ("sentinel-future", "sk-inherited-not-orbits", "http://inherited:4000", "CLAUDECODE")

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.real = engine.resolve_claude
        self.saved = {k: os.environ.get(k) for k in SENTINEL_ENV}
        os.environ.update(SENTINEL_ENV)

    def tearDown(self):
        engine.resolve_claude = self.real
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def fake(self, **cfg):
        self.dir = _cleanup.temp("fake-claude-")
        engine.resolve_claude = lambda: fake_claude.install(self.dir, **cfg)

    @POSIX_FAKE_RUN
    def test_actual_result_and_transient_classification_are_preserved(self):
        emp = engine.employee("tess")
        for err, transient in (("getaddrinfo ENOTFOUND", True),
                               ("Claude AI usage limit reached", True),
                               ("OAuth token has expired", False),
                               ("API Error 500: upstream provider failed", False),
                               ("kaboom", False)):
            self.fake(prompt={"error": err})
            out = engine.run(emp, "Do it.")
            self.assertFalse(out["ok"], err)
            self.assertEqual(out["error"], err)            # the process result is the source of truth
            self.assertEqual(out["transient"], transient, err)
            self.assertEqual(len(fake_claude.calls(self.dir)), 1)   # one provider, no fallback routing

    @POSIX_FAKE_RUN
    def test_failed_run_persists_no_inherited_sentinel(self):
        self.fake(prompt={"error": "ENOTFOUND api.anthropic.com"})
        emp = engine.employee("tess")
        out = engine.run(emp, "Do it.")
        self.assertFalse(out["ok"])
        rec = json.loads(open(os.path.join(emp["workspace"], "state", "runs.jsonl"),
                              encoding="utf-8").read().strip().splitlines()[-1])
        self.assertEqual(rec["error"], "ENOTFOUND api.anthropic.com")   # Claude's own text, unchanged
        self.assertNotIn("env", rec)
        for root, _, files in os.walk(engine.HOME):
            for f in files:
                p = os.path.join(root, f)
                with open(p, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                for b in self.BAN:
                    self.assertNotIn(b, text, "leaked into %s" % p)


class LaunchPolicy(unittest.TestCase):
    """The ordinary pass-through versus legacy stored-key seam (T002; FR-005, FR-007, FR-012).
    Ordinary mode starts from the whole inherited environment, removes only CLAUDECODE, applies
    exactly the enumerated Orbit-owned overrides, and preserves arbitrary unknown sentinels.
    Legacy mode strips conflicting routing/auth values, injects only the stored Orbit key for
    inference, and keeps the isolated employee/onboarding setting sources."""
    SENTINELS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "FUTURE_PROVIDER_TOKEN")

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.saved = {k: os.environ.get(k) for k in self.SENTINELS}
        os.environ["CLAUDECODE"] = "1"
        os.environ["ANTHROPIC_BASE_URL"] = "http://inherited:4000"
        os.environ["ANTHROPIC_API_KEY"] = "sk-inherited-not-orbits"
        os.environ["FUTURE_PROVIDER_TOKEN"] = "sentinel-future"

    def tearDown(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        os.environ.pop("CLAUDECODE", None)

    def legacy(self):
        reg = engine.registry()
        reg["auth"] = "api_key"
        engine.save_registry(reg)
        engine.save_secret("anthropic_api_key", "sk-stored-orbit")

    def test_ordinary_employee_passes_through(self):
        pol = engine.launch_policy("employee", engine.employee("tess"))
        self.assertEqual(pol["mode"], "ordinary")
        self.assertEqual(pol["setting_sources"], "user,project")
        self.assertNotIn("CLAUDECODE", pol["env"])
        self.assertEqual(pol["env"]["ANTHROPIC_BASE_URL"], "http://inherited:4000")      # the connection, preserved
        self.assertEqual(pol["env"]["ANTHROPIC_API_KEY"], "sk-inherited-not-orbits")
        self.assertEqual(pol["env"]["FUTURE_PROVIDER_TOKEN"], "sentinel-future")        # unknown future names pass through
        self.assertEqual(pol["env"]["HOME"], engine.H)
        self.assertTrue(pol["env"]["PATH"].startswith(engine.BIN + os.pathsep))
        self.assertEqual(pol["env"]["CLAUDE_CODE_FORK_SUBAGENT"], "0")
        if osinfo.KIND == "windows":
            self.assertEqual(pol["env"]["CLAUDE_CODE_USE_POWERSHELL_TOOL"], "1")
        self.assertEqual(pol["env"]["STAFF_EMPLOYEE"], "tess")                          # enumerated overrides win
        self.assertIn("fetch", pol["env"]["STAFF_ABILITIES"].split(","))
        self.assertEqual(pol["env"]["STAFFROOM_HOME"], engine.HOME)
        self.assertEqual(pol["env"]["STAFFROOM_KIT"], engine.KIT)

    def test_ordinary_onboarding_and_plugin_have_no_overlays(self):
        pol = engine.launch_policy("onboarding")
        self.assertEqual((pol["mode"], pol["setting_sources"]), ("ordinary", "user"))
        self.assertNotIn("STAFF_EMPLOYEE", pol["env"])
        self.assertNotIn("CLAUDECODE", pol["env"])
        self.assertEqual(pol["env"]["FUTURE_PROVIDER_TOKEN"], "sentinel-future")
        self.assertEqual(pol["env"]["ANTHROPIC_API_KEY"], "sk-inherited-not-orbits")   # inherited value preserved; Orbit injects nothing
        pol = engine.launch_policy("plugin")
        self.assertEqual((pol["mode"], pol["setting_sources"]), ("ordinary", None))
        self.assertNotIn("STAFF_EMPLOYEE", pol["env"])

    def test_ordinary_command_argv_selects_user_sources(self):
        reg = engine.registry()
        self.assertNotEqual(reg.get("auth"), "api_key")        # the fresh team is a pass-through install
        cmd = engine.command(engine.employee("tess"), "sonnet")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "user,project")

    def test_legacy_employee_is_isolated(self):
        self.legacy()
        pol = engine.launch_policy("employee", engine.employee("tess"))
        self.assertEqual(pol["mode"], "legacy")
        self.assertEqual(pol["setting_sources"], "project")
        self.assertNotIn("CLAUDECODE", pol["env"])
        self.assertNotIn("ANTHROPIC_BASE_URL", pol["env"])     # routing stripped (existing legacy behavior)
        self.assertEqual(pol["env"]["FUTURE_PROVIDER_TOKEN"], "sentinel-future")   # only provider prefixes strip; unknown names pass
        self.assertEqual(pol["env"]["ANTHROPIC_API_KEY"], "sk-stored-orbit")
        self.assertEqual(pol["env"]["STAFF_EMPLOYEE"], "tess")
        cmd = engine.command(engine.employee("tess"), "sonnet")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project")

    def test_legacy_onboarding_keeps_isolated_source_and_key(self):
        self.legacy()
        pol = engine.launch_policy("onboarding")
        self.assertEqual((pol["mode"], pol["setting_sources"]), ("legacy", ""))
        self.assertEqual(pol["env"]["ANTHROPIC_API_KEY"], "sk-stored-orbit")
        self.assertNotIn("ANTHROPIC_BASE_URL", pol["env"])

    def test_legacy_plugin_administration_never_sees_the_stored_key(self):
        self.legacy()
        pol = engine.launch_policy("plugin")
        self.assertNotIn("ANTHROPIC_API_KEY", pol["env"])
        self.assertNotIn("ANTHROPIC_BASE_URL", pol["env"])
        self.assertIsNone(pol["setting_sources"])


class EmployeeLaunch(unittest.TestCase):
    """T010/T013 (FR-005–FR-011, FR-010, FR-020, SC-002, SC-004): a genuine engine.run() through
    the fake Claude executable proves the whole launch surface — argv, environment snapshot,
    workspace, prompt and session handling — and that nothing of the provider connection or the
    inherited environment reaches anything Orbit persists."""

    PROMPT = "Write a one-line morning brief."

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex", picked=["web", "fetch", "browser"],
                  domains=["api.example.com"])
        self.real = engine.resolve_claude
        self.saved = {k: os.environ.get(k) for k in SENTINEL_ENV}

    def tearDown(self):
        engine.resolve_claude = self.real
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def fake(self, **cfg):
        self.dir = _cleanup.temp("fake-claude-")   # outside the Orbit home: the recorder
        engine.resolve_claude = lambda: fake_claude.install(self.dir, **cfg)  # writes sentinels by design

    def ordinary_run(self, **run_kw):
        self.fake(prompt={"result": "Morning brief: one strong line."})
        os.environ.update(SENTINEL_ENV)
        emp = engine.employee("tess")
        return emp, engine.run(emp, self.PROMPT, **run_kw)

    @POSIX_FAKE_RUN
    def test_ordinary_employee_run_end_to_end(self):
        emp, out = self.ordinary_run()
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["text"], "Morning brief: one strong line.")
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 1)
        c = recs[0]
        self.assertEqual(c["cwd"], emp["workspace"])
        self.assertEqual(c["stdin"], self.PROMPT)
        argv = c["argv"]
        self.assertEqual(argv[0], "-p")
        self.assertNotIn("--resume", argv)                 # a fresh chat starts a new session
        self.assertTrue(argv[argv.index("--session-id") + 1])
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        self.assertEqual(argv[argv.index("--effort") + 1], "medium")
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "user,project")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertIn("--strict-mcp-config", argv)
        self.assertIn(engine.GUARD, argv)                  # the guard plugin still rides along
        self.assertTrue(any(a.startswith(os.path.join(TMP, ".runtime", "tess")) for a in argv))
        cmd = engine.command(emp, "sonnet")                # unchanged sandbox/lock controls (deterministic)
        s = json.loads(cmd[cmd.index("--settings") + 1])
        self.assertTrue(s["sandbox"]["enabled"])
        self.assertIn("api.example.com", s["sandbox"]["network"]["allowedDomains"])
        env = c["env"]
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://inherited:4000")   # the connection, inherited
        self.assertEqual(env["FUTURE_PROVIDER_TOKEN"], "sentinel-future")      # unknown future names pass
        self.assertNotEqual(env.get("ANTHROPIC_API_KEY"), "sk-stored-orbit")   # no Orbit-stored key exists
        self.assertEqual(env["HOME"], engine.H)
        self.assertTrue(env["PATH"].startswith(engine.BIN + os.pathsep))
        self.assertEqual(env["CLAUDE_CODE_FORK_SUBAGENT"], "0")
        self.assertEqual(env["STAFF_EMPLOYEE"], "tess")
        self.assertEqual(env["STAFF_WORKSPACE"], emp["workspace"])
        self.assertEqual(env["STAFFROOM_HOME"], engine.HOME)
        self.assertEqual(env["STAFFROOM_KIT"], engine.KIT)
        self.assertIn("fetch", env["STAFF_ABILITIES"].split(","))
        if osinfo.KIND == "windows":
            self.assertEqual(env["CLAUDE_CODE_USE_POWERSHELL_TOOL"], "1")

    @POSIX_FAKE_RUN
    def test_chat_resumes_one_session_per_person(self):
        emp, out = self.ordinary_run(session_key="room:1")
        self.assertTrue(out["ok"], out)
        out2 = engine.run(emp, "Continue.", session_key="room:1")
        self.assertTrue(out2["ok"], out2)
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 2)
        self.assertNotIn("--resume", recs[0]["argv"])      # first chat: new session...
        self.assertIn("--resume", recs[1]["argv"])         # ...then every later message resumes it

    @POSIX_FAKE_RUN
    def test_legacy_employee_run_is_unchanged(self):
        reg = engine.registry()
        reg["auth"] = "api_key"
        engine.save_registry(reg)
        engine.save_secret("anthropic_api_key", "sk-stored-orbit")
        self.ordinary_run()
        c = fake_claude.calls(self.dir)[0]
        argv, env = c["argv"], c["env"]
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "project")
        self.assertNotIn("ANTHROPIC_BASE_URL", env)        # legacy isolation: routing values stripped
        self.assertEqual(env["ANTHROPIC_API_KEY"], "sk-stored-orbit")   # the stored key, inference only
        self.assertEqual(env["FUTURE_PROVIDER_TOKEN"], "sentinel-future")   # provider-prefixed values only strip
        self.assertEqual(env["STAFF_EMPLOYEE"], "tess")

    @POSIX_FAKE_RUN
    def test_persistence_boundary(self):
        emp, out = self.ordinary_run(session_key="room:1")
        self.assertTrue(out["ok"], out)
        ban = ("sentinel-future", "sk-inherited-not-orbits", "http://inherited:4000", "CLAUDECODE")
        reg = json.load(open(engine.REGISTRY, encoding="utf-8"))
        self.assertEqual(reg.get("auth"), "subscription")  # nothing re-binds the install to a provider
        self.assertFalse([k for k in reg if any(t in k for t in ("provider", "endpoint", "credential",
                                                                 "discovery", "readiness"))])
        rec = json.loads(open(os.path.join(emp["workspace"], "state", "runs.jsonl"),
                              encoding="utf-8").read().strip().splitlines()[-1])
        self.assertEqual((rec["employee"], rec["job"]), ("tess", "chat"))
        self.assertNotIn("env", rec)                       # no environment snapshot in run records
        self.assertFalse([k for k in rec if any(t in k for t in ("provider", "endpoint", "credential",
                                                                 "discovery", "readiness"))])
        with open(os.path.join(emp["workspace"], "state", "sessions.json"), encoding="utf-8") as fh:
            sess = json.load(fh)
        self.assertIn("room:1", sess)                      # the only run binding: an Orbit-made session id
        for root, _, files in os.walk(engine.HOME):        # sweeping the whole install folder
            for f in files:
                p = os.path.join(root, f)
                with open(p, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                for b in ban:
                    self.assertNotIn(b, text, "leaked into %s" % p)


class HireAndPluginLaunch(unittest.TestCase):
    """T011 (FR-006–FR-009, FR-012, SC-002, SC-005): structured onboarding and guard-plugin
    administration at the fake executable's argv/env level — pass-through with the declared
    controls, no unlisted overlays, and never the stored inference key."""

    STRUCTURED = {"intro": "Two quick ones.",
                  "questions": [{"type": "choice", "q": "Daily brief tone?", "options": ["Casual", "Formal"]}],
                  "name": "Sam", "role": "Market researcher",
                  "scope": "Find market numbers the owner can use.",
                  "abilities": ["memory"], "routines": {}, "access": [], "budget": "regular",
                  "description": "Research support", "first_task": "Check example.com",
                  "plan": "Look at numbers", "model": "sonnet"}

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.reals = engine.resolve_claude
        self.saved = {k: os.environ.get(k) for k in SENTINEL_ENV}

    def tearDown(self):
        engine.resolve_claude = self.reals
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def fake(self, **cfg):
        self.dir = _cleanup.temp("fake-claude-")   # outside the Orbit home (the recorder
        engine.resolve_claude = lambda: fake_claude.install(self.dir, **cfg)  # writes sentinels by design)

    def supported_desktop(self):
        """Plugin administration is a supported-desktop behavior; native-Windows Desktop refusal has
        its own focused tests (T036/T037)."""
        old = osinfo.KIND
        osinfo.KIND = "linux"
        self.addCleanup(setattr, osinfo, "KIND", old)

    def test_structured_onboarding_uses_user_source_and_no_tools(self):
        import onboard
        self.fake(prompt={"structured": self.STRUCTURED, "result": "answers ready"})
        os.environ.update(SENTINEL_ENV)
        q = onboard.questions("Market researcher", "Find market numbers", name="Sam")
        self.assertEqual(q["intro"], "Two quick ones.")
        self.assertEqual([x["id"] for x in q["questions"]], ["q1"])   # Orbit normalizes the card
        card = onboard.compose("Market researcher", "Find market numbers", "Sam",
                               answers=[{"q": "Tone?", "a": "Casual"}])
        self.assertEqual(card["budget"], "regular")
        self.assertEqual(card["abilities"], ["memory"])
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 2)
        for c in recs:
            argv, env = c["argv"], c["env"]
            self.assertEqual(c["cwd"], engine.HOME)
            self.assertEqual(argv[0], "-p")
            self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
            self.assertEqual(argv[argv.index("--effort") + 1], "low")
            self.assertEqual(argv[argv.index("--tools") + 1], "")
            self.assertEqual(argv[argv.index("--setting-sources") + 1], "user")
            self.assertEqual(argv[argv.index("--output-format") + 1], "json")
            self.assertIn("--no-session-persistence", argv)
            self.assertIn("--strict-mcp-config", argv)
            if osinfo.KIND != "windows":                   # cmd.exe %* quoting garbles the JSON tail
                self.assertIn("--json-schema", argv)       # on Windows .bat shims: recorded Windows quirk
            self.assertNotIn("CLAUDECODE", env)
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://inherited:4000")
            self.assertEqual(env["FUTURE_PROVIDER_TOKEN"], "sentinel-future")
            for k in ("STAFF_EMPLOYEE", "STAFF_WORKSPACE", "STAFFROOM_KIT", "STAFF_ABILITIES",
                      "STAFF_BROWSER_SITES", "CLAUDE_CODE_FORK_SUBAGENT"):
                self.assertNotIn(k, env)                   # onboarding gets no employee overlays
            self.assertNotEqual(env.get("ANTHROPIC_API_KEY"), "sk-stored-orbit")

    def test_plugin_administration_is_pass_through_without_overlays_or_keys(self):
        self.supported_desktop()
        self.fake()                                        # plugin answer: already installed
        os.environ.update(SENTINEL_ENV)
        s = engine.claude_session("tess")
        self.assertIn("folder", s)
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 2)                     # marketplace add, then plugin install
        ws = engine.employee("tess")["workspace"]
        for c in recs:
            argv, env = c["argv"], c["env"]
            self.assertEqual(argv[0], "plugin")
            self.assertNotIn("--setting-sources", argv)    # administration declares no setting sources
            self.assertNotIn("CLAUDECODE", env)
            self.assertEqual(c["cwd"], ws)                 # scoped to this folder only
            self.assertEqual(env["FUTURE_PROVIDER_TOKEN"], "sentinel-future")
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "http://inherited:4000")   # plain pass-through
            for k in ("STAFF_EMPLOYEE", "STAFF_WORKSPACE", "STAFFROOM_KIT", "STAFF_ABILITIES",
                      "CLAUDE_CODE_FORK_SUBAGENT"):
                self.assertNotIn(k, env)                   # no unlisted overlays for administration
            self.assertNotEqual(env.get("ANTHROPIC_API_KEY"), "sk-stored-orbit")   # no Orbit key, ever
        stamp = os.path.join(ws, ".claude", "orbit-guard.version")
        with open(os.path.join(engine.GUARD, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh, \
                open(stamp, encoding="utf-8") as out:
            self.assertEqual(out.read().strip(), json.load(fh)["version"])   # the install actually stamped

    def test_legacy_plugin_administration_stays_key_free(self):
        self.supported_desktop()
        reg = engine.registry()
        reg["auth"] = "api_key"
        engine.save_registry(reg)
        engine.save_secret("anthropic_api_key", "sk-stored-orbit")
        self.fake()
        os.environ.update(SENTINEL_ENV)
        engine.claude_session("tess")
        for c in fake_claude.calls(self.dir):
            env = c["env"]
            self.assertNotIn("ANTHROPIC_API_KEY", env)     # legacy administration never sees the stored key
            self.assertNotIn("ANTHROPIC_BASE_URL", env)    # ...nor any legacy-isolated routing value
            self.assertEqual(c["argv"][0], "plugin")       # fixed operation/workspace behavior untouched


class Panel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        ws = engine.employee("tess")["workspace"]
        os.makedirs(os.path.join(ws, "research"), exist_ok=True)
        with open(os.path.join(ws, "research", "notes.md"), "w") as fh:
            fh.write("# Notes\n\nhello")
        with open(os.path.join(ws, "state", "secret.txt"), "w") as fh:
            fh.write("nope")
        import panel
        cls.panel = panel
        cls.tok = panel.token()
        from http.server import ThreadingHTTPServer
        cls.srv = ThreadingHTTPServer(("127.0.0.1", panel.port()), panel.Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = "http://127.0.0.1:%d" % panel.port()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def req(self, path, data=None, headers=None, raw=False):
        body = None if data is None else (data if raw else json.dumps(data).encode())
        h = {"content-type": "application/json"} if data is not None and not raw else {}
        h.update(headers or {})
        r = urllib.request.Request(self.base + path, data=body, headers=h)
        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(r, timeout=10) as resp:
                return resp.status, dict(resp.headers), resp.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read().decode()

    def auth(self, extra=None):
        return {"Cookie": "sr%d=%s" % (self.panel.port(), self.tok), **(extra or {})}

    def test_claude_checklist_and_settings_are_provider_neutral(self):
        """FR-003/FR-004: readiness describes the installation, never account sign-in."""
        import panel
        cache, real = panel._availability, engine.claude_availability
        panel._availability = {"at": 0.0, "value": None}
        engine.claude_availability = lambda: {"state": "missing",
                                              "detail": "Install Claude Code from https://claude.com/claude-code."}
        try:
            st = json.loads(self.req("/api/state", headers=self.auth())[2])
            item = next(c for c in st["checklist"] if c["id"] == "claude")
            self.assertFalse(item["done"])
            blob = json.dumps(item).lower()
            self.assertNotIn("sign in", blob)
            self.assertNotIn("sign in to", blob)
            self.assertNotIn("auth login", blob)
            s = json.loads(self.req("/api/settings", headers=self.auth())[2])
            self.assertEqual(s["claude"]["state"], "missing")
            self.assertEqual(s["claude"]["detail"], "Install Claude Code from https://claude.com/claude-code.")
        finally:
            panel._availability, engine.claude_availability = cache, real

    def test_needs_the_token(self):
        self.assertEqual(self.req("/")[0], 401)
        self.assertEqual(self.req("/api/state")[0], 401)
        self.assertEqual(self.req("/?t=wrong")[0], 403)
        code, h, _ = self.req("/?t=" + self.tok)
        self.assertEqual(code, 303)
        self.assertIn("HttpOnly", h["Set-Cookie"])
        self.assertIn("SameSite=Strict", h["Set-Cookie"])

    def test_app_and_api(self):
        for path in ("/", "/team", "/e/tess/memory", "/settings"):
            code, h, body = self.req(path, headers=self.auth())
            self.assertEqual(code, 200, path)
            self.assertIn('<script src="/app.js"', body)
            self.assertIn("script-src 'self'", h["Content-Security-Policy"])
        code, _, body = self.req("/api/state", headers=self.auth())
        st = json.loads(body)
        self.assertEqual(code, 200)
        self.assertEqual([e["id"] for e in st["employees"]], ["tess"])
        self.assertIn("memory", st["employees"][0]["abilities"])
        self.assertTrue(any(c["id"] == "hire" and c["done"] for c in st["checklist"]))
        code, _, body = self.req("/api/employee/tess", headers=self.auth())
        d = json.loads(body)
        self.assertEqual(code, 200)
        self.assertIn("Tess", d["memory"]["CLAUDE.md"])
        self.assertEqual([f["path"] for f in d["files"]][0], "research/notes.md")          # newest first
        self.assertTrue(all(f["path"].split("/")[0] in ("research", "notes", "tools", "growth", "evals") for f in d["files"]))
        self.assertEqual(self.req("/api/employee/nobody", headers=self.auth())[0], 404)

    def test_unread_and_seen_in_the_panel(self):
        team.feed("tess", "Tess", "Alex", "Standup: all good.", "job")
        code, _, body = self.req("/api/state", headers=self.auth())
        self.assertEqual(code, 200)
        self.assertGreaterEqual(json.loads(body)["unread"], 1)
        code, _, body = self.req("/api/seen", {}, headers=self.auth({"Origin": self.base}))
        self.assertEqual((code, json.loads(body)["ok"]), (200, True))
        _, _, body = self.req("/api/state", headers=self.auth())
        self.assertEqual(json.loads(body)["unread"], 0)

    def test_scoped_seen_in_the_panel_keeps_another_report_unread(self):
        import hire
        hire.hire("Omar", "Social", supervisor="Alex")
        ts = "2026-11-10 11:00:00"
        try:
            team.append(team.FEED, {"id": "paneltess001", "ts": ts, "from_id": "tess", "from_name": "Tess",
                                    "to_id": "Alex", "body": "Tess panel report", "channel": "job"})
            team.append(team.FEED, {"id": "panelomar001", "ts": ts, "from_id": "omar", "from_name": "Omar",
                                    "to_id": "Alex", "body": "Omar panel report", "channel": "job"})
            h = self.auth({"Origin": self.base})
            self.assertEqual(self.req("/api/seen", {"employee": "tess"}, h)[0], 200)
            self.assertEqual([r["body"] for r in team.unread("Alex")], ["Omar panel report"])
            self.assertEqual(team.unread("Alex", "tess"), [])
            self.assertEqual(self.req("/api/seen", {"employee": "nobody"}, h)[0], 404)
            self.assertEqual(self.req("/api/seen", {}, h)[0], 200)     # the full room clears the rest
            self.assertEqual(team.unread("Alex"), [])
        finally:
            reg = engine.registry()
            reg["employees"].pop("omar", None)
            engine.save_registry(reg)

    def test_files_stay_inside_the_workspace(self):
        code, _, body = self.req("/api/file?emp=tess&path=research/notes.md", headers=self.auth())
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["text"], "# Notes\n\nhello")
        for bad in ("../../staff.json", "state/secret.txt", "/etc/passwd", "profile.json.png", ".git/config"):
            self.assertEqual(self.req("/api/file?emp=tess&path=" + urllib.parse.quote(bad), headers=self.auth())[0], 400, bad)

    def test_rejects_other_hosts_and_origins(self):
        self.assertEqual(self.req("/api/state", headers=self.auth({"Host": "evil.example:7398"}))[0], 403)
        order = {"kind": "pause", "employee_id": "tess"}
        self.assertEqual(self.req("/api/order", order, self.auth({"Origin": "https://evil.example"}))[0], 403)
        self.assertEqual(self.req("/api/order", order, self.auth())[0], 403)               # no Origin at all
        self.assertEqual(self.req("/api/order", order, {"Origin": self.base})[0], 403)      # no cookie
        self.assertEqual(engine.registry()["employees"]["tess"]["status"], "active")

    def test_orders_settings_and_rules(self):
        h = self.auth({"Origin": self.base})
        code, _, body = self.req("/api/order", {"kind": "pause", "employee_id": "tess"}, h)
        self.assertEqual(code, 200)
        self.assertIn("Paused Tess", json.loads(body)["message"])
        self.assertEqual(engine.registry()["employees"]["tess"]["status"], "paused")
        self.req("/api/order", {"kind": "resume", "employee_id": "tess"}, h)
        code, _, body = self.req("/api/order", {"kind": "run_job", "employee_id": "tess", "job": "rm -rf"}, h)
        self.assertEqual(code, 400)
        self.assertIn("Unknown routine", json.loads(body)["error"])
        code, _, body = self.req("/api/employee/tess/rules", {"text": "Reply in Arabic.\nAlways give three options."}, h)
        self.assertEqual(code, 200)
        with open(os.path.join(engine.employee("tess")["workspace"], "CLAUDE.md")) as fh:
            doc = fh.read()
        self.assertTrue(doc.rstrip().endswith("## Role-specific rules\nReply in Arabic.\nAlways give three options."))
        code, _, _ = self.req("/api/settings", {"team_name": "Acme", "workdays": ["Sun", "Mon"], "jobs": {"brief": "07:45", "eod": "99:99"},
                                               "apify": {"monthly_budget_usd": "12", "max_run_usd": "9"}, "network_domains": "api.example.com\nbad host"}, h)
        self.assertEqual(code, 200)
        reg = engine.registry()
        self.assertEqual((reg["team_name"], reg["workdays"], reg["jobs"]["brief"]["at"]), ("Acme", ["Sun", "Mon"], "07:45"))
        self.assertNotIn("eod", reg["jobs"])
        self.assertEqual((reg["apify"]["monthly_budget_usd"], reg["apify"]["max_run_usd"]), (12.0, 2.0))
        self.assertEqual(reg["network_domains"], ["api.example.com"])
        code, _, body = self.req("/api/order", b"not json", self.auth({"Origin": self.base, "content-type": "application/json"}), raw=True)
        self.assertEqual(code, 400)

    def test_access_approvals(self):
        h = self.auth({"Origin": self.base})
        team.jsave(self.panel.PENDING, {"slack:U7": {"name": "Sam", "channel": "slack", "at": "2026-10-29 10:00"},
                                        "discord:5": {"name": "Sam", "channel": "discord", "at": "2026-10-29 10:01"}})
        st = json.loads(self.req("/api/state", headers=self.auth())[2])
        self.assertIn("Sam messaged your Slack bot", [n["title"] for n in st["needs"]])
        code, _, body = self.req("/api/owner", {"id": "slack:U7", "do": "approve", "name": "Sam"}, h)
        self.assertEqual(code, 200, body)
        self.assertEqual(engine.registry()["owners"]["slack:U7"]["name"], "Sam")
        code, _, body = self.req("/api/owner", {"id": "discord:5", "do": "approve", "into": "slack:U7"}, h)
        self.assertEqual(code, 200, body)
        self.assertEqual(engine.owner_key("discord:5"), "slack:U7")
        s = json.loads(self.req("/api/settings", headers=self.auth())[2])
        self.assertEqual(sorted(s["channels"]), ["discord", "slack", "telegram"])
        st = json.loads(self.req("/api/state", headers=self.auth())[2])
        sam = next(o for o in st["owners"] if o["id"] == "slack:U7")
        self.assertEqual(sam["addresses"], ["Slack id U7", "Discord id 5"])
        self.assertEqual(self.req("/api/owner", {"id": "slack:U7", "do": "approve"}, h)[0], 400)   # gone

    def test_skills_api(self):
        h = self.auth({"Origin": self.base})
        code, _, body = self.req("/api/skill", {"emp": "tess", "do": "create", "name": "digest-format", "text": "Steps\n1. Three bullets.\n2. Sources inline.\n",
                                                "description": "How Alex wants the Monday digest. Use when asked for the digest."}, h)
        self.assertEqual(code, 200, body)
        d = json.loads(self.req("/api/employee/tess", headers=self.auth())[2])
        self.assertEqual([(s["name"], s["how"], s["by"]) for s in d["skills"]["own"]], [("digest-format", "panel", "Alex")])
        self.assertIn("research-playbook", [s["name"] for s in d["skills"]["kit"]])
        code, _, body = self.req("/api/skill?emp=tess&where=own&name=digest-format", headers=self.auth())
        self.assertEqual(code, 200)
        self.assertIn("Three bullets", json.loads(body)["text"])
        code, _, body = self.req("/api/skill?emp=tess&where=kit&name=monitoring", headers=self.auth())
        self.assertEqual((code, json.loads(body)["readonly"]), (200, True))
        code, _, body = self.req("/api/skill", {"emp": "tess", "do": "share", "name": "digest-format"}, h)
        self.assertEqual(code, 200, body)
        self.assertEqual([s["name"] for s in json.loads(self.req("/api/state", headers=self.auth())[2])["team_skills"]], ["digest-format"])
        code, _, body = self.req("/api/skill", {"emp": "tess", "do": "create", "name": "monitoring", "description": "shadowing a kit playbook", "text": "1. nope"}, h)
        self.assertEqual(code, 400)
        self.assertIn("kit", json.loads(body)["error"])
        code, _, _ = self.req("/api/skill", {"emp": "tess", "where": "team", "do": "remove", "name": "digest-format"}, h)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(self.req("/api/state", headers=self.auth())[2])["team_skills"], [])
        self.assertEqual(self.req("/api/skill?emp=nobody&where=own&name=x", headers=self.auth())[0], 404)


class Channels(unittest.TestCase):
    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")

    def test_addresses_and_owner_keys(self):
        import channels
        self.assertEqual(channels.parse("111"), ("telegram", "111"))
        self.assertEqual(channels.parse("-100123"), ("telegram", "-100123"))
        self.assertEqual(channels.parse("slack:U1"), ("slack", "U1"))
        self.assertEqual(channels.parse("local-alex"), ("", "local-alex"))
        self.assertEqual(channels.norm("111"), "telegram:111")
        self.assertEqual([channels.guess(x) for x in ("-100", "C0ABC123", "123456789012345678", "x")], ["telegram", "slack", "discord", ""])
        reg = engine.registry()
        reg["owners"]["111"]["addresses"] = ["slack:U1"]
        engine.save_registry(reg)
        self.assertEqual((engine.owner_key("telegram:111"), engine.owner_key("111"), engine.owner_key("slack:U1")), ("111", "111", "111"))
        self.assertIsNone(engine.owner_key("slack:U2"))
        self.assertEqual(engine.owner_id("alex"), "111")
        self.assertTrue(team.may_send_to("111"))
        self.assertFalse(team.may_send_to("slack:U2"))               # never a stranger
        self.assertFalse(team.may_send_to("telegram:-100999"))      # never an unregistered chat

    def test_handle_routes_owners_and_ignores_strangers(self):
        import channels
        import staffd
        sent, runs = [], []

        class Fake:
            NAME, LIMIT = "slack", 3900
            def token(self): return "xoxb-test"
            def send(self, cid, text): sent.append((cid, text)); return True
            def send_file(self, cid, path, caption=""): return True
            def typing(self, cid): pass
            def dm_chat(self, uid): return "D" + uid
            def download(self, att, d, n): return None
            def mention(self, h): return "@" + h
        fake = Fake()
        real_get, real_run = channels.get, staffd.run_async
        channels.get = lambda n: fake if n == "slack" else real_get(n)
        staffd.run_async = lambda *a, **k: runs.append((a, k))
        try:
            reg = engine.registry()
            reg["owners"] = {"slack:U1": {"name": "Alex", "aliases": []}}
            engine.save_registry(reg)
            dm = {"channel": "slack", "sender": "slack:U1", "sender_name": "Alex", "username": "alex", "chat": "slack:D1",
                  "is_group": False, "chat_title": None, "text": "help", "reply_to_text": "", "attachments": []}
            staffd.handle(dm)
            self.assertEqual(sent[-1][0], "D1")
            self.assertIn("@tess", sent[-1][1])
            staffd.handle({**dm, "text": "@tess what's new?"})
            a, k = runs[-1]
            self.assertEqual((a[0], k["session_key"], k["deliver_to"], k["channel"], k["said"]), ("tess", None, ["slack:D1"], "slack", "what's new?"))
            self.assertEqual(team.to_people(engine.employee("tess"), "supervisor"), ["slack:D1"])   # replies go where they wrote
            staffd.handle({**dm, "sender": "slack:U9", "sender_name": "Stranger"})
            self.assertEqual(len(runs), 1)
            self.assertEqual(team.jload(staffd.PENDING, {})["slack:U9"]["channel"], "slack")
            self.assertEqual(len(sent), 1)                             # strangers never get an answer
            grp = {**dm, "chat": "slack:C1", "is_group": True, "text": "tess: summarize this"}
            staffd.handle(grp)
            self.assertEqual(len(runs), 1)                             # an unregistered chat is ignored
            reg = engine.registry()
            reg["team_chats"] = {"slack": "C1"}
            engine.save_registry(reg)
            staffd.handle(grp)
            a, k = runs[-1]
            self.assertEqual((a[0], k["session_key"], k["deliver_to"], k["channel"]), ("tess", None, ["slack:C1"], "group"))
            staffd.handle({**grp, "text": "just us owners talking"})
            self.assertEqual(len(runs), 2)                             # no employee named: stay out
            team.send("slack:C1", "hello room")
            self.assertEqual(sent[-1], ("C1", "hello room"))
            team.send("slack:U9", "leak?")
            self.assertEqual(sent[-1], ("C1", "hello room"))
        finally:
            channels.get, staffd.run_async = real_get, real_run


FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, sys, time
sys.stdin.read()
if "--sleep" in open(__file__).read() and False:
    pass
def out(d):
    print(json.dumps(d), flush=True)
out({"type": "system", "subtype": "init"})
out({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "WebSearch", "input": {"query": "coffee prices"}}]}})
out({"type": "user", "message": {"content": [{"type": "tool_result", "content": "..."}]}})
out({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "staff-fetch https://www.example.com/x"}}]}})
out({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Glob", "input": {"pattern": "*"}}]}})
out({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "WS/research/prices.md"}}]}})
SLEEP
out({"type": "assistant", "message": {"content": [{"type": "text", "text": "Done."}]}})
out({"type": "result", "subtype": "success", "is_error": False, "result": "Done.", "num_turns": 4, "total_cost_usd": 0.0123})
'''


class LiveSteps(unittest.TestCase):
    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.emp = engine.employee("tess")
        self.real = engine.resolve_claude

    def tearDown(self):
        engine.resolve_claude = self.real

    def fake(self, sleep=0):
        p = os.path.join(TMP, "fake-claude")
        with open(p, "w") as fh:
            fh.write(FAKE_CLAUDE.replace("WS", self.emp["workspace"]).replace("SLEEP", "time.sleep(%d)" % sleep))
        os.chmod(p, 0o755)
        engine.resolve_claude = lambda: p

    def test_describe(self):
        import steps
        ws = "/w"
        self.assertEqual(steps.describe("WebSearch", {"query": "harbor   roast"}, ws), 'Searching the web: "harbor roast"')
        self.assertEqual(steps.describe("Bash", {"command": "staff-apify run tiktok '{\"profiles\": [\"x\"]}' --max-items 10"}, ws), "Running the TikTok scraper")
        self.assertEqual(steps.describe("Bash", {"command": "staff-browse https://www.tiktok.com/@x --scroll 5"}, ws), "Opening tiktok.com in the browser and scrolling through it")
        self.assertEqual(steps.describe("Bash", {"command": "staff-bus ask omar \"which page?\""}, ws), "Asking Omar")
        self.assertEqual(steps.describe("Read", {"file_path": "/w/STATE.md"}, ws), "Checking my notes")
        self.assertEqual(steps.describe("Edit", {"file_path": "/w/LESSONS.md"}, ws), "Updating my notes (LESSONS.md)")
        self.assertEqual(steps.describe("Write", {"file_path": "/w/research/a.md"}, ws), "Writing research/a.md")
        self.assertEqual(steps.describe("Read", {"file_path": "/w/state/inbox/x.pdf"}, ws), "Reading the file you sent")
        self.assertIsNone(steps.describe("Read", {"file_path": "/w/state/runs.jsonl"}, ws))
        self.assertIsNone(steps.describe("Bash", {"command": "ls -la"}, ws))
        self.assertIsNone(steps.describe("Bash", {"command": "git status"}, ws))
        self.assertEqual(steps.describe("Bash", {"command": "python3 /w/tools/price_check.py"}, ws), "Running my tool tools/price_check.py")
        self.assertIsNone(steps.describe("SomethingNew", {}, ws))

    @POSIX_FAKE_RUN
    def test_run_streams_steps_and_keeps_a_receipt(self):
        self.fake()
        seen = []
        res = engine.run(self.emp, "hi", job="chat", on_step=lambda s, all_: seen.append(s["text"]))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["text"], "Done.")
        want = ['Searching the web: "coffee prices"', "Reading example.com", "Looking through my files", "Writing research/prices.md"]
        self.assertEqual(seen, want)
        self.assertEqual([s["text"] for s in res["steps"]], want)
        with open(os.path.join(self.emp["workspace"], "state", "runs.jsonl")) as fh:
            rec = json.loads(fh.read().splitlines()[-1])
        self.assertEqual((rec["ok"], rec["cost_usd"], len(rec["steps"])), (True, 0.0123, 4))

    @POSIX_FAKE_RUN
    def test_timeout(self):
        self.fake(sleep=5)
        res = engine.run(self.emp, "hi", job="brief", timeout=1)
        self.assertFalse(res["ok"])
        self.assertIn("timed out", res["error"])


class Onboarding(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TMP, ignore_errors=True)
        os.makedirs(os.path.join(TMP, "team"))
        engine.save_registry({"team_name": "My team", "owners": {}, "employees": {}, "panel": {"port": 7398}})
        import panel
        self.panel = panel

    def test_welcome_hire_connect_pair(self):
        import channels
        import staffd
        p = self.panel
        self.assertTrue(p.setup_state([])["welcome"])
        with self.assertRaises(orders.OrderError):
            p.welcome({"name": " "}, "Owner")
        p.welcome({"name": "Sam", "team_name": "Acme Coffee", "about": "We roast coffee."}, "Owner")
        reg = engine.registry()
        self.assertEqual(reg["owners"], {"local-sam": {"name": "Sam", "aliases": [], "local": True}})
        with open(os.path.join(TMP, "team", "ABOUT.md")) as fh:
            self.assertIn("We roast coffee.", fh.read())
        del RUNS[:]
        orders.execute("Sam", "hire", {"name": "Sara", "role": "Market researcher", "scope": "prices", "abilities": ["web", "fetch"]})
        (a, k), = RUNS
        self.assertEqual((a[0], a[2]), ("sara", "first_day"))                 # she starts with real work
        self.assertIn("First day", a[1])
        self.assertIn("Try next", a[1])
        with self.assertRaises(orders.OrderError):
            p.welcome({"name": "Sam"}, "Sam")                                    # once only
        self.assertFalse(p.setup_state([{"id": "sara"}])["welcome"])

        sent = []

        class Fake:
            NAME, LIMIT = "telegram", 3900
            ok = True
            def token(self): return engine.secret("telegram_bot_token")
            def check(self): return (True, "@acme_team_bot") if self.ok else (False, "Unauthorized")
            def send(self, cid, text): sent.append((cid, text)); return True
            def send_file(self, *a, **k): return True
            def typing(self, cid): pass
            def dm_chat(self, uid): return uid
            def download(self, *a): return None
            def mention(self, h): return "/" + h
        fake = Fake()
        real_get = channels.get
        channels.get = lambda n: fake if n == "telegram" else real_get(n)
        try:
            with self.assertRaises(orders.OrderError):
                p.connect({"kind": "telegram", "token": "not a token"}, "Sam")
            fake.ok = False
            with self.assertRaises(orders.OrderError):
                p.connect({"kind": "telegram", "token": "123456789:" + "A" * 35}, "Sam")
            self.assertIsNone(engine.secret("telegram_bot_token"))            # a refused token isn't kept
            fake.ok = True
            r = p.connect({"kind": "telegram", "token": "123456789:" + "B" * 35}, "Sam")
            code = r["code"]
            self.assertRegex(code, r"^\d{6}$")
            self.assertEqual(r["link"], "https://t.me/acme_team_bot?start=" + code)
            if os.name != "nt":                            # Windows chmod has no group/other bits; the sandbox and guard deny the file
                self.assertEqual(oct(os.stat(os.path.join(engine.SECRETS, "telegram_bot_token")).st_mode & 0o777), "0o600")
            msg = {"channel": "telegram", "sender": "telegram:555", "sender_name": "Mallory", "username": "m", "chat": "telegram:555",
                   "is_group": False, "chat_title": None, "text": "/start 000000", "reply_to_text": "", "attachments": []}
            self.assertFalse(staffd.try_pair(msg))                             # wrong code
            self.assertIsNone(engine.owner_key("telegram:555"))
            staffd.handle({**msg, "sender": "telegram:777", "chat": "telegram:777", "text": "/start " + code})
            reg = engine.registry()
            self.assertEqual(list(reg["owners"]), ["telegram:777"])            # the local owner is now reachable
            self.assertEqual(reg["owners"]["telegram:777"]["name"], "Sam")
            self.assertNotIn("local", reg["owners"]["telegram:777"])
            self.assertEqual(sent[-1][0], "777")
            self.assertIn("Connected. Hi Sam", sent[-1][1])
            self.assertTrue(p.pairing_view()["paired"])
            self.assertIsNone(p.pairing_view()["code"])
            self.assertEqual(team.to_people(engine.employee("sara"), "supervisor"), ["telegram:777"])
            v = p.new_pairing("telegram", "telegram:777")                       # a second device for the same owner
            for _ in range(5):
                staffd.try_pair({**msg, "text": "111111"})
            self.assertIsNone(p.pairing_view()["code"])                         # five wrong tries: void
            self.assertFalse(staffd.try_pair({**msg, "text": v["code"]}))
        finally:
            channels.get = real_get

    def test_apify_token(self):
        p = self.panel
        with self.assertRaises(orders.OrderError):
            p.connect({"kind": "apify", "token": "nope"}, "Sam")
        r = p.connect({"kind": "apify", "token": "apify_api_" + "x" * 30}, "Sam")
        self.assertTrue(r["ok"])
        self.assertEqual(engine.secret("apify_token"), "apify_api_" + "x" * 30)


class Skills(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")

    def test_learn_check_share_and_precedence(self):
        import skillbook
        with self.assertRaises(skillbook.SkillError):
            skillbook.create("tess", "Bad Name", "a description long enough")
        with self.assertRaises(skillbook.SkillError):
            skillbook.create("tess", "monitoring", "shadowing a kit playbook is refused")
        d = skillbook.create("tess", "price-check", "How to check a competitor's price page. Use when asked for prices.")
        self.assertTrue(os.path.isfile(os.path.join(d, "SKILL.md")))
        ws = engine.employee("tess")["workspace"]
        links, skipped = skillbook.bundle(ws, ["monitoring"])
        self.assertIn("monitoring", links)
        self.assertNotIn("price-check", links)                       # a skeleton doesn't load
        self.assertIn("price-check", [n for n, _ in skipped])
        with open(os.path.join(d, "SKILL.md")) as fh:
            text = fh.read().replace("1. …\n", "1. Open the page with staff-fetch.\n")
        skillbook.save("tess", "own", "price-check", text, "Alex")
        links, skipped = skillbook.bundle(ws, ["monitoring"])
        self.assertIn("price-check", links)
        with self.assertRaises(skillbook.SkillError):             # never a secret
            skillbook.save("tess", "own", "price-check", text + "\nuse sk-ant-abcdefghijklmnopqrstuv\n", "Alex")
        skillbook.share("tess", "price-check", "Alex")
        hire.hire("Omar", "Watcher", supervisor="Alex")
        emp = engine.employee("omar")
        root = engine.skills_plugin(emp, abilities.skills("omar"))
        is_link = lambda p: os.path.islink(p) or bool(getattr(os.path, "isjunction", lambda _p: False)(p))
        self.assertTrue(is_link(os.path.join(root, "skills", "price-check")))
        self.assertTrue(is_link(os.path.join(root, "skills", "research-playbook")))
        skillbook.create("omar", "price-check", "Omar's own way to check prices, used when asked.", "Steps:\n1. Open the price page.\n2. Note every price with its date and link.\n")
        links, skipped = skillbook.bundle(emp["workspace"], [])
        self.assertEqual(os.path.realpath(links["price-check"]), os.path.realpath(os.path.join(emp["workspace"], "skills", "price-check")))
        self.assertEqual(skipped, [("price-check", "a own skill with that name already loads")])
        root = engine.skills_plugin(emp, [])
        self.assertEqual(os.path.realpath(os.path.join(root, "skills", "price-check")), os.path.realpath(links["price-check"]))
        self.assertFalse(os.path.lexists(os.path.join(root, "skills", "research-playbook")))
        skillbook.remove("tess", "team", "price-check", "Alex")
        self.assertFalse(os.path.isdir(os.path.join(skillbook.TEAM_DIR, "price-check")))
        self.assertEqual([r["what"] for r in team.tail(skillbook.LOG, 50)], ["learned", "updated", "shared", "learned", "unshared"])

    def test_tool_respects_the_ability(self):
        import subprocess
        tool = [sys.executable, os.path.join(KIT, "core", "tools", "skill.py")]   # same tool, no POSIX shebang needed
        env = {**os.environ, "STAFF_EMPLOYEE": "tess", "STAFF_WORKSPACE": engine.employee("tess")["workspace"], "STAFFROOM_HOME": TMP}
        r = subprocess.run(tool + ["new", "feed-finder", "--description", "Finding a site's hidden JSON feed; use when a page is slow to scrape."],
                           env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Created skills/feed-finder/SKILL.md", r.stdout)
        r = subprocess.run(tool + ["check", "feed-finder"], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("step 1 is empty", r.stderr)
        r = subprocess.run(tool + ["list"], env=env, capture_output=True, text=True)
        self.assertIn("feed-finder", r.stdout)
        self.assertIn("not loading", r.stdout)
        hire.set_abilities("tess", [a for a in abilities.chosen("tess") if a != "learn"], "test")
        r = subprocess.run(tool + ["new", "another-one", "--description", "Something else entirely, used whenever."], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("switched off", r.stderr)
        hire.set_abilities("tess", abilities.preset("default"), "test")
        self.assertIn("Bash(staff-skill *)", abilities.tools("tess")[1] if "learn" not in abilities.effective("tess") else ["Bash(staff-skill *)"])
        self.assertNotIn("staff-skill", abilities.commands("tess"))      # gated, but never outside the sandbox


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class CloudShiftPanel(unittest.TestCase):
    """T027 (FR-017–FR-019, SC-006): the panel shows account eligibility as display-only state,
    failures stay account-only, and installation readiness never depends on the account."""

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        import cloud
        import panel
        self.cloud, self.panel, self.orders = cloud, panel, orders
        self.real_status, self.real_resolve = cloud.account_status, engine.resolve_claude
        self.real_avail = dict(panel._availability)
        engine.resolve_claude = lambda: sys.executable          # a real, runnable client for L01
        panel._availability = {"at": 0.0, "value": None}
        self.account = {}

    def tearDown(self):
        self.cloud.account_status, engine.resolve_claude = self.real_status, self.real_resolve
        self.panel._availability = self.real_avail

    def account_is(self, eligible=False, method="oauth_token",
                   reason="The cloud shift needs a Claude plan sign-in on this computer."):
        self.account = {"checked_at": 1234.5, "eligible": eligible,
                        "auth_method": method, "reason": reason}
        self.cloud.account_status = lambda fresh=False: dict(self.account)

    def test_panel_shows_eligibility_without_making_installing_account_dependent(self):
        self.account_is()
        member = next(m for m in self.panel.members() if m["id"] == "tess")["cloud"]
        self.assertFalse(member["on"])
        self.assertFalse(member["eligible"])
        self.assertFalse(member["blocked"])
        self.assertEqual(member["why_not"], self.account["reason"])
        self.assertEqual(member["auth_method"], "oauth_token")
        self.assertEqual(member["checked_at"], 1234.5)
        for view in (self.panel.state(), self.panel.settings_view()):
            self.assertFalse(view["cloud_shift"]["eligible"])
            self.assertEqual(view["cloud_shift"]["auth_method"], "oauth_token")
            self.assertEqual(view["cloud_shift"]["why_not"], self.account["reason"])
        self.assertEqual(engine.claude_availability()["state"], "available")   # installation only
        self.assertEqual(self.panel.claude_available()["state"], "available")
        low = self.account["reason"].lower()
        self.assertNotIn("api key", low)
        self.assertNotIn("anthropic", low)
        with self.assertRaises(self.orders.OrderError) as ctx:
            self.orders.execute("Alex", "set_cloud", {"employee_id": "tess", "on": True})
        self.assertEqual(str(ctx.exception), self.account["reason"])
        self.assertFalse(self.cloud.is_on("tess"))
        before = set(engine.registry()["employees"])
        self.orders.execute("Alex", "hire", {"name": "Nia", "role": "Writer", "first_day": False})
        new = (set(engine.registry()["employees"]) - before).pop()
        self.assertFalse(self.cloud.is_on(new))                # ordinary work is still hired

    def test_enabled_but_ineligible_shows_blocked_and_turns_off_locally(self):
        reg = engine.registry()
        reg["employees"]["tess"]["cloud_shift"] = True
        engine.save_registry(reg)
        self.account_is()
        member = next(m for m in self.panel.members() if m["id"] == "tess")["cloud"]
        self.assertTrue(member["on"])
        self.assertFalse(member["eligible"])
        self.assertTrue(member["blocked"])                     # configured, but cloud launches are refused
        self.assertTrue(member["why_not"])
        self.orders.execute("Alex", "set_cloud", {"employee_id": "tess", "on": False})
        self.assertFalse(self.cloud.is_on("tess"))             # the local switch always turns off
        self.assertFalse(self.panel.state()["cloud_shift"]["eligible"])


class LaunchInventory(unittest.TestCase):
    """T038: every production launch of the resolved Claude executable maps to exactly one
    inventoried class (L01–L11, contracts/claude-launch.md). A new direct launch with no
    mapping fails here instead of quietly bypassing the launch contract (FR-007, SC-002)."""
    CONTRACT = os.path.join(KIT, "specs", "002-claude-connection-pass-through", "contracts", "claude-launch.md")

    # (file, top-level function) -> inventory ID. L02 executes command()'s argv through the shared
    # run()/stream() seam, so the argv builder stands in for it; L05 is the app link (no CLI child),
    # and L06 is the account-only eligibility check behind every Cloud Shift launch.
    MAPPED = {
        ("core/engine.py", "claude_availability"): "L01",
        ("core/engine.py", "command"): "L02",
        ("core/engine.py", "claude_session"): "L04",
        ("core/onboard.py", "_ask"): "L03",
        ("core/cloud.py", "account_status"): "L06",
        ("core/cloud.py", "trigger"): "L07",
        ("core/cloud.py", "send"): "L08",
        ("core/cloud.py", "environment"): "L09",
        ("core/cloud.py", "new_session"): "L10",
        ("core/cloud.py", "_transcript"): "L11",
    }
    SITE = re.compile(r"(?:=\s*\(?(?:engine\.)?resolve_claude\(\)|\[(?:engine\.)?resolve_claude\(\)(?:,|\])"
                      r"|(?:,\s*|\()\s*(?:engine\.)?resolve_claude\(\)"
                      r"|subprocess\.\w+\(\s*\[?(?:engine\.)?resolve_claude)")

    def production_files(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        y = [("orbit", os.path.join(root, "orbit"))]
        for name in sorted(os.listdir(os.path.join(root, "core"))):
            if name.endswith(".py") and name != "osinfo.py":
                y.append(("core/%s" % name, os.path.join(root, "core", name)))
        return y

    def site_functions(self):
        """{(file, function): line} for every launch-shaped use of resolve_claude()."""
        found = {}
        for rel, path in self.production_files():
            fn = None
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if re.match(r"^def (\w+)\(", line):
                        fn = line.split("def ", 1)[1].split("(", 1)[0].strip()
                    elif self.SITE.search(line) and "dirname(resolve_claude" not in line and fn:
                        found.setdefault((rel, fn), line.strip()[:80])
        return found

    def test_contract_inventories_every_class_exactly_once(self):
        with open(self.CONTRACT, encoding="utf-8") as fh:
            ids = re.findall(r"^\|\s*(L\d\d)\s*\|", fh.read(), re.M)
        self.assertEqual(len(ids), len(set(ids)), "duplicate inventory rows")
        self.assertEqual(sorted(ids), sorted("L%02d" % n for n in range(1, 12)))

    def test_every_launch_site_is_inventoried(self):
        stray = [(k, v) for k, v in self.site_functions().items() if k not in self.MAPPED]
        self.assertEqual(stray, [])

    def test_mapped_sites_exist_and_match_the_contract(self):
        found = self.site_functions()
        for site, launch_id in self.MAPPED.items():
            self.assertIn(site, found, "%s:%s was expected to launch Claude" % site)
        for site in found:
            self.assertIn(site, self.MAPPED)
        used_ids = sorted(self.MAPPED.values())
        self.assertEqual(len(used_ids), len(set(used_ids)))       # a site maps to exactly one class


class StaticContracts(unittest.TestCase):
    """T032 (FR-007, FR-010, FR-013, FR-023, SC-002, SC-007, SC-008): tracked production, setup,
    template and documentation files cannot quietly reintroduce an Anthropic-host preflight, ad hoc
    provider filtering, a generic Claude sign-in prerequisite, or a provider integration surface.
    Historical specifications, tests and the historical design note are out of scope (SC-007)."""

    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RUNTIME = re.compile(r"^(?:core/[^/]+\.py|core/panel/app\.js|orbit)$")
    DOC_ROOTS = ("README.md", "SETUP.md", "PRODUCT.md", "install.sh", "setup-windows.ps1", "docs", "templates",
                 ".github")
    SKIP_DOCS = ("docs/superpowers/",)                       # historical design, excluded by SC-007
    TEXT = (".md", ".sh", ".ps1", ".py", ".js", ".yml", ".yaml", ".json", ".txt")
    PROVIDER_IMPORTS = re.compile(
        r"^\s*(?:import|from)\s+(?:anthropic|openai|litellm|langchain|vertexai|boto3|botocore|"
        r"google\.generativeai)\b", re.M)
    ENDPOINT_FIELD = re.compile(r'"(?:base_url|api_base|api_endpoint|endpoint_url)"\s*[=:]')
    AD_HOC_FILTER = re.compile(
        r'startswith\(\s*\(?\s*"(?:ANTHROPIC_|CLAUDE_CODE_|CLAUDE_AGENT_SDK|BEDROCK|VERTEX|'
        r'FOUNDRY|AWS_)')
    GENERIC_SIGNIN = re.compile(
        r"Claude Code isn't signed in|Signed in to Claude|claude auth login|paid Claude plan", re.I)
    # The only functions allowed to mention account sign-in: Cloud Shift's own account-only block.
    CLOUD_ACCOUNT_FUNCTIONS = {"account_status", "_account_env", "_require_cloud_account",
                               "why_not", "enable", "disable", "status"}

    def _production(self):
        yield "orbit", os.path.join(self.ROOT, "orbit")
        core = os.path.join(self.ROOT, "core")
        for name in sorted(os.listdir(core)):
            if name.endswith(".py"):
                yield "core/" + name, os.path.join(core, name)

    def _documented(self):
        for name in ("README.md", "SETUP.md", "PRODUCT.md", "install.sh", "setup-windows.ps1"):
            yield name, os.path.join(self.ROOT, name)
        for root in ("docs", "templates", ".github"):
            for dirpath, dirnames, filenames in os.walk(os.path.join(self.ROOT, root)):
                dirnames[:] = sorted(d for d in dirnames if d not in ("__pycache__", "node_modules"))
                for name in sorted(filenames):
                    full = os.path.join(dirpath, name)
                    rel = os.path.relpath(full, self.ROOT).replace(os.sep, "/")
                    if rel.startswith(self.SKIP_DOCS) or not name.endswith(self.TEXT):
                        continue
                    yield rel, full

    @staticmethod
    def _lines(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            yield from enumerate(fh, 1)

    def _python_lines(self, path):
        fn = None
        for n, line in self._lines(path):
            m = re.match(r"^def (\w+)\(", line)
            if m:
                fn = m.group(1)
            yield n, fn, line

    def test_anthropic_host_probe_is_the_cloud_tick_only(self):
        hits = []
        for rel, path in self._production():
            for n, fn, line in self._python_lines(path):
                if "api.anthropic.com" not in line:
                    continue
                if rel == "core/cloud.py" and fn == "_online":
                    continue
                hits.append("%s:%d: %s" % (rel, n, line.strip()))
        self.assertEqual(hits, [], "ordinary work must never preflight an Anthropic host (FR-013)")

    def test_provider_prefix_filtering_is_legacy_only(self):
        hits = []
        declarations = 0
        for rel, path in self._production():
            for n, fn, line in self._python_lines(path):
                if line.lstrip().startswith("LEGACY_ENV_PREFIXES = ("):
                    declarations += 1
                    continue
                if "LEGACY_ENV_PREFIXES" in line:
                    if rel != "core/engine.py" or fn != "launch_policy" or "if legacy else" not in line:
                        hits.append("%s:%d: %s" % (rel, n, line.strip()))
                if self.AD_HOC_FILTER.search(line):
                    hits.append("%s:%d: %s" % (rel, n, line.strip()))
        self.assertEqual(declarations, 1, "provider prefixes belong to the one legacy compatibility seam")
        self.assertEqual(hits, [], "ordinary pass-through must not filter by provider prefixes (FR-005)")

    def test_generic_account_login_wording_is_cloud_shift_only(self):
        hits = []
        scanned = list(self._production()) + list(self._documented())
        for rel, path in scanned:
            for n, fn, line in self._python_lines(path) if path.endswith(".py") else (
                    (n, None, line) for n, line in self._lines(path)):
                if not self.GENERIC_SIGNIN.search(line):
                    continue
                if rel == "core/cloud.py" and fn in self.CLOUD_ACCOUNT_FUNCTIONS:
                    continue
                hits.append("%s:%d: %s" % (rel, n, line.strip()))
        self.assertEqual(hits, [], "sign-in/account-login wording is account-only Cloud Shift guidance (FR-004)")

    def test_ordinary_copy_uses_configured_connection_and_conditional_usage(self):
        def text(rel):
            with open(os.path.join(self.ROOT, *rel.split("/")), encoding="utf-8") as fh:
                return fh.read()

        readme, setup, product = text("README.md"), text("SETUP.md"), text("PRODUCT.md")
        onboard, app, panel = text("core/onboard.py"), text("core/panel/app.js"), text("core/panel.py")
        for rel, body in (("README.md", readme), ("SETUP.md", setup), ("PRODUCT.md", product),
                          ("core/onboard.py", onboard), ("core/panel/app.js", app)):
            self.assertIn("configured connection", body.lower(), rel)
        self.assertIn("limits when Claude reports them", readme)
        self.assertIn("Limits are the ones Claude reports", app)
        self.assertIn("when Claude reports usage is high", app)

        # `subscription` is an old persisted compatibility value, not evidence about the live connection.
        self.assertIn('reg.get("auth", "subscription")', panel)
        self.assertNotRegex(app, r"auth\s*={2,3}\s*['\"]subscription['\"]")
        self.assertIn("s.auth === 'api_key' ? 'your legacy Anthropic API key' : \"Claude's configured connection\"", app)

        # Provider/account-specific words stay at their actual boundaries: legacy key or Cloud Shift.
        cost = readme.split("## What it costs", 1)[1].split("## Commands", 1)[0]
        self.assertIn("own Anthropic API key", cost)
        self.assertIn("Cloud Shift is separate and optional", cost)
        self.assertNotRegex(onboard, r"(?i)anthropic|subscription|claude account|api key")

    def test_brain_and_hands_are_model_roles_not_connection_routing(self):
        with open(os.path.join(self.ROOT, "core", "engine.py"), encoding="utf-8") as fh:
            source = fh.read()
        match = re.search(r"^def pick_model\(.*?(?=^def )", source, re.M | re.S)
        self.assertIsNotNone(match)
        body = match.group(0)
        self.assertIn('emp.get("brain")', body)
        self.assertIn('emp.get("model", "sonnet")', body)
        self.assertNotRegex(body, r"(?i)provider|connection|anthropic|api.key|launch_policy|setting.sources")

    def test_no_provider_integration_surface_was_added(self):
        self.assertEqual(sorted(p for p in os.listdir(self.ROOT)
                                if p in ("requirements.txt", "pyproject.toml", "Pipfile", "setup.py",
                                         "package.json", "package-lock.json")), [])
        hits = []
        for rel, path in self._production():
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            if self.PROVIDER_IMPORTS.search(text):
                hits.append(rel + ": provider/inference SDK import")
            if self.ENDPOINT_FIELD.search(text):
                hits.append(rel + ": endpoint configuration field")
            name = os.path.basename(rel)
            if re.search(r"provider|relay|inference|credential|migration", name, re.I):
                hits.append(rel + ": provider-shaped module")
        for dirpath, dirnames, filenames in os.walk(self.ROOT):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]
            for name in dirnames + filenames:
                if re.search(r"migration", name, re.I):
                    hits.append(os.path.relpath(os.path.join(dirpath, name), self.ROOT).replace(os.sep, "/"))
        self.assertEqual(hits, [], "no provider schema/module/endpoint/credential/relay/inference/migration (FR-010)")


import urllib.parse  # noqa: E402


class Brain(unittest.TestCase):
    """0.9: a brain and hands, and one running conversation per crew member."""

    def setUp(self):
        fresh_team()
        self._usage = engine.usage
        engine.usage = lambda: {}

    def tearDown(self):
        engine.usage = self._usage

    def test_brain_thinks_hands_work(self):
        hire.hire("Tess", "Research", supervisor="Alex")
        emp = engine.employee("tess")
        for job in ("chat", "standup", "initiative", "eod", "review", "catchup", "first_day"):
            self.assertEqual(engine.pick_model(emp, job), "opus", job)
        for job in ("followup", "brief", "scout", "evals", "bus"):
            self.assertEqual(engine.pick_model(emp, job), "sonnet", job)
        hire.set_field("tess", "brain", "sonnet")
        hire.set_field("tess", "model", "haiku")
        emp = engine.employee("tess")
        self.assertEqual((engine.pick_model(emp, "standup"), engine.pick_model(emp, "followup")), ("sonnet", "haiku"))
        with self.assertRaises(hire.HireError):
            hire.set_field("tess", "brain", "gpt-5")
        engine.usage = lambda: {"five_hour": 85}
        self.assertEqual(engine.pick_model(emp, "standup"), "haiku")   # the plan is nearly used up: both go light

    def test_conversation_runs_on_until_heavy(self):
        hire.hire("Tess", "Research", supervisor="Alex")
        ws = engine.employee("tess")["workspace"]
        sid = "11111111-2222-3333-4444-555555555555"
        folder = os.path.join(os.path.expanduser("~/.claude/projects"), re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(ws)))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, sid + ".jsonl")

        def transcript(ctx):
            with open(path, "w") as fh:
                fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")
                fh.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [], "usage": {
                    "input_tokens": 10, "cache_read_input_tokens": ctx - 20, "cache_creation_input_tokens": 10}}}) + "\n")
        try:
            self.assertFalse(engine.fresh_start({}, ws))                                    # nothing to resume
            s = {engine.SESSION: sid, engine.SESSION + "_day": "2026-11-06"}
            self.assertFalse(engine.fresh_start(s, ws, today="2026-11-07"))                 # no transcript yet: resume
            transcript(30_000)
            self.assertFalse(engine.fresh_start(s, ws, today="2026-11-07"))                 # light: runs on across days
            transcript(90_000)
            self.assertFalse(engine.fresh_start(s, ws, today="2026-11-06"))                 # heavy, same day: runs on
            self.assertTrue(engine.fresh_start(s, ws, today="2026-11-07"))                  # heavy, new day: fresh
            transcript(170_000)
            self.assertTrue(engine.fresh_start(s, ws, today="2026-11-06"))                  # near the limit: fresh now
            self.assertEqual(engine.context_tokens(ws, sid), 170_000)
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_upgrade_turns_the_supervisor_chat_into_the_conversation(self):
        hire.hire("Tess", "Research", supervisor="Alex")
        ws = engine.employee("tess")["workspace"]
        os.makedirs(os.path.join(ws, "state"), exist_ok=True)
        with open(os.path.join(ws, "state", "sessions.json"), "w") as fh:
            json.dump({"terminal": "t-1", "panel:alex": "p-1"}, fh)
        reg = engine.registry()
        reg["employees"]["tess"].pop("brain_v1", None)
        engine.save_registry(reg)
        hire.upgrade_workspace("tess")
        with open(os.path.join(ws, "state", "sessions.json")) as fh:
            self.assertEqual(json.load(fh)[engine.SESSION], "p-1")
        self.assertTrue(engine.registry()["employees"]["tess"]["brain_v1"])


FAKE_TWICE = r'''#!/usr/bin/env python3
import json, sys
sys.stdin.read()
def out(d):
    print(json.dumps(d), flush=True)
out({"type": "system", "subtype": "init"})
out({"type": "assistant", "message": {"stop_reason": "tool_use", "content": [{"type": "text", "text": "Checking the render first."},
     {"type": "tool_use", "name": "Bash", "input": {"command": "python3 WS/tools/render.py"}}]}})
out({"type": "user", "message": {"content": [{"type": "tool_result", "content": "started in the background"}]}})
out({"type": "assistant", "message": {"stop_reason": "end_turn", "content": [{"type": "text", "text": "Subs 140 (+6). Today: the brake-fade Short, then the 21:00 slot."}]}})
out({"type": "user", "message": {"content": "<task-notification>render done</task-notification>"}})
out({"type": "assistant", "message": {"stop_reason": "end_turn", "content": [{"type": "text", "text": "LAST"}]}})
out({"type": "result", "subtype": "success", "is_error": False, "result": "LAST", "num_turns": 3, "total_cost_usd": 0.01})
'''


class Spoken(unittest.TestCase):
    """A run that ends more than one turn (a background job woke it again) delivers everything it said."""

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.emp = engine.employee("tess")
        self.real = engine.resolve_claude

    def tearDown(self):
        engine.resolve_claude = self.real

    def fake(self, last):
        p = os.path.join(TMP, "fake-claude-twice")
        with open(p, "w") as fh:
            fh.write(FAKE_TWICE.replace("WS", self.emp["workspace"]).replace("LAST", last))
        os.chmod(p, 0o755)
        engine.resolve_claude = lambda: p

    @POSIX_FAKE_RUN
    def test_the_standup_is_not_lost_behind_the_render_update(self):
        self.fake("The render passed QC; uploading next.")
        res = engine.run(self.emp, "standup", job="standup")
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["text"], "Subs 140 (+6). Today: the brake-fade Short, then the 21:00 slot.\n\nThe render passed QC; uploading next.")
        self.assertEqual([s["text"] for s in res["steps"]], ["Running my tool tools/render.py"])   # narration isn't a step

    @POSIX_FAKE_RUN
    def test_a_silent_second_turn_keeps_the_first(self):
        self.fake("SILENT")
        res = engine.run(self.emp, "standup", job="standup")
        self.assertEqual(res["text"], "Subs 140 (+6). Today: the brake-fade Short, then the 21:00 slot.")


FAKE_ARGS = r"""#!/usr/bin/env python3
import json, os, sys, time
sys.stdin.read()
time.sleep(SLEEP)
with open(os.path.join("WS", "state", "argv.json"), "w") as fh:
    json.dump(sys.argv[1:], fh)
print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "Done.", "num_turns": 1, "total_cost_usd": 0.001}), flush=True)
"""


class Window(unittest.TestCase):
    """0.10: the owner's window on a crew member's conversation, and the inbox that reaches them."""

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.emp = engine.employee("tess")
        self.ws = self.emp["workspace"]
        self.real, self.real_usage = engine.resolve_claude, engine.usage
        engine.usage = lambda: {}

    def tearDown(self):
        engine.resolve_claude, engine.usage = self.real, self.real_usage

    def fake(self, sleep=0):
        p = os.path.join(TMP, "fake-claude-args")
        with open(p, "w") as fh:
            fh.write(FAKE_ARGS.replace("WS", self.ws).replace("SLEEP", str(sleep)))
        os.chmod(p, 0o755)
        engine.resolve_claude = lambda: p

    def argv(self):
        with open(os.path.join(self.ws, "state", "argv.json")) as fh:
            return json.load(fh)

    def test_chat_window_is_the_same_conversation(self):
        w = engine.chat_window(self.emp)                                   # nothing yet: a new conversation, oriented
        self.assertTrue(w["new"])
        self.assertEqual(w["cmd"][w["cmd"].index("--session-id") + 1], w["sid"])
        self.assertTrue(w["cmd"][-1].startswith("[New conversation."))
        self.assertNotIn("-p", w["cmd"])
        self.assertEqual(w["cwd"], self.ws)
        engine.remember_session(self.ws, engine.SESSION, w["sid"])
        w2 = engine.chat_window(self.emp)                                  # next time: the same session, resumed
        self.assertFalse(w2["new"])
        self.assertEqual(w2["cmd"][-2:], ["--resume", w["sid"]])
        self.assertEqual(engine.main_session(self.ws), w["sid"])

    @POSIX_FAKE_RUN
    def test_runs_wait_while_the_owner_is_in_the_window(self):
        self.fake()
        engine.mark(self.ws, "chat", who="Alex")                           # the window is open (this process)
        self.assertEqual(engine.window_open(self.ws)["kind"], "terminal")
        threading.Timer(1.2, lambda: engine.unmark(self.ws, "chat")).start()
        t0 = time.time()
        res = engine.run(self.emp, "hi", job="brief")
        self.assertTrue(res["ok"], res)
        self.assertGreaterEqual(time.time() - t0, 1.0)                    # it waited for the window to close
        self.assertNotIn("--fork-session", self.argv())
        self.assertIsNone(engine.busy(self.ws))                            # the busy marker is gone after the run
        self.assertIsNone(engine.window_open(self.ws))

    @POSIX_FAKE_RUN
    def test_a_window_left_idle_stops_holding_the_routines(self):
        self.fake()
        sid = "22222222-3333-4444-5555-666666666666"
        engine.remember_session(self.ws, engine.SESSION, sid)
        folder = engine.transcripts(self.ws)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, sid + ".jsonl")
        try:
            with open(path, "w") as fh:
                fh.write("{}\n")
            old = time.time() - engine.WINDOW_IDLE - 60
            os.utime(path, (old, old))                                      # untouched for a while
            engine.mark(self.ws, "chat", who="Alex")
            self.assertFalse(engine.wait_for_window(self.ws))              # goes ahead at once
            res = engine.run(self.emp, "hi", job="brief")
            self.assertTrue(res["ok"], res)
            self.assertIn("--fork-session", self.argv())                   # on a copy: the owner's window keeps main
            self.assertEqual(engine.main_session(self.ws), sid)
        finally:
            engine.unmark(self.ws, "chat")
            os.remove(path)

    def test_a_dead_window_is_forgotten(self):
        p = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True)
        dead = int(p.stdout.strip())
        os.makedirs(os.path.join(self.ws, "state"), exist_ok=True)
        with open(os.path.join(self.ws, "state", "chat.json"), "w") as fh:
            json.dump({"pid": dead, "since": "x"}, fh)
        self.assertIsNone(engine.window_open(self.ws))
        self.assertFalse(os.path.exists(os.path.join(self.ws, "state", "chat.json")))

    @POSIX_FAKE_RUN
    def test_the_busy_marker_while_a_run_is_on(self):
        self.fake(sleep=1.5)
        seen = []
        threading.Timer(0.6, lambda: seen.append(engine.busy(self.ws))).start()
        res = engine.run(self.emp, "hi", job="brief")
        self.assertTrue(res["ok"], res)
        time.sleep(0.1)
        self.assertEqual(seen[0]["job"], "brief")
        self.assertEqual(seen[0]["pid"], os.getpid())
        self.assertIsNone(engine.busy(self.ws))

    def test_inbox_unread_and_seen(self):
        team.feed("tess", "Tess", "Alex", "Standup: 3 things.", "job")
        team.feed("tess", "Tess", "team", "For everyone.", "job")
        team.feed("owner", "Alex", "tess", "Thanks", "panel")             # the owner's own words aren't unread
        team.feed("tess", "Tess", "Omar", "Not for Alex.", "bus")
        rows = team.unread("Alex")
        self.assertEqual([r["body"] for r in rows], ["Standup: 3 things.", "For everyone."])
        self.assertEqual(len(team.unread("alex", "tess")), 2)
        team.mark_seen("Alex")
        self.assertEqual(team.unread("Alex"), [])
        team.feed("tess", "Tess", "Alex", "End of day: shipped.", "job")
        self.assertEqual([r["body"] for r in team.unread("Alex")], ["End of day: shipped."])


class DataRoot(unittest.TestCase):
    """T034: transcript, context and window discovery follow the exact effective Claude data root.
    An inherited CLAUDE_CONFIG_DIR is authoritative; ~/.claude is only the default. The path is
    never persisted or logged."""

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        self.emp = engine.employee("tess")
        self.ws = self.emp["workspace"]
        self.sid = "44444444-5555-6666-7777-888888888888"
        engine.remember_session(self.ws, engine.SESSION, self.sid)
        self.root = tempfile.mkdtemp(dir=TMP, prefix="claude-root-")
        self.real_env = os.environ.get("CLAUDE_CONFIG_DIR")

    def tearDown(self):
        if self.real_env is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = self.real_env
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def env(root):
        return {"CLAUDE_CONFIG_DIR": root}

    def write_transcript(self, root, ctx=170_000):
        folder = engine.transcripts(self.ws, self.env(root))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, self.sid + ".jsonl")
        with open(path, "w") as fh:
            fh.write(json.dumps({"type": "assistant", "message": {"usage": {
                "input_tokens": 10, "cache_read_input_tokens": ctx - 20,
                "cache_creation_input_tokens": 10}}}) + "\n")
        return path

    def test_default_data_root_is_home_claude(self):
        self.assertEqual(engine.claude_data_root({}), os.path.expanduser("~/.claude"))
        self.assertEqual(engine.transcripts(self.ws, {}),
                         os.path.join(os.path.expanduser("~/.claude"), "projects",
                                      re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(self.ws))))

    def test_custom_root_owns_transcript_context_and_windows(self):
        self.write_transcript(self.root)
        env = self.env(self.root)
        self.assertEqual(engine.context_tokens(self.ws, self.sid, env), 170_000)
        self.assertTrue(engine.fresh_start({engine.SESSION: self.sid, engine.SESSION + "_day": "2026-11-09"},
                                           self.ws, today="2026-11-10", env=env))
        self.assertLess(engine.window_idle(self.ws, env), 60)          # the transcript just written
        sessions = os.path.join(self.root, "sessions")
        os.makedirs(sessions, exist_ok=True)
        with open(os.path.join(sessions, "window.json"), "w") as fh:
            json.dump({"sessionId": self.sid, "pid": os.getpid(), "entrypoint": "claude"}, fh)
        self.assertEqual(engine.window_open(self.ws, env), {"since": "", "kind": "claude"})

        other = tempfile.mkdtemp(dir=TMP, prefix="claude-other-")
        try:                                                           # another data root sees none of it
            self.assertEqual(engine.context_tokens(self.ws, self.sid, self.env(other)), 0)
            self.assertIsNone(engine.window_open(self.ws, self.env(other)))
            self.assertEqual(engine.window_idle(self.ws, self.env(other)), 0)
        finally:
            shutil.rmtree(other, ignore_errors=True)

    def test_inherited_data_root_reaches_the_child_and_stays_out_of_state(self):
        os.environ["CLAUDE_CONFIG_DIR"] = self.root
        os.environ["CLAUDECODE"] = "1"                                # the recursion marker is the only removal
        self.addCleanup(os.environ.pop, "CLAUDECODE", None)
        env = engine.clean_env(self.emp)
        self.assertEqual(env.get("CLAUDE_CONFIG_DIR"), self.root)     # exact child environment keeps it
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual(engine.claude_data_root(env), self.root)
        self.assertEqual(engine.claude_data_root(), self.root)        # no-argument lookup is the same root
        for f in (os.path.join(TMP, "staff.json"), os.path.join(self.ws, "state", "sessions.json")):
            with open(f, encoding="utf-8") as fh:
                self.assertNotIn(self.root, fh.read(), f)             # the path is never persisted


class ScopedUnread(unittest.TestCase):
    """T035: an owner reading one employee's chat must not clear another employee's report, even
    when both reports share a timestamp and older global cursor state already exists."""

    TS = "2026-11-10 10:00:00"

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex")
        hire.hire("Omar", "Social", supervisor="Alex")

    def report(self, rid, emp, body):
        team.append(team.FEED, {"id": rid, "ts": self.TS, "from_id": emp,
                                "from_name": emp.capitalize(), "to_id": "Alex", "body": body, "channel": "job"})

    def bodies(self, *a):
        return [r["body"] for r in team.unread(*a)]

    def test_filtered_view_keeps_the_other_report_unread(self):
        self.report("tess00000001", "tess", "Tess report")
        self.report("omar00000001", "omar", "Omar report")
        self.assertEqual(self.bodies("Alex"), ["Tess report", "Omar report"])
        team.mark_seen("Alex", "tess")                                # the panel's employee chat
        self.assertEqual(self.bodies("Alex", "tess"), [])
        self.assertEqual(self.bodies("Alex"), ["Omar report"])        # not cleared by the filtered view
        team.mark_seen("Alex")                                        # the full room: global
        self.assertEqual(self.bodies("Alex"), [])

    def test_old_global_cursor_at_the_same_second_does_not_hide_new_reports(self):
        team.jsave(team.STATEF, {"seen:alex": self.TS, "seen_ids:alex": ["old000000001"]})
        self.report("tess00000002", "tess", "New Tess report")
        self.report("omar00000002", "omar", "New Omar report")
        self.assertEqual(self.bodies("Alex"), ["New Tess report", "New Omar report"])
        team.mark_seen("Alex", "omar")
        self.assertEqual(self.bodies("Alex"), ["New Tess report"])
        self.assertEqual(self.bodies("Alex", "omar"), [])


class ClaudeApp(unittest.TestCase):
    """0.11: a crew member's thinking routines run as the Claude app's scheduled tasks and report in its chat."""

    def setUp(self):
        fresh_team()
        hire.hire("Tess", "Research", supervisor="Alex", picked=["web", "standup", "eod", "review", "brief"])
        self.ws = engine.employee("tess")["workspace"]

    def test_cron_follows_the_owners_week(self):
        import claudeapp
        self.assertEqual(claudeapp.cron({"at": "09:00", "days": "work"}), "0 9 * * 1,2,3,4,5")
        self.assertEqual(claudeapp.cron({"at": "15:30", "days": "last_workday"}), "30 15 * * 5")
        self.assertEqual(claudeapp.cron({"at": "19:00", "days": "daily"}), "0 19 * * *")
        self.assertEqual(claudeapp.cron({"at": "10:00", "days": "Fri"}), "0 10 * * 5")
        reg = engine.registry()
        reg["workdays"] = ["Sun", "Mon", "Tue", "Wed", "Thu"]
        engine.save_registry(reg, "Sun–Thu")
        self.assertEqual(claudeapp.cron({"at": "09:00", "days": "work"}), "0 9 * * 0,1,2,3,4")
        self.assertEqual(claudeapp.cron({"at": "15:00", "days": "last_workday"}), "0 15 * * 4")
        reg["workdays"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        engine.save_registry(reg, "every day")
        self.assertEqual(claudeapp.cron({"at": "17:00", "days": "work"}), "0 17 * * *")

    def test_the_plan_has_the_thinking_routines_and_how_they_report(self):
        import claudeapp
        p = claudeapp.write_plan("tess")
        jobs = [t["job"] for t in p["tasks"]]
        self.assertEqual(sorted(jobs), ["eod", "review", "standup"])          # not the brief: it stays in the service
        st = next(t for t in p["tasks"] if t["job"] == "standup")
        self.assertEqual((st["task_id"], st["title"], st["cron"]), ("tess-standup", "Tess · Standup", "0 9 * * 1,2,3,4,5"))
        self.assertIn("alarm", st["prompt"])                                   # the run only wakes the chat…
        self.assertIn("state/claude_app.json", st["prompt"])
        self.assertIn("SendMessage", st["prompt"])
        self.assertIn(st["message"], st["prompt"])
        self.assertIn(os.path.join(engine.CORE, "jobs", "standup.md"), st["message"])   # …which does the standup itself
        self.assertIn("for Alex", st["message"])
        self.assertNotIn("{", st["prompt"])
        with open(os.path.join(self.ws, "state", "claude_app_plan.json")) as fh:
            self.assertEqual(json.load(fh)["version"], p["version"])
        self.assertEqual(claudeapp.write_plan("tess")["version"], p["version"])  # same plan, same version

    def test_routines_in_the_app_are_left_to_the_app(self):
        import claudeapp
        self.assertEqual((claudeapp.owned("tess"), claudeapp.chat_link("tess")), (set(), None))
        p = claudeapp.write_plan("tess")
        sid = "local_12345678-1234-1234-1234-123456789abc"
        with open(os.path.join(self.ws, "state", "claude_app.json"), "w") as fh:
            json.dump({"chat": sid, "routines": ["standup", "eod", "brief"], "plan": p["version"]}, fh)
        self.assertEqual(claudeapp.owned("tess"), {"standup", "eod"})          # only thinking routines move
        self.assertEqual(claudeapp.chat_link("tess"), "claude://claude.ai/epitaxy/" + sid)
        self.assertFalse(claudeapp.stale("tess"))
        reg = engine.registry()
        reg["workdays"] = ["Sun", "Mon", "Tue", "Wed", "Thu"]
        engine.save_registry(reg, "Sun–Thu")
        claudeapp.write_plan("tess")
        self.assertTrue(claudeapp.stale("tess"))                               # times changed: the chat updates its tasks
        with open(os.path.join(self.ws, "state", "claude_app.json"), "w") as fh:
            json.dump({"chat": "../../somewhere", "routines": ["standup"]}, fh)
        self.assertEqual(claudeapp.owned("tess"), set())                       # not a chat id: ignored

    def test_the_service_skips_what_the_app_runs(self):
        import datetime as dt
        import staffd
        import awake
        sid = "local_12345678-1234-1234-1234-123456789abc"
        with open(os.path.join(self.ws, "state", "claude_app.json"), "w") as fh:
            json.dump({"chat": sid, "routines": ["standup", "eod", "review"]}, fh)
        started = []
        real = (awake.settled, staffd.run_async, staffd.dt)

        class Now(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return dt.datetime(2026, 11, 9, 9, 1)                         # Monday 09:01: brief and standup are due

        class D:
            datetime, timedelta = Now, dt.timedelta
        awake.settled = lambda: True
        staffd.run_async = lambda k, prompt, job, *a, **kw: started.append(job)
        staffd.dt = D
        try:
            with open(os.path.join(self.ws, "state", "schedule.json"), "w") as fh:
                json.dump({"brief": "2026-11-08", "standup": "2026-11-08"}, fh)
            staffd.tick_jobs()
        finally:
            awake.settled, staffd.run_async, staffd.dt = real
        self.assertIn("brief", started)
        self.assertNotIn("standup", started)


class Desk(unittest.TestCase):
    """0.12: Orbit's own chat in the Claude app: hire, check and change the crew by talking."""

    def setUp(self):
        fresh_team()
        import desk
        self.desk = desk
        self.sent = []
        self.real_order = desk.order
        desk.order = lambda kind, payload: (self.sent.append((kind, payload)) or
                                            ("Hire Sara (Market researcher): Hired: handle /sara" if kind == "hire" else "ok"))

    def tearDown(self):
        self.desk.order = self.real_order

    def test_the_desk_folder_and_its_locks(self):
        d = self.desk.ensure()
        self.assertEqual(d, os.path.join(TMP, "desk"))
        self.assertNotIn(d, [os.path.join(TMP, "employees", x) for x in os.listdir(os.path.join(TMP, "employees"))]
                         if os.path.isdir(os.path.join(TMP, "employees")) else [])
        with open(os.path.join(d, "CLAUDE.md")) as fh:
            text = fh.read()
        self.assertIn(os.path.join(engine.KIT, "orbit"), text)
        self.assertIn("Alex", text)
        self.assertNotIn("{orbit}", text)
        with open(os.path.join(d, ".claude", "settings.local.json")) as fh:
            perms = json.load(fh)["permissions"]
        def rule(kind, p, suffix=""):
            p = os.path.realpath(p)
            p = "//" + p.replace("\\", "/") if osinfo.KIND == "windows" else "/" + p
            return "%s(%s%s)" % (kind, p, suffix)
        self.assertIn(rule("Read", engine.SECRETS, "/**"), perms["deny"])
        self.assertIn(rule("Edit", engine.REGISTRY), perms["deny"])
        self.assertFalse(os.path.exists(os.path.join(TMP, "CLAUDE.md")))      # not above the crew's folders
        url, new = self.desk.link()
        self.assertTrue(new and url.startswith("claude://code/new?folder="))
        with open(self.desk.STATE, "w") as fh:
            json.dump({"chat": "local_12345678-1234-1234-1234-123456789abc"}, fh)
        self.assertEqual(self.desk.link(), ("claude://claude.ai/epitaxy/local_12345678-1234-1234-1234-123456789abc", False))

    def test_the_guide_is_the_panels_interview(self):
        import onboard
        g = self.desk.guide()
        for part in (onboard.ASK_GUIDE, onboard.CARD_GUIDE, onboard.POLICY, "- jobs: ", "- web: ", "orbit hire --card"):
            self.assertIn(part, g)

    def test_hire_from_a_card_goes_through_the_service(self):
        out = self.desk.hire({"name": "Sara", "role": "Market researcher", "job": "researcher",
                              "card": {"role": "Market researcher", "scope": "Prices in Cairo", "first_task": "Three rivals",
                                       "routines": {"standup": True, "eod": True, "brief": False}, "abilities": ["web", "bogus"],
                                       "budget": "huge", "model": "opus", "access": [{"kind": "sign_in", "what": "x", "why": "y"},
                                                                                    {"kind": "pay", "what": "no", "why": "no"}]},
                              "browser": {"sites": ["YouTube.com"], "approval": "sometimes"}})
        kinds = [k for k, _ in self.sent]
        self.assertEqual(kinds, ["hire", "set_autonomy", "set_browser"])
        h = self.sent[0][1]
        self.assertEqual((h["name"], h["supervisor"], h["model"]), ("Sara", "Alex", "opus"))
        self.assertEqual(h["abilities"], ["telegram", "team_room", "web", "standup", "eod"])   # unknown ability dropped
        self.assertEqual((h["card"]["budget"], h["card"]["weekly_tokens"]), ("regular", 3_000_000))
        self.assertEqual([a["kind"] for a in h["card"]["access"]], ["sign_in"])
        self.assertEqual(self.sent[2][1], {"employee_id": "sara", "sites": ["youtube.com"], "approval": "each"})
        self.assertIn("handle sara", out)
        with self.assertRaises(ValueError):
            self.desk.hire({"card": {}})



FAKE_CHROME = '''#!%s
"""A stand-in for Chrome in tests: serves the DevTools endpoints browser.py uses, on the port it was given."""
import http.server, json, os, socketserver, sys, uuid
BID = "ws://127.0.0.1/devtools/browser/" + str(uuid.uuid4())
args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
prof, port = args["--user-data-dir"], int(args["--remote-debugging-port"])


class H(http.server.BaseHTTPRequestHandler):
    def reply(self, d):
        b = json.dumps(d).encode()
        self.send_response(200)
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self.reply({"Browser": "FakeChrome/1", "webSocketDebuggerUrl": BID} if self.path.startswith("/json/version") else {})

    def do_PUT(self):
        with open(os.path.join(prof, "opened.txt"), "a") as fh:
            fh.write(self.path + "\\n")
        self.reply({"id": "tab1"})

    def log_message(self, *a):
        pass


socketserver.TCPServer.allow_reuse_address = True       # not HTTPServer: its reverse DNS lookup can take 30 s
socketserver.TCPServer(("127.0.0.1", port), H).serve_forever()
''' % sys.executable


class OwnBrowser(unittest.TestCase):
    """Each crew member browses in a Chrome window of its own; the owner's Chrome is never theirs."""

    def setUp(self):
        fresh_team()
        import browser
        self.browser = browser
        self.ready, self.installed = browser.ready, browser.installed
        hire.hire("Tess", "Research", supervisor="Alex", picked=["web"])
        hire.hire("Omar", "Social", supervisor="Alex")

    def tearDown(self):
        self.browser.ready, self.browser.installed = self.ready, self.installed
        os.environ.pop("ORBIT_CHROME", None)
        for eid in ("tess", "omar"):
            try:
                self.browser.close(eid)
            except Exception:  # noqa: BLE001
                pass

    def test_everyone_has_one_and_it_cant_be_ticked_off(self):
        self.assertIn("own_browser", abilities.effective("tess"))
        hire.set_abilities("tess", ["web"])
        self.assertIn("own_browser", abilities.effective("tess"))
        allow, block = abilities.tools("tess")
        self.assertIn("mcp__orbit-browser", allow)
        self.assertNotIn("mcp__claude-in-chrome", allow + block)
        self.assertNotIn("--chrome", engine.command(engine.employee("tess"), "sonnet"))

    def test_it_reaches_their_runs_and_chats_when_this_computer_can_run_it(self):
        self.browser.ready = lambda: (False, "Node.js 20 or newer is missing")
        self.assertNotIn("orbit-browser", engine.mcp_servers(engine.employee("tess")))
        self.browser.ready = lambda: (True, "")
        self.browser.installed = lambda: self.browser.PKG_VERSION
        cmd = engine.command(engine.employee("tess"), "sonnet")
        with open(cmd[cmd.index("--mcp-config") + 1]) as fh:
            srv = json.load(fh)["mcpServers"]["orbit-browser"]
        self.assertTrue(srv["args"][0].endswith("browser_mcp.py") and srv["args"][1] == "tess")
        self.assertEqual(srv["env"]["STAFFROOM_HOME"], engine.HOME)
        ws = engine.employee("tess")["workspace"]
        os.makedirs(os.path.join(ws, ".claude"), exist_ok=True)
        with open(os.path.join(ws, ".claude", "settings.local.json"), "w") as fh:
            json.dump({"enabledPlugins": {"staff-guard@orbit": True}}, fh)
        with open(os.path.join(engine.GUARD, ".claude-plugin", "plugin.json")) as fh, \
                open(os.path.join(ws, ".claude", "orbit-guard.version"), "w") as out:
            out.write(json.load(fh)["version"])
        real_gate = engine.require_employee_launch
        engine.require_employee_launch = lambda emp, surface: None   # native-Windows Desktop gate: covered elsewhere
        self.addCleanup(setattr, engine, "require_employee_launch", real_gate)
        engine.claude_session("tess")
        with open(os.path.join(ws, ".mcp.json")) as fh:
            self.assertIn("orbit-browser", json.load(fh)["mcpServers"])
        with open(os.path.join(ws, ".claude", "settings.local.json")) as fh:
            d = json.load(fh)
        self.assertIn("orbit-browser", d["enabledMcpjsonServers"])
        self.assertIn("mcp__orbit-browser", d["permissions"]["allow"])

    def test_each_has_its_own_port_and_keeps_it(self):
        import socket
        a, b = self.browser.port("tess"), self.browser.port("omar")
        self.assertNotEqual(a, b)
        self.assertIn(a, self.browser.PORTS)
        self.assertEqual(self.browser.port("tess"), a)
        with socket.socket() as s:                              # something else took it while its Chrome was closed
            s.bind(("127.0.0.1", a))
            s.listen(1)
            c = self.browser.port("tess")
            self.assertNotIn(c, (a, b))

    @POSIX_FAKE_RUN                                   # the fake is a shebang script: POSIX jobs only
    def test_its_chrome_starts_once_opens_tabs_and_closes_by_its_pid(self):
        fake = os.path.join(TMP, "fake-chrome")
        with open(fake, "w") as fh:
            fh.write(FAKE_CHROME)
        os.chmod(fake, 0o755)
        os.environ["ORBIT_CHROME"] = fake
        p = self.browser.ensure("tess")
        self.assertTrue(self.browser.running("tess"))
        pid = self.browser._state("tess")["pid"]
        self.assertEqual(self.browser.ensure("tess"), p)          # the same Chrome, not a second one
        self.assertEqual(self.browser._state("tess")["pid"], pid)
        with open(os.path.join(self.browser.profile("tess"), "Local State")) as fh:
            self.assertEqual(json.load(fh)["profile"]["info_cache"]["Default"]["name"], "Tess (Orbit)")
        self.browser.open_tab("tess", "studio.youtube.com")
        with open(os.path.join(self.browser.profile("tess"), "opened.txt")) as fh:
            self.assertIn("https://studio.youtube.com", fh.read())
        self.assertTrue(self.browser.close("tess"))
        self.assertFalse(self.browser.running("tess"))
        self.assertFalse(self.browser.close("tess"))
        self.browser.set_private("tess", True, "Alex")             # private: a fresh profile every start
        self.browser.ensure("tess")
        self.assertFalse(os.path.exists(os.path.join(self.browser.profile("tess"), "opened.txt")))

    def test_the_connector_opens_chrome_only_for_a_tool_call(self):
        sys.path.insert(0, os.path.join(KIT, "core"))
        import browser_mcp
        msgs = [json.dumps(m).encode() + b"\n" for m in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "browser_navigate"}})]
        sent, wrote, ensured = [], [], []
        browser_mcp.relay(iter(msgs), lambda l: sent.append(l) or True, lambda: ensured.append(1), wrote.append, "tess")
        self.assertEqual((sent, ensured, wrote), (msgs, [1], []))

        def broken():
            raise self.browser.BrowserError("there's no Chrome on this computer")
        sent, wrote = [], []
        browser_mcp.relay(iter(msgs), lambda l: sent.append(l) or True, broken, wrote.append, "tess")
        self.assertEqual(sent, msgs[:2])                            # the call isn't passed on...
        r = json.loads(wrote[0])                                    # ...it's answered with the reason
        self.assertEqual((r["id"], r["result"]["isError"]), (3, True))
        self.assertIn("orbit browser tess", r["result"]["content"][0]["text"])

    def test_an_old_grant_is_rewritten_in_todays_words(self):
        hire.set_browser("omar", ["youtube.com"], "none", "Alex")
        path = os.path.join(engine.employee("omar")["workspace"], "CLAUDE.md")
        with open(path) as fh:
            md = fh.read()
        old = md[:md.index("\n## Granted by your owner: posting for them\n")] + (
            "\n## Granted by your owner: acting in their browser\n- Use the Claude in Chrome tools, in the owner's own Chrome.\n")
        with open(path, "w") as fh:
            fh.write(old)
        self.assertTrue(hire.refresh_browser_md("omar"))
        with open(path) as fh:
            md = fh.read()
        self.assertNotIn("Claude in Chrome", md)
        self.assertEqual(md.count("Granted by your owner: posting for them"), 1)
        self.assertFalse(hire.refresh_browser_md("omar"))          # already current: nothing to write

    def test_the_owner_turns_the_sandbox_on_and_off(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("orbit_cli_sb", os.path.join(KIT, "orbit"))
        spec = importlib.util.spec_from_loader("orbit_cli_sb", loader)
        cli = importlib.util.module_from_spec(spec)
        loader.exec_module(cli)
        real = engine.claude_session
        engine.claude_session = lambda eid: None                    # the Claude chats are tested elsewhere
        try:
            cli.say = lambda *a: None
            cli.yes = lambda *a, **k: True                          # the Windows MXC-off confirmation
            cli.sandbox_cmd("on")
            self.assertTrue(engine.sandboxed())
            s = json.loads(engine.settings_json(engine.employee("tess"), []))
            self.assertTrue(s["sandbox"]["enabled"])
            cli.sandbox_cmd("off")
            self.assertFalse(engine.sandboxed())
            self.assertIs(engine.registry().get("sandbox"), False)  # explicit opt-out, no longer the old pop
            s = json.loads(engine.settings_json(engine.employee("tess"), []))
            self.assertEqual(s, {"enabledPlugins": {}, "sandbox": {"enabled": False}})
            self.assertNotIn("hooks", s)                            # on Windows too: no MXC hook after the opt-out
        finally:
            engine.claude_session = real

if __name__ == "__main__":
    unittest.main()
