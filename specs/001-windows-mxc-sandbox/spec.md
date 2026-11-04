# Feature Specification: Native Windows with Microsoft Execution Containers (MXC)

**Feature ID**: `001-windows-mxc-sandbox`
**Created**: 2026-11-04
**Status**: Draft
**Input**: "Add support for Windows MXC as the main sandbox solution on Windows and fall back to WSL2 when MXC is bypassed by user, bypassed by user configuration, or not available. Fully replace the need for WSL2."

## Overview

Orbit turns a person's own computer into their AI team. Today, Windows users must install Windows Subsystem for Linux (WSL2) and run the whole of Orbit — installer, service, sandboxing, everything — inside a Linux distribution. Sandboxing relies on native Windows sandboxing being absent in Orbit's deputized shell, so WSL2 exists purely as a way to reuse the Linux sandboxing story.

This feature makes Orbit a **first-class native Windows application**, using Microsoft Execution Containers (MXC) — Microsoft's policy-driven containment system for running untrusted agent workloads on Windows 11 — as the **primary, default sandbox**. Orbit's entire ownership policy (which files a crew member can never read, where they can write, which network hosts they may reach, which commands they may not run) is expressed through MXC containment.

WSL2 is demoted to an explicit **fallback mode**, used only when:

1. The owner **bypasses MXC** (opts out of containment, per owner choice), or
2. The owner **configures WSL2 mode** (chooses it over the default), or
3. MXC is **not available or not supported** on the machine.

**Target user**: a non-technical owner on Windows 11 who should not need to know what WSL, bubblewrap, or PowerShell are. Everything that today must happen "inside WSL" (install, service, sandbox, browser, notifications, speech) must work natively.

## User Scenarios & Testing

### Primary user story

**US1 — First setup on Windows, no WSL2**: An owner downloads Orbit on a clean Windows 11 machine (WSL2 never installed), runs one installer, and finishes setup — Claude tools installed, team data in `~/Staff`, service running at login, first employee hired. They never see a Linux prompt nor a mention of WSL. *Acceptance: no step requires WSL2 or a Linux shell; the team folder and service live natively.*

**US2 — Owner converses from their phone**: The owner's chat bot, control panel, voice notes, and live calls all work exactly as documented, on native Windows. *Acceptance: all platform checks in `orbit doctor` pass with no WSL2 present.*

**US3 — Sandboxed work, native**: An employee runs headless shells, reading files, writing its workspace, and fetching approved web pages. Each shell/PowerShell command executes inside an MXC container; the agent process and its flows run unmodified, exactly as on macOS/Linux. A command trying to read the owner's credential store, write outside its scope, or reach a non-allowlisted host **fails**. *Acceptance: the agent process is launched identically to the macOS/Linux path; all positive and negative containment tests pass per Orbit's existing policy model, translated onto MXC controls at the command level.*

**US4 — Owner bypasses MXC, intentionally**: An owner who for any reason does not trust or cannot use MXC can set a config switch to use WSL2 mode (Orbit's current behavior). Orbit explains the security tradeoff and moves (or instructs how to move) its service and data flow into the WSL2 environment as it works today. *Acceptance: explicit user action only — Orbit never switches modes by itself.*

**US5 — MXC not available**: On a machine where MXC is unsupported (wrong Windows build, missing prerequisites — e.g., a Windows version lacking ProcessContainer policy features, a non-supported OS, missing executor/precondition), Orbit detects it at setup/start, clearly reports why, and either completes setup in WSL2 fallback mode (with the same UX today) or tells the owner exactly what to install. *Acceptance: detection precedes any sandboxed run; messaging names the fix and the alternative.*

**US6 — Sandboxed probe before first use**: At setup (and re-checkable at any time in `orbit doctor`), Orbit runs a **positive probe** (a contained workload succeeds at allowed actions) and a **negative probe** (a denied write, denied read, and denied network connection each fail) before the first real employee run. *Acceptance: Orbit never hands crew work to an environment it has not probed in both directions.*

**US7 — Switch modes later**: An owner can change the sandbox mode after initial setup. Switching must never lose or corrupt their existing team data (registry, secrets, skills, run logs). *Acceptance: switching modes keeps the `~/Staff` tree consistent and re-launchable; data written in one mode is readable in the other where the filesystem overlaps, and inaccessible data is clearly named in the doctor/plugin output.*

**US8 — Existing WSL2 users unchanged**: A current Windows owner who uses WSL2 keeps working exactly as before; existing tests and docs keep passing. *Acceptance: all existing behaviors under WSL2 mode are verified unchanged by the existing test suite.*

### Edge cases

- Intermediate Windows states: WSL2 is partially installed (WSL enabled, no distro) — doctor names the state and the fix.
- MXC changes between a check and a run (discovery said “supported”, launch fails) — Orbit surfaces launch errors with the run's job name, never silently runs an unsandboxed shell.
- Owner changes their `Staff` data root (`STAFFROOM_HOME`) — must remain valid in both modes.
- A run outlives a timeout — containment must never leave a running sandboxed workload after the harness gives up.
- Secrets were already saved under WSL2 — switching modes must not expose them through paths that the other mode does not protect (e.g., NTFS ACLs vs. chmod on Ext4).
- Multiple Windows accounts on one machine — containment policy must stay within the logged-in owner's data.

## Functional Requirements

### R1 — Native Windows platform (first class)

- **R1.1**: Orbit detects a native Windows host (not WSL2, not Linux, not macOS) as its own platform kind, distinct from WSL2.
- **R1.2**: All platform-dependent behaviors choose the native-Windows branch when the host is native Windows: browser opening (default Windows browser), notifications, path and environment reads (native Windows values, not bridges through a Linux layer), Python/tool lookups, file paths.
- **R1.3**: Live-call audio capture, voice transcription, chat bots, and the control panel all work natively without `/mnt/c`-style bridging.

### R2 — MXC containment as the primary sandbox on native Windows

- **R2.1**: The default and primary sandboxing technology for employee agent runs on native Windows is MXC. Orbit never relies on deputized-shell sandboxing as the containment boundary for agent workloads on native Windows.
- **R2.2**: Orbit translates its single existing policy model onto MXC policy surfaces, preserving parity with the macOS/Linux/WSL2 behavior:

  | Orbit policy (today) | What MXC containment must enforce |
  | --- | --- |
  | Secret deny-reads (credential stores, secrets folder, chat/browser/mail, Desktop/Documents/Downloads) | Those files and stores are unreadable by a workload, using their **Windows-native locations** (credential stores, browser cookie/password stores, Desktop/Documents/Downloads, `~/.ssh`, etc.) |
  | Write-scope limited to owner-approved folders | Workloads can write only inside the team tree and the employee's own workspace (plus a per-command temp area) |
  | Network allowlist (pypi/PyPI downloads + owner-approved domains) | Outbound network is denied by default and allowed only to the configured domains, both for HTTP(S) and other protocols |
  | Excluded commands (gateway tools run outside the sandbox under their own limits) | Those commands pass through unwrapped, exactly as they do under Claude Code's own sandbox on macOS/Linux — their own limits remain in force |
  | “Full autonomy” softens allowlist behavior per existing rules | Mode-specific behavior preserved; no new allowlist widening beyond what the owner configured |
  | Denied command families (native shells, remote pushes, etc.), mod/skill/ability gates | Preserved as they exist at the permission/mode layer today (unchanged); containment covers what the OS-level layer already covers on macOS/Linux |

- **R2.3**: **Containment surface parity**: containment applies exactly to the surface Claude Code's own sandbox covers on macOS/Linux — shell command execution (Bash/PowerShell tool calls) — achieved through Claude Code's documented hook mechanism so that MXC becomes the per-command sandbox. The agent process itself, its agentic loop, file/web tools, and their permission behavior run **unmodified**; Orbit does not wrap, relocate, or constrain how Claude handles its own flows beyond the shell boundary.
- **R2.4**: If containment can't start (MXC installation broken, prerequisite missing, executor launch failure), the command **fails closed**: the hook denies the command rather than letting it run unsandboxed; Orbit surfaces the reason. Orbit must also not send built-in-sandbox requirement settings on native Windows that would prevent the agent from starting at all (the built-in sandbox does not exist there; those settings remain unchanged on macOS/Linux/WSL2).
- **R2.5**: Policy production is deterministic: for a given owner registry state and employee, Orbit generates the same containment policy, and logs what it generated (for audit and support).

### R3 — every service/flow migrated off WSL2

On native Windows, with WSL2 absent, all of the following work natively and with no Linux-shell step:

- **R3.1 Initialization**: `orbit setup` completes end to end (checks, business info, bot token, first hire, service start).
- **R3.2 Service**: The background service (the always-on team) starts at Windows login, keeps running, is restart-safe, and is stoppable by the owner — without a hidden Linux process, a Startup shortcut pointing into WSL, or WMI bridging.
- **R3.3 Doctor**: `orbit doctor` covers the platform checks (MXC prerequisites per the Windows version support matrix, containment probe, speech tooling, Python deps, chat channel readiness, service liveness), and fixes/messaging reference native-Windows commands, not `setup-linux.sh`.
- **R3.4 Speech**: Voice notes and live calls work natively (FFmpeg-based audio pipeline and transcription available on Windows; built or downloaded automatically by an explicit Orbit step, or clearly guided).
- **R3.5 Suite**: Existing flows the docs enumerate — demo, hire, pause/resume, abilities, roles, skills, run, secrets, groups/teams, panel open — work identically from the owner's mental model (“one command in a window”).
- **R3.6 Documentation**: README/SETUP (or equivalents) presents native Windows as the primary Windows path, WSL2 as the fallback. Install scripts cover the native route.

### R4 — WSL2 fallback semantics

- **R4.1**: WSL2 mode is the **fallback**, triggered by exactly these conditions: (a) MXC bypassed by the owner's explicit action, (b) MXC not available/supported. Nothing else switches modes automatically.
- **R4.2**: Configuration is a single, discoverable switch (in Orbit's own settings/doctor UX, not an env var hunt), with values covering “MXC (default)”, “WSL2”, and an explicit override documented for bypassing MXC.
- **R4.3**: When WSL2 mode is chosen or needed, Orbit's setup either (i) completes the existing WSL2 flow for the owner (today's experience preserved) or (ii) explains precisely what's wrong and what to do. Both options produce a working crew.
- **R4.4**: If neither MXC nor WSL2 can produce a contained environment, Orbit refuses to run crew work rather than running unsandboxed, with a clear message of the two prerequisites.
- **R4.5**: Mode choice is per-machine, decided at setup (and re-checkable), not silently per-run. Doctor reports the currently effective mode and why.

### R5 — Existing platforms preserved

- **R5.1**: macOS and Linux behavior are entirely unchanged.
- **R5.2**: WSL2 behavior is preserved as today (same policy, same install path including WSL1 rejection, same bwrap/socat/AppArmor setup, same service bridging); existing tests keep passing unchanged.

### R6 — Verification, diagnostics, safety

- **R6.1**: Setup and doctor probe containment in both directions before the environment counts as ready (positive tool behaviors and negative denials).
- **R6.2**: When the probed environment mismatches any Orbit policy requirement, doctor reports the mismatch in owner language (e.g., “this Windows build can't enforce network restrictions; you need a newer build or WSL2 mode”).
- **R6.3**: On denied operations inside the sandbox, Orbit surfaces appropriate diagnostics for support (hashes of events, reasons, suggested fixes) without overwhelming owners.

## Key Entities

- **Owner** — a person; owns the registry, secrets, domains, and the mode choice.
- **Employee (crew member)** — an agent (a hiring record + workspace + profile) whose runtime is contained; unchanged from today.
- **Sandbox policy** — Orbit's ownership-derived access rules (exact same model as today); new: its **MXC-native expression** on Windows.
- **Containment runtime** — the OS-provided environment MXC instantiates for a contained shell command (one per contained command — short-lived and stateless between commands; no long-lived agent-session container).
- **Platform mode** — the effective containment path on this machine: `mxc` (native Windows + MXC) or `wsl2` (Orbit inside WSL2, unchanged); recorded in Orbit's own settings, surfaced by doctor.

## Assumptions & Dependencies

1. **MXC version**: Built on the stable, publicly released MXC request schema (v1.0.0 or later), with an official discovery path for "is MXC supported on this machine and build?". Backends used ProcessContainer at minimum; experimental MXC backends (Windows Sandbox, MicroVM, Hyperlight) are out of scope.
2. **Consumption without a build toolchain**: Orbit is a script kit for non-technical owners; the owner's machine is not required to have Rust/Node toolchains. Orbit consumes MXC through its ready-made official runtime (executor/service) artifacts, not by building from source.
3. **Containment surface** (owner decision, 2026-11-04): the agent process must run unmodified — whole-agent containment was rejected. Parity baseline therefore matches Claude Code's own sandbox semantics on macOS/Linux/WSL2: the OS-level boundary covers **shell commands only**; Claude's file/web tools keep following the permission system as they do on every platform. MXC is integrated via Claude Code's documented hook layer (the same surface Orbit's guard already uses), never by wrapping the agent.
4. **Existing permission/mode/gates** (Claude-side settings file: allow/deny lists, ability gates, guard/plan tracking, secret storage) are unchanged on native Windows; containment adds the OS-level boundary, not permission rules.
5. **Telemetry**: Orbit's use of MXC does not enable Microsoft telemetry on the owner's behalf; any MXC telemetry is left to Microsoft's defaults, surfaced in the privacy docs/README.
6. **Claude tooling is installed natively** on Windows by/for the owner, as it is for Windows users today; Orbit's setup instructs it when missing.
7. Owner data tree (`~/Staff` semantics) is unchanged in shape and stored under the owner's Windows profile; switching modes later is a data-transition topic, not a structural change.

## Out of scope

- Changes to macOS or Linux behavior (beyond shared code receiving the new platform kind).
- Whole-agent containment (wrapping or relocating the agent process / agentic loop inside a container) — **rejected by owner decision, 2026-11-04**; Claude's own flows stay untouched.
- Experimental MXC backends (Windows Sandbox, MicroVM/NVX, Hyperlight), and MXC lifecycle/container management beyond the per-command containment model required for agent shell work.
- GUI/window/clipboard containment beyond what MXC ProcessContainer applies by default.
- Git/Python tooling upgrades, voice model distribution changes, or any new employee workflow features.
- WSL1 support (still rejected, as today).
- Historical data migration from WSL2 to native beyond the documented switch flow (see R4.3 and US7).

## Success Criteria

- **SC1 — Setup parity**: On a clean Windows 11 machine with WSL2 not installed, a non-technical owner completes `setup` including the first hire and the service running at login, in under 30 minutes, with no Linux shell and no manual command beyond Orbit's own prompts.
- **SC2 — Containment enforcement**: 100% of the negative probe tests (secret read, out-of-scope write, non-allowlisted network destination, denied command family) fail closed on native Windows MXC mode, matching the same tests on macOS/Linux/WSL2.
- **SC3 — No silent mode changes**: Fallback to WSL2 occurs only through the two documented triggers (owner configuration or MXC unavailability); a test battery demonstrates no other path changes the mode (no accidental per-run switching).
- **SC4 — Zero regression**: Existing macOS, Linux, and WSL2 behaviors are unchanged — all existing tests pass unmodified.
- **SC5 — Recognizable setup failures**: Every must-fix doctor condition names its cause and its fix command; testing across at least: no CLAUDE tooling, unsupported Windows build, missing MXC prerequisites, no network connectivity, missing speech tools.
- **SC6 — Performance parity**: MXC containment per shell command adds no more than ~1 second of startup overhead per contained command, and an average employee run's duration increases by no more than 10% versus the macOS/Linux baseline feel — the crew stays "already fast".
- **SC7 — Owner understanding**: A first-run owner can answer, in their own words, where their platform mode is (doctor output says it), what their crew can and cannot do, and how to switch modes — without consulting technical docs.
