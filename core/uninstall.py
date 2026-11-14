"""The uninstall command: stop the crew, take the OS integrations and shims back out, then ask
which data to keep or remove. Python 3.9 compatible. Harness-owned.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys

import engine
import osinfo

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../Orbit (core/ sits inside it)
LABEL = "com.staffroom.staffd"
PLIST = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % LABEL)
UNIT = os.path.expanduser("~/.config/systemd/user/orbit.service")

# Data under ~/Staff the user chooses about. (key, path inside HOME, label, note).
# Anything else under HOME (.git, .gitignore, demo state) goes with the home itself.
CATEGORIES = [
    ("employees", "employees", "employee workspaces", "profiles, plans, notes, skills, git history"),
    ("secrets", ".secrets", "secrets", "bot tokens and API keys"),
    ("settings", "staff.json", "settings & registry", "team name, owners, employee records"),
    ("logs", "team", "logs & chat history", "message bus, chat logs, service logs"),
    ("models", "models", "voice model", "~550 MB, re-downloadable with `orbit doctor --get-voice-model`"),
    ("caches", ".runtime", "runtime cache", "browser profiles, service runtime files"),
]


def ask(q, default=""):
    try:
        a = input("%s%s: " % (q, " [%s]" % default if default else "")).strip()
    except EOFError:
        a = ""
    return a or default


def yes(q, default=False):
    a = ask(q + (" (Y/n)" if default else " (y/N)")).lower()
    return default if not a else a.startswith("y")


def rmtree_force(path):
    """Delete a file or tree even where git left read-only loose objects (employee workspaces
    and ~/Staff itself are git repos; Windows can't unlink those as-is)."""
    if os.path.isfile(path) or os.path.islink(path):
        try:
            os.chmod(path, stat.S_IWRITE)
        except OSError:
            pass
        os.remove(path)
        return
    if not os.path.exists(path):
        return

    def force(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    try:
        shutil.rmtree(path, onexc=force)          # Python 3.12+
    except TypeError:
        shutil.rmtree(path, onerror=force)        # older interpreters


def stop_service():
    """Reuse the CLI's own stop: task unregister, Startup shortcut, watchdog tree-kill."""
    r = subprocess.run([sys.executable, os.path.join(KIT, "orbit"), "stop"], capture_output=True, text=True)
    out = (r.stdout or "").strip()
    if out:
        print(out)
    if r.returncode != 0:
        print("Stopping the service failed: %s" % ((r.stderr or "").strip() or "exit %s" % r.returncode))


def remove_os_integrations():
    """What stop() doesn't delete: the launchd plist, the systemd user unit."""
    if osinfo.KIND == "mac":
        if os.path.exists(PLIST):
            rmtree_force(PLIST)
            print("Removed %s" % PLIST)
    elif os.path.exists(UNIT):
        subprocess.run(["systemctl", "--user", "disable", "orbit.service"], capture_output=True)
        rmtree_force(UNIT)
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        print("Removed %s" % UNIT)


def windows_shim_dir():
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Orbit", "bin")


def remove_windows_path_entry(shim):
    """Drop the shim dir from the user's Path (setup-windows.ps1 appended it)."""
    ps = ("$p=[Environment]::GetEnvironmentVariable('Path','User');"
          "$n=($p -split ';' | Where-Object { $_ -and $_ -ne '%s' }) -join ';';"
          "[Environment]::SetEnvironmentVariable('Path',$n,'User')") % shim.replace("'", "''")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def remove_shims():
    """The `orbit`/`staff` commands: setup-windows.ps1's shim dir on Windows, install.sh's
    symlinks (~/.local/bin) elsewhere. Only removes symlinks that point into this kit."""
    if osinfo.KIND == "windows":
        shim = windows_shim_dir()
        if os.path.isdir(shim):
            rmtree_force(shim)
            print("Removed %s" % shim)
        remove_windows_path_entry(shim)
        print("Removed the shim folder from your PATH (new windows won't have `orbit`).")
        return
    for name in ("orbit", "staff"):
        link = os.path.expanduser("~/.local/bin/" + name)
        if os.path.islink(link) and os.path.realpath(link).startswith(os.path.realpath(KIT) + os.sep):
            os.remove(link)
            print("Removed %s" % link)


def data_choices():
    """Ask about each data category that exists. Returns the keys the user chose to keep."""
    if not os.path.isdir(engine.HOME):
        print("\nNo data folder at %s — nothing to decide." % engine.HOME)
        return []
    print("\nData lives in %s. For each kind, choose what survives:" % engine.HOME)
    kept = []
    for key, rel, label, note in CATEGORIES:
        p = os.path.join(engine.HOME, rel)
        if not os.path.exists(p):
            continue
        if yes("  Remove the %s (%s)? [Enter keeps it]" % (label, note)):
            rmtree_force(p)
            print("  Removed %s" % p)
        else:
            kept.append(key)
    return kept


def remove_home(kept):
    """When nothing was kept, the whole data folder goes (it is a git repo: .git, .gitignore,
    demo state). When something was kept, it stays with what's left of it."""
    if not os.path.isdir(engine.HOME):
        return
    if kept:
        print("\nKept in %s: %s" % (engine.HOME, ", ".join(kept)))
        return
    rmtree_force(engine.HOME)
    print("\nRemoved %s" % engine.HOME)


def remove_kit(interactive):
    if not interactive:
        print("\nThe kit folder stays: %s (delete it yourself when you're ready)." % KIT)
        return
    if yes("\nAlso remove the Orbit kit folder (%s)? [Enter keeps it]" % KIT):
        cwd = os.path.realpath(os.getcwd())
        kit = os.path.realpath(KIT)
        if cwd == kit or cwd.startswith(kit + os.sep):
            os.chdir(os.path.expanduser("~"))    # a cwd inside the kit keeps the folder locked on Windows
        rmtree_force(KIT)
        if os.path.exists(KIT):
            print("Couldn't fully remove %s — some files are in use; delete what's left yourself." % KIT)
        else:
            print("Removed %s. Orbit is gone." % KIT)
    else:
        print("Kit folder kept: %s" % KIT)


def run(args=None):
    all_flag = bool(getattr(args, "all", False))
    print("Uninstalling Orbit. The service stops and OS integrations come out; data is your call.")
    stop_service()
    remove_os_integrations()
    remove_shims()
    if all_flag:
        print("\n--all: removing all data in %s" % engine.HOME)
        for _key, rel, _label, _note in CATEGORIES:
            rmtree_force(os.path.join(engine.HOME, rel))
        remove_home([])
        remove_kit(interactive=False)
    else:
        kept = data_choices()
        remove_home(kept)
        remove_kit(interactive=True)
    print("\nPython packages installed by setup (requests, playwright, …) were left alone: other "
          "projects may use them. Remove with `pip uninstall` if you want.")
