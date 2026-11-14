"""Uninstall tests: the data keep/remove choices, full-home removal, the kit-folder offer.
Runs against a throwaway team folder. Every helper that would touch the real machine is stubbed
(stop_service, remove_os_integrations, remove_shims, remove_kit) — the data/kit logic alone runs
against the throwaway home, so no test can stop the service, edit the PATH, or delete the kit.
python3 -m unittest tests.test_uninstall
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="staffroom-test-")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _cleanup  # noqa: E402
_cleanup.on_exit(TMP)

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "core"))
_cleanup.home(TMP)

import uninstall  # noqa: E402

SYSTEM_HELPERS = ("stop_service", "remove_os_integrations", "remove_shims", "remove_kit")


def make_data():
    """All six categories on disk, like a used team home."""
    os.makedirs(os.path.join(uninstall.engine.HOME, "employees", "ada"), exist_ok=True)
    os.makedirs(os.path.join(uninstall.engine.HOME, ".secrets"), exist_ok=True)
    for rel, content in (("staff.json", "{}"), ("team/bus.jsonl", "x\n"),
                         ("models/v.bin", "x"), (".runtime/panel/token", "x")):
        p = os.path.join(uninstall.engine.HOME, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(content)


class PromptTestCase(unittest.TestCase):
    """Scripts ask()'s answers and stubs every helper that would leave this machine."""

    def setUp(self):
        self._saved = {name: getattr(uninstall, name) for name in ("ask",) + SYSTEM_HELPERS}
        self.answers = []
        self.asked = []
        self.calls = {name: [] for name in SYSTEM_HELPERS}

        def fake_ask(q, default=""):
            self.asked.append(q)
            return self.answers.pop(0) if self.answers else default
        uninstall.ask = fake_ask
        uninstall.stop_service = lambda: self.calls["stop_service"].append(1)
        uninstall.remove_os_integrations = lambda: self.calls["remove_os_integrations"].append(1)
        uninstall.remove_shims = lambda: self.calls["remove_shims"].append(1)
        uninstall.remove_kit = lambda interactive: self.calls["remove_kit"].append(interactive)

    def tearDown(self):
        for name, fn in self._saved.items():
            setattr(uninstall, name, fn)
        if os.path.realpath(os.getcwd()).startswith(TMP):
            os.chdir(os.path.dirname(TMP))
        _cleanup._rmtree(TMP)
        os.makedirs(TMP, exist_ok=True)

    def run_cmd(self, **kw):
        uninstall.run(SimpleNamespace(**kw))


class TestUninstall(PromptTestCase):

    def test_keep_everything(self):
        make_data()
        self.answers = ["", "", "", "", "", ""]          # Enter keeps each category
        self.run_cmd()
        for rel in ("employees/ada", ".secrets", "staff.json", "team/bus.jsonl",
                    "models/v.bin", ".runtime/panel/token"):
            self.assertTrue(os.path.exists(os.path.join(uninstall.engine.HOME, rel)))
        self.assertEqual(len(self.asked), 6)             # every kind got its say
        self.assertEqual(self.calls["stop_service"], [1])
        self.assertEqual(self.calls["remove_os_integrations"], [1])
        self.assertEqual(self.calls["remove_shims"], [1])
        self.assertEqual(self.calls["remove_kit"], [True])   # the kit offer came at the end

    def test_remove_everything(self):
        make_data()
        self.answers = ["y"] * 6
        self.run_cmd()
        self.assertFalse(os.path.exists(uninstall.engine.HOME))   # the whole git-repo'd home goes
        self.assertEqual(len(self.asked), 6)

    def test_keep_some(self):
        make_data()
        self.answers = ["", "y", "y", "y", "y", "y"]     # keep only the workspaces
        self.run_cmd()
        home = uninstall.engine.HOME
        self.assertTrue(os.path.exists(os.path.join(home, "employees", "ada")))
        for rel in (".secrets", "staff.json", "team", "models", ".runtime"):
            self.assertFalse(os.path.exists(os.path.join(home, rel)))
        self.assertTrue(os.path.isdir(home))             # kept data keeps the home standing

    def test_absent_categories_are_not_asked(self):
        make_data()
        shutil.rmtree(os.path.join(uninstall.engine.HOME, "models"))
        self.answers = ["", "", "", "", ""]              # five kinds on disk now
        self.run_cmd()
        self.assertEqual(len(self.asked), 5)

    def test_no_home(self):
        self.run_cmd()                                   # nothing installed: no data prompts, no crash
        self.assertEqual(self.asked, [])
        self.assertEqual(self.calls["stop_service"], [1])

    def test_all_flag_removes_everything_without_asking(self):
        make_data()
        self.run_cmd(all=True)
        self.assertEqual(self.calls["stop_service"], [1])
        self.assertEqual(self.calls["remove_os_integrations"], [1])
        self.assertEqual(self.calls["remove_shims"], [1])
        self.assertEqual(self.calls["remove_kit"], [False])  # the kit folder is announced, not offered
        self.assertEqual(self.asked, [])                 # --all never asks
        self.assertFalse(os.path.exists(uninstall.engine.HOME))


class TestKitOffer(unittest.TestCase):
    """The kit folder (the source repo) goes only when the user types y, and the cwd
    moves out first so Windows doesn't hold the folder locked."""

    def setUp(self):
        self.fake_kit = _cleanup.temp("staffroom-fakekit-")
        self.real_kit, self.real_home = uninstall.KIT, uninstall.engine.HOME
        uninstall.KIT = self.fake_kit
        uninstall.engine.HOME = _cleanup.temp("staffroom-nohome-")
        os.makedirs(os.path.join(self.fake_kit, "core"), exist_ok=True)
        with open(os.path.join(self.fake_kit, "orbit"), "w") as fh:
            fh.write("# kit")
        self._ask = uninstall.ask

    def tearDown(self):
        uninstall.KIT, uninstall.engine.HOME = self.real_kit, self.real_home
        uninstall.ask = self._ask
        if os.path.realpath(os.getcwd()).startswith(self.fake_kit):
            os.chdir(os.path.dirname(self.fake_kit))

    def test_removed_on_yes(self):
        os.chdir(self.fake_kit)                          # as if launched from inside the kit
        uninstall.ask = lambda q, default="": "y"
        uninstall.remove_kit(interactive=True)
        self.assertFalse(os.path.exists(self.fake_kit))
        self.assertFalse(os.path.realpath(os.getcwd()).startswith(self.fake_kit))  # moved off the lock

    def test_kept_on_enter(self):
        uninstall.ask = lambda q, default="": default
        uninstall.remove_kit(interactive=True)
        self.assertTrue(os.path.isdir(self.fake_kit))


@unittest.skipUnless(sys.platform != "win32", "the ~/.local/bin symlink shim is POSIX-only")
class TestPosixShims(unittest.TestCase):
    """install.sh leaves two symlinks in ~/.local/bin; only ours (into the kit) may go."""

    def test_own_symlinks_removed_others_left(self):
        bindir = os.path.expanduser("~/.local/bin")
        os.makedirs(bindir, exist_ok=True)
        ours = os.path.join(bindir, "staff")
        theirs = os.path.join(bindir, "staffroom-uninstall-test-keep")
        made = []
        try:
            for link, target in ((ours, os.path.join(KIT, "staff")), (theirs, KIT)):
                if not os.path.lexists(link):
                    os.symlink(target, link)
                    made.append(link)
            uninstall.remove_shims()
            self.assertFalse(os.path.lexists(ours))       # our symlink went
            self.assertTrue(os.path.lexists(theirs))      # someone else's entry stays
        finally:
            for link in made:
                if os.path.lexists(link):
                    os.remove(link)


if __name__ == "__main__":
    unittest.main()
