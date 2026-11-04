# Research: Native Windows with MXC

Feature: `001-windows-mxc-sandbox`. Each entry: Decision, Rationale, Alternatives considered.

## D1 — How Orbit invokes MXC

**Decision**: Consume MXC through its official **executor binary** (`wxc-exec.exe`) fed a versioned, stable-schema JSON container-creation request, **generated per shell command** (not per run — see D9). Orbit ships/installs the MXC runtime as an installer artifact; no Rust or Node SDK embeds into Orbit, and the owner's machine needs no toolchains.

**Rationale**:
- Microsoft's README explicitly documents non-SDK consumption: "Platform-specific executor binaries, such as `wxc-exec.exe`, accept JSON container-creation requests defined by the stable schema. Use for testing or when the SDK cannot be embedded in your app." Orbit is a Python/Bash kit — the SDK cannot be (idiomatically) embedded.
- Command-level sizing keeps per-command startup inside the over-privileged "shell sandbox" latency envelope owners already see on macOS/Linux; it also avoids inheriting any long-running-container lifecycle semantics for agent work.
- The stable schema is versioned (`schemas/stable`), so Orbit's generated requests remain valid across MXC updates.

**Alternatives considered**:
- *Node SDK (`@microsoft/mxc-sdk`)*: capability-rich (streaming stdio, timeouts as first-class parameters), but requires a Node runtime on the owner's machine and couples Orbit to npm distribution. Rejected as primary; noted as acceptable if the executor path proves too limited during implementation (e.g., if streaming stdio through the executor is awkward for interactive tool output).
- *Rust SDK*: no Rust toolchain in Orbit's kit. Rejected.
- *Windows-native sandbox-runtime (`srt-win`)*: the Anthropic sandbox-runtime package has a Windows-native sandbox, but it is alpha, tied to Claude Code's own sandbox model, and mutually exclusive with the owner's explicit MXC requirement. Rejected.

**Implementation-time verification required**: the exact distribution artifact for the MXC runtime/executor on Windows (GitHub release asset vs. contents of the npm/`.NET` packages) and its checksum verification; also the executor CLI shape — request-file path plus wrapped command argument — verified against the current release before the installer task (T020) lands.

## D2 — Policy translation (Orbit → MXC, per shell command)

**Decision**: a single Orbit-side translation of the existing policy model, produced **per contained command**. Field names in the right column follow `contracts/mxc-request.md` (Orbit's canonical mapping); the actual MXC stable-schema field names are verified at implementation time (T020's artifact verification).

| Orbit policy surface (from `engine.settings_json()`) | MXC request field (stable schema) |
| --- | --- |
| `filesystem.denyRead` = `SECRET_PATHS` | `filesystem.deny_read` with **Windows-native paths** (`%USERPROFILE%\.ssh`, `%USERPROFILE%\.aws`, `%APPDATA%\gnupg`, `%APPDATA%\rclone`, `.netrc`, Chrome/Edge cookie & password stores, Desktop/Documents/Downloads, Orbit's secrets folder) |
| `filesystem.allowWrite` = team tree | `filesystem.allow_write` = employee workspace + team tree + per-command temp |
| `network.allowedDomains` = pypi/pythonhosted + owner domains (+ gateway needs, `strictAllowlist` per autonomy) | `network.egress default: deny` + allowed destinations; backend host filtering where supported |
| `excludedCommands` (gateway commands run outside the sandbox with their own limits) | The hook passes gateway commands through unwrapped (they enforce their own limits) — Orbit replicates the exclusion matcher per command |
| `failIfUnavailable: true` | At the hook layer: a failed wrapper build/launch denies the command with the reason (fail-closed per command). At run level: Orbit omits sandbox `failIfUnavailable` from the settings blob on native Windows (the built-in sandbox doesn't exist there) so the agent starts normally |

**Rationale**: Orbit's policy model is already expressed as denyRead/allowWrite/allowedDomains; MXC's filesystem and network policy patterns match (deny-then-allow reads; allow-only writes and network). Command-level parity keeps the macOS/Linux sandbox surface (shell commands only) — Claude's file/web tools keep following permission rules exactly as they do on every platform.

**Alternatives considered**: whole-agent containment (stronger boundary, but rejected — Orbit must not intervene with Claude's own flows); wrapping outside Claude's hook layer (bypasses the permission pipeline and unsandboxed-retry semantics). Both rejected.

## D3 — Native Windows service & installer

**Decision**:
- Service: a Windows **Scheduled Task** (logon trigger, hidden, restart-on-boot semantics via `orbit service-run` watchdog loop that already exists) running `pythonw.exe … orbit service-run` with `STAFFROOM_HOME` set. `orbit stop/restart/status` manage the task + the existing PID/stamp file. No WMI bridge, no `conhost` hack, no hidden `wsl.exe`.
- Installer: `setup-windows.ps1`, winget-based, installs Python 3 (x64/ARM64), git, ffmpeg, tesseract-ocr, MXC runtime artifacts, and `pip --user` deps (requests, bs4, playwright, websocket-client). Echoes the same post-install guidance as `install.sh` (run `orbit setup`).
- Doctor: `platform_checks()` gains a native-Windows branch: Python presence, MXC runtime present + version, containment probe (positive+negative, see D6), Python deps, ffmpeg/tesseract, whisper model, service running. Removes the WSL-only checks from the native path (they remain for the WSL2 mode).

**Rationale**: Scheduled Tasks are the standard logon-persistent mechanism a non-admin script can use; the stamp-file liveness design in `orbit`/`staffd` already survives across service supervisors on Linux-without-systemd, so reuse is the cheapest correct path.

**Alternatives considered**: NSSM service (extra download, admin); SysV-style Python double-fork (already exists as the generic branch — kept for non-scheduled-task setups); Startup-folder shortcut (no auto-restart on crash; rejected in favor of the task).

## D4 — Mode selection & fallback persistence

**Decision**: record the effective mode in the Orbit registry (`"platform": {"sandbox_mode": "mxc" | "wsl2"}`), written at setup (or by `orbit command` guided switching), surfaced verbatim by doctor. Native-Windows default is `mxc`; `wsl2` is set only by the owner or after a failed/unavailable MXC check. Detection runs at setup and on `orbit start` of the service, never per employee run.

**Rationale**: matches spec R4 (no silent per-run switching; single discoverable switch); the registry is already the owner-owned settings file committed to git in `~/Staff`.

**Alternatives considered**: environment variable (hidden, violates SC7); auto-switching per run (spec forbids).

## D5 — Windows speech stack

**Decision**: doctor's `--get-voice-model` works unchanged (it's a download). For `--get-whisper` on native Windows: detect/build order is (1) prebuilt if the ecosystem offers an official Windows build at implementation time, otherwise (2) guided build — winget installs Git, CMake, and Visual Studio Build Tools (C++), then the existing whisper.cpp build flow runs with the Windows compiler; doctor prints each step's native command. FFmpeg is a winget install, same role as apt on Linux.

**Rationale**: whisper.cpp has no first-party Windows binary today; the existing source-build flow must be re-pointed at MSVC. All of this is behind one Orbit command, preserving the owner's mental model (`orbit doctor --get-whisper`).

**Alternatives considered**: faster-whisper/Python re-implementation (changes the transcribe tool contract — rejected for this feature's scope); skip voice on Windows (breaks R3.4 — rejected).

## D6 — Verification (probes) & diagnostics

**Decision**:
- **Setup probe** (and doctor re-check): generate a min-policy request; run (positive) `echo`/file-write-inside-scope; then (negative) attempt a write outside `allowWrite`, a read of a deny-listed path, and a direct connect to a non-allowlisted host; a contained workload that outlives its timeout must be terminated (no orphaned sandboxed process). All negatives must fail; any pass = environment unsuitable → refuse + report (per spec R2.4, R6).
- **Diagnostics**: on containment failure/denial, Orbit captures the executor's diagnostic output (and, where accepted, its `--audit`-mode artifacts as an optional doctor triage command) and renders an owner-readable summary + support bundle path.

**Rationale**: MXC's own platform-support guidance states discovery is not proof; only positive+negative workload tests prove enforcement. Orbit's existing "failIfUnavailable" philosophy maps directly.

**Alternatives considered**: trusting only discovery APIs (not sufficient); audit mode for every run (disabled-by-default — telemetry/latency; triage-only).

## D7 — Paths & flows that must stop bridging through WSL

Inventory from exploration (all addressed by R3 tasks):

| Flow | File(s) today | Native replacement |
| --- | --- | --- |
| Platform kind | `core/osinfo.py` `_kind()` | `windows` kind when `sys.platform == "win32"` and not WSL (keep `wsl` detection via `/proc/version`) |
| Browser open | `osinfo.open_url` (`wslview`/`explorer.exe`) | `webbrowser`/`os.startfile` |
| Env reads | `osinfo.win_env` via `cmd.exe`, `wslpath` | native `os.environ` / `os.path` |
| Notifications | `osinfo.notify` (no Windows branch today) | native toast (best-effort) — optional, doc'd |
| Windows-Python audio | `osinfo.win_python()` + `calls.py` `/mnt/c` cwd | `sys.executable` on native; cwd = normal |
| Service bridging | `orbit` `wsl_script()`, `_ps()`, WMI | Scheduled task (D3) |
| Sandbox policy | `engine.settings_json()` + `SECRET_PATHS`/`/mnt` | MXP translation (D2) + native Windows secret paths |
| Deny rules | `engine.BASE_DENIED` | Keep Windows shells denied (on native Windows they're the local tools) plus `wsl.exe` |
| Install/doctor | `install.sh`, `setup-linux.sh`, `platform_checks` | `setup-windows.ps1` + native doctor branch; WSL paths preserved for fallback |
| Whisper build | `orbit get_whisper` | D5 |
| Tests | `tests/test_platforms.py` (`ORBIT_OS=wsl`) | add `ORBIT_OS=windows` cases; keep WSL cases |
| CI | `.github/workflows/tests.yml` (Ubuntu + WSL) | add `windows-latest` unit-test job |

## D8 — Data coexistence when modes change

**Decision**: `~/Staff` on native Windows lives under the owner's Windows profile (e.g., `%USERPROFILE%\Staff`). When an owner switches modes, doctor reports both locations (WSL2's tree visible via `\\wsl.localhost\…`) and prints the documented copy direction; Orbit never moves data silently (spec Out of Scope). Registry, secrets permissions (NTFS ACLs vs chmod) are mode-specific nuances the doctor states explicitly.

**Alternatives considered**: automatic migration (out of scope per spec); shared NTFS location used by both modes (pitfall: WSL 9p mount semantics + secrets exposure; rejected).

## D9 — Integration surface with Claude Code: per-command hook (owner-decision record)

**Decision**: Orbit integrates MXC containment through Claude Code's documented hook layer — **a `PreToolUse` hook, matcher `Bash|PowerShell`**, that rewrites each shell command into an MXC executor invocation and returns `permissionDecision: "allow"` together with `updatedInput`. The agent process and its flows run unmodified.

**Verified against official hooks reference** (code.claude.com/docs/en/hooks.md, fetched 2026-11-04):
- `PreToolUse` supports `updatedInput` "directly under `hookSpecificOutput` [which] replaces a tool's arguments before it runs"; the replaced input is re-evaluated against permission rules.
- `permissionDecision: "allow"` combined with `updatedInput` "auto-approves" the rewritten call; **deny and ask rules are still evaluated regardless**.
- In auto mode, a hook returning `updatedInput` without a decision can be denied against the original review — hence the hook always pairs the rewrite with an explicit `allow`.
- Matchers `Bash|PowerShell` are exact-string lists; the `if` field can narrow per-handler.
- Commands Claude's own sandbox would exclude (`excludedCommands` — Orbit's gateway commands) are passed through unwrapped by Orbit's own matcher, replicating today's semantics.

**Rationale**: This is Orbit's existing integration surface (the staff guard is a hook), sanctioned behavior, no intervention in how Claude handles its own flows — the boundary lands where Claude Code's own sandbox lands on macOS/Linux (shell commands only).

**Alternatives considered**: whole-agent containment (rejected, owner decision 2026-11-04); static per-session container reuse (multi-command sessions would need lifecycle backends (`isolation_session`) and reintroduces agent-flow state, deferred; a per-command model is stateless and simpler).

**Implementation-time verification required**: the tool names Claude Code exposes on Windows — whether shell calls surface as a `Bash` tool, a `PowerShell` tool, or another name — so the matcher matches the real surface; verified against the installed Claude Code before the hook-wiring task (T033) lands, mirroring D1's approach.
