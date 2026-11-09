# Tasks: Claude Connection Pass-Through

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/claude-launch.md](./contracts/claude-launch.md), [quickstart.md](./quickstart.md)

**Tests**: Required. Use fake Claude only; no live provider credentials, inference, or network.

## Phase 1 — Setup: Shared Test Harness

**Purpose**: Provide one deterministic fake executable for every story and platform test.

- [X] T001 Create a reusable fake-Claude harness in `tests/fake_claude.py` that supports version and auth-status responses, JSON and stream-JSON inference output, argv/environment recording, configurable exit/failure modes, a non-echoing credential sentinel, and a separate harmless emitted marker.

---

## Phase 2 — Foundational: Launch Policy Seam

**Purpose**: Establish the shared ordinary-versus-legacy policy required before story-specific callers change.

- [X] T002 Add failing launch-policy unit tests in `tests/test_core.py` proving ordinary mode starts from the inherited environment, removes only `CLAUDECODE`, applies exactly the enumerated Orbit-owned overrides from `contracts/claude-launch.md`, and preserves arbitrary unknown sentinels, while legacy API-key mode strips conflicting routing/auth values, injects only the stored key for inference, and retains isolated employee/onboarding setting sources.
- [X] T003 Implement the side-effect-free ordinary-versus-legacy environment and setting-source policy in `core/engine.py` without adding provider schemas, discovery, routing, persisted readiness state, or a new inference module.

- [X] T038 [P] Define the launch-inventory regression guard in `tests/test_core.py`: parse L01–L11 from `contracts/claude-launch.md`, reject any production direct use of the resolved Claude executable in `orbit` or `core/` not mapped to an inventory ID, and reject conditional sites L02–L04 whose resolved class pair is undeclared or outside the contract. The guard runs against this contract from Phase 2 onward; its remaining static checks (wording, preflight, provider artifacts) are activated at T032 after all launch-site migrations.

**Checkpoint**: Shared policy behavior is tested; production launch callers are not yet switched.

---

## Phase 3 — User Story 1: Account-Free Setup and Status (P1)

**Goal**: Setup, doctor, checklist, and Settings require a working Claude executable but never a Claude account session.

**Independent test**: A fake executable with a successful version and `loggedIn:false` passes setup; missing and non-executable clients produce one installation/repair action without account-login guidance.

### Tests

- [X] T004 [US1] Add availability/setup tests in `tests/test_platforms.py` for exactly `available`, `missing`, and `broken` states, including a signed-out fake client, successful version invocation, missing executable, failed version invocation, matching setup and doctor gating, and proof that general setup and doctor never call account status or mention `claude auth login`. (FR-001–FR-004)
- [X] T005 [P] [US1] Add checklist, Settings, and panel-response tests in `tests/test_core.py` requiring provider-neutral Claude availability and rejecting signed-in/out state or generic `claude auth login` guidance. (FR-003, FR-004)

### Implementation

- [X] T006 [US1] Add a shared version-only Claude availability helper in `core/engine.py` and update `claude_status()` plus mandatory setup/doctor gating in `orbit` to use it, returning only `available`, `missing`, or `broken` with installation/repair guidance. (FR-001, FR-002, FR-004)
- [X] T007 [US1] Replace the general account-readiness cache/checklist data in `core/panel.py` with the shared installation availability result while keeping account status out of ordinary readiness. (FR-003, FR-004)
- [X] T008 [US1] Update Claude availability rendering in `core/panel/app.js` so missing/broken describes the client, available never claims an account method, and Cloud Shift account state remains separate. (FR-003)
- [X] T009 [P] [US1] Remove global account-login prerequisites from `install.sh` and `setup-windows.ps1` while retaining installed/executable Claude Code requirements and actionable missing-client guidance. (FR-001, FR-002, FR-023)

**Checkpoint**: User Story 1 works independently; an owner can install and inspect Orbit while signed out. *(Verified locally: US1 unit/UI tests pass on the fake client; the full setup→hiring→employee end-to-end validation is T012 in User Story 2.)*

---

## Phase 4 — User Story 2: Exact Claude Connection Pass-Through (P1)

**Goal**: Every ordinary local model-backed flow uses Claude's existing connection and user configuration without Orbit becoming a provider system.

**Independent test**: Known and arbitrary inherited sentinels reach employee, onboarding, and plugin-administration fake launches with the required setting sources and unchanged Orbit safety controls; legacy stored-key launches remain isolated.

### Tests

- [X] T010 [US2] Add employee launch-matrix tests in `tests/test_core.py` requiring `--setting-sources user,project`, preservation of known and arbitrary future-provider sentinels, `CLAUDECODE` removal, every enumerated Orbit-owned override key from `contracts/claude-launch.md` winning over inherited values, and unchanged sandbox, guard, strict-MCP, model, effort, allowed/denied tool, workspace, prompt, and session arguments. (FR-005–FR-011, SC-002, SC-004)
- [X] T011 [US2] Add structured-onboarding, guard-plugin administration, and legacy compatibility tests in `tests/test_core.py`: pass-through onboarding uses `user` plus no-tools/schema/strict-MCP/model/effort/no-session controls; ordinary onboarding and guard-plugin launches preserve known and arbitrary inherited sentinels, delete only `CLAUDECODE`, and receive no unlisted overlays; legacy employee/onboarding/plugin-administration sources remain isolated; plugin administration keeps its fixed operation/workspace, matches the setting-source behavior declared for its class, and never receives the stored inference key. (FR-005–FR-009, FR-012, SC-002, SC-005)
- [X] T012 [P] [US2] Add the signed-out end-to-end setup → structured hiring → employee-task scenario using one temporary Orbit home in `tests/test_platforms.py`, asserting successful fake output and no account-login command or instruction. (SC-001)
- [X] T013 [US2] Add persistence-boundary tests in `tests/test_core.py` proving no provider profile, endpoint, credential, model-discovery result, readiness result, or run binding is written to `staff.json`, employee files, sessions, or UI state. (FR-010, FR-020, FR-022, SC-008)

### Implementation

- [X] T014 [US2] Route employee command construction and execution through the shared launch policy in `core/engine.py`, select `user,project` outside legacy mode, preserve arbitrary inherited values by default, remove only `CLAUDECODE`, and retain every explicit Orbit safety/session control. (FR-005–FR-011)
- [X] T015 [P] [US2] Route structured hiring through the shared launch policy in `core/onboard.py`, select `user` outside legacy mode, retain the existing isolated legacy source, and preserve no-tools, schema, strict-MCP, model, effort, prompt, and no-session-persistence controls. (FR-006–FR-009, FR-012)
- [X] T016 [US2] Route guard-plugin install/update commands in `core/engine.py` through the assigned ordinary or legacy-isolated non-key policy without changing plugin commands, scope, workspace, generated interactive-session settings, or application links. (FR-007, FR-008, FR-012)

**Checkpoint**: User Story 2 works independently; hiring and every employee business flow use Claude's effective configuration while legacy API-key mode remains unchanged. *(Verified: `EmployeeLaunch` matrix, `HireAndPluginLaunch`, persistence-boundary, and `SignedOutSetup` tests pass against the fake Claude; the four `engine.run()`-through tests and the T012 scenario execute in the macOS/Linux/WSL2 CI jobs — native Windows cannot run the fake `.bat` shim with the real employee argv, matching the repo's precedent for `LiveSteps`.)*

---

## Phase 5 — User Story 3: Provider-Neutral Execution and Failures (P2)

**Goal**: Ordinary work starts without an Anthropic-host preflight and reports actual Claude failures without provider assumptions or copied credentials.

**Independent test**: Socket access to `api.anthropic.com` fails while fake Claude succeeds immediately; actual transient failures retain delayed retry behavior and provider-neutral diagnostics.

### Tests

- [X] T017 [US3] Add socket-trap and employee execution tests in `tests/test_core.py` proving successful ordinary work never probes `api.anthropic.com`, starts fake Claude immediately, preserves resume/new-session safeguards, and never starts an Orbit provider fallback. (FR-013, FR-014, FR-016, SC-003)
- [X] T018 [US3] Add diagnostic-provenance tests in `tests/test_core.py` for connection, authentication, provider, network, rate-limit, and unknown failures: preserve process result/failure class and existing Claude-output handling for each class, retain transient metadata, keep owner wording provider-neutral for each class with no generic account-login prescription, and prove a non-echoed inherited sentinel—credential values or otherwise—never enters Orbit-generated registry, employee, UI, activity, run-metadata, or log records. (FR-004, FR-015, FR-020, SC-009)
- [X] T019 [P] [US3] Add routine, catch-up, and agent-follow-up dispatch tests in `tests/test_platforms.py` proving `core/staffd.py` does not gate model-backed work on Anthropic reachability, actual transient failure invokes existing retry callbacks, and plain reminders/duplicate-work/due-window behavior remains. (FR-013, FR-016)

### Implementation

- [X] T020 [US3] Remove ordinary `online()`/`wait_online()` gating and endpoint-based replay from `core/engine.py`, preserve resume/new-session retry safeguards, and make `friendly_error()`/`why_failed()` provider-neutral without adding inherited environment/settings values to run records. (FR-013–FR-016, FR-020)
- [X] T021 [US3] Remove Anthropic-connectivity gating from model-backed routine, catch-up, and agent-follow-up paths in `core/staffd.py` while preserving awake checks, due windows, retry delays, plain-reminder delivery, and duplicate-work controls. (FR-013, FR-016)
- [X] T022 [US3] Generalize non-cloud account/plan wording and comments in `core/team.py`, `core/panel.py`, and `core/guard/staff-guard/hooks/register.js` without changing scheduling, guard, or activity behavior. (FR-004, FR-015, FR-021)

**Checkpoint**: User Story 3 works independently; healthy alternative connections are never blocked by Anthropic reachability and failures remain provider-neutral. *(Verified: `ProviderNeutralRun` traps sockets and the pre-run wait, proves one immediate fake invocation and unchanged resume→new-session recovery; `Diagnostics` checks six real failure classes for provider-neutral wording and distinct plain reasons; `DiagnosticProvenance` proves the actual process error and transient flag survive while no inherited sentinel enters `runs.jsonl` or the Orbit home; `Strategy`/`Asleep` prove routines, catch-up, and follow-ups start with `engine.online` never called, retries re-arm at +10 minutes, and due-window/plain-reminder behavior holds. The run-through-fake classes execute in the macOS/Linux/WSL2 CI jobs; native Windows skips them as recorded in `quickstart.md`. Full suite: 134 tests, 34 baseline-native-Windows failure ids and **zero new failures** — the two renamed tests and `test_clean_env_never_leaks_api_settings` left the list, `test_a_missed_day_is_made_up_for_in_one_run` and `test_no_run_starts_in_a_few_second_wake` now pass because they read the real employee workspace, and flaky `CloudShift` did not recur.)*

---

## Phase 6 — User Story 4: Account-Only Cloud Shift Boundary (P2)

**Goal**: Cloud Shift remains a fresh, isolated Claude-account feature without making ordinary local work account-dependent.

**Independent test**: The full auth-method matrix, stale-display-cache transition, manual/automatic enablement, L07–L11 launch families, and eligibility loss all enforce the account-only contract while local work continues.

### Tests

- [X] T023 [US4] Add Cloud Eligibility Result tests in `tests/test_platforms.py` requiring a monotonic `checked_at`, `eligible=True` only for `loggedIn:true` plus `authMethod:"claude.ai"`, preserved `auth_method`, empty `reason` only when eligible, and a read-only in-memory cache no longer than 60 seconds. Cover `none`, `third_party`, `api_key`, `api_key_helper`, and `oauth_token`. (FR-017, SC-006)
- [X] T024 [US4] Add account-environment tests in `tests/test_platforms.py` requiring construction from an empty mapping, forced owner home/profile, known executable/system path and platform temp directory, only the exact POSIX/macOS or Windows bootstrap keys in `contracts/claude-launch.md`, controlled `TERM` only for session bootstrap, and absence of `CLAUDECODE`, `CLAUDE_CONFIG_DIR`, proxies, known provider values, and arbitrary `FUTURE_PROVIDER_TOKEN`. (FR-019)
- [X] T025 [US4] Add Cloud Shift lifecycle tests in `tests/test_platforms.py` proving manual enablement, new-hire auto-enablement, and local cloud operations bypass a stale positive display cache; eligibility loss keeps an existing `employees.<id>.cloud_shift` flag but blocks later cloud operations with an account-only reason; ordinary work remains available; owner disable clears the local flag without requiring positive eligibility and makes remote cleanup best-effort. (FR-017, FR-018, SC-006)
- [X] T026 [US4] Add per-inventory launch tests for L07 `trigger()`, L08 `send()`, L09 `environment()`, L10 `new_session()`, and L11 `_transcript()` in `tests/test_platforms.py`, requiring a fresh eligibility check, the account allowlist, empty setting sources for inference commands, and unchanged cloud-specific tool/session arguments. (FR-017, FR-019)
- [X] T027 [P] [US4] Add Cloud Shift status, hire/manage response, and account-only copy assertions in `tests/test_core.py` for eligible, ineligible, cached-display, and enabled-but-ineligible states without changing general Claude availability. (FR-003, FR-017, FR-018)

### Implementation

- [X] T028 [US4] Implement the transient Cloud Eligibility Result and account environment in `core/cloud.py`: memory-only cache capped at 60 seconds for read status, exact `claude.ai` qualification, fresh-check mode, empty-mapping platform allowlist, forced default owner account location, and no persisted auth/provider/credential fields. (FR-017, FR-019, FR-022)
- [X] T029 [US4] Route L07–L11 through fresh eligibility and account-environment launch helpers in `core/cloud.py`, explicitly disable user setting sources, preserve cloud command arguments, expose eligibility-loss errors through existing state, make disable locally authoritative with best-effort remote cleanup, move any remaining cloud-only Anthropic connectivity helper out of `core/engine.py`, and remove the global probe when no caller remains. (FR-017, FR-019)
- [X] T030 [US4] Update new-hire auto-enablement and manual Cloud Shift order paths in `core/orders.py` to require fresh eligibility, never infer cloud eligibility from ordinary Claude availability, and preserve ordinary first-day local work when cloud setup is rejected. (FR-017, FR-018)
- [X] T031 [P] [US4] Expose cached read-only Cloud Shift eligibility/reason and enabled-but-ineligible state in `core/panel.py`, and condition hire/manage promises and controls in `core/panel/app.js` without claiming local work is broken. (FR-003, FR-017, FR-018, FR-021)

**Checkpoint**: User Story 4 works independently; local work is account-free while every Orbit-initiated Cloud Shift operation enforces its separate account contract. *(Verified: `CloudAccount` covers the exact `loggedIn`/`authMethod` matrix, the monotonic 60 s display cache with fresh bypass, an empty-mapping account allowlist (forced owner home/profile, executable plus known system path, platform temp dir, no inherited provider/proxy/unknown values, interactive-only `TERM`), fresh manual and new-hire enablement, eligibility-loss blocking with the configured flag preserved, locally authoritative best-effort disable, and all L07–L11 launches taking a fresh check, the account environment, and empty setting sources for inference. `CloudShiftPanel` proves display-only member/state/settings fields, account-only reasons, order and hire rejection with local work intact, and enabled-but-ineligible handling; `engine.online`/`wait_online` are removed and the cloud tick owns its own `_online()`. Full suite: 145 tests, the same 34 baseline-native-Windows failure ids and **zero new failures**.)*

---

## Phase 7 — Polish and Cross-Cutting Validation

**Purpose**: Complete documentation, launch-inventory enforcement, repository-wide copy checks, and supported-platform regression gates.

- [X] T032 Activate the T038 launch-inventory regression guard after all launch-site migrations, then add the remaining tracked-file contract tests in `tests/test_core.py`: reject ordinary `api.anthropic.com` probes and ad hoc provider filtering, allow account-login wording only in exact Cloud Shift messages, and forbid provider modules/schemas/endpoints/credential stores/relays/inference dependencies/migrations. (FR-007, FR-010, FR-013, FR-023, SC-002, SC-007, SC-008)
- [X] T033 [P] Rewrite assisted setup and recovery guidance in `SETUP.md` for installation-only readiness, externally configured Claude, persistent unattended service configuration, trusted owner hooks/plugins, provider-neutral diagnosis, and the separate optional Cloud Shift account requirement. (FR-023–FR-025)
- [X] T034 [P] Update requirements, architecture, privacy/non-guarantees, Windows/WSL instructions, and Cloud Shift boundaries in `README.md` so account sign-in is one supported Claude configuration rather than an ordinary-work prerequisite. (FR-021, FR-023–FR-025)
- [X] T035 Resolve every non-allowlisted static-contract hit across `orbit`, `core/`, `install.sh`, `setup-windows.ps1`, `SETUP.md`, `README.md`, `docs/`, `templates/`, and `.github/workflows/tests.yml` while retaining exact account-only Cloud Shift guidance and historical/test-fixture exclusions. (FR-003, FR-004, FR-021, FR-023, SC-007)
- [X] T036 Run `python -m unittest tests.test_core tests.test_platforms` and every Scenario A–K check from `specs/002-claude-connection-pass-through/quickstart.md`; fix only feature-caused regressions and record unrelated native-Windows limitations separately.
- [X] T037 Run `python -m unittest tests.test_core tests.test_platforms` in the macOS, Ubuntu 24.04, and WSL2 jobs, and the existing native-Windows subset (`tests.test_mxc`, `tests.test_platforms -k Windows`, `tests.test_platforms -k .Mode.`) per `.github/workflows/tests.yml`; verify legacy API-key, sandbox, guard, MCP, session, no-migration, and credential-sentinel gates, recording pre-existing failures or an unavailable CI job in `specs/002-claude-connection-pass-through/quickstart.md` without claiming or weakening an unverified assertion. (SC-004, SC-005, SC-008, SC-009)

---

## Dependencies and User Story Order

### Phase dependencies

- T001 precedes all fake-Claude tests.
- T002 precedes T003; T003 blocks production launch-policy integration in T014–T016; T038 follows T002 and can run in parallel with T003.
- User Story 1 tests T004–T005 precede T006–T008; T009 is independently parallelizable.
- User Story 2 tests T010–T013 precede T014–T016; T012 also depends on completed User Story 1.
- User Story 3 tests T017–T019 precede T020–T022 and assume ordinary launches from User Story 2.
- User Story 4 tests T023–T027 precede T028–T031; T029–T031 depend on T028.
- T032–T035 follow all story implementations; T032 activates the T038 guard against the fully migrated launch sites; T036–T037 are final gates.

### User story completion graph

```text
Setup T001 → Foundation T002–T003, T038
                    ├─→ US1 (T004–T009) ─→ US2 end-to-end T012
                    ├─→ US2 (T010–T016) ─→ US3 (T017–T022)
                    └─→ US4 tests (T023–T027)
US1 + US4 foundation ────────────────→ US4 implementation (T028–T031)
US1 + US2 + US3 + US4 ──────────────→ Polish (T032–T037)
```

US1 and the non-end-to-end parts of US2 can begin after Foundation. US4 test preparation can proceed alongside US2/US3, but its panel integration follows US1's general availability work.

## Parallel Execution Examples

### Foundation

- T038 (launch-inventory guard definition) can be written in parallel with T003 once T002's policy contract is known.

### User Story 1

- T004 (`tests/test_platforms.py`) and T005 (`tests/test_core.py`) can be written in parallel.
- T009 (installer scripts) can proceed alongside panel implementation after the test contract is known.

### User Story 2

- T012 (`tests/test_platforms.py`) can be written in parallel with T010–T011/T013 (`tests/test_core.py`).
- T015 (`core/onboard.py`) can proceed in parallel with T014 (`core/engine.py`) after T003 and its own tests.

### User Story 3

- T019 (`tests/test_platforms.py`) can be written in parallel with T017–T018 (`tests/test_core.py`).
- After tests, `core/staffd.py` work can proceed separately from provider-neutral copy work.

### User Story 4

- T027 (`tests/test_core.py`) can be written in parallel with T023–T026 (`tests/test_platforms.py`).
- After T028, T031 (`core/panel.py`, `core/panel/app.js`) can proceed alongside cloud launch integration.

### Polish

- T033 (`SETUP.md`) and T034 (`README.md`) can proceed in parallel after T032 activates the static contract defined at T038.

## Implementation Strategy

### MVP first

Complete Phases 1–3 (T001–T009). This independently delivers account-free setup, doctor, checklist, Settings, and installers without claiming runtime pass-through is complete.

### Incremental delivery

1. Build the deterministic fake, the shared launch-policy seam, and the launch-inventory guard (T038).
2. Deliver User Story 1 as the setup/status MVP.
3. Deliver User Story 2 so hiring and ordinary employee work use Claude's existing connection.
4. Deliver User Story 3 and User Story 4; after US1, their test preparation can overlap, but production changes follow their tests.
5. Finish tracked-file, documentation, targeted-suite, and CI gates.

### Completion discipline

- Write each story's listed failing tests before its implementation tasks.
- Stop at each checkpoint and run that story's independent test.
- Do not add provider configuration, credentials, endpoint fields, routing, inference clients, or migrations to make a test pass.
- Do not mark T036 or T037 complete while a feature-caused failure remains.
