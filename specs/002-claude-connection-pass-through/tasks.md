# Tasks: Claude Connection Pass-Through

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [contracts/claude-launch.md](./contracts/claude-launch.md)

**Tests**: Required. Fake Claude only; no live provider credentials or network.

## Phase 1 — Test Seams and Launch Policy Foundation

- [ ] T001 Add reusable fake-Claude argv/environment/status fixtures for provider-neutral launches in `tests/test_core.py` and `tests/test_platforms.py`.
- [ ] T002 [P] Add ordinary pass-through environment tests covering `ANTHROPIC_*`, provider `CLAUDE_CODE_*`, proxy/config values, Orbit overrides, and `CLAUDECODE` removal in `tests/test_core.py`. [FR-005, FR-007, FR-020]
- [ ] T003 [P] Add legacy Orbit API-key environment tests proving conflicting inherited routing values remain stripped and only the stored key is injected in `tests/test_core.py`. [FR-012, SC-005]
- [ ] T004 Implement one small pass-through-versus-legacy launch environment/source policy in `core/engine.py`; replace duplicated launch filtering only after T002–T003 fail as expected. [FR-005, FR-012]

## Phase 2 — User Story 1: Account-Free Setup and Status

- [ ] T005 [US1] Add tests proving an installed fake Claude with `loggedIn:false` passes the mandatory setup/doctor Claude check and missing/broken executables fail clearly in `tests/test_platforms.py`. [FR-001, FR-002, SC-001]
- [ ] T006 [US1] Change `claude_status()` and setup gating in `orbit` to executable/version availability only; remove global account-login instructions. [FR-001, FR-002, FR-004]
- [ ] T007 [P] [US1] Replace `core/panel.py` account-readiness cache/checklist state with provider-neutral Claude availability and add response tests in `tests/test_core.py`. [FR-003, FR-004]
- [ ] T008 [US1] Update Claude status rendering in `core/panel/app.js` so unavailable means missing/broken client, never merely signed out. [FR-003]

**Checkpoint**: Setup works with no Claude account. No runtime pass-through claim yet.

## Phase 3 — User Story 2: Exact Claude Connection Pass-Through

- [ ] T009 [US2] Add command-construction tests requiring `--setting-sources user,project` for ordinary work while preserving sandbox, guard, strict MCP, tool, prompt, model, effort, and session arguments in `tests/test_core.py`. [FR-006, FR-008, FR-011, SC-002, SC-004]
- [ ] T010 [US2] Update ordinary command/environment construction in `core/engine.py` to load user/project settings and preserve Claude connection environment outside legacy API-key mode. [FR-005–FR-009, FR-011]
- [ ] T011 [P] [US2] Add structured-onboarding tests requiring user settings, inherited connection sentinels, no tools, strict MCP, schema, model, and effort in `tests/test_core.py`. [FR-006–FR-008]
- [ ] T012 [US2] Update `core/onboard.py` to use shared launch policy, load the user setting source outside legacy API-key mode, and generalize Claude-plan policy wording. [FR-006–FR-009, FR-012]
- [ ] T013 [US2] Update guard plugin administration environment in `core/engine.py` to use shared policy without changing plugin commands or workspace controls; add regression assertion. [FR-007, FR-008]
- [ ] T014 [P] [US2] Add tests showing no provider profile, endpoint, credential, or model-discovery state is written to registry or employee files in `tests/test_core.py`. [FR-010, FR-020, FR-022]

**Checkpoint**: Hiring and employee work use Claude's user configuration; legacy API-key mode remains isolated.

## Phase 4 — User Story 3: Provider-Neutral Execution and Failures

- [ ] T015 [US3] Add a socket-trap test proving a successful employee run makes no `api.anthropic.com` preflight and starts fake Claude immediately in `tests/test_core.py`. [FR-013, FR-014, SC-003]
- [ ] T016 [US3] Remove ordinary `online()`/`wait_online()` use and endpoint-based replay from `core/engine.py`; preserve resume/new-session safeguards and leave any still-used account-cloud probe intact until T022. [FR-013, FR-014, FR-016]
- [ ] T017 [P] [US3] Add scheduled-job and agent-follow-up tests proving `core/staffd.py` dispatches model-backed work without Anthropic preflight and invokes existing transient retry callbacks after actual failure in `tests/test_platforms.py`. [FR-013, FR-016]
- [ ] T018 [US3] Remove Anthropic-connectivity gating from model-backed scheduler paths in `core/staffd.py`; preserve awake, due-window, retry-delay, plain-reminder delivery, and duplicate-work controls. [FR-013, FR-016]
- [ ] T019 [P] [US3] Add provider-neutral auth/network/rate-limit error and routine-reason assertions in `tests/test_core.py`. [FR-004, FR-015]
- [ ] T020 [US3] Generalize `friendly_error()`, `why_failed()`, and non-cloud plan-only wording/comments in `core/engine.py`, `core/panel.py`, `core/team.py`, and `core/guard/staff-guard/hooks/register.js`. [FR-015]

**Checkpoint**: Healthy alternative connections are never blocked by Anthropic reachability; failures do not prescribe account login.

## Phase 5 — User Story 4: Account-Only Cloud Shift Boundary

- [ ] T021 [US4] Add cached account-eligibility tests proving only `loggedIn:true` plus `authMethod:"claude.ai"` qualifies, while `none`, `third_party`, `api_key`, `api_key_helper`, and `oauth_token` do not; assert sanitized environment/settings in `tests/test_platforms.py`. [FR-017, FR-019, SC-006]
- [ ] T022 [US4] Implement account-only eligibility and any Anthropic-specific connectivity helper inside `core/cloud.py` (shared helper only if needed), keeping Cloud Shift commands isolated and removing the obsolete global engine probe once no caller remains. [FR-017, FR-019]
- [ ] T023 [US4] Extend new-hire tests proving ineligible Claude connections never set `cloud_shift`, while qualifying account behavior remains, in `tests/test_platforms.py`; adjust `core/orders.py` only if strengthened `cloud.available()` is insufficient. [FR-018]
- [ ] T024 [P] [US4] Expose Cloud Shift eligibility/reason through `core/panel.py` and condition hire/manage promises in `core/panel/app.js`; add state/render assertions. [FR-003, FR-017, FR-018]

**Checkpoint**: Ordinary work is account-free; Cloud Shift still requires and truthfully reports its separate account contract.

## Phase 6 — Documentation, Copy, and Regression

- [ ] T025 [P] Remove global login prerequisites from `install.sh` and `setup-windows.ps1`; retain Claude installation instructions. [FR-002, FR-023]
- [ ] T026 [P] Rewrite assisted setup requirements in `SETUP.md` for externally configured Claude, persistent unattended configuration, and account-optional operation. [FR-023, FR-024, FR-025]
- [ ] T027 [P] Update `README.md` requirements/overview and `core/panel/app.js` generic budget/connection copy without changing account-only Cloud Shift descriptions. [FR-003, FR-021, FR-023, FR-024, FR-025]
- [ ] T028 Run targeted suites `python -m unittest tests.test_core tests.test_platforms`; fix only regressions caused by this feature.
- [ ] T029 Run full `python -m unittest discover -s tests` on each supported CI platform or record existing platform-specific failures separately. [SC-004, SC-005]
- [ ] T030 Run all static checks in `quickstart.md`, verify no inherited credential sentinel appears in registry/files/log/UI fixtures, and confirm no provider module/schema/dependency was added. [FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, SC-007, SC-008]

## Dependencies and Execution Order

- T001 precedes all fake-Claude integration tests.
- T002–T003 precede T004.
- T004 precedes T010, T012, and T013.
- T005 precedes T006; T007 can run in parallel after T001.
- T009 precedes T010; T011 precedes T012.
- T015 precedes T016; T017 precedes T018; T019 precedes T020.
- T021 precedes T022; T022 precedes T023–T024.
- Documentation tasks T025–T027 may run after behavior/copy contracts stabilize.
- T028–T030 are final gates.

## Parallel Opportunities

- T002 and T003.
- T007 while T005–T006 proceed.
- T011 and T014 after T004.
- T017 and T019 after T001.
- T024 after T022 while T023 proceeds.
- T025, T026, and T027.
