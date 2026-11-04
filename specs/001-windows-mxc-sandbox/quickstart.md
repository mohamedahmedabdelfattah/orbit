# Quickstart: Validation guide — Native Windows with MXC

Feature: `001-windows-mxc-sandbox`. On-demand validation guide (not a release gate — see the note at the end). Prerequisite reading: [spec.md](./spec.md), [contracts/mxc-request.md](./contracts/mxc-request.md), [contracts/cc-hook.md](./contracts/cc-hook.md).

## Scenario A — First setup on Windows 11, no WSL2 (spec US1, SC1, SC5, SC7)

**Prerequisites**: a Windows 11 (x64 or ARM64) machine or VM where WSL2 has never been installed; network access; a Claude sign-in.

**Steps**:

1. Open PowerShell (no admin). Run the Windows installer script from the kit folder. Expect: Python, git, ffmpeg, tesseract, MXC runtime, pip deps installed; each step prints what/why; no step mentions WSL or Linux.
2. Run `orbit setup`. Expect: platform checks include the MXC containment probe (positive: allowed write succeeds; negative: out-of-scope write, secret read, non-allowlisted connect each *fail*), Claude sign-in check, chat bot pairing, first hire. Expect effective mode reported (doctor/summary): `mxc`.3. `orbit doctor`. Exit code 0; all must-fix checks ☑ with fix commands naming native tools (winget/orbit commands), `setup-linux.sh` never referenced.
4. Message the first employee in chat/panel and ask for file work. Expect: run succeeds; the agent flows exactly as on macOS/Linux (one unmodified agent process); the run log records mode `mxc`; shell commands are the contained surface.

**Expected**: within ~30 minutes; no Linux shell involved; no orphan processes.

## Scenario B — Containment negatives (spec US3, SC2) — on Windows 11 only

Ask the employee (or a direct `orbit run`) to, in separate runs:

1. Read `~/.ssh`-equivalent or the browser cookie store → denied by containment, reported as a sandbox violation (Orbit surfaces name + reason).
2. Write outside its workspace (Desktop, `C:\`, etc.) → denied.
3. Connect to a domain not on the allowlist → denied.

**Expected**: every denial fails **inside** the contained run (exit/diagnostic), never falls back to an unsandboxed retry.

## Scenario C — Probing an unsupported host (spec US5, R4)

Force the probe on a machine/build lacking MXC support (or temporarily rename the MXC runtime to simulate missing prerequisites).

**Expected**: setup/doctor reports unsuitability with a machine-readable reason; Orbit recommends WSL2 fallback; no crew run happens unsandboxed; doctor exit code 1.

## Scenario D — Owner bypasses MXC → WSL2 fallback (spec US4, R4)

Use Orbit's own settings/doctor switching to select WSL2 mode on a machine that also has WSL2 + the current Linux-side setup.

**Expected**: `orbit setup` (or the guided switch) walks the existing WSL2 flow unchanged; doctor shows mode `wsl2` decided by `owner`; existing `/mnt` sandbox behaviors and bwrap checks return; the native MXC path is untouched afterwards (switch back anytime; data guidance per doctor).

## Scenario E — Regression: macOS / Linux / existing WSL2 (spec R5, SC4)

Run the existing test suite (`python3 -m unittest discover tests`) on a Mac/Linux and inside WSL2. **Expected**: all pass unmodified; no behavioral diffs; the new windows-mode code paths are inert without affinity (ORBIT_OS/env not set).

## Scenario F — Mode switch without data loss (spec US7)

Pre-create a team on one mode; switch on the other; repair a path or copy as doctor instructs; run again.

**Expected**: doctor names both locations, no silent moves, registry continues loading, no corrupt state; switching back works.

## What's tested automatically vs. hinted (owner decision, 2026-11-04)

- **Automated (CI, every push)**: policy translation, hook decision logic, probe matrix, doctor output, mode switching, WSL2/mac/Linux regression — all via the fake-executor seam.
- **Not automated, on-demand only**: real-host MXC scenarios (A–D) on a Windows 11 machine. These are a validation guide, not a release checklist — releases proceed without them. Code/tests/workflow carry a comment noting that MXC containment itself is not part of automated testing.
