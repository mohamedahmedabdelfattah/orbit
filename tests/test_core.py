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
import threading
import unittest
import urllib.error
import urllib.request

TMP = tempfile.mkdtemp(prefix="staffroom-test-")
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
        sb = s["sandbox"]
        self.assertTrue(sb["enabled"] and not sb["allowUnsandboxedCommands"] and sb["failIfUnavailable"])
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
        self.dir = tempfile.mkdtemp(prefix="fake-claude-")
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
        self.dir = tempfile.mkdtemp(prefix="fake-claude-")
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
        self.dir = tempfile.mkdtemp(prefix="fake-claude-")   # outside the Orbit home: the recorder
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
        self.dir = tempfile.mkdtemp(prefix="fake-claude-")   # outside the Orbit home (the recorder
        engine.resolve_claude = lambda: fake_claude.install(self.dir, **cfg)  # writes sentinels by design)

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
            self.assertEqual((a[0], k["session_key"], k["deliver_to"], k["channel"], k["said"]), ("tess", "slack:U1", ["slack:D1"], "slack", "what's new?"))
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
            self.assertEqual((a[0], k["session_key"], k["deliver_to"], k["channel"]), ("tess", "group", ["slack:C1"], "group"))
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
        self.assertTrue(os.path.islink(os.path.join(root, "skills", "price-check")))
        self.assertTrue(os.path.islink(os.path.join(root, "skills", "research-playbook")))
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
        tool = os.path.join(KIT, "bin", "staff-skill")
        env = {**os.environ, "STAFF_EMPLOYEE": "tess", "STAFF_WORKSPACE": engine.employee("tess")["workspace"], "STAFFROOM_HOME": TMP}
        r = subprocess.run([tool, "new", "feed-finder", "--description", "Finding a site's hidden JSON feed; use when a page is slow to scrape."],
                           env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Created skills/feed-finder/SKILL.md", r.stdout)
        r = subprocess.run([tool, "check", "feed-finder"], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("step 1 is empty", r.stderr)
        r = subprocess.run([tool, "list"], env=env, capture_output=True, text=True)
        self.assertIn("feed-finder", r.stdout)
        self.assertIn("not loading", r.stdout)
        hire.set_abilities("tess", [a for a in abilities.chosen("tess") if a != "learn"], "test")
        r = subprocess.run([tool, "new", "another-one", "--description", "Something else entirely, used whenever."], env=env, capture_output=True, text=True)
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
    SITE = re.compile(r"(?:=\s*\(?(?:engine\.)?resolve_claude\(\)|\[(?:engine\.)?resolve_claude\(\),"
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
    DOC_ROOTS = ("README.md", "SETUP.md", "install.sh", "setup-windows.ps1", "docs", "templates",
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
        for name in ("README.md", "SETUP.md", "install.sh", "setup-windows.ps1"):
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

if __name__ == "__main__":
    unittest.main()
