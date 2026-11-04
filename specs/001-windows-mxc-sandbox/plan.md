# Implementation Plan: Native Windows with Microsoft Execution Containers (MXC)

**Feature**: `001-windows-mxc-sandbox` — [spec.md](./spec.md)
**Status**: Plan complete
**Branch**: none created (no git-extension hook; work lands on the current branch by owner choice)

## Technical Context

| Dimension | Decision | Notes |
| --- | --- | --- |
| Runtime | Python 3.9-compatible, no new heavy dependencies | Orbit is a script kit; `wxc-exec` is an external binary, not a Python lib |
| Host OS | Windows 11 x64/ARM64 (ProcessContainer backend), plus existing mac/Linux/WSL2 unchanged | Discovery decides; fallback per spec R4 |
| MXC consumption | Official MXC runtime artifacts executing versioned stable-schema JSON container-creation requests (the project's documented SDK-free path — "use when the SDK cannot be embedded in your app"); executor binary `wxc-exec.exe` on Windows | Avoids requiring Node/Rust toolchains on the owner's machine |
| Policy model | Single translation layer Orbit-side: Orbit policy (deny-read/allow-write/network allowlist) → MXC request JSON | Same policy structure already exists in `engine.settings_json()` |
| Service | Windows Scheduled Task (logon trigger) running `pythonw.exe … orbit service-run`; existing stamp-file liveness (`staffd_alive`) reused | Replaces WMI/`wsl.exe` bridging; macOS launchd / Linux systemd paths untouched |
| Installer | New `setup-windows.ps1` (PowerShell, winget-based) parallel to `install.sh` + `setup-linux.sh` | Owner runs once from a PowerShell window; no admin unless a tool requires it |
| Tests | Unit tests with `ORBIT_OS="windows"` fakes (policy translation, config, service wiring); real MXC probes are manual/quickstart, not CI | CI runners (Windows Server) don't satisfy MXC host requirements — documented |
| CI | GitHub Actions: existing Ubuntu suite + new `windows-latest` job running unit tests only | see "Why CI doesn't test real MXC" below |

**Constitution check**: `.specify/memory/constitution.md` does not exist — no project constitution constraints; N/A. No gate violations.

## Architecture Decisions (summary — full rationale in research.md)

1. **Contain per shell command; never wrap the agent.** On native Windows, Claude Code's own sandbox does not exist, and changing how the agent runs is out of scope (owner decision). Orbit integrates through Claude Code's documented hook surface — a `PreToolUse` hook matching `Bash|PowerShell` rewrites each shell command into an MXC executor invocation before it runs. The agent process, file/web tools, and permission behavior remain exactly as on macOS/Linux. Orbit also omits the `failIfUnavailable` sandbox requirement on native Windows so the agent still starts (that requirement remains for mac/Linux/WSL2).
2. **Executor-binary (JSON request) consumption** instead of embedding a Node/Rust SDK: matches Orbit's "no toolchains on the owner's machine" posture; the stable schema is versioned and documented by Microsoft. Requests are generated **per shell command** by a fast Orbit-side helper invoked from the hook.
3. **One new core module** owns the policy translation, request generation, hook script, and probe, so `engine.py` stays the single policy source and the platform layer stays thin.
4. **Mode selection lives in the Orbit registry** (next to other owner-owned settings), set at setup, changeable by a doctor-guided command; native Windows defaults to MXC, degrades to a `wsl2` recommendation only on the spec's two triggers.
5. **Windows Scheduled Task for the service**, with the existing `staffd_alive` stamp file as liveness (`orbit status`/doctor work unchanged conceptually).

---

## Phase 0: Research

See [research.md](./research.md). Open items resolved at plan time:

- D1 MXC consumption mode (executor + stable schema) — resolved, with distribution-artifact verification listed as an implementation-time check against the current release.
- D2 Policy translation table Orbit→MXC (filesystem/network/command surfaces) — resolved.
- D3 Service and installer mechanics on native Windows — resolved.
- D4 Fallback semantics and mode persistence — resolved per spec R4.
- D5 Windows speech stack (ffmpeg + whisper build toolchain messaging) — resolved (explicit guided download/build step; details in research).
- D6 Verification/Diagnostics paths — resolved (probe + audit-mode as doctor triage).

## Phase 1: Design

- [data-model.md](./data-model.md) — entities, config fields, state transitions.
- [contracts/](./contracts/) — `mxc-request.md` (the JSON container-creation contract Orbit emits per contained command), `cc-hook.md` (the PreToolUse hook contract), and `service-task.md` (scheduled task naming/inputs/outputs contract).
- [quickstart.md](./quickstart.md) — end-to-end validation: native install without WSL2, positive/negative containment probes, fallback toggle, WSL2 regression pass.

## Post-design constitution re-check

N/A (no constitution).

## Risks (tracked to tasks)

| Risk | Mitigation |
| --- | --- |
| ProcessContainer capabilities vary by Windows build (network host filtering, Learning Mode) | Capability probe at setup maps to spec R6.2; unsupported → WSL2 recommendation |
| Per-command container startup may add noticeable latency | SC6 bound (~1 s/command); probe measures it; if a build is slow, doctor reports and the batch policy can group long chains |
| Hook-returned command change interacts with auto-mode classifier review | Hook returns `permissionDecision: "allow"` together with `updatedInput` (documented auto-approve pairing); deny/ask rules still evaluate the rewritten command |
| MXC distribution method may change between releases | Vendor/install step verifies artifact checksum & schema version at install time (task T020) |
| MSVC build toolchain needed for whisper on Windows | Guided winget install of Build Tools as an explicit doctor step (docs-first, optional feature) |
| Data transition when switching modes (WSL2 → native) | Doctor warns + documented copy direction; no silent data moves (spec Out of Scope) |
| CI can't exercise real MXC | Not a gate (owner decision 2026-11-04): automated testing covers everything with the fake-executor seam; a comment/hint notes MXC real-host behavior is outside automated testing — see "Why CI doesn't test real MXC" below |

## Why CI doesn't test real MXC (informational note, not a gate)

Owner decision, 2026-11-04: **MXC containment itself is not testable in automated CI** and does **not** carry a manual release checklist. The rest of the feature — platform detection, policy translation, hook decision logic, doctor checks, fallback semantics, mode switching — is fully automated via the fake-executor seam.

- GitHub-hosted `windows-latest` runners are **Windows Server** images; MXC's ProcessContainer requires Windows 11 client builds with per-build policy support. Real-host probe scenarios therefore can't run as automated tests.
- The CI workflow and test files carry a short comment/hint stating that MXC real-host behavior is not part of automated testing, pointing to `specs/001-windows-mxc-sandbox/quickstart.md` as an on-demand validation guide — to be used only when someone chooses to validate on real Windows 11 hardware, never as a release requirement.
- No release checklist, no gating step: releases proceed on the automated suite alone.
