# Tasks: `orbit sandbox off` disables MXC on native Windows

**Feature**: MXC owner opt-out (see `PLAN.md` at repo root for design and rationale)
**Source plan**: `D:\Programming\Projects\AI\Orbit\PLAN.md`
**Note**: Generated directly from PLAN.md; this repo has no `.specify/` scaffolding.

## User Stories (derived from PLAN.md)

- **US1 (P1)** — Owner can turn MXC off on native Windows with `orbit sandbox off`, and the next run runs without the MXC hook (default installs keep MXC on).
- **US2 (P2)** — Owner can see the MXC state: `orbit sandbox` status and `orbit doctor` reflect the owner's choice instead of demanding a "fix".
- **US3 (P3)** — Docs match reality: no stale "MXC stays on / remains mandatory" claims.
- **US4 (P1)** — `orbit setup` asks whether the crew runs in a sandbox and, on Windows, which mode (MXC / WSL2) among the available ones. The default answer is **no sandbox** (explicit `sandbox: false`), per owner's decision.

## Phase 1: Foundational (core toggle semantics — blocks all stories)

- [x] T001 [US1] In `orbit` `sandbox_cmd` (lines 1085–1102): on `off`, set `reg["sandbox"] = False` instead of `reg.pop("sandbox", None)`; keep `on` writing `True` and keep the `engine.claude_session(eid)` refresh loop unchanged. Update the function docstring (it currently says MXC "remains mandatory").
- [x] T002 [US1] In `orbit` `main()` (sandbox subparser, ~line 1139): add `--yes` flag (`sb.add_argument("--yes", action="store_true")`); in `sandbox_cmd`, when `osinfo.KIND == "windows"` and `engine.recorded_sandbox_mode() == "mxc"` and state is `off` and not `--yes`, prompt for typed confirmation (monkeypatchable via `input`), warning that shell commands will run unsandboxed with full user rights and listing what stays (guard plugin, secret deny-lists, PowerShell-tool requirement). Abort without writing the registry if not confirmed.
- [x] T003 [US1] In `core/engine.py` `settings_json` (lines 461–469): attach the MXC blob only unless the owner opted out — off-branch triggers when `not sandboxed() and not (osinfo.KIND == "windows" and recorded_sandbox_mode() == "mxc" and registry().get("sandbox") is not False)`. Do not touch `sandbox_blob` (engine.py:434–458) or `sandboxed()` (428–431). Update the docstring to describe the three states: absent (default, MXC on), `True` (sandbox+MXC), `False` (explicit opt-out, no MXC).

## Phase 2: US1 — turn MXC off end-to-end

**Goal**: `orbit sandbox off` (confirmed) → next run's settings JSON is `{"enabledPlugins": {}, "sandbox": {"enabled": false}}` with no `hooks` key; fresh/default Windows registry keeps the MXC hook.
**Independent test**: set a temp registry with `"sandbox": false` on Windows (`ORBIT_OS=windows`), call `engine.settings_json(employee, [])`, assert no `hooks` and `sandbox.enabled == false`; with the key absent, assert `hooks` present.

- [x] T004 [P] [US1] Add tests in `tests/test_core.py` (settings_json block ~line 2198): (a) Windows default registry → `hooks` present; (b) Windows + `"sandbox": false` → no `hooks`, `sandbox.enabled == false`; (c) Windows + `"sandbox": true` → `hooks` present; (d) macOS/WSL + `"sandbox": false` → byte-identical to today's off state `{"enabledPlugins": {}, "sandbox": {"enabled": false}}`.
- [x] T005 [P] [US1] Add tests in `tests/test_platforms.py` (sandbox_blob block ~lines 2073–2086 and `sandboxed()` ~line 704): `sandbox_cmd("off")` on Windows writes `False` (not pop) and prompts when MXC mode is on (patch `input` to return `"y"`), does not prompt with `--yes`, aborts and leaves registry unchanged on refusal; macOS/WSL `off` never prompts.
- [x] T006 [US1] Run the changed test files: `python -m pytest tests/test_core.py tests/test_platforms.py tests/test_mxc.py` (fallback `python -m unittest tests.test_core tests.test_platforms tests.test_mxc`). All green, no skipped new tests.

## Phase 3: US2 — status and doctor reflect the owner's choice

**Goal**: `orbit sandbox` (no args) shows the MXC state including explicit opt-out; `orbit doctor` on Windows with opt-out reports MXC as "disabled by owner's choice" and does not fail on the MXC checks.
**Independent test**: `orbit sandbox` output shows opt-out wording; `orbit doctor` exits 0 with the informational line on an opted-out Windows registry.

- [ ] T007 [US2] In `orbit` `say_sandbox_status()` and `sandbox_change_summary()`: show/say the native-Windows MXC state — default ("MXC containment on"), opt-out ("MXC containment off at owner's choice"), or `sandbox: true`. Cover the non-Windows branches unchanged.
- [x] T008 [US2] In `orbit` `windows_checks` (lines 306–335): when the registry shows the explicit opt-out (`registry().get("sandbox") is False` and mode is `mxc`), downgrade the build gate, `wxc-exec.exe` presence, and probe checks to informational lines ("MXC disabled by owner's choice — `orbit sandbox on` restores containment") instead of failures.
- [x] T009 [P] [US2] Add doctor/status tests in `tests/test_platforms.py`: opted-out Windows registry → `windows_checks` reports the informational note and no failure; default registry → checks still enforce (existing behavior preserved).

## Phase 4: Polish & cross-cutting

- [x] T010 [P] Update CLI help and module docstring in `orbit` (line 24): document that native Windows keeps MXC by default and `orbit sandbox off` (with confirmation or `--yes`) disables it.
- [x] T011 [P] Update `docs/toolbelt.md` lines 25–26 and `docs/SETUP.md` line 79: replace "Native Windows always keeps its MXC boundary" with the three-state behavior and what is lost vs. kept on opt-out (lost: per-command ProcessContainer, egress deny, filesystem allow-write; kept: guard plugin, secret deny-lists, PowerShell-tool requirement, `CLAUDE_CODE_USE_POWERSHELL_TOOL`).
- [x] T012 [P] Update `README.md` lines 258–270 and 343–344 to match the new behavior.
- [x] T013 Run the full verification: `python -m pytest tests/` green; grep `orbit`, `docs/`, `README.md` for stale claims ("MXC stays on", "remains mandatory", "cannot be turned off") → no matches.
      Note: no pytest on this machine — `python -m unittest` used throughout. `tests.test_core`, `tests.test_platforms`, `tests.test_mxc` all green. Full `discover` shows 22 failures + 11 errors, **byte-identical to the pre-change baseline at HEAD** (verified in a throwaway worktree): pre-existing cross-module interference, out of scope here. Stale-claim grep clean.

## Phase 5: US4 — setup asks the sandbox choice (default: no sandbox)

**Goal**: fresh `orbit setup` asks "Run the crew in a sandbox?" with bare-Enter = No; on Windows a follow-up picks among available modes (MXC when build/probe pass, WSL2 when `wsl.exe` exists; default MXC when available); declining writes `sandbox: false` and setup completes without MXC must-fix failures.
**Independent test**: with patched `yes`/`ask`/`input` and a temp registry, `setup_sandbox_choice()` (a) on bare Enter writes `sandbox: false` on every platform; (b) on Windows + "yes" + passing probe writes `sandbox: true` and mode mxc; (c) with MXC broken and wsl.exe present offers WSL2 only; (d) with neither available, default answer exits without registry changes.

- [x] T014 [US4] In `orbit`, extract a `setup_sandbox_choice(reg)` function and call it from `setup()` (line 798) before the `platform_checks()` gate (line 804): non-Windows asks one yes/no question (default No → `reg["sandbox"] = False`, yes → `True`, saved with reason "setup: sandbox <state>"); Windows shows the current containment state, asks yes/no (default No → explicit `sandbox: false`), and on yes offers only available modes — MXC requires `_win_build()` ≥ 10.0.26100, `mxc.discover()["ok"]` and `sandbox_probe()` verdict `usable`; WSL2 requires `osinfo.which("wsl.exe")`; record with `mxc.set_mode(..., decided_by="owner")`; neither available → print both fixes and offer "continue without a sandbox? (y/N)" (default exits setup). Reuse the existing `yes()`/`ask()` helpers (orbit:82–91).
- [x] T015 [US4] Verify (and adjust only if needed) the interaction with existing gates: after T008, `windows_checks()` (orbit:306) must downgrade MXC items for an opted-out registry so setup's `must and not ok` filter (orbit:804) passes without MXC; keep the WSL2 fallback block (orbit:806–817) unchanged; keep the WSL2-mode gate (orbit:191–197) so a Windows-side setup in wsl2 mode still redirects to WSL.
- [x] T016 [P] [US4] Add `setup_sandbox_choice` tests in `tests/test_platforms.py` (patch `yes`/`ask`/`input` and `mxc.discover`/`sandbox_probe`/`_win_build`/`osinfo.which`): the four cases above, plus a re-run where the registry already has `sandbox: true` and the owner answers yes (state unchanged) and answers bare-Enter (explicit downgrade to `false` recorded with reason).
- [x] T017 [US4] Update `docs/SETUP.md` setup walkthrough: the new sandbox question, its No-default, the Windows mode offer and the "no mode available" path.

## Dependencies

- T001 → T002 → T003 (registry write, then CLI surface, then engine read; semantics must agree before tests).
- Phase 2 (T004–T006) depends on Phase 1 complete. T004 and T005 are parallel (different files).
- Phase 3 (T007–T009) depends on T001/T003 (status/doctor read the same registry state).
- Phase 4 depends on Phases 2–3.
- Phase 5 (T014–T017) depends on T001/T003 (the explicit `sandbox: false` semantics it writes) and on T008 (windows_checks downgrade; T015 verifies the setup path rides on it).

## Parallel execution examples

- After T001–T003 land: run T004 and T005 in parallel (different test files).
- In Phase 3: T009 parallelizes with T007/T008.
- In Phase 4: T010, T011, T012 are independent (different files).

## Implementation strategy

MVP = Phases 1–2 only (owner can actually turn MXC off and it is proven by tests). Phase 3 makes the state visible so users aren't confused by doctor. Phase 4 keeps docs honest. Phase 5 makes the choice a first-class setup step with no-sandbox as the default answer. Fail-safe invariant throughout: a registry with the key absent (every existing install) keeps MXC on — upgrading never silently unsandboxes anyone; setup's default answer is No, but answering No writes the explicit opt-out, so every setup'd machine gets a deliberate choice.
