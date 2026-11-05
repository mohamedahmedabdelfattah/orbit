# WSL2 architecture

This document describes every architectural role WSL2 has in Orbit. It covers the current fallback path, not a proposed redesign.

## Scope and role

WSL2 is a complete Orbit runtime, not an MXC backend selected inside the native Windows process. In WSL2 mode, Orbit runs its Linux installation inside a WSL distribution:

- Linux Python runs `orbit`, `staffd`, the panel, channels, tools, and Claude Code.
- Claude Code's Linux sandbox uses Bubblewrap. WSL2 supplies the Linux kernel and namespace support Bubblewrap needs.
- Team data lives in the distribution at `~/Staff` by default.
- A Windows startup shortcut launches the Linux service through `wsl.exe` after Windows login.
- Small Windows bridges open the Windows browser, keep Windows awake, and capture Windows audio.

Native Windows MXC mode is separate. It has its own kit, registry, secrets, service, and `%USERPROFILE%\Staff` tree. Selecting `wsl2` in the native registry only stops native Orbit from accepting work and tells the owner to operate the WSL installation.

Primary code: [`core/osinfo.py`](../core/osinfo.py), [`core/engine.py`](../core/engine.py), and [`orbit`](../orbit).

## Two modes are two installations

| Concern | Native Windows / MXC | WSL2 fallback |
|---|---|---|
| Platform kind | `osinfo.KIND == "windows"` | `osinfo.KIND == "wsl"` |
| Kit | Windows checkout, for example `C:\Users\me\orbit` | Linux checkout, normally `~/orbit` on the distribution filesystem |
| Team home | `%USERPROFILE%\Staff` | `~/Staff` in the distribution |
| Registry | Windows team home's `staff.json` | WSL team home's `staff.json` |
| Claude installation/auth | Windows Claude Code | Linux Claude Code inside WSL; separate installation, same owner account |
| Shell boundary | One MXC ProcessContainer per PowerShell call | Claude Code Linux sandbox using Bubblewrap |
| Background service | Windows Scheduled Task | Windows Startup shortcut launching hidden `wsl.exe`, then Linux watchdog |
| Secrets protection | NTFS ACLs plus policy | Linux modes plus sandbox; Windows drives denied through `/mnt` |

No shared mode store joins these installations. `core/mxc.py::set_mode()` writes only the native Windows registry. Inside WSL, `core/mxc.py::mode()` resolves to `wsl2` without reading the native registry.

## End-to-end flows

### Installation

1. Owner enables WSL and installs a WSL2 distribution with `wsl --install`; WSL1 is rejected.
2. Kit is cloned onto the distribution filesystem at `~/orbit`. Keeping it off `/mnt/c` preserves Linux executable bits and avoids NTFS mode differences.
3. [`setup-linux.sh`](../setup-linux.sh) installs Bubblewrap, `socat`, Python/pip, Git, FFmpeg, Tesseract, Poppler, CMake/compiler, PulseAudio libraries, and Playwright's Chromium libraries. On restricted Ubuntu hosts it installs the documented AppArmor profile for Bubblewrap user namespaces.
4. Claude Code is installed and authenticated inside the distribution.
5. [`install.sh`](../install.sh) verifies WSL2, installs user Python packages and Chromium, links `orbit` into `~/.local/bin`, and starts the service.

Operator steps live in [`SETUP.md`](../SETUP.md#windows-through-wsl-the-fallback). `install.sh` detects the old WSL1 kernel suffix `-Microsoft`; WSL2 normally reports `microsoft-standard`.

### Employee run and sandbox

1. WSL Python starts the unmodified Linux `claude -p` process from the employee workspace.
2. [`core/engine.py::sandbox_blob()`](../core/engine.py) sends Claude Code the same sandbox policy used on Linux:
   - `failIfUnavailable: true`;
   - unsandboxed execution disabled;
   - approved network domains only;
   - employee workspace as the working area and team bus as an extra write path;
   - secrets and colleagues' workspaces denied.
3. On WSL, `/mnt` is added to `SECRET_PATHS`. Shell commands therefore cannot read mounted Windows drives.
4. Windows executables and service controls (`powershell.exe`, `cmd.exe`, `wsl.exe`, `schtasks.exe`) remain denied to employee shell calls. The staff guard also rejects Windows program launches and `wslview`.
5. Claude Code creates the immediate Bubblewrap boundary. WSL2 is the Linux host for that boundary; WSL2 alone is not the per-command least-privilege policy.
6. Approved toolbelt gateways can run outside Claude's shell sandbox and enforce their own URL, budget, and local-network rules. This behavior is shared with Linux.

Sources: [`core/engine.py`](../core/engine.py), [`core/abilities.py`](../core/abilities.py), and [`core/guard/staff-guard/hooks/register.js`](../core/guard/staff-guard/hooks/register.js).

### Boot and background service

WSL distributions can stop after their last Windows client exits. Orbit therefore anchors the service from Windows:

1. `orbit start` in WSL calls `orbit::wsl_script()`.
2. The generated PowerShell creates `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Orbit.lnk`.
3. Shortcut target is `conhost.exe --headless wsl.exe -d <distro> -u <user> -e ... orbit service-run`.
4. Orbit starts the shortcut command through `Win32_Process.Create`. Starting it directly from the initiating WSL process would leave it in that command's WSL job and let it die with the command.
5. Linux `orbit service-run` writes `~/Staff/team/service.pid`, starts `core/staffd.py`, and restarts it after failures.
6. `staffd` writes `staffd_alive`; `orbit status` and `orbit doctor` use its age as liveness evidence.
7. `orbit stop` terminates the Linux watchdog. Current WSL stop behavior does not remove the Windows startup shortcut.

Sources: [`orbit::wsl_script()` and `orbit::service_run()`](../orbit), plus service tests in [`tests/test_platforms.py`](../tests/test_platforms.py).

### Panel and Windows browser

The panel server remains in WSL and listens on `127.0.0.1:<port>`. Windows/WSL localhost forwarding lets the Windows browser reach it.

`core/osinfo.py::open_url()` tries these WSL interoperability routes in order:

1. `wslview`;
2. `explorer.exe <url>`;
3. `cmd.exe /c start`.

The panel remains loopback-only and token-protected. Employee shells cannot reach localhost through the Linux sandbox policy; gateways independently reject local addresses.

Sources: [`core/osinfo.py`](../core/osinfo.py) and [`core/panel.py`](../core/panel.py).

### Sleep control

`core/osinfo.py::keep_awake_cmd()` runs a small PowerShell loop from WSL. It repeatedly calls Windows `SetThreadExecutionState` while the Linux worker PID exists. This resets the host Windows idle timer; a Linux-only inhibitor would not control host sleep.

Source: [`core/osinfo.py`](../core/osinfo.py).

### Live calls and audio

WSL cannot directly capture audio played by ordinary Windows apps. Orbit splits this flow across both environments:

1. WSL `core/calls.py` finds Python for Windows with `py.exe`, `python.exe`, or `python3.exe`.
2. `wslpath` converts the listener script and WSL meeting-audio directory to Windows-visible paths, normally `\\wsl.localhost\<distro>\...`.
3. Windows Python runs `core/tools/call_listen.py` with `soundcard` and `numpy`, capturing WASAPI loopback plus microphone audio.
4. Audio files are written into the WSL employee workspace through the converted path.
5. WSL `whisper-cli` transcribes chunks locally, writes transcript/minutes, then removes raw audio.

Windows Python is therefore an explicit peripheral bridge, not the Orbit runtime or sandbox.

Sources: [`core/calls.py`](../core/calls.py), [`core/osinfo.py::win_python()`](../core/osinfo.py), and [`core/tools/call_listen.py`](../core/tools/call_listen.py).

### Path and environment interoperability

`core/osinfo.py` owns WSL-to-Windows conversions:

- `distro()` reads `WSL_DISTRO_NAME`.
- `win_path()` runs `wslpath -w`.
- `lin_path()` runs `wslpath -u`.
- `win_env()` asks `cmd.exe` for Windows environment values.
- `win_python()` finds and validates Python for Windows.
- Windows subprocesses use `/mnt/c` as a neutral current directory when available.

These helpers support host browser/audio/service operations. Employee commands are separately denied access to Windows executable families and `/mnt`.

## Files, tools, and data

| Surface | WSL2 behavior | Source |
|---|---|---|
| Team state | Linux `~/Staff`; employee workspaces, team bus, logs, secrets, models | `core/engine.py`, `orbit::ensure_home()` |
| Windows files | Mounted under `/mnt`; entire mount is in sandbox `denyRead` | `core/engine.py` |
| OCR and PDFs | Linux Tesseract + Poppler | `setup-linux.sh`, `core/tools/docs.py` |
| Voice notes | Linux FFmpeg + locally built `whisper-cli` | `setup-linux.sh`, `orbit::get_whisper()` |
| Headless browser | Linux Playwright Chromium | `install.sh`, `setup-linux.sh` |
| Live-call capture | Windows Python; output/transcription in WSL | `core/calls.py` |
| Browser opening | Windows browser through WSL interop | `core/osinfo.py` |
| Service startup | Windows shortcut, Linux watchdog/service | `orbit` |
| Line endings/modes | Shell scripts forced to LF; kit copied to Linux disk in CI | `.gitattributes`, `.github/workflows/tests.yml` |

## Fallback selection and migration

Native `orbit sandbox wsl2` performs a guided mode selection. It currently:

- checks only that `wsl.exe` is present;
- records `platform.sandbox_mode = "wsl2"` in the native team registry;
- blocks native `engine.run()` and native `orbit start`;
- prints instructions for installing and operating the independent WSL copy;
- prints both data locations and manual copy directions.

It does not install a distribution, verify a WSL2 distro, clone/configure Orbit inside WSL, copy team data, transfer secrets, stop the already-running native service, or start the WSL service. Moving data is manual because NTFS ACLs and Linux `chmod` do not transfer as equivalent controls.

The reverse switch validates MXC discovery/probes and records `mxc` in the native registry. It does not stop a WSL service or merge the WSL registry.

Current transition defects and required fixes are tracked in [`mxc-platform-review.md`](../specs/001-windows-mxc-sandbox/mxc-platform-review.md#p0-and-p1-findings).

## Test coverage

The WSL GitHub Actions job in [`.github/workflows/tests.yml`](../.github/workflows/tests.yml):

- provisions Ubuntu 24.04 under WSL2;
- verifies `osinfo.KIND == "wsl"`;
- runs `setup-linux.sh` and all unit modules;
- directly starts a Bubblewrap sandbox;
- verifies PowerShell, `cmd.exe`, and `wslpath` interoperability;
- installs Orbit from the Linux filesystem;
- verifies the service, Windows panel access, and startup shortcut;
- verifies Windows Python can load live-call packages.

Unit coverage in [`tests/test_platforms.py`](../tests/test_platforms.py) checks platform detection, `/mnt` denial, WSL sandbox fail-closed settings, startup-script generation, path bridges, and WSL/native mode behavior.

The MXC feature ledger still records macOS/Linux/WSL2 full-suite validation as pending in [`specs/001-windows-mxc-sandbox/GATES.md`](../specs/001-windows-mxc-sandbox/GATES.md).

## Source inventory

Direct WSL architecture and behavior:

- [`core/osinfo.py`](../core/osinfo.py): detection, browser, sleep, paths, environment, Windows Python.
- [`core/engine.py`](../core/engine.py): `/mnt` secret boundary, denied Windows commands, Linux sandbox settings, native `wsl2` run gate.
- [`core/calls.py`](../core/calls.py) and [`core/tools/call_listen.py`](../core/tools/call_listen.py): Windows audio bridge.
- [`orbit`](../orbit): doctor, service bridge, startup shortcut, mode switch, data-location guidance.
- [`install.sh`](../install.sh) and [`setup-linux.sh`](../setup-linux.sh): WSL/Linux installation and WSL1 rejection.
- [`README.md`](../README.md) and [`SETUP.md`](../SETUP.md): owner and setup-agent procedures.
- [`.github/workflows/tests.yml`](../.github/workflows/tests.yml), [`tests/test_platforms.py`](../tests/test_platforms.py), and [`tests/test_mxc.py`](../tests/test_mxc.py): WSL regression and mode tests.
- [`core/guard/staff-guard/hooks/register.js`](../core/guard/staff-guard/hooks/register.js): employee denial of Windows programs and `wslview`.
- [`.gitattributes`](../.gitattributes): LF shell files for WSL/Linux.

Incidental platform-specific tooling references:

- [`core/tools/docs.py`](../core/tools/docs.py): Linux/WSL OCR implementation.
- [`core/skills/content-creator/kit/setup.sh`](../core/skills/content-creator/kit/setup.sh): Linux/WSL Node and FFmpeg prerequisites.
- [`core/awake.py`](../core/awake.py): platform-neutral wake/sleep timing note.
