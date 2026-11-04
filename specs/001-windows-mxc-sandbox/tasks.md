# Tasks: Native Windows with MXC (001-windows-mxc-sandbox)

**Feature**: replace WSL2 with native Windows + MXC containment, WSL2 as fallback ([spec](./spec.md) · [plan](./plan.md) · [research](./research.md) · [data-model](./data-model.md) · [contracts](./contracts/) · [quickstart](./quickstart.md))

**Conventions**: `[P]` = parallelizable (independent files). `[US#]` = user story from spec.md. Tests reference the fake-executor seam (T002) — no real MXC in CI.

---

## Phase 1 — Setup

- [ ] T001 Create the new core module skeleton `core/mxc.py` with the module doc describing its one job (translate Orbit policy to a per-contained-command MXC stable-schema request; issue contained commands through the hook helper and probe the sandbox; refuse instead of unsandbox), the pinned request schema major version constant, and executor invocation constants — matching the doc style of `core/osinfo.py`
- [ ] T002 [P] Add the fake-executor seam inside `core/mxc.py`: a single overridable `_spawn_executor(args, env, ...)` plus `set_executor_stub()`/stub helpers so unit tests can intercept launches (pattern: `ORBIT_OS` fakes in `core/osinfo.py`)
- [ ] T003 [P] Extend `tests/test_platforms.py` with an `ORBIT_OS="windows"` fixture harness (imports modules under `ORBIT_OS`, asserts `osinfo.KIND == "windows"` once Phase 2 exists) — mirror the existing `ORBIT_OS="wsl"` harness at line 83

## Phase 2 — Foundational (blocking for all stories)

- [ ] T010 Extend `core/osinfo.py::_kind()` to return `"windows"` for native Windows (`sys.platform == "win32"` without the `/proc/version` microsoft marker and with no WSL env), keeping `"wsl"` detection intact
- [ ] T011 Update `core/osinfo.py` metadata for the new kind: `DEVICE` ("PC"), `SUPPORTED`, `NAME` ("Windows"), `_MAC`/`local()` device lookup — and `BIN_DIRS`/`path_dirs()`/`which()` for native Windows (`%LOCALAPPDATA%\Programs` etc.), leaving mac/wsl/linux branches byte-identical
- [ ] T012 [P] Native browser/notification/env in `core/osinfo.py`: `open_url()` via `webbrowser`/`os.startfile`; add a best-effort `notify()` Windows branch (PowerShell toast); `win_env`/`win_python`/`win_path` guarded to WSL-only (native paths read directly)
- [ ] T013 [P] In `core/engine.py`: add the native-Windows `SECRET_PATHS` set exactly per `data-model.md` column "Windows-native value" (`%USERPROFILE%` credential stores, Chrome/Edge/caches, Desktop/Documents/Downloads, Orbit secrets folder); keep the `wsl` + `/mnt` branch unchanged; keep `BASE_DENIED` shell families (add nothing new)
- [ ] T014 Mode storage in the registry (helpers in `core/mxc.py` reading/writing via `engine.registry()`): fields `platform.sandbox_mode` (`"mxc"|"wsl2"`, default `"mxc"` on `windows` kind), `platform.decided_by` (`"owner"|"unavailable"`), `platform.decided_at`, `platform.mxc_unavailable_reason` — validation: mode changes only by owner action or a recorded unavailability reason (data-model §1)
- [ ] T015 [P] Unit tests (ORBIT_OS=windows): kind detection, metadata, open_url dispatch targeter (stubbed), secret-path presence, mode helpers default/validation — in `tests/test_platforms.py`

## Phase 3 — US1: first setup on Windows, no WSL2

**Goal**: `orbit setup` completes on native Windows with zero WSL2 steps (spec SC1, SC5). **Independent test**: run setup on a clean Win11 box per quickstart Scenario A — no Linux shell step anywhere.

- [ ] T020 [US1] Create `setup-windows.ps1`: installs Python 3 (x64/ARM64), git, ffmpeg, tesseract via winget; installs the MXC runtime from the official artifact (pinned at authoring time; `Get-FileHash` checksum verified) and verifies its prerequisites, recording the runtime version in a kit-local version file; `pip install --user requests beautifulsoup4 playwright websocket-client`; prints `orbit setup` guidance — same messaging tone as `install.sh`
- [ ] T021 [US1] In `install.sh`: keep as the WSL2/Linux installer; add a native-Windows detection that says "you're on native Windows: run setup-windows.ps1 in PowerShell" and exits 0 — no behavior change for WSL2/Linux users
- [ ] T022 [US1] Service: extend `orbit::start_other()`/`stop()` with a native-Windows branch — create/delete the Scheduled Task per `contracts/service-task.md` (name `Orbit`, logon trigger, `pythonw.exe … orbit service-run`, `STAFFROOM_HOME` env, hidden); liveness via the existing `staffd_alive` stamp; failure messaging must not mention WSL
- [ ] T023 [US1] Doctor: extend `orbit::platform_checks()` with a native-Windows branch (Python found on PATH, MXC runtime present + schema version match, Python deps, ffmpeg/tesseract, speech model, service running); must-fix/optional flags per spec R3.3; every fix message names a native command
- [ ] T024 [P] [US1] Unit tests (ORBIT_OS=windows): scheduled-task creation command construction (fake `_ps`-equivalent / subprocess capture), start/stop idempotence, doctor check output golden strings in `tests/test_platforms.py`
- [ ] T025 [US1] Docs: README.md + SETUP.md — native Windows as the primary Windows path (one PowerShell command, then `orbit setup`), WSL2 presented as the fallback with its existing section preserved; update CLAUDE.md/PRODUCT.md platform lines, plus the one-line MXC-telemetry note in the privacy docs (spec Assumption 5)

## Phase 4 — US3: sandboxed employee runs, native (MXC)

**Goal**: each shell/PowerShell command runs contained under MXC via the PreToolUse hook, with full policy parity and an unmodified agent process (spec R2.1–R2.4, SC2). **Independent test**: translation invariants + hook-decision matrix + negative-probe parity in unit tests; quickstart Scenario B manually.

- [ ] T030 [US3] Policy translation in `core/mxc.py::build_request(emp, command, cwd)`: map `engine`'s existing policy sources → `contracts/mxc-request.md` (deny_read incl. Windows secret paths, allow_write truncated to workspace+team+temp, network egress deny-default + allowlist incl. `BASE_DOMAINS` + registry domains + gateway hosts, timeout) — deterministic, cached per run (data-model §2)
- [ ] T031 [US3] Request invariants tests (T030): determinism (two builds byte-equal modulo temp/time, R2.5), fail-closed defaults, deny∩allow disjointness, no silent loosening — per the contract's invariants 1–5, in `tests/test_mxc.py`
- [ ] T032 [US3] Hook implementation `core/mxc.py::handle_pre_tool_use()`: read the hook JSON (stdin), decide per `contracts/cc-hook.md` — excluded → no decision; contained → `allow` + `updatedInput` with the contained command; impossible → `deny` + plain-language reason (R2.4); emit diagnostics entries for the run log, including a hash of the generated request per contained command for audit/support (R2.5)
- [ ] T033 [US3] Hook registration wiring in `core/engine.py::settings_json()`: on native Windows, add the `PreToolUse` hook (matcher `Bash|PowerShell`, Orbit helper in exec form) to the settings blob, and omit the built-in sandbox's `failIfUnavailable` key (agent must start normally); verify hooks are honored via `--settings`, else write to the workspace `.claude/settings.json` (contract note); mac/Linux/WSL2 settings output byte-identical to today
- [ ] T034 [P] [US3] Hook decision-matrix + executor-flow unit tests via the fake seam (excluded pass-through, allow+rewrite auto-approve pairing, deny-on-failure, no widening) in `tests/test_mxc.py`; ORBIT_OS=wsl regression untouched
- [ ] T035 [P] [US3] Denial/sandbox-validation surfacing: parse executor failure/diagnostic output into owner-readable summaries + support-bundle path in `core/mxc.py` (feeds R6.3)

## Phase 5 — US6: probing before first use

**Goal**: setup/doctor prove both directions before any crew run (spec R6.1–R6.3). **Independent test**: probe verdict states exercised via fake executor; quickstart Scenarios A/C.

- [ ] T040 [US6] Implement `core/mxc.py::probe()` — min-policy request set per plan D6: positive (allowed write succeeds), negatives (write outside scope, deny_read access, non-allowlisted connect, contained workload terminated at its `timeout_ms` — no orphaned sandboxed process) with a probe-result structure per data-model §3 (`usable`/`unusable-with-reason`, capability notes incl. per-command startup milliseconds for SC6)
- [ ] T041 [US6] Wire the probe into `orbit setup` (before service start / first hire) and `orbit doctor` (a must-fix check) per spec R6.1; unusable on native Windows ⇒ refuse unsandboxed and print the two prerequisites (mxc fix or wsl2 fallback) — R4.4
- [ ] T042 [P] [US6] Triage command: `orbit doctor --audit` runs the executor's audit mode on a tiny workload and renders the owner-readable report from T035 — explicitly never used on real runs (contract note)
- [ ] T043 [US6] Unit tests: probe matrix (all pass ⇒ usable; each negative passing ⇒ unusable with matching reason) in `tests/test_mxc.py`

## Phase 6 — US5: MXC unavailable ⇒ WSL2 fallback

**Goal**: the unavailability trigger works exactly as specified (spec R4.1/R4.3, SC3). **Independent test**: quickstart Scenario C.

- [ ] T050 [US5] Unavailability handling in `core/mxc.py`/`orbit`: on probe/discovery failure record `platform.decided_by="unavailable"` + reason (data-model §1), recommend and (with one confirmation) run the existing WSL2 flow guidance; never switch silently mid-run
- [ ] T051 [US5] Doctor surfaces the recorded reason + both fix paths (mxc repair | wsl2 mode) verbatim (SC5); golden-string tests in `tests/test_platforms.py`

## Phase 7 — US4: owner bypass/config ⇒ WSL2 mode

**Goal**: explicit mode selection with tradeoffs documented (spec R4.1/R4.2/R4.5). **Independent test**: quickstart Scenario D.

- [ ] T060 [US4] Mode switch UX: a guided doctor-driven switch (powers `wsl2` ⇄ `mxc`) writing `platform` fields via T014 helpers; refuses when the target mode's prerequisites are missing, and for `wsl2` prints the WSL2-side install/doctor steps (existing flow — no silent bootstrapping of WSL)
- [ ] T061 [US4] Guard in `orbit start`/`engine.run`: selected mode gates the whole native-vs-WSL flow (wsl2 on native Windows host tells the owner to run Orbit inside WSL2 today's way) — no per-run auto-switch (SC3); tests in `tests/test_platforms.py`

## Phase 8 — US7: switch modes later, no data loss

**Goal**: mode changes never lose/corrupt `~/Staff` (spec US7). **Independent test**: quickstart Scenario F.

- [ ] T070 [US7] Doctor mode-inventory check: on switch, print both data locations (`%USERPROFILE%\Staff` vs `\\wsl.localhost\…`), the documented copy direction, and the NTFS-ACL/chmod nuance — no automatic moves (research D8)
- [ ] T071 [P] [US7] Registry transition tests (fields set, no overwrite of unrelated keys, both-mode reload) in `tests/test_mxc.py`

## Phase 9 — US2: peripherals & speech, native

**Goal**: calls, voice notes, notifications, panel/browser flows work natively (spec R3.4/R3.5). **Independent test**: doctor checks pass on a clean Win11 box; a live call + voice note round-trip.

- [ ] T080 [US2] `orbit::get_whisper()` native-Windows branch per plan D5: prebuilt-if-available else guided winget (git, cmake, VS Build Tools C++) + existing whisper.cpp build flow; doctor messaging per quickstart
- [ ] T081 [P] [US2] `core/calls.py::ready()` native branch: use `sys.executable` (no `/mnt/c` cwd, no `win_python` hop) and native Windows mic messaging; verify capture path(s) exercised via fake subprocess in `tests/test_platforms.py`
- [ ] T082 [P] [US2] Sweep remaining WSL bridges for native short-circuits: `osinfo.open_url`/`notify` verified in T012 panel/`demo` consumers; `tesseract`/`ffmpeg` doctor fix strings point at winget/`setup-windows.ps1`

## Phase 10 — US8: regression + CI + release polish

**Goal**: zero regressions; ship-ready docs/CI (spec R5, SC4).

- [ ] T090 [US8] Add `windows-latest` job to `.github/workflows/tests.yml` running the unit suite (fake executor; no MXC); keep the existing Ubuntu/WSL smoke jobs unchanged; include a workflow comment stating: "MXC containment itself is not part of automated testing (CI runners are Windows Server; MXC requires Windows 11 hosts) — fake-executor stubs cover the Orbit-side logic; see specs/001-windows-mxc-sandbox/quickstart.md for on-demand real-host validation"
- [ ] T091 [P] [US8] Full-suite run on macOS/Linux/WSL2 confirming SC4 (no behavioral diffs; wsl cases byte-stable); fix any incidental breakage without touching mac/linux semantics
- [ ] T092 [P] [US8] Release ops: bump `VERSION`, note the feature in `PRODUCT.md`/README header; docs mention (comment/hint only, not a checklist) that MXC real-host behavior is outside automated testing and quickstart.md is an on-demand validation guide
- [ ] T093 [P] [US8] `tests/test_platforms.py` golden review: every new ORBIT_OS=windows assertion documented inline (why it exists, which spec rule it guards)

---

## Dependencies & order

```
Phase 2 (foundational) ─┬─> Phase 3 (US1) ─> Phase 5 (US6) ─> Phase 6 (US5) ─> Phase 7 (US4)
                        └─> Phase 4 (US3) ──┘ (translation/runs need only Phase 2 + T002 seam)
Phase 8 (US7) after Phase 7 (mode fields exist)
Phase 9 (US2) after Phase 3 (doctor/installer conventions)
Phase 10 (US8) last (regression + release)
```

- US1 and US3 can proceed **in parallel** once Phase 2 lands (independent files: installer/service vs. translation/runs).
- US5 (T050) reuses US6's probe verdicts — implement after T040–T043.
- No story depends on real MXC at test time (seam from T002).

## Parallel execution examples

- After T010–T014: run T012, T013, T015 simultaneously with T020 (US1) and T030 (US3) starting next.
- Within US1: T024 ∥ T025 after T022/T023.
- Within US2: T080, T081, T082 all parallel.

## Implementation strategy (MVP first)

1. **MVP slice = Phase 2 + US3 + US6**: policy translation, contained runs, probe — the feature's non-negotiable core, fully unit-testable via the seam.
2. Then US1 (owner-facing install/service) so the MVP is demoable end-to-end per Scenario A.
3. Then fallback semantics (US5→US4→US7), peripherals (US2), and the regression/CI sweep (US8).
