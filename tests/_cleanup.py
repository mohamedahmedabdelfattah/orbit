"""Test hygiene: when a test module ends, its temporary folders go, and so do any Claude Code transcript folders
(~/.claude/projects/<path-slug>) that runs inside them created, so tests leave nothing behind in the owner's
Claude app or `claude --resume` list."""
from __future__ import annotations

import atexit
import os
import re
import shutil
import stat
import tempfile


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
