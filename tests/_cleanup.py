"""Test hygiene: when a test module ends, its temporary folders go, and so do any Claude Code transcript folders
(~/.claude/projects/<path-slug>) that runs inside them created, so tests leave nothing behind in the owner's
Claude app or `claude --resume` list."""
from __future__ import annotations

import atexit
import os
import re
import shutil
import stat
import sys
import tempfile
import unittest


def _rmtree(path: str):
    """Delete a tree (or a single file) even where git left read-only loose objects
    (Windows can't unlink those as-is)."""
    if os.path.isfile(path) or os.path.islink(path):
        try:
            os.chmod(path, stat.S_IWRITE)
        except OSError:
            pass
        os.remove(path)
        return
    if not os.path.exists(path) and not os.path.isjunction(path):
        return
    def force(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    try:
        shutil.rmtree(path, onexc=force)          # Python 3.12+
    except TypeError:
        shutil.rmtree(path, onerror=force)        # older interpreters


def temp(prefix: str) -> str:
    """A temporary directory registered for cleanup with the rest of this test module."""
    d = tempfile.mkdtemp(prefix=prefix)
    on_exit(d)
    return d


def on_exit(*dirs):
    def clean():
        projects = os.path.expanduser("~/.claude/projects")
        for d in dirs:
            slugs = {re.sub(r"[^A-Za-z0-9]", "-", p) for p in (d, os.path.realpath(d))}
            _rmtree(d)
            try:
                names = os.listdir(projects)
            except OSError:
                names = []
            for n in names:
                if any(n.startswith(s) for s in slugs):
                    _rmtree(os.path.join(projects, n))
    atexit.register(clean)


# The kit's own modules bind paths from engine.HOME at import; `_sweep` rewrites them, so no map is
# kept here. If a future constant escapes it (a dict of paths, a default argument), add it here.


def home(tmp):
    """Point this process's Orbit home at `tmp`: the env for children and fresh imports, plus a
    rebind of the path constants kit modules froze at import time (engine.HOME included).
    `unittest discover` imports every test module before running any test, so without this every
    module after the first would read and write the first module's home."""
    tmp = os.path.normpath(tmp)
    os.environ["STAFFROOM_HOME"] = tmp
    os.environ.pop("STAFF_WORKSPACE", None)         # a clean ambient baseline per module suite;
    os.environ.pop("STAFF_EMPLOYEE", None)          # a module that needs them passes them in env=
    core = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core")
    if core not in sys.path:
        sys.path.insert(0, core)
    import engine                                   # already imported under discover: sys.modules wins
    old = os.path.normpath(engine.HOME)
    if old == tmp:
        return
    _sweep(old, tmp, os.path.dirname(os.path.abspath(engine.__file__)))
    engine.HOME = tmp
    engine.REGISTRY = os.path.join(tmp, "staff.json")
    engine.SECRETS = os.path.join(tmp, ".secrets")


def _sweep(old, new, core):
    """Rewrite every module-level constant in the kit's own modules that still points into the old
    home — plain strings (team.ORDERS, derived from team.TEAM) and string lists (engine.SECRET_PATHS
    holds SECRETS). Only kit files are touched: a temp-folder prefix is too specific to match
    anything else."""
    kit = os.path.dirname(core)
    for _name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f or not os.path.normpath(os.path.abspath(f)).startswith(kit + os.sep):
            continue
        for attr in dir(mod):
            if attr.startswith("__"):
                continue
            try:
                v = getattr(mod, attr)
            except Exception:                       # exotic modules: leave them alone
                continue
            if isinstance(v, str) and v.startswith(old):
                try:
                    setattr(mod, attr, new + v[len(old):])
                except Exception:
                    pass
            elif isinstance(v, list):
                try:
                    fixed = [new + x[len(old):] if isinstance(x, str) and x.startswith(old) else x
                             for x in v]
                    if fixed != v:
                        setattr(mod, attr, fixed)
                except Exception:
                    pass


class _HomeSuite(unittest.TestSuite):
    """Runs a test module's suite against its own temporary home, whatever ran before it."""

    def __init__(self, tests, tmp, env=None):
        super().__init__(tests)
        self._tmp = tmp
        self._env = env or {}

    def run(self, *args, **kwargs):
        home(self._tmp)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return super().run(*args, **kwargs)


def home_suite(tests, tmp, env=None):
    """For a module's load_tests: give the module its own home (and extra env) for the whole run."""
    return _HomeSuite(tests, tmp, env)
