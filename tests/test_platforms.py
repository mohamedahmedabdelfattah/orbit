"""Windows (WSL) and Linux: what differs from a Mac, tested on any computer by pretending.
Never records real audio or calls Claude.  python3 -m unittest tests.test_platforms
"""
from __future__ import annotations

import io
import re
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from types import SimpleNamespace
from unittest import mock

TMP = tempfile.mkdtemp(prefix="orbit-platforms-test-")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cleanup  # noqa: E402
_cleanup.on_exit(TMP)                      # nothing left behind: temp folders, transcripts


def load_tests(loader, tests, pattern):
    return _cleanup.home_suite(tests, TMP)
os.environ["STAFFROOM_HOME"] = TMP
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "core"))
sys.path.insert(0, os.path.join(KIT, "core", "tools"))
_cleanup.home(TMP)                          # now too: named-class loads skip load_tests

import calls  # noqa: E402
import engine  # noqa: E402
import osinfo  # noqa: E402

sys.path.insert(0, os.path.join(KIT, "tests"))
import fake_claude  # noqa: E402

_orbit_cli = None
LISTEN = os.path.join(KIT, "core", "tools", "call_listen.py")


def orbit_cli():
    """orbit has no .py extension: load it by source path, exactly like the CI failure steps."""
    global _orbit_cli
    if _orbit_cli is None:
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("orbit_cli", os.path.join(KIT, "orbit"))
        spec = importlib.util.spec_from_loader("orbit_cli", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        _orbit_cli = mod
    return _orbit_cli

# A stand-in for the soundcard package: a speaker that plays a tone, a microphone, and (with FAKE_SILENT=1)
# a loopback that sends nothing, as a silent Windows loopback does.
FAKE_SOUNDCARD = '''
import os, time
import numpy as np
SILENT = os.environ.get("FAKE_SILENT") == "1"
class _Rec:
    def __init__(self, silent): self.silent = silent
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def record(self, numframes):
        time.sleep(numframes / 48000.0)
        if self.silent:
            return np.zeros((0, 2), dtype=np.float32)
        return np.full((numframes, 2), 0.25, dtype=np.float32)
class _Mic:
    def __init__(self, silent=False): self.silent = silent
    def recorder(self, samplerate, blocksize=None): return _Rec(self.silent)
class _Speaker:
    name = "Speakers"
def default_speaker(): return _Speaker()
def get_microphone(id, include_loopback=False): return _Mic(SILENT)
def default_microphone(): return _Mic()
'''


def fake_soundcard_dir():
    d = tempfile.mkdtemp(dir=TMP)
    with open(os.path.join(d, "soundcard.py"), "w") as fh:
        fh.write(FAKE_SOUNDCARD)
    return d


def wait_for(cond, secs=10):
    end = time.time() + secs
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.1)
    return False


def win_py(code, os_kind="windows"):
    """This Python pretending to be another computer (ORBIT_OS=windows): engine and osinfo are imported
    fresh in a subprocess, so kind-dependent module state is really that kind's."""
    return subprocess.run([sys.executable, "-c", code],
                          env=dict(os.environ, ORBIT_OS=os_kind, PYTHONPATH=os.path.join(KIT, "core")),
                          capture_output=True, text=True)


def module_available(name):
    import importlib.util
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


# The listener and the live-call path both use the real numpy + soundcard packages (the fake card
# itself imports numpy). Those are an optional install, so the host may not have them.
HAVE_AUDIO = module_available("numpy") and module_available("soundcard")
# POSIX-only fixtures: shell-script executables, `sh -n`, tesseract stand-ins, pwd/getuid. The same
# checks run in the macOS/Linux/WSL2 CI jobs; a native Windows host does not execute them.
POSIX_FIXTURE = unittest.skipUnless(os.name == "posix", "needs a POSIX shell and POSIX-only fixtures")


class Words(unittest.TestCase):
    def test_mac_words_stay_on_a_mac(self):
        old = osinfo.KIND
        try:
            osinfo.KIND = "mac"
            self.assertEqual(osinfo.local("transcribed on this Mac"), "transcribed on this Mac")
        finally:
            osinfo.KIND = old

    def test_windows_says_pc_and_leaves_product_names_alone(self):
        r = subprocess.run([sys.executable, "-c", "import osinfo; print(osinfo.DEVICE); print(osinfo.local("
                            "'on this Mac, your Mac, the Mac; a MacBook and Macintosh stay'))"],
                           env=dict(os.environ, ORBIT_OS="wsl", PYTHONPATH=os.path.join(KIT, "core")),
                           capture_output=True, text=True)
        dev, text = r.stdout.strip().splitlines()
        self.assertEqual(dev, "PC")
        self.assertEqual(text, "on this PC, your PC, the PC; a MacBook and Macintosh stay")

    def test_panel_has_no_fixed_mac_words(self):
        with open(os.path.join(KIT, "core", "panel", "app.js"), encoding="utf-8") as fh:
            js = fh.read()
        for phrase in ("this Mac", "on the Mac"):
            self.assertNotIn(phrase, js.replace("'Match the Mac'", ""))


class Listener(unittest.TestCase):
    """core/tools/call_listen.py, the listener Windows and Linux use, with a fake sound card."""

    def run_listener(self, silent=False, secs=1.6):
        d = tempfile.mkdtemp(dir=TMP)
        env = dict(os.environ, PYTHONPATH=fake_soundcard_dir(), FAKE_SILENT="1" if silent else "0")
        p = subprocess.Popen([sys.executable, LISTEN, d, "--max-min", "5"], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertTrue(wait_for(lambda: os.path.exists(os.path.join(d, "listener.pid"))), p.stderr.read() if p.poll() else "")
        self.assertTrue(wait_for(lambda: os.path.exists(os.path.join(d, "alive"))))
        time.sleep(secs)
        open(os.path.join(d, "stop"), "w").close()
        p.communicate(timeout=10)                            # drain and close both captured pipes
        return d, p

    @unittest.skipUnless(HAVE_AUDIO, "needs numpy and soundcard")
    def test_two_streams_at_16k_until_stop(self):
        d, p = self.run_listener()
        self.assertEqual(p.returncode, 0)
        for f in ("them.pcm", "you.pcm"):
            n = os.path.getsize(os.path.join(d, f)) // 4
            self.assertGreater(n, 16000 * 1.2, f)           # ~1.6 s+ at 16 kHz (48 kHz averaged 3:1)
            self.assertLess(n, 16000 * 4, f)
        self.assertFalse(os.path.exists(os.path.join(d, "listener.pid")))
        self.assertFalse(os.path.exists(os.path.join(d, "alive")))

    @unittest.skipUnless(HAVE_AUDIO, "needs numpy and soundcard")
    def test_silent_loopback_is_padded_so_times_line_up(self):
        d, p = self.run_listener(silent=True, secs=2.0)
        them = os.path.getsize(os.path.join(d, "them.pcm")) // 4
        you = os.path.getsize(os.path.join(d, "you.pcm")) // 4
        self.assertGreater(them, 16000 * 1.0)             # silence written, not nothing
        self.assertLess(abs(them - you), 16000)           # within a second of the microphone

    def test_missing_package_says_how_to_install(self):
        d = tempfile.mkdtemp(dir=TMP)
        empty = tempfile.mkdtemp(dir=TMP)
        with open(os.path.join(empty, "soundcard.py"), "w") as fh:
            fh.write("raise ImportError('No module named soundcard')\n")
        r = subprocess.run([sys.executable, LISTEN, d], env=dict(os.environ, PYTHONPATH=empty), capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        with open(os.path.join(d, "error.txt")) as fh:
            self.assertTrue(fh.read().startswith("NEEDS_SETUP"))


class LinuxCall(unittest.TestCase):
    """calls.py on Linux: starts the Python listener, transcribes, stops, hands over minutes."""

    def setUp(self):
        import hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        self.eid = hire.hire("Lina", "Call notes", "Minutes", supervisor="Alex", picked=["meetings"])
        self.saved = (osinfo.KIND, calls.ready, calls._whisper, calls.CHUNK_S, os.environ.get("PYTHONPATH"))
        osinfo.KIND = "linux"
        calls.ready = lambda: (True, "")
        calls._whisper = lambda a, prompt="": [(0, "Thirty one dollars a kilo.")] if len(a) else []
        calls.CHUNK_S = 1
        os.environ["PYTHONPATH"] = fake_soundcard_dir()

    def tearDown(self):
        osinfo.KIND, calls.ready, calls._whisper, calls.CHUNK_S, pp = self.saved
        if pp is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = pp
        for eid in list(calls.CALLS):
            calls.stop(eid)

    @unittest.skipUnless(HAVE_AUDIO, "needs numpy and soundcard")
    def test_start_listen_stop(self):
        ended = []
        st = calls.start(self.eid, "Alex", "Supplier", on_end=lambda eid, info: ended.append(info))
        self.assertEqual(st["employee"], self.eid)
        live = calls.CALLS[self.eid]
        self.assertIsNotNone(live.get("proc"))
        self.assertTrue(calls._listening(live))
        time.sleep(1.5)
        calls.stop(self.eid)
        self.assertTrue(wait_for(lambda: self.eid not in calls.CALLS, 15))
        self.assertEqual(live["proc"].poll(), 0)           # the listener ended cleanly
        self.assertTrue(ended)
        with open(live["transcript_abs"], encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("heard on this computer", body)
        self.assertIn("Them: Thirty one dollars a kilo.", body)
        self.assertFalse(os.path.exists(live["audio"]))      # raw audio deleted

    @unittest.skipUnless(HAVE_AUDIO, "needs numpy and soundcard")
    def test_listener_that_dies_ends_the_call(self):
        st = calls.start(self.eid, "Alex", "Short")
        live = calls.CALLS[self.eid]
        live["proc"].kill()
        self.assertTrue(wait_for(lambda: self.eid not in calls.CALLS, 15), st)


class Service(unittest.TestCase):
    def setUp(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("orbit_cli", os.path.join(KIT, "orbit"))
        spec = importlib.util.spec_from_loader("orbit_cli", loader)
        self.cli = importlib.util.module_from_spec(spec)
        loader.exec_module(self.cli)
        self.kind = osinfo.KIND

    def tearDown(self):
        osinfo.KIND = self.kind

    def test_linux_checks_name_the_sandbox_and_the_fix(self):
        osinfo.KIND = "linux"
        real = osinfo.which
        osinfo.which = lambda n: None if n in ("bwrap", "socat", "tesseract") else real(n)
        reg = engine.registry()
        try:
            self.assertFalse(any("sandbox" in r[1] for r in self.cli.platform_checks()))   # off: nothing to install
            engine.save_registry({**reg, "sandbox": True})
            rows = self.cli.platform_checks()
        finally:
            osinfo.which = real
            engine.save_registry(reg)
        sandbox = next(r for r in rows if "sandbox" in r[1])
        self.assertFalse(sandbox[0])
        self.assertTrue(sandbox[2])                           # must be fixed before setup goes on
        self.assertIn("setup-linux.sh", sandbox[1])
        ocr = next(r for r in rows if "tesseract" in r[1])
        self.assertFalse(ocr[2])                              # optional

    @POSIX_FIXTURE
    def test_windows_start_script(self):
        osinfo.KIND = "wsl"
        os.environ["WSL_DISTRO_NAME"] = "Ubuntu-24.04"
        try:
            ps = self.cli.wsl_script()
        finally:
            os.environ.pop("WSL_DISTRO_NAME", None)
        import pwd
        me = pwd.getpwuid(os.getuid()).pw_name
        self.assertIn('-d "Ubuntu-24.04" -u "%s" -e "/usr/bin/env" "STAFFROOM_HOME=%s"' % (me, engine.HOME), ps)
        self.assertIn("service-run", ps)
        self.assertIn("Invoke-CimMethod -ClassName Win32_Process -MethodName Create", ps)   # outside WSL's job
        self.assertIn("GetFolderPath('Startup')", ps)
        self.assertIn("'--headless wsl.exe '", ps)
        self.assertEqual(ps.count("$a = '"), 1)

    def test_stop_ends_the_background_service(self):
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        os.makedirs(os.path.dirname(self.cli.SERVICE_PID), exist_ok=True)
        with open(self.cli.SERVICE_PID, "w") as fh:
            fh.write(str(p.pid))
        self.assertEqual(self.cli.service_pid(), p.pid)
        self.cli.stop_service_run()
        p.wait(10)
        self.assertIsNone(self.cli.service_pid())


class NativeService(unittest.TestCase):
    """Native Windows service/doctor contracts use captured PowerShell and fake MXC results only."""

    def setUp(self):
        self.cli = orbit_cli()
        self.old_kind, self.old_registry = osinfo.KIND, engine.registry()
        osinfo.KIND = "windows"
        engine.save_registry({"team_name": "Test", "owners": {}, "employees": {},
                              "platform": {"sandbox_mode": "mxc", "decided_by": "owner",
                                           "decided_at": "2026-11-10", "mxc_unavailable_reason": None}})

    def tearDown(self):
        osinfo.KIND = self.old_kind
        engine.save_registry(self.old_registry)

    def test_scheduled_task_creation_is_exact_and_idempotent(self):
        scripts, said = [], []
        with mock.patch.object(self.cli, "service_pythonw", return_value=sys.executable), \
                mock.patch.object(self.cli, "win_ps", side_effect=lambda script: scripts.append(script) or SimpleNamespace(returncode=0)), \
                mock.patch.object(self.cli, "running", return_value=True), \
                mock.patch.object(self.cli, "say", side_effect=said.append):
            self.assertTrue(self.cli.start_windows())
            self.assertTrue(self.cli.start_windows())
        creates = [s for s in scripts if "Register-ScheduledTask" in s]
        starts = [s for s in scripts if "Start-ScheduledTask" in s]
        self.assertEqual(len(creates), 2)
        self.assertEqual(creates[0], creates[1])
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", creates[0])
        self.assertIn("New-ScheduledTaskSettingsSet -Hidden", creates[0])
        self.assertIn("-TaskName 'Orbit'", creates[0])
        self.assertIn("-Force", creates[0])
        self.assertEqual(starts, ["Start-ScheduledTask -TaskName 'Orbit'"] * 2)
        with open(os.path.join(engine.HOME, ".runtime", "orbit-service.cmd"), encoding="utf-8") as fh:
            service = fh.read()
        self.assertIn('set "STAFFROOM_HOME=%s"' % engine.HOME, service)
        self.assertIn('"%s" service-run' % os.path.join(engine.KIT, "orbit"), service)
        self.assertTrue(all("Running." in line for line in said))

    def test_native_doctor_names_both_mxc_fixes_without_wsl_commands(self):
        import mxc
        old_build = os.environ.get("ORBIT_WIN_BUILD")
        os.environ["ORBIT_WIN_BUILD"] = "10.0.26100"
        if old_build is None:
            self.addCleanup(os.environ.pop, "ORBIT_WIN_BUILD", None)
        else:
            self.addCleanup(os.environ.__setitem__, "ORBIT_WIN_BUILD", old_build)
        with mock.patch.object(self.cli, "service_pythonw", return_value=sys.executable), \
                mock.patch.object(osinfo, "which", side_effect=lambda name: name if name == "tesseract" else None), \
                mock.patch.object(mxc, "discover", return_value={"ok": True, "reason": ""}), \
                mock.patch.object(self.cli, "sandbox_probe", return_value={"verdict": "usable"}):
            rows = self.cli.windows_checks()
        self.assertTrue(all(ok for ok, _, must in rows if must), rows)
        self.assertFalse(any("setup-linux.sh" in message for _, message, _ in rows))

        with mock.patch.object(self.cli, "service_pythonw", return_value=sys.executable), \
                mock.patch.object(osinfo, "which", return_value=None), \
                mock.patch.object(mxc, "discover", return_value={"ok": False, "reason": "runtime missing"}):
            rows = self.cli.windows_checks()
        runtime = next(message for ok, message, must in rows if must and "MXC sandbox runtime" in message)
        self.assertIn("setup-windows.ps1", runtime)
        self.assertIn("orbit sandbox wsl2", runtime)
        self.assertNotIn("setup-linux.sh", runtime)

    def _fake_ps(self, scripts, register_rc=1, task_exists="no"):
        """win_ps that captures each script; the task's registration is denied, other calls succeed."""
        import types
        def fake(script):
            scripts.append(script)
            rc = register_rc if "Register-ScheduledTask" in script else 0
            return types.SimpleNamespace(returncode=rc, stdout=task_exists if "Get-ScheduledTask" in script else "",
                                         stderr="Access is denied" if rc else "")
        return fake

    def test_start_windows_falls_back_to_the_startup_shortcut_when_registration_is_denied(self):
        scripts, said = [], []
        with mock.patch.object(self.cli, "service_pythonw", return_value=sys.executable), \
                mock.patch.object(self.cli, "win_ps", side_effect=self._fake_ps(scripts)), \
                mock.patch.object(self.cli, "running", return_value=True), \
                mock.patch.object(self.cli, "say", side_effect=said.append):
            self.assertTrue(self.cli.start_windows())
        fallback = [s for s in scripts if "GetFolderPath('Startup')" in s]
        self.assertEqual(len(fallback), 1)
        self.assertIn("orbit-service.cmd", fallback[0])
        self.assertIn("Win32_Process", fallback[0])
        self.assertTrue(any("Startup folder" in line for line in said), said)

    def test_start_windows_keeps_an_existing_task_when_registration_is_denied(self):
        scripts, said = [], []
        with mock.patch.object(self.cli, "service_pythonw", return_value=sys.executable), \
                mock.patch.object(self.cli, "win_ps", side_effect=self._fake_ps(scripts, task_exists="yes")), \
                mock.patch.object(self.cli, "running", return_value=True), \
                mock.patch.object(self.cli, "say", side_effect=said.append):
            self.assertTrue(self.cli.start_windows())
        self.assertEqual([s for s in scripts if "GetFolderPath('Startup')" in s], [])
        self.assertTrue(any("existing one" in line for line in said), said)

    def test_stop_says_so_when_the_task_survives_the_unregister(self):
        """A denied unregister used to print plain 'Stopped.' — the crew's autostart silently stayed."""
        scripts, said = [], []
        with mock.patch.object(self.cli, "win_ps", side_effect=self._fake_ps(scripts, task_exists="yes")), \
                mock.patch.object(self.cli, "stop_service_run"), \
                mock.patch.object(self.cli, "service_pid", return_value=None), \
                mock.patch.object(self.cli, "say", side_effect=said.append):
            self.cli.stop()
        self.assertTrue(any("still registered" in line for line in said), said)

    def test_stop_warns_when_a_watchdog_survives(self):
        said = []
        with mock.patch.object(self.cli, "win_ps", side_effect=self._fake_ps([], task_exists="no")), \
                mock.patch.object(self.cli, "stop_service_run"), \
                mock.patch.object(self.cli, "service_pid", return_value=4242), \
                mock.patch.object(self.cli, "say", side_effect=said.append):
            self.cli.stop()
        warn = next(line for line in said if "still alive" in line)
        self.assertIn("4242", warn)
        self.assertIn("taskkill /PID 4242 /T /F", warn)

    def test_stop_is_quiet_when_everything_really_stopped(self):
        said = []
        with mock.patch.object(self.cli, "win_ps", side_effect=self._fake_ps([], task_exists="no")), \
                mock.patch.object(self.cli, "stop_service_run"), \
                mock.patch.object(self.cli, "service_pid", return_value=None), \
                mock.patch.object(self.cli, "say", side_effect=said.append):
            self.cli.stop()
        self.assertTrue(any("Stopped." in line for line in said))
        self.assertFalse(any("But the" in line for line in said), said)

    @unittest.skipUnless(os.name == "nt", "signal names are platform state")
    def test_service_run_uses_this_platforms_path_separator(self):
        """service_run once joined PATH with ':' — POSIX-only — so the service's whole environment had
        one unusable PATH blob on Windows: claude (and everything else) became FileNotFoundError."""
        home = tempfile.mkdtemp(dir=TMP)
        seen = {}
        code = (
            "import importlib.machinery, importlib.util, os, subprocess, sys, types\n"
            "loader = importlib.machinery.SourceFileLoader('orbit_cli', r'%s')\n"
            "spec = importlib.util.spec_from_loader('orbit_cli', loader)\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "loader.exec_module(m)\n"
            "m.SERVICE_PID = r'%s'\n"
            "def fake_popen(argv, **kw):\n"
            "    seen = kw['env']['PATH']\n"           # noqa: F841 - captured in the parent via exit code
            "    os.makedirs(r'%s', exist_ok=True)\n"
            "    open(r'%s', 'w').write(kw['env']['PATH'])\n"
            "    return types.SimpleNamespace(wait=lambda *a: 1)\n"
            "m.subprocess.Popen = fake_popen\n"
            "m.time.sleep = lambda *a: (_ for _ in ()).throw(KeyboardInterrupt())\n"
            "try:\n"
            "    m.service_run()\n"
            "except KeyboardInterrupt:\n"
            "    pass\n")
        pid_file = os.path.join(home, "team", "service.pid")
        path_file = os.path.join(home, "team", "seen-path.txt")
        r = subprocess.run([sys.executable, "-c", code % (os.path.join(KIT, "orbit"), pid_file, home, path_file)],
                           env=dict(os.environ, STAFFROOM_HOME=home), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(path_file, encoding="utf-8") as fh:
            seen_path = fh.read()
        parts = seen_path.split(os.pathsep)
        self.assertGreater(len(parts), 1, seen_path)     # not one unusable blob
        self.assertTrue(all(os.path.isdir(p) for p in parts), seen_path)

    @unittest.skipUnless(os.name == "nt", "signal names are platform state")
    def test_service_run_never_touches_posix_only_signals(self):
        """service_run died on native Windows at signal.SIGHUP (AttributeError) right after writing its
        pid file — invisible under pythonw, no staffd.out, nothing. The body must run clean here."""
        home = tempfile.mkdtemp(dir=TMP)
        code = (
            "import importlib.machinery, importlib.util, os, subprocess, sys, types\n"
            "loader = importlib.machinery.SourceFileLoader('orbit_cli', r'%s')\n"
            "spec = importlib.util.spec_from_loader('orbit_cli', loader)\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "loader.exec_module(m)\n"
            "m.SERVICE_PID = r'%s'\n"
            "m.subprocess.Popen = lambda *a, **k: types.SimpleNamespace(wait=lambda *a: 1)\n"
            "m.time.sleep = lambda *a: (_ for _ in ()).throw(KeyboardInterrupt())\n"
            "try:\n"
            "    m.service_run()\n"
            "    print('returned')\n"
            "except KeyboardInterrupt:\n"
            "    print('ran-clean')\n")
        pid_file = os.path.join(home, "team", "service.pid")
        r = subprocess.run([sys.executable, "-c", code % (os.path.join(KIT, "orbit"), pid_file)],
                           env=dict(os.environ, STAFFROOM_HOME=home), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("AttributeError", r.stderr)
        self.assertEqual(r.stdout.strip(), "ran-clean")

    @unittest.skipUnless(os.name == "nt", "Windows console encoding")
    def test_doctor_survives_a_cp1252_console(self):
        """A Windows console/pipe defaults to cp1252, which cannot encode Orbit's ✓/✗: doctor must not
        crash on it (it once exited with UnicodeEncodeError before printing any check)."""
        home = tempfile.mkdtemp(dir=TMP)
        r = subprocess.run([sys.executable, os.path.join(KIT, "orbit"), "doctor"],
                           env=dict(os.environ, PYTHONIOENCODING="cp1252", STAFFROOM_HOME=home),
                           capture_output=True, timeout=300)
        self.assertNotIn(b"UnicodeEncodeError", r.stderr)
        out = r.stdout.decode("utf-8", "replace")
        self.assertIn("Windows", out)                        # the checks really printed, not a crash
        self.assertIn(r.returncode, (0, 1))


class Documents(unittest.TestCase):
    def setUp(self):
        import docs
        self.docs = docs
        self.mac = docs.MAC
        docs.MAC = False
        self.bin = tempfile.mkdtemp(dir=TMP)
        with open(os.path.join(self.bin, "tesseract"), "w") as fh:   # a stand-in that knows ara and eng
            fh.write('#!/bin/sh\nif [ "$1" = "--list-langs" ]; then printf "List of available languages (3):\\n'
                     'ara\\neng\\nosd\\n"; exit 0; fi\necho "read $1 with $4"\n')
        os.chmod(os.path.join(self.bin, "tesseract"), 0o755)
        self.path = os.environ["PATH"]
        os.environ["PATH"] = self.bin + os.pathsep + self.path

    def tearDown(self):
        self.docs.MAC = self.mac
        os.environ["PATH"] = self.path

    @POSIX_FIXTURE
    def test_ocr_uses_tesseract_with_arabic_and_english(self):
        img = os.path.join(TMP, "scan.png")
        with open(img, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n")
        got = self.docs.ocr(img)
        self.assertEqual(got, {1: "read %s with ara+eng" % img})
        self.assertEqual(self.docs.ocr(img, langs="en")[1], "read %s with eng" % img)
        with self.assertRaises(self.docs.DocError):
            self.docs.ocr(img, langs="ja")                    # not installed: says which apt package

    def test_word_files_without_textutil(self):
        p = os.path.join(TMP, "memo.docx")
        body = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
                '<w:p><w:r><w:t>First line</w:t></w:r></w:p><w:p><w:r><w:t>سطر عربي</w:t></w:r></w:p></w:body></w:document>')
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("word/document.xml", body)
        self.assertEqual(self.docs._office_text(p), "First line\nسطر عربي")
        h = os.path.join(TMP, "page.html")
        with open(h, "w", encoding="utf-8") as fh:
            fh.write("<html><style>x{}</style><p>Hello</p><p>World</p></html>")
        self.assertEqual(self.docs._office_text(h), "Hello\nWorld")


class Sandbox(unittest.TestCase):
    def test_windows_programs_and_services_are_denied(self):
        for rule in ("Bash(powershell.exe *)", "Bash(cmd.exe *)", "Bash(wsl.exe *)", "Bash(systemctl *)"):
            self.assertIn(rule, engine.BASE_DENIED)

    def test_windows_drives_are_out_of_reach_in_wsl(self):
        r = subprocess.run([sys.executable, "-c", "import engine; print('/mnt' in engine.SECRET_PATHS)"],
                           env=dict(os.environ, ORBIT_OS="wsl", PYTHONPATH=os.path.join(KIT, "core")),
                           capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "True", r.stderr)


class Onboarding(unittest.TestCase):
    """The hiring interview's card reaches the crew member: CLAUDE.md, the registry, the first task, the budget."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})

    def card(self):
        return {"responsibilities": ["Read the monthly statement", "Flag odd lines"], "first_task": "Propose a category list.",
                "plan": ["Day 1: categories", "Day 2: first ledger"], "weekly_tokens": 1000000,
                "access": [{"kind": "finance_read_only", "what": "Read CIB statements", "why": "for the books", "site": "CIB"}],
                "interview": [{"q": "How often?", "a": "Monthly"}]}

    def test_card_is_written_where_the_crew_member_reads(self):
        eid = self.hire.hire("Nora", "Bookkeeper", "Keep my books", supervisor="Alex", picked=["documents"], card=self.card())
        reg = engine.registry()["employees"][eid]
        self.assertEqual(reg["weekly_tokens"], 1000000)
        self.assertEqual(reg["card"]["first_task"], "Propose a category list.")
        with open(os.path.join(TMP, "employees", eid, "CLAUDE.md"), encoding="utf-8") as fh:
            md = fh.read()
        for bit in ("Read the monthly statement", "Day 1: categories", "Read CIB statements (CIB)", "How often? → Monthly",
                    "Money: read only"):
            self.assertIn(bit, md)
        import team
        prompt = team.job_prompt(eid, engine.employee(eid), "first_day")
        self.assertIn("Propose a category list.", prompt)
        self.assertNotIn("What I can't do", prompt)

    def test_budget_pauses_routines_not_chats(self):
        import team
        eid = self.hire.hire("Bea", "Researcher", "Research", supervisor="Alex", picked=["web"])
        self.hire.set_field(eid, "weekly_tokens", "1000")
        emp = engine.employee(eid)
        os.makedirs(os.path.join(emp["workspace"], "state"), exist_ok=True)
        with open(os.path.join(emp["workspace"], "state", "runs.jsonl"), "w") as fh:
            fh.write('{"ts": "%s", "employee": "%s", "job": "chat", "ok": true, "tokens": 5000}\n' % (time.strftime("%Y-%m-%dT%H:%M:%S"), eid))
        self.assertEqual(engine.stats(emp)["tokens_7d"], 5000)
        self.assertTrue(team.over_budget(emp))
        self.hire.set_field(eid, "weekly_tokens", "0")
        self.assertFalse(team.over_budget(engine.employee(eid)))

    def test_old_runs_without_tokens_are_estimated(self):
        self.assertEqual(engine.tokens_of({"cost_usd": 0.5}), 100000)
        self.assertEqual(engine.tokens_of({"tokens": 42, "cost_usd": 9}), 42)

    def test_demo_interview_is_scripted(self):
        import panel
        old = panel.DEMO
        panel.DEMO = True
        try:
            q = panel.interview("questions", {"name": "Sara", "role": "Researcher"})
            self.assertGreaterEqual(len(q["questions"]), 3)
            c = panel.interview("card", {"name": "Sara", "role": "Researcher", "answers": []})
            self.assertIn("responsibilities", c)
        finally:
            panel.DEMO = old


class ClaudeSession(unittest.TestCase):
    """The folder a Claude app session opens in carries the same locks as the crew member's runs."""

    def test_local_settings_mirror_the_run(self):
        import hire
        # This test covers the settings blob itself on every host. Native-Windows Desktop refusal is a
        # separate gate with its own focused tests (T036/T037), so it must not hide the Windows sandbox
        # branch here.
        real_guard = engine.require_employee_launch
        engine.require_employee_launch = lambda emp, surface: None
        self.addCleanup(setattr, engine, "require_employee_launch", real_guard)
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        eid = hire.hire("Cleo", "Researcher", "Research", supervisor="Alex", picked=["web"])
        ws = engine.employee(eid)["workspace"]
        os.makedirs(os.path.join(ws, ".claude"), exist_ok=True)
        with open(os.path.join(ws, ".claude", "settings.local.json"), "w") as fh:   # the guard already installed
            json.dump({"enabledPlugins": {"staff-guard@orbit": True}}, fh)
        with open(os.path.join(engine.GUARD, ".claude-plugin", "plugin.json")) as fh, \
                open(os.path.join(ws, ".claude", "orbit-guard.version"), "w") as out:   # ...at the kit's version
            out.write(json.load(fh)["version"])
        s = engine.claude_session(eid)
        with open(os.path.join(ws, ".claude", "settings.local.json")) as fh:
            d = json.load(fh)
        reg = engine.registry()
        reg["sandbox"] = True                           # the team's sandbox on: the settings blob carries it
        engine.save_registry(reg)
        s = engine.claude_session(eid)
        with open(os.path.join(ws, ".claude", "settings.local.json")) as fh:
            d = json.load(fh)
        self.assertTrue(d["sandbox"]["enabled"])
        if osinfo.KIND == "windows":                     # native Windows: MXC holds the line via the hook
            self.assertNotIn("failIfUnavailable", d["sandbox"])   # the agent must start normally (T033)
            self.assertIn("PreToolUse", d.get("hooks", {}))
        else:
            self.assertTrue(d["sandbox"]["failIfUnavailable"])    # mandatorily sandboxed builds fail closed
        self.assertIn("Bash(git push *)", d["permissions"]["deny"])
        self.assertFalse(any(r.startswith("Write(") for r in d["permissions"]["deny"]))
        self.assertEqual(d["env"]["STAFF_EMPLOYEE"], eid)
        self.assertTrue(d["enabledPlugins"]["staff-guard@orbit"])                 # kept
        self.assertTrue(s["link"].startswith("claude://code/new?folder="))
        self.assertIn("Cleo", s["hello"])


class BrowserGrant(unittest.TestCase):
    """'Posts for you': only the panel switch grants it; the registry, CLAUDE.md and sessions follow."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        self.eid = hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex", picked=["web", "act_in_browser"])

    def test_hiring_or_presets_never_grant_it(self):
        import abilities
        self.assertNotIn("act_in_browser", abilities.effective(self.eid))
        self.assertNotIn("act_in_browser", abilities.preset("super"))
        self.hire.set_abilities(self.eid, ["web", "act_in_browser"])
        self.assertNotIn("act_in_browser", abilities.effective(self.eid))

    def test_switch_on_and_off(self):
        import abilities
        b = self.hire.set_browser(self.eid, ["https://www.YouTube.com/upload", "etsy.com"], "batch", "Alex")
        self.assertEqual(b["sites"], ["youtube.com", "etsy.com"])
        self.assertIn("act_in_browser", abilities.effective(self.eid))
        self.hire.set_abilities(self.eid, ["web"])                       # the ticks grid keeps the consent as it is
        self.assertIn("act_in_browser", abilities.effective(self.eid))
        env = engine.clean_env(engine.employee(self.eid))
        self.assertEqual(env["STAFF_BROWSER_SITES"], "youtube.com,etsy.com")
        self.assertNotIn("--chrome", engine.command(engine.employee(self.eid), "sonnet"))   # its own window, never yours
        with open(os.path.join(TMP, "employees", self.eid, "CLAUDE.md"), encoding="utf-8") as fh:
            md = fh.read()
        self.assertEqual(md.count("Granted by your owner"), 1)
        self.assertIn("your own browser window", md)
        self.assertIn("orbit browser %s" % self.eid, md)
        self.hire.set_browser(self.eid, ["youtube.com"], "each", "Alex")   # again: replaced, not repeated
        with open(os.path.join(TMP, "employees", self.eid, "CLAUDE.md"), encoding="utf-8") as fh:
            md = fh.read()
        self.assertEqual(md.count("Granted by your owner"), 1)
        self.assertIn("Approve each item separately", md)
        self.hire.set_browser(self.eid, [], "each", "Alex")
        self.assertNotIn("act_in_browser", abilities.effective(self.eid))
        self.assertNotIn("--chrome", engine.command(engine.employee(self.eid), "sonnet"))
        with open(os.path.join(TMP, "employees", self.eid, "CLAUDE.md"), encoding="utf-8") as fh:
            self.assertNotIn("Granted by your owner", fh.read())

    def test_money_sites_cannot_be_granted(self):
        with self.assertRaises(self.hire.HireError):
            self.hire.set_browser(self.eid, ["paypal.com"], "each", "Alex")


class FullAutonomy(unittest.TestCase):
    """The owner's switch: no permission stops; with the team's sandbox on, an open network inside it."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        self.eid = hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex", picked=["web", "full_autonomy"])

    def run_settings(self):
        emp = engine.employee(self.eid)
        cmd = engine.command(emp, "sonnet")
        return cmd, json.loads(cmd[cmd.index("--settings") + 1])

    def sandbox(self, on):
        reg = engine.registry()
        reg["sandbox"] = on
        engine.save_registry(reg)

    def test_off_by_default_and_never_by_ticks(self):
        cmd, st = self.run_settings()
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "dontAsk")
        self.assertFalse(engine.sandboxed())
        native_mxc = osinfo.KIND == "windows" and engine.recorded_sandbox_mode() == "mxc"
        self.assertEqual(st["sandbox"]["enabled"], native_mxc)
        self.sandbox(True)
        cmd, st = self.run_settings()
        self.assertTrue(st["sandbox"]["network"]["strictAllowlist"])

    def test_on_then_off(self):
        self.hire.set_autonomy(self.eid, True, "Alex")
        cmd, st = self.run_settings()
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "bypassPermissions")
        self.sandbox(True)
        cmd, st = self.run_settings()
        self.assertFalse(st["sandbox"]["network"]["strictAllowlist"])
        self.assertTrue(st["sandbox"]["enabled"])                       # the boundary stays
        self.assertIn(engine.SECRETS, st["sandbox"]["filesystem"]["denyRead"])
        with open(os.path.join(TMP, "employees", self.eid, "CLAUDE.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read().count("Granted by your owner: full autonomy"), 1)
        self.hire.set_autonomy(self.eid, False, "Alex")
        cmd, st = self.run_settings()
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "dontAsk")
        with open(os.path.join(TMP, "employees", self.eid, "CLAUDE.md"), encoding="utf-8") as fh:
            self.assertNotIn("full autonomy", fh.read())

    def test_dont_ask_browser_grant(self):
        self.hire.set_browser(self.eid, ["youtube.com"], "none", "Alex")
        with open(os.path.join(TMP, "employees", self.eid, "CLAUDE.md"), encoding="utf-8") as fh:
            md = fh.read()
        self.assertIn("Don't ask me", md)
        self.assertNotIn("wait for their", md)


class Switches(unittest.TestCase):
    """The owner's switches from chat, from a Yes in Claude (orbit grant), and crew connections."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex", picked=["web"])
        hire.hire("Nora", "Bookkeeper", "Books", supervisor="Alex", picked=["documents"])

    def ab(self, eid):
        import abilities
        return abilities.effective(eid)

    def test_chat_commands(self):
        import grants
        self.assertIn("full autonomy", grants.from_text("Alex", "Suoo full autonomy on"))
        self.assertIn("full_autonomy", self.ab("suoo"))
        self.assertIn("off", grants.from_text("Alex", "turn off full autonomy for suoo"))
        self.assertNotIn("full_autonomy", self.ab("suoo"))
        self.assertIn("without asking", grants.from_text("Alex", "Suoo can post on YouTube and TikTok without asking"))
        b = engine.registry()["employees"]["suoo"]["browser"]
        self.assertEqual((b["sites"], b["approval"]), (["youtube.com", "tiktok.com"], "none"))
        self.assertIn("no longer", grants.from_text("Alex", "suoo stop posting"))
        self.assertIn("work together", grants.from_text("Alex", "connect Suoo with Nora: send Nora every sponsor deal"))
        with open(os.path.join(TMP, "employees", "nora", "CLAUDE.md"), encoding="utf-8") as fh:
            self.assertIn("staff-bus ask suoo", fh.read())
        for ordinary in ("what's the autonomy of a drone?", "post the video on youtube tomorrow", "Suoo, how are you?"):
            self.assertIsNone(grants.from_text("Alex", ordinary), ordinary)

    def test_orbit_grant_needs_the_key(self):
        import grants
        kit = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "orbit")
        env = dict(os.environ, STAFFROOM_HOME=TMP)
        r = subprocess.run([sys.executable, kit, "grant", "suoo", "autonomy", "on"], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)                            # an employee running it gets nothing
        self.assertNotIn("full_autonomy", self.ab("suoo"))
        env["ORBIT_GRANT_KEY"] = grants.key()
        r = subprocess.run([sys.executable, kit, "grant", "suoo", "autonomy", "on"], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("full_autonomy", self.ab("suoo"))


class Updates(unittest.TestCase):
    def test_newer_release_is_offered_never_applied_on_its_own(self):
        import update
        update._save({"latest": "99.0.0", "notes": "- New things", "checked": time.time()})
        s = update.status()
        self.assertTrue(s["newer"])
        self.assertEqual(s["current"], update.current())
        update.dismiss()
        self.assertTrue(update.status()["dismissed"])
        self.assertTrue(update.announce_once("99.0.0"))
        self.assertFalse(update.announce_once("99.0.0"))
        update._save({"latest": "0.0.1", "checked": time.time()})
        self.assertFalse(update.status()["newer"])

    def test_a_rewritten_history_still_updates_and_keeps_the_old_copy(self):
        import update
        root = tempfile.mkdtemp(dir=TMP)
        up, kit = os.path.join(root, "up"), os.path.join(root, "kit")

        def g(cwd, *a):
            return subprocess.run(["git", "-C", cwd, "-c", "user.name=T", "-c", "user.email=t@example.com"] + list(a),
                                  capture_output=True, text=True, check=True)

        def put(version, text):
            for name, body in (("VERSION", version), ("a.txt", text)):
                with open(os.path.join(up, name), "w") as fh:
                    fh.write(body + "\n")
        os.makedirs(up)
        g(up, "init", "-q", "-b", "main")
        put("1.0.0", "Old sample name")
        g(up, "add", "-A"); g(up, "commit", "-qm", "one"); g(up, "tag", "v1.0.0")
        subprocess.run(["git", "clone", "-q", up, kit], check=True)
        g(up, "checkout", "-q", "--orphan", "rewritten")                  # the official history is rewritten…
        put("1.0.1", "New sample name")
        g(up, "add", "-A"); g(up, "commit", "-qm", "one, rewritten"); g(up, "tag", "v1.0.1")
        real = (engine.KIT, update.official_copy, update.restart)
        engine.KIT, update.official_copy, update.restart = kit, (lambda: True), (lambda: None)
        try:
            update._save({"latest": "1.0.1", "checked": time.time()})
            msg = update.apply()                                           # …and this copy still moves to it
            self.assertIn("before-v1.0.1", msg)
            with open(os.path.join(kit, "a.txt")) as fh:
                self.assertEqual(fh.read().strip(), "New sample name")
            self.assertEqual(update.current(), "1.0.1")
            old = subprocess.run(["git", "-C", kit, "show", "before-v1.0.1:a.txt"], capture_output=True, text=True)
            self.assertEqual(old.stdout.strip(), "Old sample name")         # the old copy is kept on a branch
        finally:
            engine.KIT, update.official_copy, update.restart = real
            update._save({})


class ContentKit(unittest.TestCase):
    """The content creator comes trained: the skill loads with the ability, and the kit is whole."""

    @POSIX_FIXTURE
    def test_skill_and_kit(self):
        import abilities
        kit = os.path.join(engine.KIT, "core", "skills", "content-creator")
        with open(os.path.join(kit, "SKILL.md"), encoding="utf-8") as fh:
            self.assertIn("abilities: content", fh.read())
        for f in ("setup.sh", "make.sh", "vo.py", "mix.py", "render.js", "short.html", "script.json", "short.json",
                  "fonts/Poppins-Bold.ttf", "fonts/Poppins-BoldItalic.ttf"):
            self.assertTrue(os.path.exists(os.path.join(kit, "kit", f)), f)
        for f in ("vo.py", "mix.py"):
            subprocess.run([sys.executable, "-m", "py_compile", os.path.join(kit, "kit", f)], check=True)
        for f in ("setup.sh", "make.sh"):
            subprocess.run(["sh", "-n", os.path.join(kit, "kit", f)], check=True)
        self.assertIn("content-creator", [s for a in abilities.catalog() if a["id"] == "content" for s in a["skills"]])
        with open(os.path.join(engine.KIT, "core", "roles.json"), encoding="utf-8") as fh:
            role = next(r for r in json.load(fh)["roles"] if r["id"] == "creator")
        self.assertIn("content", role["abilities"])


class ConnectorsAndRoles(unittest.TestCase):
    """The connector library, granting one, and roles saved from a trained crew member."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"111": {"name": "Alex"}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        hire.hire("Suoo", "Content creator", "Videos for YouTube and TikTok", supervisor="Alex", picked=["web", "content"])

    def test_library_is_whole_and_matches_every_role(self):
        import connectors
        lib = connectors.library()
        self.assertGreater(len(lib), 50)
        self.assertTrue(all(c["url"].startswith("https://") for c in lib))
        with open(os.path.join(engine.KIT, "core", "roles.json"), encoding="utf-8") as fh:
            roles = [r["id"] for r in json.load(fh)["roles"] if r["id"] != "blank"]
        for rid in roles:
            self.assertTrue(connectors.for_job(rid, ""), rid)            # every defined role has suggestions
        self.assertTrue(connectors.for_job(None, "manage our restaurant bookings calendar and email"))   # and undefined ones

    def test_grant_reaches_runs_and_revokes(self):
        import connectors
        connectors.grant("suoo", "notion", "Alex")
        cmd = engine.command(engine.employee("suoo"), "sonnet")
        cfg = cmd[cmd.index("--mcp-config") + 1]
        with open(cfg) as fh:
            self.assertEqual(json.load(fh)["mcpServers"]["notion"]["url"], "https://mcp.notion.com/mcp")
        self.assertIn("mcp__notion", cmd)
        connectors.grant("suoo", "https://mcp.example-app.com/mcp", "Alex", "Example")
        self.assertIn("example", engine.registry()["employees"]["suoo"]["connectors"])
        self.assertIn("no longer", connectors.revoke("suoo", "notion", "Alex"))
        self.assertNotIn("notion", engine.registry()["employees"]["suoo"]["connectors"])
        with self.assertRaises(ValueError):
            connectors.grant("suoo", "not-a-connector", "Alex")

    def test_chat_command_for_a_connector(self):
        import grants
        self.assertIn("Canva", grants.from_text("Alex", "connect Suoo to Canva"))
        self.assertIn("canva", engine.registry()["employees"]["suoo"]["connectors"])
        self.assertIn("no longer", grants.from_text("Alex", "disconnect Suoo from canva"))

    def test_save_a_role_and_hire_from_it(self):
        import rolebook
        ws = engine.employee("suoo")["workspace"]
        os.makedirs(os.path.join(ws, "skills", "hooks"), exist_ok=True)
        with open(os.path.join(ws, "skills", "hooks", "SKILL.md"), "w") as fh:
            fh.write("---\\nname: hooks\\ndescription: Write hooks.\\n---\\nOpen with a question.\\n")
        with open(os.path.join(ws, "CLAUDE.md"), encoding="utf-8") as fh:
            md = fh.read()
        with open(os.path.join(ws, "CLAUDE.md"), "w", encoding="utf-8") as fh:
            fh.write(re.sub(r"_Your supervisor adds rules here[^\\n]*", "- Shorts are about 20 seconds.", md))
        self.assertIn("1 skill", rolebook.save_role("suoo", "Channel manager", "Alex"))
        roles = rolebook.all_roles()
        self.assertEqual(roles["situations"][0]["id"], "yours")
        mine = next(r for r in roles["roles"] if r["id"] == "channel-manager")
        self.assertEqual(mine["source"], "yours")
        self.assertNotIn("full_autonomy", mine["abilities"])
        new = self.hire.hire("Zain", "Content creator", mine["scope"], supervisor="Alex", picked=mine["abilities"])
        rolebook.apply_template(new, "channel-manager")
        zws = engine.employee(new)["workspace"]
        self.assertTrue(os.path.exists(os.path.join(zws, "skills", "hooks", "SKILL.md")))
        with open(os.path.join(zws, "CLAUDE.md"), encoding="utf-8") as fh:
            self.assertIn("Shorts are about 20 seconds.", fh.read())
        out = rolebook.export_role("channel-manager", tempfile.mkdtemp(dir=TMP))
        self.assertTrue(os.path.exists(os.path.join(out, "role.json")))


class Proactive(unittest.TestCase):
    """Every crew member works like an ambitious employee: a plan, a standup, an initiative, and they're heard."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})

    def test_new_hires_have_a_plan_and_the_routines(self):
        import abilities
        eid = self.hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex")
        self.assertTrue(os.path.exists(os.path.join(TMP, "employees", eid, "PLAN.md")))
        self.assertTrue({"standup", "initiative"} <= abilities.effective(eid))
        self.assertIn("initiative", abilities.jobs(eid))

    def test_existing_crew_is_upgraded_once(self):
        import abilities
        eid = self.hire.hire("Old", "Researcher", "Research", supervisor="Alex", picked=["web", "brief"])
        os.remove(os.path.join(TMP, "employees", eid, "PLAN.md"))
        self.hire.upgrade_workspace(eid)
        self.assertTrue(os.path.exists(os.path.join(TMP, "employees", eid, "PLAN.md")))
        self.assertTrue({"standup", "initiative"} <= abilities.effective(eid))
        self.hire.set_abilities(eid, ["web", "brief"])          # the owner turns them off: an upgrade doesn't undo it
        self.hire.upgrade_workspace(eid)
        self.assertNotIn("initiative", abilities.effective(eid))

    def test_a_routine_pops_up_when_there_is_no_phone_channel(self):
        import osinfo
        import team
        shown = []
        real = osinfo.notify
        osinfo.notify = lambda title, text, **kw: shown.append((title, text)) or True
        try:
            team.to_room("suoo", "Suoo", "Alex", "job")("Plan for approval: 2 Shorts a day.")
            team.to_room("suoo", "Suoo", "Alex", "panel")("A chat reply.")
            team.to_room("suoo", "Suoo", "Alex", "job")("SILENT")
        finally:
            osinfo.notify = real
        self.assertEqual(shown, [("Suoo · Orbit", "Plan for approval: 2 Shorts a day.")])


class ApifyStore(unittest.TestCase):
    """Live prices, fresh-only crawls, and Apify Store actors for crew with Full autonomy (no network, no spend)."""

    def setUp(self):
        import apify
        self.apify = apify
        self.env = {k: os.environ.get(k) for k in ("STAFF_EMPLOYEE", "STAFF_ABILITIES")}
        self.http = apify._http

    def tearDown(self):
        self.apify._http = self.http
        for k, v in self.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        for k in [k for k in self.apify.CATALOG if k.startswith("store-")]:
            self.apify.CATALOG.pop(k)

    def fake_actor(self, users, ok, cats=("SOCIAL_MEDIA",)):
        total = 1000
        self.apify._http = lambda *a, **k: {"data": {"title": "Some tool", "categories": list(cats), "pricingInfos": [{"pricingModel": "PAY_PER_EVENT", "minimalMaxTotalChargeUsd": 0.5}],
                                                      "stats": {"totalUsers30Days": users, "publicActorRunStats30Days": {"TOTAL": total, "SUCCEEDED": int(total * ok)}}}}

    def test_prices_alias(self):
        inp, dropped, notes = self.apify.build_input("prices", {"keyword": "kettle", "marketplaces": ["www.amazon.eg"],
                                                                "maxProductResults": 50, "customPrompt": "x"}, 10)
        self.assertEqual(inp["maxProductResults"], 10)
        self.assertIn("customPrompt", dropped)
        self.assertEqual(self.apify.resolve("price"), "prices")
        self.assertEqual(self.apify.resolve("store:apify/e-commerce-scraping-tool"), "prices")   # vetted: for anyone

    def test_store_actors_need_full_autonomy_and_the_bar(self):
        os.environ["STAFF_EMPLOYEE"] = "suoo"
        os.environ["STAFF_ABILITIES"] = "web,apify"
        self.fake_actor(5000, 0.99)
        with self.assertRaises(PermissionError):
            self.apify.resolve("store:someone/good-tool")
        os.environ["STAFF_ABILITIES"] = "web,apify,full_autonomy"
        self.assertTrue(self.apify.resolve("store:someone/good-tool").startswith("store-"))
        self.fake_actor(40, 0.99)
        with self.assertRaises(PermissionError):
            self.apify.resolve("store:someone/tiny-tool")
        self.fake_actor(5000, 0.80)
        with self.assertRaises(PermissionError):
            self.apify.resolve("store:someone/flaky-tool")
        self.fake_actor(5000, 0.99, ("FINANCE",))
        with self.assertRaises(PermissionError):
            self.apify.resolve("store:someone/money-tool")


class Strategy(unittest.TestCase):
    """The plan is visible and agreed in one click; days are scored, tomorrow is prepared, the strategy reviewed
    weekly; a Mac that was offline or asleep doesn't cost a day's routines."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7396}, "workdays": ["Mon", "Tue", "Wed", "Thu", "Fri"]})

    PLAN = """# PLAN — Suoo, Content creator

Status: **proposed** 2026-11-02

## The goal
Drift..Master earns money. In 90 days (by 2027-01-31):
- 1,000 subs and 4,000 long-form watch hours.

## Milestones
| By | What | Status |
|---|---|---|
| 2026-11-02 | Short #1 scheduled | done |
| 2026-11-16 | 28 Shorts out | open |

## Numbers (updated every standup)
| Date | Metric | Value | Target |
|---|---|---|---|
| 2026-11-01 | Subs | 250 | 500 by 2026-12-02 |

## Decisions I need
1. Cadence: 2 Shorts a day (recommended), or 3.
2. Cross-post to TikTok.
"""

    def test_the_plan_is_read_and_agreed_in_one_click(self):
        import orders
        import plan
        eid = self.hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex")
        self.assertEqual(plan.summary(eid)["status"], "none")            # the template's placeholders aren't a plan
        with open(os.path.join(TMP, "employees", eid, "PLAN.md"), "w", encoding="utf-8") as fh:
            fh.write(self.PLAN)
        s = plan.summary(eid)
        self.assertEqual(s["status"], "proposed")
        self.assertEqual(s["goal"], "Drift..Master earns money. In 90 days (by 2027-01-31): 1,000 subs and 4,000 long-form watch hours.")
        self.assertEqual(s["next"], {"by": "2026-11-16", "what": "28 Shorts out", "status": "open"})
        self.assertEqual(s["numbers"][0]["value"], "250")
        self.assertEqual(len(s["decisions"]), 2)
        import panel
        needs = panel.needs_you(panel.members(), [], {}, {})
        self.assertTrue(any(n["kind"] == "plan" and n["href"] == "/e/%s/plan" % eid for n in needs))
        orders.execute("Alex", "agree_plan", {"employee_id": eid})
        s = plan.summary(eid)
        self.assertEqual(s["status"], "agreed")
        self.assertIn("by Alex", s["agreed"])

    def test_review_runs_on_the_owners_last_workday(self):
        import team
        self.assertTrue(team.due_today("last_workday", 4))              # Mon–Fri: Friday
        self.assertFalse(team.due_today("last_workday", 3))
        reg = engine.registry()
        reg["workdays"] = ["Sun", "Mon", "Tue", "Wed", "Thu"]            # an Egyptian week: Thursday
        engine.save_registry(reg)
        self.assertTrue(team.due_today("last_workday", 3))
        self.assertFalse(team.due_today("last_workday", 4))

    def test_new_and_existing_crew_score_the_day_and_review_the_week(self):
        import abilities
        new = self.hire.hire("Nora", "Researcher", "Research", supervisor="Alex")
        self.assertTrue({"eod", "review"} <= set(abilities.jobs(new)))
        old = self.hire.hire("Old", "Researcher", "Research", supervisor="Alex", picked=["web", "standup"])
        reg = engine.registry()
        reg["employees"][old]["proactive_v1"] = True
        engine.save_registry(reg)
        with open(os.path.join(TMP, "employees", old, "PLAN.md"), "w", encoding="utf-8") as fh:
            fh.write(self.PLAN)
        self.hire.upgrade_workspace(old)
        self.assertTrue({"eod", "review"} <= set(abilities.jobs(old)))
        with open(os.path.join(TMP, "employees", old, "PLAN.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertLess(text.index("## Reviews"), text.index("## Decisions I need"))
        self.hire.set_abilities(old, ["web", "standup"])                 # the owner turns them off: it stays off
        self.hire.upgrade_workspace(old)
        self.assertNotIn("review", abilities.jobs(old))

    def test_a_due_routine_starts_without_reachability_and_retry_rearms(self):
        """T019 (FR-013, FR-016): a due routine starts on its own schedule even when the provider is
        unreachable — nothing probes reachability first — and a network failure still re-arms it ten
        minutes later through the same provider."""
        import datetime as dt
        import staffd
        now = dt.datetime.now()
        if now.hour == 0 and now.minute < 2:
            self.skipTest("too close to midnight")
        eid = self.hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex", picked=["standup"])
        reg = engine.registry()
        reg["jobs"] = {"standup": {"at": (now - dt.timedelta(minutes=1)).strftime("%H:%M"), "days": "daily"}}
        engine.save_registry(reg)
        started = []
        real_run = staffd.run_async
        staffd.run_async = lambda *a, **k: started.append(k)
        try:
            staffd.tick_jobs()
            self.assertEqual(len(started), 1)                              # due is due, reachable or not
            self.assertFalse(hasattr(engine, "online"))                    # nothing gates on reachability
            st_f = os.path.join(engine.employee(eid)["workspace"], "state", "schedule.json")
            started[0]["retry"]()                                          # it failed on the network: again in 10 min
            with open(st_f) as fh:
                st = json.load(fh)
            self.assertNotIn("standup", st)
            retry_at = dt.datetime.strptime(st["wait:standup"], "%Y-%m-%d %H:%M")
            self.assertGreaterEqual(retry_at, (now + dt.timedelta(minutes=9)).replace(second=0))
            self.assertLessEqual(retry_at, dt.datetime.now() + dt.timedelta(minutes=11))
            staffd.tick_jobs()
            self.assertEqual(len(started), 1)                              # not before then
        finally:
            staffd.run_async = real_run

    def test_a_routine_that_works_is_posted(self):
        import threading
        import team
        eid = self.hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex")
        real = engine.run
        done, posted = threading.Event(), []
        try:
            engine.run = lambda *a, **k: {"ok": True, "text": "This week: 1.4K median views.", "error": "", "steps": []}
            team.run_async(eid, "p", "review", None, [], on_done=lambda out: posted.append(out) or done.set())
            self.assertTrue(done.wait(10))
            self.assertEqual(posted, ["This week: 1.4K median views."])
        finally:
            engine.run = real

    def test_a_failed_routine_never_says_please_resend(self):
        import threading
        import team
        eid = self.hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex")
        real = engine.run
        done, posted, retried = threading.Event(), [], []
        try:
            engine.run = lambda *a, **k: {"ok": False, "transient": True, "text": "x", "error": "ENOTFOUND", "steps": []}
            team.run_async(eid, "p", "standup", None, [], on_done=posted.append, retry=lambda: retried.append(1) or done.set())
            self.assertTrue(done.wait(10))
            self.assertEqual((retried, posted), ([1], []))
            done.clear()
            engine.run = lambda *a, **k: {"ok": False, "transient": False, "text": "Something went wrong. Please resend.",
                                          "error": "API Error 500", "steps": []}
            team.run_async(eid, "p", "eod", None, [], on_done=lambda out: posted.append(out) or done.set())
            for _ in range(100):
                if any("didn't run" in r.get("body", "") for r in team.tail(team.FEED, 20)):
                    break
                time.sleep(0.1)
            self.assertEqual(posted, [])
            lines = [r["body"] for r in team.tail(team.FEED, 20) if r.get("from_id") == eid]
            self.assertTrue(any(x.startswith("My end of day didn't run: an error on my side") for x in lines), lines)
            self.assertFalse(any("resend" in x for x in lines))
        finally:
            engine.run = real


class Sharing(unittest.TestCase):
    """A crew member someone trained is offered for sharing, with everything private taken out; it travels as
    one file or to the community; whoever hires from it starts with the experience."""

    DRAFT = {"title": "Shorts channel manager", "summary": "Runs a YouTube Shorts channel to monetisation.",
             "experience": "## Quality\n- Every Short ships with a voiceover; silent ones were rejected.",
             "rules": "- Ask before publishing.", "removed": ["the owner's name", "the channel's name"],
             "skills": [{"name": "daily-standup", "text": "---\nname: daily-standup\ndescription: The standup.\n---\nNumbers first."},
                        {"name": "invented", "text": "not a real skill"}]}

    def setUp(self):
        import hire
        import shutil
        self.hire = hire
        shutil.rmtree(os.path.join(TMP, "team", "roles"), ignore_errors=True)
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7395}})
        self.eid = hire.hire("Suoo", "Content creator", "Drift..Master videos", supervisor="Alex")
        ws = os.path.join(TMP, "employees", self.eid)
        os.makedirs(os.path.join(ws, "skills", "daily-standup"), exist_ok=True)
        with open(os.path.join(ws, "skills", "daily-standup", "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nname: daily-standup\ndescription: Alex's Drift..Master standup.\n---\nNumbers first.")
        with open(os.path.join(ws, "LESSONS.md"), "w", encoding="utf-8") as fh:
            fh.write("# LESSONS\n" + "".join("- 2026-11-0%d · Alex: lesson %d\n" % (i % 9 + 1, i) for i in range(9)))

    def test_distill_save_send_import_hire(self):
        import onboard
        import orders
        import rolebook
        seen = []
        real = onboard._ask
        onboard._ask = lambda system, prompt, schema, timeout=150: seen.append(prompt) or dict(self.DRAFT, _tokens=9)
        try:
            d = rolebook.distill(self.eid)
        finally:
            onboard._ask = real
        self.assertIn("Alex's Drift..Master standup", seen[0])                # Claude sees the private text…
        self.assertEqual([s["name"] for s in d["skills"]], ["daily-standup"])   # …and can't add skills it didn't have
        self.assertEqual(d["stats"]["lessons"], 9)
        orders.execute("Alex", "save_role", {"employee_id": self.eid, "title": d["title"], "draft": d})
        rid = "shorts-channel-manager"
        folder = os.path.join(TMP, "team", "roles", rid)
        with open(os.path.join(folder, "skills", "daily-standup", "SKILL.md")) as fh:
            self.assertNotIn("Drift..Master", fh.read())                       # what's saved is the rewritten copy
        with open(os.path.join(folder, "role.json")) as fh:
            role = json.load(fh)
        self.assertEqual((role["trained_by"], role["stats"]["lessons"]), ("Alex", 9))
        self.assertNotIn("Drift", role["scope"])
        z = rolebook.package(rid)
        with open(z, "rb") as fh:
            data = fh.read()
        import shutil
        shutil.rmtree(folder)
        import base64
        msg = orders.execute("Alex", "import_role", {"data": "data:application/zip;base64," + base64.b64encode(data).decode()})
        self.assertIn("trained by Alex", msg)
        listed = next(r for r in rolebook.all_roles()["roles"] if r["id"] == rid)
        self.assertEqual((listed["source"], listed["trained_by"], listed["skills_in"]), ("yours", "Alex", ["daily-standup"]))
        self.assertIn("voiceover", listed["experience"])
        orders.execute("Alex", "hire", {"name": "Zain", "role": "Channel manager", "template": rid, "first_day": False})
        with open(os.path.join(TMP, "employees", "zain", "EXPERIENCE.md")) as fh:
            xp = fh.read()
        self.assertIn("trained by Alex", xp)
        self.assertIn("silent ones were rejected", xp)
        self.assertTrue(os.path.isfile(os.path.join(TMP, "employees", "zain", "skills", "daily-standup", "SKILL.md")))

    def test_unsafe_or_wrong_files_are_refused(self):
        import rolebook
        for files in ({"../evil/role.json": "{}"}, {"notes.txt": "hi"}):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for n, t in files.items():
                    z.writestr(n, t)
            with self.assertRaises(rolebook.RoleError):
                rolebook.import_role(data=buf.getvalue())
        with self.assertRaises(rolebook.RoleError):
            rolebook.import_role(data=b"not a zip")
        with self.assertRaises(rolebook.RoleError):
            rolebook.import_role("http://example.com/role.zip")

    def test_the_trainer_is_offered_to_share_once(self):
        import rolebook
        self.assertEqual(rolebook.share_nudge(), [])                         # one day in: not yet
        reg = engine.registry()
        reg["employees"][self.eid]["hired"] = "2026-01-01"
        engine.save_registry(reg)
        got = rolebook.share_nudge()
        self.assertEqual([k for k, _ in got], [self.eid])
        self.assertEqual(rolebook.share_nudge(), [])                         # once

    def test_community_sharing_without_github_tools(self):
        import shutil
        import rolebook
        rolebook.save_role(self.eid, "Shorts channel manager", "Alex", draft=dict(self.DRAFT, trained_by="Alex"))
        real = shutil.which
        shutil.which = lambda name, *a, **k: None if name == "gh" else real(name, *a, **k)
        try:
            out = rolebook.publish("shorts-channel-manager", "Alex")
        finally:
            shutil.which = real
        self.assertFalse(out["pr"])
        self.assertTrue(out["url"].startswith("https://github.com/BasemTarekkamal/orbit/issues/new?"))
        self.assertTrue(os.path.isfile(out["file"]))
        self.assertIn("drag", out["how"])


class Asleep(unittest.TestCase):
    """A sleeping laptop: no run starts in its few-second wakes, a missed day is made up for in one run, a due
    follow-up isn't lost, its report reaches the owner, and the computer stays up while a run is going. Nothing
    here probes the provider's reachability: due work starts, and a failure is reported and retried (T019)."""

    def setUp(self):
        import hire
        self.hire = hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7394}, "workdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})
        import awake
        import staffd
        self.awake, self.staffd = awake, staffd
        self.real = (staffd.run_async, awake._since)
        self.started = []
        staffd.run_async = lambda *a, **k: self.started.append((a, k))
        self.eid = hire.hire("Suoo", "Content creator", "Videos", supervisor="Alex", picked=["standup", "eod", "reminders"])
        self.ws = engine.employee(self.eid)["workspace"]
        self.st_f = os.path.join(self.ws, "state", "schedule.json")
        if os.path.exists(self.st_f):                                     # an earlier test's Suoo, same folder
            os.remove(self.st_f)

    def tearDown(self):
        self.staffd.run_async, self.awake._since = self.real

    def write_schedule(self, st):
        os.makedirs(os.path.dirname(self.st_f), exist_ok=True)
        with open(self.st_f, "w") as fh:
            json.dump(st, fh)

    def test_no_run_starts_in_a_few_second_wake(self):
        import datetime as dt
        now = dt.datetime.now()
        reg = engine.registry()
        reg["jobs"] = {"standup": {"at": (now - dt.timedelta(minutes=1)).strftime("%H:%M"), "days": "daily"},
                       "eod": {"at": "17:00", "days": ""}}          # not due today: exactly one routine is due
        engine.save_registry(reg)
        self.awake._since = time.time() - 5                               # awake for 5 seconds
        self.assertFalse(self.awake.settled())
        self.staffd.tick_jobs()
        self.staffd.tick_reminders()
        self.assertEqual(self.started, [])
        self.awake._since = time.time() - 120                             # really awake now
        self.staffd.tick_jobs()
        self.assertEqual(len(self.started), 1)
        self.assertFalse(hasattr(engine, "online"))                       # no reachability check anywhere

    def test_a_missed_day_is_made_up_for_in_one_run(self):
        import datetime as dt
        import team
        now = dt.datetime.now()
        reg = engine.registry()
        at = (now - dt.timedelta(hours=6)).strftime("%H:%M") if now.hour >= 6 else "00:00"
        if now.hour < 6:
            self.skipTest("too close to midnight")
        reg["jobs"] = {"standup": {"at": at, "days": "daily"}, "eod": {"at": at, "days": "daily"}}
        engine.save_registry(reg)
        old = (now - dt.timedelta(days=2)).strftime("%F")
        self.write_schedule({"standup": old, "eod": old})
        self.staffd.tick_jobs()
        self.assertEqual(len(self.started), 1)
        a, k = self.started[0]
        self.assertEqual(a[2], "catchup")
        self.assertIn("Standup", a[1])
        self.assertIn("End of day", a[1])
        self.assertFalse(any("offline" in r.get("body", "") for r in team.tail(team.FEED, 5)))
        self.staffd.tick_jobs()
        self.assertEqual(len(self.started), 1)                            # once
        k["retry"]()                                                      # the network failed again: it comes back
        with open(self.st_f) as fh:
            st = json.load(fh)
        self.assertEqual(st["catchup"], ["eod", "standup"])

    def test_a_new_routine_is_not_a_missed_one(self):
        import datetime as dt
        now = dt.datetime.now()
        if now.hour < 6:
            self.skipTest("too close to midnight")
        reg = engine.registry()
        reg["jobs"] = {"standup": {"at": (now - dt.timedelta(hours=6)).strftime("%H:%M"), "days": "daily"},
                       "eod": {"at": (now - dt.timedelta(hours=6)).strftime("%H:%M"), "days": "daily"}}
        engine.save_registry(reg)
        self.staffd.tick_jobs()
        self.assertEqual(self.started, [])

    def test_a_due_followup_runs_reports_and_retries(self):
        import datetime as dt
        import osinfo
        sys.path.insert(0, os.path.join(KIT, "core", "tools"))
        import remind
        import team
        ws = self.ws
        past = (dt.datetime.now() - dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        future = (dt.datetime.now() + dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        remind.save(ws, [
            {"id": "R-0001", "at": past, "to": "me", "text": "Make the batch", "repeat": "daily", "agent": True},
            {"id": "R-0002", "at": future, "to": "me", "text": "Later", "repeat": "none", "agent": True},
            {"id": "R-0003", "at": past, "to": "me", "text": "Stretch", "repeat": "none", "agent": False}])
        self.staffd.tick_reminders()
        self.assertEqual(len(self.started), 1)                            # the due follow-up runs, no reachability gate
        self.assertFalse(hasattr(engine, "online"))                       # nothing probed the provider
        self.assertTrue(any(r.get("body") == "Reminder: Stretch" for r in team.tail(team.FEED, 5)))
        ids = [r["id"] for r in remind.load(ws)]
        self.assertIn("R-0002", ids)                                      # not due yet: untouched
        self.assertNotIn("R-0003", ids)                                   # plain reminder: delivered and consumed
        a, k = self.started[0]
        self.assertEqual(a[2], "followup")
        shown, real = [], osinfo.notify
        osinfo.notify = lambda t, b, **kw: shown.append(b) or True
        try:
            k["on_done"]("Standup: 3 Shorts ready.")                      # no phone channel: it still reaches the owner
        finally:
            osinfo.notify = real
        self.assertTrue(any(r.get("body") == "Standup: 3 Shorts ready." for r in team.tail(team.FEED, 5)))
        self.assertEqual(shown, ["Standup: 3 Shorts ready."])
        k["retry"]()
        ids = [r["id"] for r in remind.load(ws)]
        self.assertIn("R-0001r", ids)                                     # the failed one comes back in 10 minutes
        self.assertIn("R-0001", ids)                                      # the daily one still stands

    def test_sleep_is_seen_and_told(self):
        import panel
        now = time.time()
        with open(self.awake.FILE, "w") as fh:
            json.dump([], fh)
        self.awake.record(now - 8 * 3600, now - 7 * 3600)
        self.awake.record(now - 7 * 3600 + 30, now - 3600)                 # a dark wake between: one sleep
        s = self.awake.slept(24)
        self.assertEqual(s["longest"], 7.0)
        needs = panel.needs_you(panel.members(), [], {}, {})
        self.assertEqual(needs[0]["kind"], "asleep")
        self.assertIn("slept 7.0 hours", needs[0]["title"])
        os.remove(self.awake.FILE)

    def test_the_computer_stays_up_during_a_run(self):
        real = osinfo.KIND
        try:
            osinfo.KIND = "mac"
            self.assertEqual(osinfo.keep_awake_cmd(42, battery=True), ["caffeinate", "-s", "-i", "-w", "42"])
            self.assertEqual(osinfo.keep_awake_cmd(42), ["caffeinate", "-s", "-w", "42"])
            self.assertEqual(osinfo.keep_awake_cmd(42, battery=True, seconds=120), ["caffeinate", "-s", "-i", "-t", "120"])
            osinfo.KIND = "wsl"
            cmd = osinfo.keep_awake_cmd(42, battery=True)
            self.assertEqual(cmd[:2], ["bash", "-c"])
            self.assertIn("kill -0 42", cmd[2])
            self.assertIn("SetThreadExecutionState(1)", cmd[2])
        finally:
            osinfo.KIND = real
        spawned, real_spawn = [], self.awake._spawn
        self.awake._spawn = lambda c: spawned.append(c)
        try:
            self.awake.hold(42)
            reg = engine.registry()
            reg["keep_awake"] = "off"
            engine.save_registry(reg)
            self.awake.hold(42)
        finally:
            self.awake._spawn = real_spawn
        self.assertLessEqual(len(spawned), 1)                             # "off" means off


class CloudShift(unittest.TestCase):
    """Laptop first; closed or offline, the crew carries on in the cloud; back, the work comes home. No real cloud here."""

    def setUp(self):
        import cloud
        import hire
        self.cloud, self.hire = cloud, hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7392}, "workdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                              "cloud_environment": "env_test"})
        self.real_resolve = engine.resolve_claude
        engine.resolve_claude = lambda: sys.executable        # a real file; the account check is faked below
        self.real_status = cloud.account_status
        self.acct = {"checked_at": 1.0, "eligible": True, "auth_method": "claude.ai", "reason": ""}
        cloud.account_status = lambda fresh=False: dict(self.acct)
        self.eid = hire.hire("Cleo", "Researcher", "Coffee", supervisor="Alex")
        self.ws = os.path.join(TMP, "employees", self.eid)
        if os.path.exists(cloud._path(self.eid)):
            os.remove(cloud._path(self.eid))
        self.calls, self.sent = [], []
        self.real = (cloud.trigger, cloud.send, cloud.new_session, cloud.pull)
        cloud.trigger = lambda action, tid="", body=None: self.calls.append((action, tid, body)) or {"trigger": {"id": "trig_%d" % len(self.calls)}}
        cloud.send = lambda sid, text: self.sent.append(text)
        cloud.new_session = lambda emp, desk, first: "session_new"

    def tearDown(self):
        self.cloud.trigger, self.cloud.send, self.cloud.new_session, self.cloud.pull = self.real
        self.cloud.account_status, engine.resolve_claude = self.real_status, self.real_resolve

    def test_the_schedule_skips_only_today(self):
        import datetime as dt
        thu = dt.date(2026, 11, 5)
        days = self.cloud.cron_for("10:00", thu, today=thu).split()[3].split(",")
        self.assertNotIn("5", days)
        self.assertIn("6", days)                                         # Friday: on
        self.assertNotIn("7", days)                                      # Saturday: not a workday here
        self.assertIn("9", days)
        everyday = self.cloud.cron_for("14:30", None, today=thu)
        self.assertEqual(everyday.split()[1:3], ["30", "14"])
        self.assertIn("5", everyday.split()[3].split(","))
        self.assertTrue(everyday.startswith("CRON_TZ="))

    def test_setup_makes_one_routine_per_check_time_with_no_connected_apps(self):
        st = self.cloud.setup(self.eid)
        self.assertEqual(sorted(st["slots"]), ["10:00", "14:00", "18:00"])     # an hour after standup, initiative, end of day
        made = [c for c in self.calls if c[0] == "create"]
        self.assertEqual(len(made), 3)
        self.assertTrue(all(c[2]["persistent_session_id"] == "session_new" for c in made))
        self.assertTrue(all(c[2]["notifications"]["channel"]["push"] for c in made))
        self.assertEqual(sum(1 for c in self.calls if c[2] == {"clear_mcp_connections": True}), 3)
        self.assertIn("Standing instructions from Alex", self.sent[0])     # the owner's instruction, not a stray prompt

    def test_here_says_skip_gone_it_fires_back_it_pulls(self):
        import datetime as dt
        now = dt.datetime.now()
        if not 1 <= now.hour <= 22:
            self.skipTest("too close to midnight")
        reg = engine.registry()
        reg["workdays"] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        at = (now + dt.timedelta(minutes=30)).strftime("%H:%M")
        reg["jobs"] = {"standup": {"at": (now + dt.timedelta(minutes=30) - dt.timedelta(hours=1)).strftime("%H:%M")}}
        engine.save_registry(reg)
        yesterday = (now - dt.timedelta(days=1)).strftime("%F")
        self.cloud._save(self.eid, {"session": "session_old", "seeded_at": time.strftime("%F"), "slots": {at: {"trigger": "t1", "skipped": yesterday}}})
        self.calls.clear()
        self.cloud._tick_one(self.eid)                                    # 30 minutes ahead, and here: skip today
        self.assertEqual(self.calls[0][:2], ("update", "t1"))
        self.assertIn("cron_expression", self.calls[0][2])
        self.assertEqual(self.cloud.state(self.eid)["slots"][at]["skipped"], now.strftime("%F"))
        self.calls.clear()
        self.cloud._tick_one(self.eid)
        self.assertEqual(self.calls, [])                                  # once a day
        self.assertFalse(self.cloud.missed(self.cloud.state(self.eid)))
        # a check time passed with no skip: the cloud took that shift
        past = (now - dt.timedelta(minutes=30)).strftime("%H:%M")
        self.cloud._save(self.eid, {"session": "session_old", "seeded_at": time.strftime("%F"), "slots": {past: {"trigger": "t2", "skipped": yesterday}}})
        self.assertTrue(self.cloud.missed(self.cloud.state(self.eid)))
        pulled = []
        self.cloud.pull = lambda e: pulled.append(e) or {"files": 2, "reports": 1}
        self.cloud._tick_one(self.eid)
        self.assertEqual(pulled, [self.eid])
        self.assertEqual(self.cloud.state(self.eid)["session"], "session_old")   # one desk, for good
        self.assertFalse(self.cloud.missed(self.cloud.state(self.eid)))
        with open(os.path.join(self.ws, "state", "schedule.json")) as fh:
            self.assertIn("cloud", json.load(fh)["catchup"])              # and the crew member merges the work

    def test_the_desk_hears_what_changed_here(self):
        self.cloud.build_desk(self.eid)
        self.cloud._commit(self.cloud._desk_dir(self.eid))
        self.assertEqual(self.cloud.delta(self.eid), "")
        with open(os.path.join(self.ws, "LESSONS.md"), "a") as fh:
            fh.write("- A new lesson.\n")
        with open(os.path.join(self.ws, "TASKS.md"), "a") as fh:
            fh.write("- A new task.\n")
        change = self.cloud.delta(self.eid)
        self.assertIn("+- A new lesson.", change)
        self.assertNotIn("A new task", change)                            # the board travels in the note itself
        self.assertEqual(self.cloud.delta(self.eid), "")

    def test_the_desk_carries_know_how_not_secrets_or_media(self):
        for rel, body in (("research/a.md", "notes"), ("content/x.mp4", "video"), ("api_token.txt", "s3cret"), (".env", "KEY=1"),
                          ("state/cloud.json", "{}"), (".mcp.json", "{}"), ("kit/Poppins.ttf", "font")):
            p = os.path.join(self.ws, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write(body)
        desk = self.cloud.build_desk(self.eid)
        have = {os.path.relpath(os.path.join(b, n), desk).replace(os.sep, "/")
                for b, _, ns in os.walk(desk) for n in ns if ".git" + os.sep not in b + os.sep}
        self.assertTrue({"research/a.md", "kit/Poppins.ttf", "ROLE.md", "CLAUDE.md", "handbook.md", "handoff.py", "PLAN.md"} <= have)
        self.assertFalse({"content/x.mp4", "api_token.txt", ".env", "state/cloud.json", ".mcp.json"} & have)
        with open(os.path.join(desk, "CLAUDE.md")) as fh:
            md = fh.read()
        self.assertIn("Cleo", md)
        self.assertIn("Never post, publish, upload, log in", md)
        with open(os.path.join(desk, "jobs", "standup.md")) as fh:
            self.assertNotIn("{name}", fh.read())
        self.assertEqual(subprocess.run(["git", "remote"], cwd=desk, capture_output=True, text=True).stdout, "")   # uploaded as it is

    def test_handoff_prints_what_changed_and_only_once(self):
        desk = self.cloud.build_desk(self.eid)
        with open(os.path.join(desk, "research.md"), "w") as fh:
            fh.write("found it")
        with open(os.path.join(desk, "render.mp4"), "wb") as fh:
            fh.write(b"x" * 100)
        run = lambda: subprocess.run([sys.executable, "handoff.py"], cwd=desk, capture_output=True, text=True).stdout
        out = run()
        self.assertIn("<<<ORBIT-FILE research.md\nfound it\n>>>ORBIT-FILE", out)
        self.assertIn("ORBIT-LEFT-ON-DESK render.mp4 (100 bytes)", out)
        self.assertTrue(out.strip().endswith("ORBIT-DONE"))
        self.assertNotIn("research.md", run())

    def test_the_work_comes_home_without_touching_memory(self):
        import team
        lines = [{"type": "user", "timestamp": "2026-11-05T07:00:00Z", "message": {"content": [{"type": "tool_result", "content":
                  "<<<ORBIT-FILE research/new.md\nfresh\n>>>ORBIT-FILE\n<<<ORBIT-FILE PLAN.md\ncloud plan\n>>>ORBIT-FILE\n"
                  "<<<ORBIT-FILE ../../evil.md\nno\n>>>ORBIT-FILE\n<<<ORBIT-FILE .git/config\nno\n>>>ORBIT-FILE\nORBIT-LEFT-ON-DESK a.mp4 (5 bytes)\nORBIT-DONE"}]}},
                 {"type": "assistant", "timestamp": "2026-11-05T07:01:00Z", "message": {"content": [{"type": "text", "text": "Cloud shift: wrote research/new.md."}]}},
                 {"type": "assistant", "timestamp": "2026-11-04T07:01:00Z", "message": {"content": [{"type": "text", "text": "Cloud shift: an older one."}]}}]
        path = os.path.join(TMP, "transcript.jsonl")
        with open(path, "w") as fh:
            fh.write("\n".join(json.dumps(x) for x in lines))
        self.cloud._transcript = lambda emp, sid: path
        with open(os.path.join(self.ws, "PLAN.md"), encoding="utf-8") as fh:
            before = fh.read()
        self.cloud._save(self.eid, {"session": "session_x", "pulled_upto": "2026-11-04T12:00:00Z"})
        got = self.real[3](self.eid)
        self.assertEqual(got["reports"], 1)
        day = time.strftime("%F")
        root = os.path.join(self.ws, "notes", "cloud", day)
        with open(os.path.join(root, "research", "new.md")) as fh:
            self.assertEqual(fh.read(), "fresh")
        with open(os.path.join(self.ws, "PLAN.md"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)                           # its memory is merged by the crew member, never overwritten
        self.assertFalse(os.path.exists(os.path.join(self.ws, "notes", "evil.md")))
        self.assertFalse(os.path.exists(os.path.join(root, ".git")))
        with open(os.path.join(root, "REPORTS.md")) as fh:
            self.assertIn("ORBIT-LEFT-ON-DESK a.mp4", fh.read())
        self.assertTrue(any(r.get("body") == "Cloud shift: wrote research/new.md." for r in team.tail(team.FEED, 5)))
        self.assertIn("notes/cloud/%s/" % day, self.cloud.merge_note(self.eid))
        self.assertEqual(self.cloud.merge_note(self.eid), "")             # once

    def test_switching_it_on_and_off(self):
        import grants
        self.assertIsNone(grants.from_text("Alex", "Nobody cloud on"))
        reply = grants.from_text("Alex", "Cleo cloud on")
        self.assertIn("cloud desk", reply)
        self.assertTrue(self.cloud.is_on(self.eid))
        self.calls.clear()
        reply = grants.from_text("Alex", "Cleo cloud off")
        self.assertIn("off", reply)
        self.assertFalse(self.cloud.is_on(self.eid))
        self.assertTrue(all(c[2] == {"enabled": False} for c in self.calls) and self.calls)

    def test_paused_or_retired_means_no_cloud_shifts(self):
        import orders
        self.cloud.enable(self.eid)
        self.calls.clear()
        orders.execute("Alex", "pause", {"employee_id": self.eid})
        self.assertEqual(len(self.calls), 3)
        self.assertTrue(all(c[2] == {"enabled": False} for c in self.calls))
        self.calls.clear()
        orders.execute("Alex", "resume", {"employee_id": self.eid})
        self.assertTrue(all(c[2].get("enabled") is True for c in self.calls) and self.calls)
        self.calls.clear()
        orders.execute("Alex", "retire", {"employee_id": self.eid})
        self.assertTrue(all(c[2] == {"enabled": False} for c in self.calls) and self.calls)

    def test_new_hires_get_it_only_with_a_qualifying_account(self):
        import orders
        before = set(engine.registry()["employees"])
        result = orders.execute("Alex", "hire", {"name": "Nia", "role": "Writer", "first_day": False})
        self.assertIn("Hired", result)
        first = (set(engine.registry()["employees"]) - before).pop()
        self.assertTrue(self.cloud.is_on(first))
        self.acct.update(eligible=False, auth_method="oauth_token",
                         reason="The cloud shift needs a Claude plan sign-in on this computer.")
        before = set(engine.registry()["employees"])
        orders.execute("Alex", "hire", {"name": "Nia Two", "role": "Writer", "first_day": False})
        second = (set(engine.registry()["employees"]) - before).pop()
        self.assertFalse(self.cloud.is_on(second))
        with self.assertRaises(self.cloud.CloudError) as ctx:
            self.cloud.enable(self.eid)
        self.assertIn("sign-in", str(ctx.exception))


class CloudAccount(unittest.TestCase):
    """T023–T026 (FR-017–FR-019, SC-006): Cloud Shift is an account-only boundary. Eligibility is a
    transient, memory-cached result; account launches get an empty-mapping allowlist; and every
    Orbit-initiated cloud operation takes a fresh check. No real cloud or account here."""

    AUTH_MATRIX = {"none": (False, "none"), "third_party": (True, "third_party"),
                   "api_key": (True, "api_key"), "api_key_helper": (True, "api_key_helper"),
                   "oauth_token": (True, "oauth_token")}

    class FakeRun:
        """Stands in for every `claude` subprocess: auth status, trigger, send and /schedule."""

        def __init__(self):
            self.calls = []
            self.auth = {"loggedIn": True, "authMethod": "claude.ai"}

        def __call__(self, cmd, **kw):
            cmd = list(cmd)
            self.calls.append((cmd, kw))
            if cmd[1:3] == ["auth", "status"]:
                return SimpleNamespace(stdout=json.dumps(self.auth), stderr="", returncode=0)
            if "--cloud" in cmd:
                return SimpleNamespace(stdout='{"ok": true}', stderr="", returncode=0)
            if "/schedule" in (kw.get("input") or ""):
                return SimpleNamespace(stdout="env_ABCDEFGHIJ", stderr="", returncode=0)
            lines = [json.dumps({"type": "user", "message": {"content": [
                        {"type": "tool_result", "content": 'HTTP 200 {"trigger": {"id": "trig_9"}}'}]}}),
                     json.dumps({"type": "result", "usage": {"input_tokens": 3, "output_tokens": 2}})]
            return SimpleNamespace(stdout="\n".join(lines), stderr="", returncode=0)

    def setUp(self):
        import cloud
        import hire
        self.cloud, self.hire = cloud, hire
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}}, "employees": {},
                              "defaults": {"model": "sonnet"}, "panel": {"port": 7393},
                              "workdays": ["Mon", "Tue", "Wed", "Thu", "Fri"]})
        self.real_resolve = engine.resolve_claude
        self.claude = os.path.join(TMP, "claude-account-exe")
        with open(self.claude, "w") as fh:
            fh.write("")
        engine.resolve_claude = lambda: self.claude
        self.eid = hire.hire("Ada", "Analyst", "Market", supervisor="Alex")
        self.real_run, self.real_cache = cloud.subprocess.run, dict(cloud._CACHE)
        self.fake = self.FakeRun()
        cloud.subprocess.run = self.fake
        self.real_setup = cloud.setup

        def setup(emp_id):                                    # the desk build is other tests'; the schedule is this one's
            st = cloud.state(emp_id)
            st["slots"] = {"10:00": {"trigger": "t1"}}
            cloud._save(emp_id, st)
            return st
        cloud.setup = setup
        cloud._CACHE.update({"at": 0.0, "result": None})

    def tearDown(self):
        self.cloud.subprocess.run, self.cloud.setup = self.real_run, self.real_setup
        engine.resolve_claude = self.real_resolve
        self.cloud._CACHE.clear()
        self.cloud._CACHE.update(self.real_cache)

    def auth(self, logged_in=True, method="claude.ai"):
        self.fake.auth = {"loggedIn": logged_in, "authMethod": method}
        self.cloud._CACHE.update({"at": 0.0, "result": None})

    def launches(self):
        return [c for c in self.fake.calls if c[0][1:3] != ["auth", "status"]]

    # -- T023
    def test_eligibility_is_exactly_logged_in_claude_ai(self):
        for method, (logged_in, auth_method) in self.AUTH_MATRIX.items():
            self.fake.auth = {"loggedIn": logged_in, "authMethod": auth_method}
            res = self.cloud.account_status(fresh=True)
            self.assertFalse(res["eligible"], method)
            self.assertEqual(res["auth_method"], auth_method)
            self.assertTrue(res["reason"])
            self.assertNotIn("anthropic", res["reason"].lower())
            self.assertNotIn("api key", res["reason"].lower())
        self.fake.auth = {"loggedIn": False, "authMethod": "claude.ai"}
        self.assertFalse(self.cloud.account_status(fresh=True)["eligible"])   # a method without a login
        self.fake.auth = {"loggedIn": True, "authMethod": "claude.ai"}
        res = self.cloud.account_status(fresh=True)
        self.assertTrue(res["eligible"])
        self.assertEqual(res["auth_method"], "claude.ai")
        self.assertEqual(res["reason"], "")                                  # empty only when eligible
        self.assertIsInstance(res["checked_at"], float)

    def test_read_cache_is_short_and_fresh_mode_bypasses_it(self):
        first = self.cloud.account_status()
        second = self.cloud.account_status()
        self.assertEqual(len([c for c in self.fake.calls if c[0][1:3] == ["auth", "status"]]), 1)
        self.assertGreaterEqual(second["checked_at"], first["checked_at"])
        self.assertTrue(second["eligible"])
        self.fake.auth = {"loggedIn": True, "authMethod": "third_party"}
        self.assertTrue(self.cloud.account_status()["eligible"])              # a stale positive display cache
        self.assertFalse(self.cloud.account_status(fresh=True)["eligible"])   # fresh bypasses it
        self.assertEqual(len([c for c in self.fake.calls if c[0][1:3] == ["auth", "status"]]), 2)
        self.assertFalse(self.cloud.account_status()["eligible"])             # the fresh result is now cached
        self.cloud._CACHE["at"] -= 61                                        # older than 60 seconds
        self.fake.auth = {"loggedIn": True, "authMethod": "claude.ai"}
        self.assertTrue(self.cloud.account_status()["eligible"])              # re-checked after expiry

    # -- T024
    SENTINELS = {"CLAUDECODE": "1", "CLAUDE_CONFIG_DIR": "C:/inherited", "ANTHROPIC_BASE_URL": "http://inherited:4000",
                 "ANTHROPIC_API_KEY": "sk-inherited-not-orbits", "HTTPS_PROXY": "http://proxy:8080",
                 "FUTURE_PROVIDER_TOKEN": "sentinel-future"}

    def test_account_environment_is_built_from_an_empty_mapping(self):
        import tempfile
        saved = {k: os.environ.get(k) for k in self.SENTINELS}
        os.environ.update(self.SENTINELS)
        try:
            env = self.cloud._account_env(self.claude)
            interactive = self.cloud._account_env(self.claude, interactive=True)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        for name in self.SENTINELS:
            self.assertNotIn(name, env)
        self.assertFalse([k for k in env if k.startswith(("ANTHROPIC_", "CLAUDE_"))])
        self.assertEqual(env["HOME"], engine.H)
        dirs = env["PATH"].split(os.pathsep)
        self.assertIn(os.path.dirname(self.claude), dirs)
        self.assertIn(engine.BIN, dirs)
        self.assertIn(osinfo.path_dirs()[0], dirs)
        if osinfo.KIND == "windows":
            self.assertEqual(env["TEMP"], tempfile.gettempdir())
            self.assertEqual(env["TMP"], tempfile.gettempdir())
            self.assertEqual(env["USERPROFILE"], engine.H)
            allowed = {"PATH", "HOME", "TEMP", "TMP", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "SYSTEMROOT",
                       "WINDIR", "COMSPEC", "PATHEXT", "USERNAME", "USERDOMAIN", "APPDATA", "LOCALAPPDATA",
                       "PROGRAMDATA", "PYTHONUTF8"}
        else:
            self.assertEqual(env["TMPDIR"], tempfile.gettempdir())
            allowed = {"PATH", "HOME", "TMPDIR", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE"}
        self.assertLessEqual(set(env), allowed)
        self.assertNotIn("TERM", env)
        self.assertEqual(interactive["TERM"], "xterm-256color")               # session bootstrap only
        self.assertEqual({k for k in interactive if k != "TERM"}, set(env))

    # -- T025
    def test_manual_enable_and_auto_enable_require_a_fresh_check(self):
        import orders
        self.assertTrue(self.cloud.account_status()["eligible"])              # prime a positive display cache
        self.fake.auth = {"loggedIn": True, "authMethod": "api_key"}
        with self.assertRaises(self.cloud.CloudError) as ctx:
            self.cloud.enable(self.eid)
        self.assertIn("sign-in", str(ctx.exception))
        self.assertFalse(self.cloud.is_on(self.eid))
        before = set(engine.registry()["employees"])
        orders.execute("Alex", "hire", {"name": "Nia", "role": "Writer", "first_day": False})
        new = (set(engine.registry()["employees"]) - before).pop()
        self.assertFalse(self.cloud.is_on(new))                              # ordinary work is still hired

    def test_eligibility_loss_keeps_the_switch_but_blocks_cloud_launches(self):
        import panel
        self.cloud.enable(self.eid)
        self.assertTrue(self.cloud.is_on(self.eid))
        self.cloud._save(self.eid, {"slots": {"10:00": {"trigger": "t1"}}})
        self.auth(True, "oauth_token")
        with self.assertRaises(self.cloud.CloudError):
            self.cloud.trigger("update", "t1", {"enabled": False})            # a fresh launch is refused
        st = self.cloud.status(self.eid)
        self.assertTrue(st["on"])                                            # the flag stays configured
        self.assertFalse(st["eligible"])
        self.assertTrue(st["blocked"])
        self.assertTrue(st["why_not"])
        self.assertIn(self.eid, [m["id"] for m in panel.members()])           # local work still shows

    def test_owner_disable_is_local_and_remote_cleanup_is_best_effort(self):
        self.cloud.enable(self.eid)
        self.cloud._save(self.eid, {"slots": {"10:00": {"trigger": "t1"}}})
        self.auth(True, "third_party")
        real, tried = self.cloud.trigger, []

        def refuse(*a, **k):
            tried.append(a)
            raise self.cloud.CloudError("The cloud shift needs a Claude plan sign-in on this computer.")
        self.cloud.trigger = refuse
        try:
            reply = self.cloud.disable(self.eid)                             # no positive eligibility needed
        finally:
            self.cloud.trigger = real
        self.assertIn("off", reply)
        self.assertFalse(self.cloud.is_on(self.eid))
        self.assertEqual(len(tried), 1)                                       # cleanup was attempted, then skipped

    # -- T026
    def test_launch_helpers_take_a_fresh_check_and_the_account_environment(self):
        made = self.cloud.trigger("create", body={"name": "x"})
        self.assertEqual(made["trigger"]["id"], "trig_9")
        self.assertEqual(len([c for c in self.fake.calls if c[0][1:3] == ["auth", "status"]]), 1)
        cmd, kw = self.launches()[0]
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "")
        self.assertIn("RemoteTrigger", cmd)
        self.assertIn("--no-session-persistence", cmd)
        self.assertEqual(kw["env"], self.cloud._account_env(self.claude))

        self.fake.calls.clear()
        self.cloud.send("session_1", "hello")
        cmd, kw = self.launches()[0]
        self.assertEqual(cmd[cmd.index("--cloud") + 1], "session_1")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "")
        self.assertEqual(kw["env"], self.cloud._account_env(self.claude))

        self.fake.calls.clear()
        self.assertEqual(self.cloud.environment(), "env_ABCDEFGHIJ")
        cmd, kw = self.launches()[0]
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "")
        self.assertEqual(kw["env"], self.cloud._account_env(self.claude))

    def test_launch_helpers_bypass_a_stale_positive_cache(self):
        self.assertTrue(self.cloud.account_status()["eligible"])
        self.fake.auth = {"loggedIn": True, "authMethod": "third_party"}
        self.cloud._save(self.eid, {"slots": {}})
        for fn, args in ((self.cloud.trigger, ("list",)),
                         (self.cloud.send, ("session_1", "hello")),
                         (self.cloud.environment, ()),
                         (self.cloud.new_session, (self.eid, TMP, "hi")),
                         (self.cloud._transcript, (self.eid, "session_1"))):
            with self.assertRaises(self.cloud.CloudError, msg=fn.__name__):
                fn(*args)                                                     # every L07–L11 takes a fresh check

    def test_transcript_launch_uses_the_account_environment(self):
        import io
        real_popen, real_expand = self.cloud.subprocess.Popen, self.cloud.os.path.expanduser
        holder = {}

        class P:
            def __init__(self, cmd, **kw):
                holder.update(cmd=list(cmd), kw=kw)
                self.stdin = io.StringIO()
                folder = os.path.join(os.path.expanduser("~/.claude/projects"),
                                      re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(os.path.join(
                                          engine.HOME, ".runtime", "ada", "cloud-pull"))))
                os.makedirs(folder, exist_ok=True)
                holder["path"] = os.path.join(folder, "new.jsonl")
                with open(holder["path"], "w") as fh:
                    fh.write("{}\n")

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

            def terminate(self):
                pass

            def kill(self):
                pass

        self.cloud.subprocess.Popen = P
        self.cloud.os.path.expanduser = lambda p: os.path.join(TMP, "home") + p[1:]
        try:
            got = self.cloud._transcript(self.eid, "session_1")
        finally:
            self.cloud.subprocess.Popen, self.cloud.os.path.expanduser = real_popen, real_expand
        self.assertEqual(got, holder["path"])
        cmd = holder["cmd"]
        self.assertIn("--teleport", cmd)
        self.assertEqual(cmd[cmd.index("--teleport") + 1], "session_1")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "")
        self.assertEqual(holder["kw"]["env"], self.cloud._account_env(self.claude))


class ExtraComputing(unittest.TestCase):
    """The third option: the owner's own private GitHub repository. Never needed; nothing happens until it's connected."""

    def setUp(self):
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {}, "employees": {}, "panel": {"port": 7391}})
        import compute
        self.c = compute
        self.bin = tempfile.mkdtemp(dir=TMP)
        self.path = os.environ["PATH"]

    def tearDown(self):
        os.environ["PATH"] = self.path

    def fake_gh(self, visibility="PRIVATE", permission="ADMIN"):
        log = os.path.join(self.bin, "gh.log")
        with open(os.path.join(self.bin, "gh"), "w") as fh:
            fh.write("#!/bin/sh\necho \"$@\" >> %s\ncase \"$1 $2\" in\n"
                     "\"repo view\") echo '{\"visibility\":\"%s\",\"viewerPermission\":\"%s\"}';;\n"
                     "\"api repos/a/b/contents/.github/workflows/orbit-compute.yml\") exit 1;;\n"
                     "*) echo '{}';;\nesac\n" % (log, visibility, permission))
        os.chmod(os.path.join(self.bin, "gh"), 0o755)
        os.environ["PATH"] = self.bin + os.pathsep + self.path
        return log

    @POSIX_FIXTURE
    def test_connect_needs_a_private_repo_you_can_write_to(self):
        self.fake_gh("PUBLIC")
        with self.assertRaisesRegex(self.c.ComputeError, "isn't private"):
            self.c.connect("a/b")
        self.fake_gh("PRIVATE", "READ")
        with self.assertRaisesRegex(self.c.ComputeError, "can't write"):
            self.c.connect("a/b")
        log = self.fake_gh()
        self.assertEqual(self.c.connect("https://github.com/a/b"), "a/b")
        with open(log) as fh:
            self.assertIn("-X PUT repos/a/b/contents/.github/workflows/orbit-compute.yml", fh.read())
        with self.assertRaisesRegex(self.c.ComputeError, "owner/name"):
            self.c.connect("justaname")

    def test_not_connected_is_fine(self):
        self.assertEqual(self.c.repo(), "")
        with self.assertRaisesRegex(self.c.ComputeError, "isn't connected"):
            self.c.run("echo hi", [], 5)

    def test_only_your_own_files_travel(self):
        ws = tempfile.mkdtemp(dir=TMP)
        with self.assertRaisesRegex(self.c.ComputeError, "isn't in your folder"):
            self.c._within(ws, "../../etc/passwd")
        with self.assertRaisesRegex(self.c.ComputeError, "doesn't exist"):
            self.c._within(ws, "nope.txt")

    def test_the_workflow_is_valid_and_has_no_secrets(self):
        self.assertIn("workflow_dispatch", self.c.WORKFLOW_YML)
        self.assertIn("contents: read", self.c.WORKFLOW_YML)
        self.assertNotIn("secrets.", self.c.WORKFLOW_YML)
        self.assertIn("COMMAND: ${{ inputs.command }}", self.c.WORKFLOW_YML)   # passed by env, never pasted into the script

class NativeWindows(unittest.TestCase):
    """Native Windows, no WSL underneath (T003/T015): its kind, its paths, its secrets, and the
    sandbox shape its runs carry. Module-state assertions run in a subprocess with ORBIT_OS=windows
    (engine is imported once per process, so in-process fakes can't influence the module state) —
    the same trick the existing ORBIT_OS=wsl harness uses."""

    def win_py(self, code, kind="windows"):
        r = win_py(code, kind)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    # --- the kind and its identity (T010/T011)
    def test_windows_without_wsl_is_its_own_kind(self):
        self.assertEqual(self.win_py("import osinfo; print(osinfo.KIND)").strip(), "windows")

    def test_a_windows_pc_is_supported_and_titled(self):
        out = self.win_py("import osinfo; print(osinfo.DEVICE, osinfo.SUPPORTED, osinfo.NAME)").strip()
        self.assertEqual(out, "PC True Windows")            # the panel/build can say "on this PC"

    def test_windows_says_pc(self):
        self.assertEqual(self.win_py("import osinfo; print(osinfo.local('on this Mac'))").strip(),
                         "on this PC")

    # --- programs and paths (T011)
    def test_windows_programs_are_found_in_windows_places(self):
        dirs = json.loads(self.win_py("import osinfo, json; print(json.dumps(osinfo.path_dirs()))"))
        norm = [os.path.normcase(d) for d in dirs]
        self.assertTrue(any("winget\\links" in d for d in norm), norm[:2])   # winget-installed CLIs
        self.assertTrue(any(d.endswith("system32") for d in norm))          # where wxc-exec lands too
        self.assertTrue(any("powershell" in d for d in norm))               # PowerShell.exe resolves

    def test_native_paths_read_directly_wsl_hops_survive(self):
        win = json.loads(self.win_py("import osinfo, json, sys; print(json.dumps("
                                     "[osinfo.win_path(r'C:\\x'), osinfo.win_env('APPDATA') != '', "
                                     "osinfo.win_python() == [sys.executable]]))"))
        self.assertEqual(win, [r"C:\x", True, True])        # native Windows: no wslpath/cmd.exe/py.exe hops

    @unittest.skipUnless(os.name == "nt", "real Windows paths")
    def test_home_built_on_the_default_has_no_forward_slashes(self):
        """expanduser('~/Staff') keeps the '/' on Windows ('C:\\Users\\me/Staff'), and a path built on
        HOME is then read by cmd.exe as a switch: mklink says 'Invalid switch - "Staff\\.runtime\\..."'
        and every routine dies before it starts. normpath must remove it."""
        out = self.win_py("import os; os.environ.pop('STAFFROOM_HOME', None); import engine; print(engine.HOME)").strip()
        self.assertNotIn("/", out)
        self.assertTrue(out.endswith("\\Staff"), out)

    # --- secrets (T013)
    def test_windows_secrets_are_the_windows_stores(self):
        paths = json.loads(self.win_py("import engine, json; print(json.dumps(engine.SECRET_PATHS))"))
        joined = " ".join(os.path.normcase(p).replace("\\", "/") for p in paths)
        for bit in (".ssh", ".aws", "gnupg", "rclone", ".netrc", "credentials.json", "channels",
                    "google/chrome", "microsoft/edge", "inetcookies",
                    "desktop", "documents", "downloads"):
            self.assertIn(bit, joined, bit)                 # every column in data-model "Windows-native value"
        self.assertFalse(any(p.startswith("/mnt") for p in paths))          # no /mnt bridge on native Windows

    def test_wsl_runs_still_wall_off_the_windows_drives(self):
        out = self.win_py("import engine; print(any(p == '/mnt' for p in engine.SECRET_PATHS))", "wsl")
        self.assertEqual(out.strip(), "True")

    @unittest.skipUnless(os.name == "nt", "real Windows paths")
    def test_crew_browser_found_where_windows_installers_put_it(self):
        """Chrome's Windows installer never adds itself to PATH, and the kit's own Playwright Chromium
        lives under LOCALAPPDATA: browser.chrome() must find both, or doctor keeps saying 'no Chrome'.
        The roots are set in-process (os.environ) because some Windows builds rewrite the child
        environment block's shell-folder variables at process creation."""
        pf, la = tempfile.mkdtemp(dir=TMP), tempfile.mkdtemp(dir=TMP)
        os.makedirs(os.path.join(pf, "Google", "Chrome", "Application"))
        os.makedirs(os.path.join(la, "ms-playwright", "chromium-9999", "chrome-win64"))
        app = os.path.join(pf, "Google", "Chrome", "Application")
        with open(os.path.join(app, "chrome.exe"), "w") as fh:
            fh.write("fake")
        exe = os.path.join(la, "ms-playwright", "chromium-9999", "chrome-win64", "chrome.exe")
        with open(exe, "w") as fh:
            fh.write("fake")
        code = ("import os, sys;"
                "os.environ['ProgramFiles'] = os.environ['ProgramFiles(x86)'] = sys.argv[1];"
                "os.environ['LOCALAPPDATA'] = sys.argv[2];"
                "import browser; print(browser.chrome() or 'none')")
        env = dict(os.environ, ORBIT_OS="windows", PYTHONPATH=os.path.join(KIT, "core"))
        r = subprocess.run([sys.executable, "-c", code, pf, la], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(os.path.normcase(r.stdout.strip()),
                         os.path.normcase(os.path.join(app, "chrome.exe")))   # real Chrome wins
        os.remove(os.path.join(app, "chrome.exe"))
        r = subprocess.run([sys.executable, "-c", code, pf, la], env=env, capture_output=True, text=True)
        self.assertEqual(os.path.normcase(r.stdout.strip()),
                         os.path.normcase(exe))                              # then the setup's Chromium
        os.remove(exe)
        r = subprocess.run([sys.executable, "-c", code, pf, la], env=env, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "none")                           # none: doctor says so honestly

    # --- the sandbox shape of a native run (T033)
    def test_windows_runs_carry_the_containment_hook_not_fail_unavailable(self):
        r = json.loads(self.win_py(
            "import engine, json; b = engine.sandbox_blob({'id': 't', 'workspace': '.', 'name': 't'}, []); "
            "h = (b.get('hooks') or {}).get('PreToolUse', [{}])[0]; hk = h.get('hooks', [{}])[0]; "
            "print(json.dumps({'fail': b['sandbox'].get('failIfUnavailable'), "
            "'matcher': h.get('matcher'), 'command': hk.get('command', ''), 'args': hk.get('args', [])}))"))
        self.assertEqual(r["fail"], None)                   # the agent starts normally; MXC holds the line
        self.assertEqual(r["matcher"], "Bash|PowerShell")
        self.assertEqual(r["command"], sys.executable)      # exec form: no shell quoting of a path with spaces
        self.assertTrue(any(a.replace("\\", "/").endswith("core/mxc.py") for a in r["args"]))
        self.assertIn("--hook", r["args"])                  # Orbit's helper, not an inline blob

    def test_wsl_runs_keep_the_fail_unavailable_sandbox(self):   # T034 regression parity
        for kind in ("wsl", "mac", "linux"):
            r = json.loads(self.win_py(
                "import engine, json; b = engine.sandbox_blob({'id': 't', 'workspace': '.', 'name': 't'}, []); "
                "print(json.dumps([b['sandbox'].get('failIfUnavailable'), 'hooks' in b]))", kind))
            self.assertEqual(r, [True, False], kind)


class EmployeeEntryMode(unittest.TestCase):
    """T036/T037: every native-Windows employee entry point uses the same MXC/WSL2 decision.
    MXC permits contained headless/terminal work, WSL2 mode refuses all native-side work, and
    employee Desktop sessions remain unavailable until feature 003 is implemented."""

    def setUp(self):
        self.old_kind, self.old_registry = osinfo.KIND, engine.registry()
        osinfo.KIND = "windows"
        self.ws = os.path.join(TMP, "employees", "tess-entry-mode")
        os.makedirs(os.path.join(self.ws, "state"), exist_ok=True)
        engine.save_registry({
            "team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}},
            "employees": {"tess": {"name": "Tess", "role": "Research", "workspace": self.ws,
                                    "status": "active", "abilities": []}},
            "defaults": {"model": "sonnet"}, "panel": {"port": 7391},
            "platform": {"sandbox_mode": "mxc", "decided_by": "owner", "decided_at": "2026-11-10",
                         "mxc_unavailable_reason": None},
        })
        self.emp = engine.employee("tess")

    def tearDown(self):
        osinfo.KIND = self.old_kind
        engine.save_registry(self.old_registry)

    def patch(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, old)

    def mode(self, value):
        reg = engine.registry()
        reg["platform"] = {"sandbox_mode": value, "decided_by": "owner", "decided_at": "2026-11-10",
                           "mxc_unavailable_reason": None}
        engine.save_registry(reg)

    @staticmethod
    def setting(cmd):
        return json.loads(cmd[cmd.index("--settings") + 1])

    def test_mxc_headless_and_terminal_work_share_the_containment_controls(self):
        calls = []
        self.patch(engine, "skills_plugin", lambda emp, wanted: os.path.join(TMP, "entry-mode-skills"))
        self.patch(engine, "resolve_claude", lambda: "claude")
        self.patch(engine, "wait_for_window", lambda *a, **k: True)
        self.patch(engine, "stream", lambda cmd, prompt, ws, env, timeout, on_step=None:
                   (calls.append((cmd, prompt, ws, env)) or ({"result": "done", "num_turns": 1}, [])))

        result = engine.run(self.emp, "Do the work", "followup")
        window = engine.chat_window(self.emp)
        self.assertTrue(result["ok"])
        self.assertEqual(len(calls), 1)
        headless, interactive = calls[0][0], window["cmd"]
        self.assertIn("-p", headless)
        self.assertNotIn("-p", interactive)
        self.assertEqual(headless[headless.index("--setting-sources") + 1], "user,project")
        self.assertEqual(interactive[interactive.index("--setting-sources") + 1], "user,project")
        h_settings, i_settings = self.setting(headless), self.setting(interactive)
        self.assertEqual(h_settings, i_settings)                         # sandbox, MXC hook and guard inputs
        hook = h_settings["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertEqual(hook["command"], sys.executable)
        self.assertTrue(any(a.replace("\\", "/").endswith("core/mxc.py") for a in hook["args"]))
        self.assertIn("--hook", hook["args"])
        self.assertEqual(headless.count(engine.GUARD), 1)
        self.assertEqual(interactive.count(engine.GUARD), 1)

    def test_wsl2_mode_refuses_run_and_terminal_chat_before_launch(self):
        self.mode("wsl2")
        self.patch(engine, "stream", lambda *a, **k: self.fail("a blocked run reached Claude"))
        result = engine.run(self.emp, "Do the work")
        self.assertFalse(result["ok"])
        self.assertIn("inside WSL", result["text"])
        with self.assertRaises(SystemExit) as stopped:
            orbit_cli().chat("tess", show=True)
        self.assertIn("inside WSL", str(stopped.exception))

    def test_wsl2_mode_refuses_open_panel_and_employee_app(self):
        import claudeapp
        import orders
        import panel
        self.mode("wsl2")
        opened = []
        self.patch(osinfo, "open_terminal", lambda *a, **k: opened.append((a, k)) or True)
        with self.assertRaisesRegex(RuntimeError, "inside WSL"):
            claudeapp.open_chat("tess")
        with self.assertRaisesRegex(orders.OrderError, "inside WSL"):
            panel.claude_session("tess")
        old_argv = sys.argv
        sys.argv = ["orbit", "open", "tess"]
        self.addCleanup(setattr, sys, "argv", old_argv)
        with self.assertRaises(SystemExit) as stopped:
            orbit_cli().main()
        self.assertIn("inside WSL", str(stopped.exception))
        self.assertEqual(opened, [])

    def test_refresh_checks_the_mode_before_touching_employee_session_files(self):
        import claudeapp
        import desk
        import hire
        import staffd
        for mode in ("mxc", "wsl2"):
            with self.subTest(mode=mode):
                self.mode(mode)
                touched = []
                with mock.patch.object(desk, "ensure", return_value=desk.DIR), \
                        mock.patch.object(hire, "upgrade_workspace", side_effect=lambda emp: touched.append("upgrade")), \
                        mock.patch.object(engine, "claude_session", side_effect=lambda emp: touched.append("session")), \
                        mock.patch.object(claudeapp, "write_plan", side_effect=lambda emp: touched.append("plan")), \
                        mock.patch.object(staffd, "log"):
                    staffd.refresh_sessions()
                self.assertEqual(touched, [], "blocked Desktop refresh modified %s employee state" % mode)

    def test_mxc_panel_uses_contained_terminal_argv_but_desktop_surfaces_refuse(self):
        import claudeapp
        import panel
        launched = []
        self.patch(osinfo, "open_terminal", lambda argv, name="": launched.append((list(argv), name)) or True)
        result = panel.claude_session("tess")
        argv = [os.path.join(engine.KIT, "orbit"), "chat", "tess"]
        self.assertEqual(launched, [(argv, "chat-tess")])
        self.assertEqual(result["how"], "terminal")
        self.assertEqual(result["command"], subprocess.list2cmdline([sys.executable] + argv))
        with self.assertRaisesRegex(RuntimeError, "Desktop sessions"):
            engine.claude_session("tess")
        with self.assertRaisesRegex(RuntimeError, "Desktop sessions"):
            claudeapp.open_chat("tess")
        old_argv = sys.argv
        sys.argv = ["orbit", "open", "tess"]
        self.addCleanup(setattr, sys, "argv", old_argv)
        with self.assertRaises(SystemExit) as stopped:
            orbit_cli().main()
        self.assertIn("Desktop sessions", str(stopped.exception))


class PlatformMessagesAndDesk(unittest.TestCase):
    """T037: notification text, terminal argv, and the native-Windows owner desk remain platform-owned."""

    def setUp(self):
        self.old_kind, self.old_registry = osinfo.KIND, engine.registry()
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)
        engine.save_registry({"team_name": "Test", "owners": {"local-alex": {"name": "Alex", "local": True}},
                              "employees": {}, "panel": {"port": 7391}})

    def tearDown(self):
        osinfo.KIND = self.old_kind
        engine.save_registry(self.old_registry)

    def patch(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, old)

    @staticmethod
    def notification_body(text, more):
        body = " ".join((text or "").split())
        if len(body) > 200:
            body = body[:197].rsplit(" ", 1)[0] + "…"
        if more:
            body = (body + " (%s)" % more)[:240]
        return body

    def test_every_notification_platform_receives_the_same_computed_body(self):
        raw = "  Line one\nline   two's " + ("long-word " * 30)
        expected = self.notification_body(raw, "Mission Control")
        calls = []
        self.patch(osinfo.subprocess, "run", lambda args, **kw: calls.append(list(args)) or SimpleNamespace(returncode=0))
        self.patch(osinfo, "which", lambda name: name if name == "notify-send" else None)
        os.makedirs(osinfo.RUNTIME, exist_ok=True)

        osinfo.KIND = "mac"
        self.patch(osinfo, "notifier", lambda: "Orbit.app")
        self.assertTrue(osinfo.notify("Crew", raw, "Mission Control"))
        with open(os.path.join(osinfo.RUNTIME, "notify.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "Crew\n%s\n" % expected)

        osinfo.KIND = "linux"
        self.assertTrue(osinfo.notify("Crew", raw, "Mission Control"))
        self.assertEqual(calls[-1], ["notify-send", "Crew", expected])

        osinfo.KIND = "windows"
        self.assertTrue(osinfo.notify("Crew", raw, "Mission Control"))
        ps = calls[-1][-1]
        self.assertIn("$n.ShowBalloonTip(5000, 'Crew', '%s', 2)" % expected.replace("'", "''"), ps)
        self.assertNotIn("\n", expected)
        self.assertIn("…", expected)

    def test_native_terminal_launch_and_fallback_display_keep_an_argv_boundary(self):
        osinfo.KIND = "windows"
        calls = []
        self.patch(osinfo.subprocess, "Popen", lambda argv, **kw: calls.append((list(argv), kw)) or SimpleNamespace())
        argv = [os.path.join(engine.KIT, "orbit"), "chat", "name with spaces"]
        expected = [sys.executable] + argv
        self.assertTrue(osinfo.open_terminal(argv, "crew chat"))
        self.assertEqual(calls[0][0], expected)
        self.assertEqual(calls[0][1]["creationflags"], getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010))
        self.assertNotIn(os.path.basename(calls[0][0][0]).lower(), ("cmd.exe", "powershell.exe"))
        self.assertEqual(osinfo.display_argv(argv), subprocess.list2cmdline(expected))
        osinfo.KIND = "linux"
        self.assertEqual(osinfo.display_argv(["orbit", "chat", "name with spaces"]),
                         "orbit chat 'name with spaces'")

    def test_windows_front_desk_allows_only_the_exact_orbit_command_and_normalized_paths(self):
        import desk
        osinfo.KIND = "windows"
        desk.ensure()
        with open(os.path.join(desk.DIR, ".claude", "settings.local.json"), encoding="utf-8") as fh:
            perms = json.load(fh)["permissions"]
        orbit = os.path.normpath(os.path.join(engine.KIT, "orbit"))
        command = subprocess.list2cmdline([os.path.normpath(sys.executable), orbit])
        command_rules = [r for r in perms["allow"] if r.startswith(("PowerShell(", "Bash("))]
        self.assertEqual(command_rules, ["PowerShell(%s *)" % command, "PowerShell(%s)" % command])
        self.assertNotIn("PowerShell(orbit *)", perms["allow"])
        self.assertFalse(any(r.startswith("Bash(") for r in perms["allow"]))

        def absolute(path):
            return "//" + os.path.realpath(path).replace("\\", "/")
        self.assertIn("Read(%s/**)" % absolute(engine.HOME), perms["allow"])
        self.assertIn("Write(%s/**)" % absolute(desk.DIR), perms["allow"])
        self.assertIn("Read(%s/**)" % absolute(engine.SECRETS), perms["deny"])
        self.assertIn("Edit(%s)" % absolute(engine.REGISTRY), perms["deny"])
        self.assertIn("Write(%s/**)" % absolute(os.path.join(engine.HOME, "employees")), perms["deny"])

    def test_platform_docs_keep_connection_and_native_desktop_boundaries_honest(self):
        docs = {}
        for name in ("README.md", "SETUP.md", "PRODUCT.md"):
            with open(os.path.join(KIT, name), encoding="utf-8") as fh:
                docs[name] = fh.read()
        with open(os.path.join(KIT, "VERSION"), encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), "0.13.0")
        for name, text in docs.items():
            self.assertIn("configured connection", text.lower(), name)
        flat = {name: " ".join(text.split()) for name, text in docs.items()}
        self.assertIn("Native-Windows employee Desktop chats stay disabled", flat["README.md"])
        self.assertIn("Native-Windows employee Desktop chats remain disabled", flat["SETUP.md"])
        self.assertIn("Product-release readiness remains blocked", flat["PRODUCT.md"])
        self.assertNotIn("real-host MXC validation is optional", docs["PRODUCT.md"])
        self.assertIn("orbit open <h>                   their own Claude-app chat (Mac/Linux/WSL; native Windows stays gated)",
                      docs["README.md"])


class Mode(unittest.TestCase):
    """The containment path on Windows: MXC by default, WSL2 only by owner choice or a recorded
    unavailability — nothing else may decide it (R4.1, SC3). In-process against the registry."""

    def setUp(self):
        self.kind = osinfo.KIND
        reg = engine.registry()
        reg.pop("platform", None)
        engine.save_registry(reg)

    def tearDown(self):
        osinfo.KIND = self.kind
        reg = engine.registry()
        reg.pop("platform", None)
        engine.save_registry(reg)

    def test_windows_defaults_to_mxc_and_elsewhere_to_wsl2(self):
        import mxc
        try:
            osinfo.KIND = "windows"
            self.assertEqual(mxc.mode(), "mxc")             # the mode isn't stored here: it's the default
            info = mxc.mode_info()
            self.assertEqual(info, {"sandbox_mode": "mxc", "decided_by": "", "decided_at": "",
                                    "mxc_unavailable_reason": None})
            osinfo.KIND = "wsl"
            self.assertEqual(mxc.mode(), "wsl2")            # a Mac/WSL/Linux box: the old way, always
        finally:
            osinfo.KIND = self.kind

    def test_only_an_owner_or_recorded_unavailability_moves_the_mode(self):
        import mxc
        osinfo.KIND = "windows"
        with self.assertRaises(ValueError):
            mxc.set_mode("banana")                          # not a mode
        with self.assertRaises(ValueError):
            mxc.set_mode("wsl2", "anyone")                  # decided_by must be owner or unavailable
        mxc.set_mode("wsl2")                                # an owner choice needs no reason
        info = mxc.mode_info()
        self.assertEqual((info["sandbox_mode"], info["decided_by"]), ("wsl2", "owner"))
        self.assertTrue(info["decided_at"])
        self.assertIsNone(info["mxc_unavailable_reason"])

    def test_unavailability_falls_back_to_wsl2_with_its_reason_recorded(self):
        import mxc
        osinfo.KIND = "windows"
        with self.assertRaises(ValueError):
            mxc.record_unavailable("")                      # a silent fallback is forbidden (R4.1)
        mxc.record_unavailable("the MXC runtime is missing")
        self.assertEqual(mxc.mode_info()["sandbox_mode"], "wsl2")
        self.assertEqual(mxc.mode_info()["decided_by"], "unavailable")
        self.assertEqual(mxc.unavailable_reason(), "the MXC runtime is missing")

    def test_a_stored_mode_beats_the_default(self):
        import mxc
        reg = engine.registry()
        reg["platform"] = {"sandbox_mode": "wsl2", "decided_by": "owner", "decided_at": "2026-11-04",
                           "mxc_unavailable_reason": None}
        self.assertEqual(mxc.mode_info(reg)["sandbox_mode"], "wsl2")
        osinfo.KIND = "wsl"
        reg["platform"]["sandbox_mode"] = "mxc"             # nonsense on non-Windows, but storage is neutral
        self.assertEqual(mxc.mode_info(reg)["sandbox_mode"], "mxc")


class SandboxOptOut(unittest.TestCase):
    """The owner's explicit opt-out ("sandbox": false): on native Windows mxc mode it removes the MXC
    hook, an absent key (every pre-choice install) keeps it on, and only the explicit False counts.
    The settings shape runs in an ORBIT_OS=windows subprocess (module state is really that kind's);
    the CLI choice runs in-process against the registry."""

    def setUp(self):
        self.kind = osinfo.KIND
        reg = engine.registry()
        reg.pop("sandbox", None)
        reg.pop("platform", None)                           # the mxc default, like a fresh install
        engine.save_registry(reg)

    def tearDown(self):
        osinfo.KIND = self.kind
        reg = engine.registry()
        reg.pop("sandbox", None)
        reg.pop("platform", None)
        engine.save_registry(reg)

    def _settings(self, sandbox_value, kind="windows"):
        code = ("import os, json, tempfile;"
                "home = tempfile.mkdtemp(); os.environ['STAFFROOM_HOME'] = home;"
                "import engine;"
                "engine.save_registry({} if %(v)r == 'absent' else {'sandbox': %(v)r});"
                "print(json.dumps(json.loads(engine.settings_json("
                "{'id': 't', 'workspace': '.', 'name': 't'}, []))))") % {"v": sandbox_value}
        r = win_py(code, kind)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_a_windows_default_keeps_mxc(self):             # T004: absent key == containment on
        s = self._settings("absent")
        self.assertTrue(s["sandbox"]["enabled"])
        self.assertIn("hooks", s)

    def test_an_explicit_false_removes_the_mxc_hook(self):  # the owner's opt-out is honored
        self.assertEqual(self._settings(False), {"enabledPlugins": {}, "sandbox": {"enabled": False}})

    def test_sandbox_true_still_carries_the_hook(self):
        s = self._settings(True)
        self.assertTrue(s["sandbox"]["enabled"])
        self.assertIn("hooks", s)

    def test_the_other_platforms_never_change(self):        # T004: byte-identical off/on states
        self.assertEqual(self._settings("absent", "mac"), {"enabledPlugins": {}, "sandbox": {"enabled": False}})
        self.assertEqual(self._settings(False, "mac"), {"enabledPlugins": {}, "sandbox": {"enabled": False}})
        mac_on = self._settings(True, "mac")
        self.assertTrue(mac_on["sandbox"]["enabled"] and mac_on["sandbox"]["failIfUnavailable"])
        self.assertNotIn("hooks", mac_on)

    def _cli(self, yes_answer=None):
        """orbit_cli with quiet output and a scripted confirmation; yes_answer None means
        the confirmation must never be asked."""
        cli = orbit_cli()
        asked = []

        def fake_yes(q, default=True):
            if yes_answer is None:
                raise AssertionError("the confirmation must not be asked here")
            asked.append(q)
            return yes_answer

        patches = [mock.patch.object(cli, "yes", fake_yes),
                   mock.patch.object(cli, "say", lambda *a: None),
                   mock.patch.object(engine, "claude_session", lambda eid: None)]
        for p in patches:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in patches])
        return cli, asked

    def test_off_prompts_on_windows_and_an_aborted_answer_changes_nothing(self):
        cli, asked = self._cli(yes_answer=False)
        cli.sandbox_cmd("off")
        self.assertTrue(asked)                              # the owner was warned and asked
        self.assertNotIn("sandbox", engine.registry())      # nothing written on a refusal
        reg = engine.registry()
        reg["sandbox"] = True
        engine.save_registry(reg)
        cli.sandbox_cmd("off")
        self.assertIs(engine.registry().get("sandbox"), True)   # an aborted downgrade keeps the sandbox

    def test_a_confirmed_off_writes_the_explicit_false(self):
        cli, _ = self._cli(yes_answer=True)
        cli.sandbox_cmd("off")
        self.assertIs(engine.registry().get("sandbox"), False)

    def test_the_yes_flag_skips_the_prompt(self):
        cli, asked = self._cli(yes_answer=None)
        cli.sandbox_cmd("off", confirmed=True)
        self.assertEqual(asked, [])
        self.assertIs(engine.registry().get("sandbox"), False)

    def test_off_on_a_mac_never_prompts(self):
        cli, asked = self._cli(yes_answer=None)
        osinfo.KIND = "mac"
        cli.sandbox_cmd("off")
        self.assertEqual(asked, [])
        self.assertIs(engine.registry().get("sandbox"), False)

    def test_status_names_the_opt_out(self):
        cli, _ = self._cli(yes_answer=None)
        osinfo.KIND = "windows"
        reg = engine.registry()
        reg["sandbox"] = False
        engine.save_registry(reg)
        lines = []
        with mock.patch.object(cli, "say", lambda m="": lines.append(m)):
            cli.say_sandbox_status()
        self.assertTrue(any("off at the owner's choice" in m for m in lines))

    def test_doctor_reports_an_opted_out_mxc_as_the_owners_choice(self):    # T008/T009
        import mxc as mxc_mod
        cli = orbit_cli()
        osinfo.KIND = "windows"
        reg = engine.registry()
        reg["sandbox"] = False
        engine.save_registry(reg)
        with mock.patch.object(cli, "_win_build", lambda: "10.0.19045"), \
             mock.patch.object(cli, "service_pythonw", lambda: sys.executable), \
             mock.patch.object(cli, "sandbox_probe", lambda: {"verdict": "refused"}), \
             mock.patch.object(mxc_mod, "discover", lambda: {"ok": False, "reason": "the runtime is gone"}):
            out = cli.windows_checks()
        self.assertTrue(any(ok and "off at the owner's choice" in m for ok, m, must in out))
        broken = [m for ok, m, must in out if not ok and must]
        self.assertFalse(any("wxc-exec" in m or "24H2" in m or "sandbox proof" in m for m in broken),
                         broken)                            # MXC is informational now, never must-fix

    def test_doctor_still_enforces_mxc_without_the_opt_out(self):
        import mxc as mxc_mod
        cli = orbit_cli()
        osinfo.KIND = "windows"
        with mock.patch.object(cli, "service_pythonw", lambda: sys.executable), \
             mock.patch.object(mxc_mod, "discover", lambda: {"ok": False, "reason": "the runtime is gone"}):
            out = cli.windows_checks()
        self.assertTrue(any(not ok and must and "wxc-exec" in m for ok, m, must in out),
                        out)                                # the default keeps MXC must-fix

    def test_setup_choice_defaults_to_no_sandbox_everywhere(self):   # T016: bare Enter = no sandbox
        cli, asked = self._cli(yes_answer=None)             # no mode confirmation is expected either
        for kind in ("windows", "mac", "wsl"):
            osinfo.KIND = kind
            reg = engine.registry()
            reg.pop("sandbox", None)
            engine.save_registry(reg)
            with mock.patch.object(cli, "yes", lambda q, default=True: default):   # bare Enter
                cli.setup_sandbox_choice(reg)
            self.assertIs(engine.registry().get("sandbox"), False, kind)
            self.assertNotIn("platform", engine.registry(), kind)   # no mode was recorded either

    def test_a_rerun_downgrades_the_sandbox_on_bare_enter(self):    # T016: re-run over "sandbox": true
        cli, _ = self._cli(yes_answer=None)
        osinfo.KIND = "windows"
        reg = engine.registry()
        reg["sandbox"] = True
        engine.save_registry(reg)
        with mock.patch.object(cli, "yes", lambda q, default=True: default):
            cli.setup_sandbox_choice(reg)
        self.assertIs(engine.registry().get("sandbox"), False)   # the explicit opt-out, deliberately re-asked

    def test_setup_choice_yes_on_windows_picks_mxc_when_it_passes(self):
        cli, _ = self._cli(yes_answer=None)
        osinfo.KIND = "windows"
        with mock.patch.object(cli, "yes", lambda q, default=True: True), \
             mock.patch.object(cli, "_win_build", lambda: "10.0.26100"), \
             mock.patch.object(cli, "sandbox_probe", lambda: {"verdict": "usable"}):
            import mxc as mxc_mod
            with mock.patch.object(mxc_mod, "discover", lambda: {"ok": True, "reason": ""}):
                cli.setup_sandbox_choice(engine.registry())
        reg = engine.registry()
        self.assertIs(reg["sandbox"], True)
        self.assertEqual((reg["platform"]["sandbox_mode"], reg["platform"]["decided_by"]), ("mxc", "owner"))

    def test_setup_choice_yes_offers_wsl2_only_when_mxc_is_broken(self):
        cli, asked = self._cli(yes_answer=None)
        osinfo.KIND = "windows"
        import mxc as mxc_mod
        modes = []
        with mock.patch.object(cli, "yes", lambda q, default=True: True), \
             mock.patch.object(cli, "_win_build", lambda: "10.0.19045"), \
             mock.patch.object(cli, "sandbox_probe", lambda: {"verdict": "usable"}), \
             mock.patch.object(mxc_mod, "discover", lambda: {"ok": True, "reason": ""}), \
             mock.patch.object(osinfo, "which", lambda name: "wsl.exe" if name == "wsl.exe" else None), \
             mock.patch.object(mxc_mod, "set_mode", lambda m, decided_by="": modes.append(m)):
            cli.setup_sandbox_choice(engine.registry())
        self.assertEqual(modes, ["wsl2"])                   # only the available mode was offered, no prompt
        self.assertEqual(asked, [])
        self.assertNotIn("sandbox", engine.registry())      # WSL2 mode doesn't set the Windows-side flag

    def test_setup_choice_with_no_mode_available_defaults_to_exiting(self):
        cli, _ = self._cli(yes_answer=None)
        osinfo.KIND = "windows"
        answers = iter([True, False])                       # wants a sandbox; declines running unsandboxed

        def fake_yes(q, default=True):
            return next(answers)

        with mock.patch.object(cli, "yes", fake_yes), \
             mock.patch.object(cli, "_win_build", lambda: "10.0.19045"), \
             mock.patch.object(osinfo, "which", lambda name: None):
            with self.assertRaises(SystemExit):
                cli.setup_sandbox_choice(engine.registry())
        self.assertNotIn("sandbox", engine.registry())      # the refusal changed nothing

    def test_setup_choice_continue_without_a_sandbox_when_asked(self):
        cli, _ = self._cli(yes_answer=None)
        osinfo.KIND = "windows"
        answers = iter([True, True])                        # sandbox yes, "continue unsandboxed?" yes

        def fake_yes(q, default=True):
            return next(answers)

        with mock.patch.object(cli, "yes", fake_yes), \
             mock.patch.object(cli, "_win_build", lambda: "10.0.19045"), \
             mock.patch.object(osinfo, "which", lambda name: None):
            cli.setup_sandbox_choice(engine.registry())
        self.assertIs(engine.registry().get("sandbox"), False)   # the explicit opt-out, as everywhere



class ClaudeAvailability(unittest.TestCase):
    """T004 (FR-001–FR-004): the mandatory Claude check is installation-only. A signed-out client
    passes; a missing or broken install gets installation/repair guidance with no account-login
    wording, and no general path probes account status at all."""

    def setUp(self):
        self.real = engine.resolve_claude

    def tearDown(self):
        engine.resolve_claude = self.real

    def status(self):
        return orbit_cli().claude_status()                 # the same check setup and doctor use

    def fake(self, **cfg):
        d = tempfile.mkdtemp(dir=TMP)
        p = fake_claude.install(d, **cfg)
        engine.resolve_claude = lambda: p
        return p

    def test_signed_out_client_passes_the_mandatory_check(self):
        p = self.fake(auth={"loggedIn": False, "authMethod": "none"})
        ok, msg = self.status()
        self.assertTrue(ok, msg)
        self.assertEqual(engine.claude_availability()["state"], "available")
        self.assertNotIn("sign", msg.lower())
        self.assertNotIn("auth login", msg.lower())
        self.assertIn("installed and available", msg)
        all_calls = fake_claude.calls(os.path.dirname(p))
        self.assertTrue(all_calls, "the fake was never invoked")
        self.assertTrue(all(c["argv"] == ["--version"] for c in all_calls),
                        "general availability must never call account status: %r" % [c["argv"] for c in all_calls])

    def test_missing_client(self):
        engine.resolve_claude = lambda: os.path.join(TMP, "no", "such", "claude")
        ok, msg = self.status()
        self.assertFalse(ok)
        a = engine.claude_availability()
        self.assertEqual(a["state"], "missing")
        self.assertIn("Install", a["detail"])
        self.assertNotIn("auth login", msg.lower())
        self.assertNotIn("auth login", a["detail"].lower())

    def test_broken_install(self):
        self.fake(version={"exit": 3})
        a = engine.claude_availability()
        self.assertEqual(a["state"], "broken")
        ok, msg = self.status()
        self.assertFalse(ok)
        self.assertIn("repair", msg.lower())
        self.assertNotIn("auth login", msg.lower())
        self.assertNotIn("sign", msg.lower())

    @unittest.skipUnless(os.name == "nt", "Windows install layout")
    def test_windows_finds_claude_exe_without_path_help(self):
        """The service runs with a minimal PATH: resolve_claude must still find the Windows installer's
        ~/.local/bin/claude.exe (the POSIX globs once matched nothing, so hiring broke with
        FileNotFoundError before Claude was even asked)."""
        profile = tempfile.mkdtemp(dir=TMP)
        bin_dir = os.path.join(profile, ".local", "bin")
        os.makedirs(bin_dir)
        exe = os.path.join(bin_dir, "claude.exe")
        with open(exe, "w") as fh:
            fh.write("fake")
        code = "import engine; print(engine.resolve_claude() or 'none')"
        r = subprocess.run([sys.executable, "-c", code],
                           env={"USERPROFILE": profile, "SYSTEMDRIVE": "C:",
                                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                                "PATH": os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32"),
                                "ORBIT_OS": "windows", "PYTHONPATH": os.path.join(KIT, "core")},
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(os.path.normcase(r.stdout.strip()), os.path.normcase(exe))


class SignedOutSetup(unittest.TestCase):
    """T012 (SC-001): the whole setup → structured hiring → employee-task story on one temporary
    Orbit home, with a fully signed-out fake Claude — every step succeeds on the effective
    connection, and no general path calls or mentions an account-login command."""

    @classmethod
    def setUpClass(cls):
        if osinfo.KIND == "windows":                       # only setUpClass touches the shared home
            raise unittest.SkipTest("needs the POSIX fake shim (employee argv vs. cmd.exe quoting); "
                                    "SC-001 runs in the macOS/Linux/WSL2 CI jobs")
        engine.save_registry({"team_name": "Signed-out test", "owners": {"111": {"name": "Alex"}},
                              "employees": {}, "defaults": {"model": "sonnet"}, "panel": {"port": 7397}})
        os.makedirs(os.path.join(TMP, "team"), exist_ok=True)

    def setUp(self):
        self.reals = engine.resolve_claude
        self.dir = _cleanup.temp("fake-claude-")
        engine.resolve_claude = lambda: fake_claude.install(
            self.dir, auth={"loggedIn": False},
            prompt={"result": "Morning notes ready.",
                    "structured": {"intro": "One quick one.",
                                   "questions": [{"type": "text", "q": "Anything else?"}],
                                   "name": "Sam", "role": "Market researcher",
                                   "scope": "Find market numbers the owner can use.",
                                   "abilities": ["memory"], "routines": {}, "access": [],
                                   "budget": "regular", "description": "Research support",
                                   "first_task": "Check example.com", "plan": "Look at numbers",
                                   "model": "sonnet"}})

    def tearDown(self):
        engine.resolve_claude = self.reals

    def test_signed_out_setup_then_hiring_then_first_task(self):
        import hire
        import onboard
        ok, msg = orbit_cli().claude_status()              # the setup/doctor check, signed out
        self.assertTrue(ok, msg)
        self.assertNotIn("sign in", msg.lower())
        self.assertNotIn("auth login", msg.lower())
        q = onboard.questions("Market researcher", "Find market numbers", name="Sam")
        self.assertTrue(q["questions"] and q["intro"])
        card = onboard.compose("Market researcher", "Find market numbers", "Sam",
                               answers=[{"q": "Anything else?", "a": "No"}])
        self.assertEqual(card["budget"], "regular")        # the interview produced a real card
        eid = hire.hire(card["name"], card["role"], card["role"], supervisor="Alex", picked=["fetch"])
        out = engine.run(engine.employee(eid), "Write today's morning brief.")
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["text"], "Morning notes ready.")
        recs = fake_claude.calls(self.dir)
        self.assertEqual(len(recs), 4)                     # availability, interview, card, task
        self.assertTrue(all(c["argv"][0] in ("--version", "-p") for c in recs),
                        "no path may call account status or any other subcommand: %r"
                        % [c["argv"][:2] for c in recs])
        for c in recs:                                     # nothing resolved an account
            self.assertNotEqual(c["argv"][:2], ["auth", "status"])
        texts = (msg, out["text"], json.dumps(card))
        for t in texts:
            self.assertNotIn("auth login", t.lower())


if __name__ == "__main__":
    unittest.main()
