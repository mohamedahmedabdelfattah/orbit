---

description: "Execution tasks for the safe upstream synchronization"
---

# Tasks: Safe Upstream Synchronization

**Input**: Design documents from `specs/004-safe-upstream-merge/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required. The specification requires structural checks, focused regressions for every affected invariant, all six Python modules in separate processes, the guard plugin suite, platform evidence, documentation validation, cleanup proof, and history/tree proof.

**Organization**: Tasks are grouped by user story. Because this work operates on one active merge/index, the safe delivery order is content integration (US1), compatibility and safety (US2), candidate validation (US3), then local history recording and publication handoff (US4). Only tasks explicitly marked `[P]` may overlap.

**Active-merge rule**: Do not abort, reset, rebase, broadly stage, delete `backup-before-sync`, remove the replacement ref early, merge/pull `origin/main`, or write any remote. Do not create intermediate commits; T084 records the one genuine integration merge only after the required local gates pass.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Safe to run in parallel because it changes different files and has no incomplete dependency.
- **[Story]**: User story traceability (`US1`–`US4`).
- Every task names the exact repository or evidence path it affects.

## Phase 1: Setup (Shared Evidence Structure)

**Purpose**: Freeze the observed safety envelope and create auditable records before changing conflicted source.

- [x] T001 Create `specs/004-safe-upstream-merge/evidence/integration-ledger.md` and record full commit/tree identities for `366cf73`, `256ed16`, `93773e0`, `500d772`, `backup-before-sync`, `MERGE_HEAD`, the replacement object, and observed `origin/main`; enforce the Baseline Reference constraints: `baseline_id` is unique, `revision_id` resolves to a full commit, `tree_id` is captured independently, upstream version is `0.12.0`, product points are 0.8.0-era, `role` does not imply content integration from ancestry alone, `verified_at` follows both resolutions, and `verification_status` is exactly `verified`, `mismatch`, or `missing` with only `verified` inputs admitted.
- [x] T002 [P] Create `specs/004-safe-upstream-merge/evidence/validation-results.md` with I0–I5, G1, D1, H1, X1, REL1, and PUB1 rows seeded from the planning snapshot; every Validation Evidence record must use a unique `evidence_id`, an existing contract `gate_id`, the exact `candidate_tree_id`, one platform from `host|macos|linux|wsl2|windows_unit|windows_mxc_x64|windows_mxc_arm64|not_applicable`, one status from `pass|fail|pending|not_applicable`, a secret-free `observed` result, an artifact for `pass`/`fail`, `recorded_at`, and one blocking scope from `integration|cross_platform|product_release|publication`.
- [x] T003 [P] Create `specs/004-safe-upstream-merge/evidence/publication-options.md` with the default `hold_local` posture and the four contract options, explicitly stating that only `hold_local` needs no positive approval and that no remote command is authorized by this task list.
- [x] T004 Capture the initial `git status --short`, staged/unstaged/untracked path sets, three `UU` paths, conflict-marker locations, stage-1 blob identities, and current replacement list in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`; stop and update the design instead of continuing if they differ without explanation from `README.md`, `core/engine.py`, and `core/osinfo.py` using semantic base `500d772`.

---

## Phase 2: Foundational (Blocking Integration Inventory)

**Purpose**: Establish complete two-sided accounting, resolution records, invariants, and recovery proof before source remediation.

**⚠️ CRITICAL**: No user-story source work begins until this phase is complete.

- [x] T005 Regenerate `500d772..366cf73` and `500d772..256ed16` name-status inventories and their intersection/union in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`; require explained regeneration of the planning totals 71 local, 35 upstream, 14 shared, and 92 union paths.
- [x] T006 Populate one Change Coverage Entry per union path in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`: unique immutable `entry_id`; a path present in an authoritative input or planned evidence; `local_state` and `upstream_state` each from `unchanged|added|modified|deleted|absent`; `risk_tier` from `security_session|control_plane|docs_version|evidence`; `outcome` from `pending|retained_local|retained_upstream|combined|approved_exclusion`; resolution/invariant/evidence links; rationale except for identical unchanged paths; and explicit `owner_approval` for every `approved_exclusion`.
- [x] T007 Verify the four-path local product-point delta (`README.md`, `core/grants.py`, `core/staffd.py`, `tests/test_platforms.py`) against `500d772..93773e0` and record why each remains local work in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T008 Instantiate R-ENGINE-COMMAND, R-ENGINE-RUN, R-OSINFO-NOTIFY, R-README-COST, R-INTERACTIVE-PLATFORM, R-CLAUDE-DATA-ROOT, R-UNREAD-SCOPE, R-PROVIDER-COPY, R-TEST-EVIDENCE, R-CLEANUP, and R-RELEASE-STATUS in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`; each Resolution Decision must have a unique `resolution_id`, specific path/region, source-backed local/upstream intent, combined decision, rejected alternatives, non-empty runtime invariant links, focused evidence links, and status `proposed|applied|verified|blocked`, where `verified` requires clean diff plus passing evidence.
- [x] T009 Instantiate every BI-* invariant from `specs/004-safe-upstream-merge/data-model.md` in `specs/004-safe-upstream-merge/evidence/integration-ledger.md` with a unique ID, reviewable source, observable statement, non-empty affected paths, evidence links, and release scope exactly `integration`, `product_release`, or `both`.
- [x] T010 Create `specs/004-safe-upstream-merge/evidence/history-proof.md` and record the Recovery Point constraints: `backup-before-sync` resolves to the local baseline revision/tree, `verified_at` is present, status is one of `available|missing|mismatch|owner_released`, and it remains `available`; also record that no remote ref or recovery ref changed during setup.

**Checkpoint**: The authoritative inputs, 92-path inventory, 14 overlaps, eleven resolution records, invariant catalog, replacement metadata, and recovery route are auditable before source changes.

---

## Phase 3: User Story 1 — Update the Fork Without Losing Either Line of Work (Priority: P1) 🎯 MVP

**Goal**: Produce a marker-free, parseable 0.12.0 content candidate in which every local/upstream path is accounted for and every shared path has a semantic review or an explicit compatibility remediation link.

**Independent Test**: Regenerate both input inventories; require every union path to have one ledger entry, all 14 overlap reviews to exist, no unapproved exclusion, no unresolved index path, no accidental marker, `VERSION=0.12.0`, and all expected local/upstream artifacts present. High-risk behavioral verification remains the explicit US2 gate rather than being called complete here.

### Acceptance Checks for User Story 1

- [x] T011 [US1] Run and record the expected pre-resolution failures (`UU` scan, marker scan, `git diff --check`, staged diff check, and Python parse of `core/engine.py`) in the I2/I3 sections of `specs/004-safe-upstream-merge/evidence/validation-results.md` before editing source.

### Explicit Conflict Remediation

- [x] T012 [P] [US1] Resolve R-README-COST in `README.md` by retaining provider-neutral configured-connection language, usage limits only when Claude reports them, upstream brain/hands token guidance, optional stored Anthropic API-key compatibility, and a separate eligibility-gated Cloud Shift bullet with no duplicate/contradictory paragraph.
- [x] T013 [US1] Resolve R-ENGINE-COMMAND in `core/engine.py::command` by combining `launch_policy("employee", emp)`, ordinary `user,project` versus legacy `project` setting sources, platform tools/MXC/guard/MCP controls, and upstream interactive behavior that omits `-p`/stream flags and uses `default` unless autonomy requires `bypassPermissions`; leave no whole-side conflict choice.
- [x] T014 [US1] Resolve R-ENGINE-RUN in `core/engine.py::run` by preserving one main conversation, job-selected brain/hands model, resume/new fallback, ORIENT only on new sessions, context rollover, busy/chat coordination, idle-window fork, remembered successful session, and `finally` cleanup while removing every `online()`/`wait_online()` call, Anthropic-host preflight, and provider-specific wait/replay; retain native-Windows WSL2 refusal before process launch.
- [x] T015 [P] [US1] Resolve R-OSINFO-NOTIFY in `core/osinfo.py::notify` so Mac, Linux, and native Windows all receive one normalized/truncated `body` including optional `more`, Windows passes `q(body)` rather than raw text, and best-effort handling covers `OSError` plus `subprocess.SubprocessError`.
- [x] T016 [US1] Review three focused worktree diffs, stage only `README.md`, `core/engine.py`, and `core/osinfo.py`, verify index stages 1/2/3 are gone, and record the applied resolution hashes/statuses in `specs/004-safe-upstream-merge/evidence/integration-ledger.md` without using `git add -A`.

### Semantic Review of the Eleven Auto-Merged Overlaps

- [x] T017 [US1] Compare local, upstream, and candidate changes for `SETUP.md`; reconcile native/WSL setup and desk command claims or link exact follow-up resolution tasks, then record symbols/claims, invariant IDs, evidence IDs, outcome, and rationale in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T018 [US1] Compare local, upstream, and candidate changes for `core/guard/staff-guard/hooks/register.js`; verify containment/guard behavior and upstream 1.6.1 changes coexist without duplicate or weakened branches, then record the terminal review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T019 [US1] Compare local, upstream, and candidate changes for `core/onboard.py`; preserve shared launch policy and identify every ordinary-work subscription/provider claim for R-PROVIDER-COPY, then record the review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T020 [US1] Compare local, upstream, and candidate changes for `core/orders.py`; verify a local hire is always created and Cloud Shift auto-enables only after fresh qualifying account evidence, then record the review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T021 [US1] Compare local, upstream, and candidate changes for `core/panel.py`; preserve installation-only Claude availability and separate Cloud Shift eligibility while mapping employee session and `/api/seen` gaps to R-INTERACTIVE-PLATFORM/R-UNREAD-SCOPE, then record the review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T022 [US1] Compare local, upstream, and candidate changes for `core/panel/app.js`; map employee session opening, filtered seen behavior, brain/hands, and subscription copy to their resolution records and record the semantic review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T023 [US1] Compare local, upstream, and candidate changes for `core/staffd.py`; preserve provider-neutral routine scheduling, Claude-app-owned routine skipping, actual-transient rearming, and map refresh/session launch to the shared mode gate, then record the review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T024 [US1] Compare local, upstream, and candidate changes for `core/team.py`; preserve main-conversation delivery and transient retry while mapping global/filtered seen behavior to R-UNREAD-SCOPE, then record the review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T025 [US1] Compare local, upstream, and candidate changes for `orbit`; preserve installation-only readiness and platform commands while mapping `inbox`, `chat`, and `open` to scoped-seen/mode/argv remediation, then record the review in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T026 [US1] Compare local, upstream, and candidate changes for `tests/test_core.py`; identify obsolete `engine.online`, pre-brain Sonnet, pre-ORIENT prompt, and early `unittest.main()` assumptions without restoring production regressions, then record R-TEST-EVIDENCE follow-ups in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T027 [US1] Compare local, upstream, and candidate changes for `tests/test_platforms.py`; identify the MXC exec `command`+`args` expectation, mode/entry-point gaps, and native notification/terminal/desk coverage, then record R-TEST-EVIDENCE follow-ups in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.

### Complete Content Accounting

- [x] T028 [US1] Review every non-overlap entry in the 92-path union by risk tier, confirm expected local-only/upstream-only retention and deletions/additions, and assign a justified outcome plus evidence mapping in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`; stop for owner approval rather than creating `approved_exclusion` implicitly.
- [x] T029 [US1] Verify `VERSION` is exactly `0.12.0`, upstream additions including `core/claudeapp.py`, `core/desk.py`, `core/desk.md`, and `core/jobs/claude_app.md` exist, and local `core/mxc.py`, Windows setup assets, and all `specs/001-*`, `specs/002-*`, and `specs/003-*` artifacts remain; record the artifact comparison in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T030 [US1] Remove the staged extra blank line at EOF from `core/claudeapp.py` and confirm the focused staged diff no longer fails `git diff --cached --check` for that path.
- [x] T031 [US1] Review `.specify/feature.json` and every file under `specs/004-safe-upstream-merge/` (including this `tasks.md` and `evidence/`) as deliberate candidate additions, register them separately from the 92 historical input paths in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`, and leave final staging to T082.
- [x] T032 [US1] Run the US1 independent content check and record it in `specs/004-safe-upstream-merge/evidence/validation-results.md`: zero `UU`, zero accidental markers in candidate files, parseable `core/engine.py`/`core/osinfo.py`, exact 0.12.0 version, complete union accounting, fourteen overlap reviews, zero unapproved exclusion, and explicit US2 links for every not-yet-verified high-risk behavior.

**Checkpoint**: The merge is textually resolved and completely content-accounted. It is not yet a validated safety-compatible candidate and MUST NOT be committed or published.

---

## Phase 4: User Story 2 — Preserve Safety and Connection Invariants While Adding Upstream Features (Priority: P1)

**Goal**: Make local provider/platform/containment boundaries and upstream conversation, brain/hands, unread, notification, terminal/app-chat, and desk behavior coexist in one candidate.

**Independent Test**: Run focused matrices proving ordinary/legacy × interactive/unattended launch policy, no provider preflight, main-session lifecycle, effective Claude data root, all employee MXC/WSL2 gates, platform argv/notification/desk behavior, scoped unread cursors, Cloud Shift separation, provider-neutral copy, and upstream brain/hands/desk/report flows.

### Tests for User Story 2 (Write Before Implementation)

- [x] T033 [P] [US2] Add failing command/run contract cases to `tests/test_core.py` for ordinary `user,project` versus legacy `project`, headless `dontAsk` versus interactive `default`, autonomy `bypassPermissions`, identical guard/MCP/MXC boundaries, absent `engine.online`/Anthropic socket preflight, actual-result transient handling, main-session resume/new/ORIENT/fork/persistence, and busy-marker cleanup.
- [x] T034 [US2] Add failing default/custom/application-owned `CLAUDE_CONFIG_DIR` cases to `tests/test_core.py` proving transcript lookup, context rollover, `window_open`, `window_idle`, and session continuity use the exact effective child data root without persisting or logging it.
- [x] T035 [US2] Add failing two-employee, same-timestamp, old-global-state, CLI/panel filtered-view tests to `tests/test_core.py` for scoped unread cursors, plus focused brain/hands aliases, local-hire-with-ineligible-Cloud-Shift, report delivery, employee chat, and owner desk behavior.
- [x] T036 [P] [US2] Add failing native `mxc`/`wsl2` entry-point cases to `tests/test_platforms.py` covering `engine.run`, terminal chat, `orbit open`, panel session opening, employee Claude-app opening, and `staffd.refresh_sessions`; require WSL2-mode refusal on every native employee path and shared MXC controls for terminal work.
- [x] T037 [US2] Add failing Mac/Linux/native-Windows notification body, argv-based terminal launch/copy fallback, native employee Desktop refusal, and least-privilege Windows front-desk permission/path cases to `tests/test_platforms.py`.
- [x] T038 [US2] Extend `tests/test_core.py::StaticContracts` and relevant `tests/test_platforms.py` documentation checks so ordinary work must say configured Claude connection, usage language is conditional on Claude reporting it, `auth == "subscription"` is not rendered as proof of subscription, legacy API-key and Cloud Shift wording stay at their real boundaries, and brain/hands remains model-role rather than provider routing.
- [x] T039 [US2] Reconcile auto-merged expectations in `tests/test_core.py`: remove all reads/patches of `engine.online`, update only applicable default-chat expectations to brain/Opus, expect `ORIENT` only for a new main conversation, retain original pass-through/no-fallback assertions, and move `unittest.main()` after the final test class.
- [x] T040 [US2] Correct `tests/test_platforms.py::NativeWindows` containment-hook assertions to inspect the exec-form hook `command` plus `args` for `mxc.py --hook` without weakening the production hook shape.

### Implementation for User Story 2

- [x] T041 [US2] Implement one effective Claude data-root helper in `core/engine.py` and route `transcripts`, `context_tokens`, `window_open`, and `window_idle` through the exact launch-policy environment; preserve inherited `CLAUDE_CONFIG_DIR`, use the default only when absent, and never persist/log the resolved path or secret environment values.
- [x] T042 [US2] Implement one reusable employee-launch platform/mode guard in `core/engine.py` that applies on native Windows before any process/app/session setup, allows contained MXC terminal/headless work, refuses native-side employee work when recorded mode is WSL2, and refuses native employee Desktop sessions pending feature 003 without changing Mac/Linux/actual-WSL behavior.
- [x] T043 [US2] Route `core/engine.py::command`, `chat_window`, and `claude_session` through the shared launch policy and mode guard so interactive/headless differences change only interaction flags while setting sources, environment, platform tools, guard, MCP, deny rules, and MXC hook remain equivalent.
- [x] T044 [US2] Finalize `core/engine.py::run` against the new tests: keep process-result connection truth and the all-entry mode guard while preserving main-session resume/new fallback, ORIENT, model-by-job, context rollover, owner-window fork, session persistence, cross-process busy coordination, and unconditional marker cleanup with no provider-specific wait/replay.
- [x] T045 [P] [US2] Implement lazy scoped cursors in `core/team.py`: normalized `owner_key`; `scope` exactly `global|employee`; `employee_id` required only for employee scope and valid for current/historical employees; monotonic `seen_timestamp`; same-timestamp IDs belonging to that scope; unread uses the newer global/matching employee cursor; filtered marking advances only one employee; old global-only state remains valid without eager migration.
- [x] T046 [P] [US2] Change `core/osinfo.py::open_terminal` to accept an argv boundary and own per-platform launch/display quoting; add native Windows new-console launch using the current Python executable plus Orbit script without `cmd.exe`/PowerShell reparsing, retain Mac/WSL/Linux behavior, and keep R-OSINFO-NOTIFY's computed-body/error semantics.
- [x] T047 [US2] Update `orbit` so `inbox <handle>` and pre-chat display mark only that employee, unfiltered inbox marks globally, `chat` and `open` enforce the shared employee mode guard, and terminal launch/copy output passes argv to `core/osinfo.py` rather than constructing POSIX shell text.
- [x] T048 [US2] Update `core/panel.py` so employee session opening enforces the shared mode/Desktop decision, passes argv to `osinfo.open_terminal`, `/api/seen` accepts an optional validated employee ID, filtered calls advance only that cursor, and full-room calls retain global marking.
- [x] T049 [US2] Update `core/panel/app.js` so the employee Chat tab sends its employee ID to `/api/seen`, Today/full-room views omit it, the client does not zero unrelated unread counts after a scoped mark, and employee session errors accurately describe WSL2/native-Desktop gating.
- [x] T050 [US2] Gate `core/staffd.py::refresh_sessions` through the same employee launch decision before plugin/session work while preserving provider-neutral scheduling, Claude-app-owned routine skipping, actual-transient rearming, and service behavior on Mac/Linux/WSL.
- [x] T051 [US2] Enforce platform-appropriate employee app behavior in `core/claudeapp.py`: retain upstream plan/state/link generation on non-native-Windows platforms, actual Claude app opening where currently supported on Mac, and existing contained terminal fallback on Linux/WSL; refuse native-Windows employee Desktop opening until feature 003 is implemented and do not convert that refusal into an uncontained fallback.
- [x] T052 [US2] Implement platform-specific least-privilege owner front-desk settings in `core/desk.py`: preserve POSIX `Bash(...)` rules where applicable, use exact PowerShell/Windows executable and normalized path rules on native Windows, allow only required Orbit control-plane commands, and provide no route around employee mode gates.
- [x] T053 [US2] Reconcile brain/hands and additive compatibility across `core/engine.py`, `core/hire.py`, `core/panel.py`, and `core/panel/app.js`: chats/thinking use brain default `opus`, production/scanning uses hands default `sonnet`, high reported usage may choose existing `haiku`, aliases pass to Claude without provider probing/routing, absent `brain` keeps defaults, and `brain_v1`/main-session migration remains additive.
- [x] T054 [US2] Review and, only where tests expose drift, correct scheduler/account composition in `core/staffd.py`, `core/team.py`, `core/orders.py`, and `core/panel.py`: no provider reachability gate, app-owned routines not double-run, actual transient failure re-arms later, local hire always succeeds, Cloud Shift auto-enables only from fresh qualifying evidence, and general availability remains installation-only; record the outcome in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`.
- [x] T055 [US2] Apply R-PROVIDER-COPY in `core/onboard.py`, `core/panel/app.js`, `README.md`, `SETUP.md`, and `PRODUCT.md`: ordinary work says “Claude's configured connection,” usage/limits are qualified “when Claude reports” them, brain/hands stays provider-neutral, only the legacy path names an Anthropic API key, and only Cloud Shift requires qualifying account language; do not rename persisted `auth == "subscription"` compatibility data.
- [x] T056 [US2] Verify and repair Cloud Shift separation in `core/orders.py`, `core/hire.py`, `core/panel.py`, and `core/panel/app.js` so ineligibility never blocks local hire/chat/routine/desk work and account-only guidance appears only on Cloud Shift controls.
- [x] T057 [US2] Run all focused US2 selectors from `tests/test_core.py` and `tests/test_platforms.py` in separate Python processes, require every newly added case to pass, and record candidate tree, platform, exact selectors, failures/skips, and artifacts under I2/I4 in `specs/004-safe-upstream-merge/evidence/validation-results.md`.
- [x] T058 [US2] Update every R-* record and affected BI-* entry in `specs/004-safe-upstream-merge/evidence/integration-ledger.md` to `verified` only when its focused diff and evidence pass; leave any failure `blocked` and stop rather than granting an implicit exception.

**Checkpoint**: Local safety/connection invariants and upstream 0.9–0.12 behavior coexist and have focused candidate-bound evidence. Full-suite, documentation, cleanup, and platform readiness remain US3.

---

## Phase 5: User Story 3 — Validate One Coherent Release Candidate (Priority: P2)

**Goal**: Determine the candidate's exact local, cross-platform, documentation, cleanup, guard, and feature-003 release status without weakening checks or treating unavailable evidence as passing.

**Independent Test**: I0–I5 and D1 pass against one staged tree; G1/X1 are either candidate-bound passes or explicit pending evidence; REL1 is explicitly blocked while feature 003 remains unimplemented; every failure/skip is exact and no live owner data or sensitive recorder remains.

### Validation Infrastructure and Documentation

- [x] T059 [US3] Complete R-CLEANUP in `tests/_cleanup.py`, `tests/fake_claude.py`, `tests/test_core.py`, `tests/test_platforms.py`, and `tests/test_mxc.py`: register the `orbit-mxc-test-*` root and every `fake-claude-*` recorder under shared cleanup, keep recorders inside registered roots, remove disposable transcript slugs/listener/service children, and ensure full inherited environment recordings cannot survive process exit.
- [x] T060 [P] [US3] Add a repository-owned `claude plugin test` invocation for `core/guard/staff-guard/tests/guard.test.ts` to `.github/workflows/tests.yml` after Claude Code installation, requiring all ten tests without account sign-in/network inference and preserving existing macOS/Linux/native-Windows/WSL2 jobs.
- [x] T061 [US3] Perform the source-backed D1 correction pass in `README.md`, `SETUP.md`, `PRODUCT.md`, `.github/workflows/tests.yml`, and `VERSION`: current product is 0.12.0, native/WSL commands match source, cost/account/desk/conversation claims are non-contradictory, and feature-003 real-host evidence is not described as optional/non-gating or already implemented.

### Structural and Contract Gates

- [x] T062 [US3] Run I3 against the intended candidate paths and record it in `specs/004-safe-upstream-merge/evidence/validation-results.md`: zero unresolved index entries; zero accidental markers outside named fixtures; clean worktree/staged diff checks; parse/compile `orbit` and changed Python; `node --check` both JavaScript files; parse JSON/structured assets; no unintended duplicate active definitions; exact `VERSION=0.12.0`; expected local/upstream artifacts present.
- [x] T063 [US3] Run the currently implemented feature-001 commands in `specs/001-windows-mxc-sandbox/verify_gates.py` (`planning`, phase checks, `ci`, and `full` as supported), bind outputs to the candidate tree, and record exact pass/fail/pending results under I4/X1 in `specs/004-safe-upstream-merge/evidence/validation-results.md` without using historical evidence as a candidate pass.
- [x] T064 [US3] Run the feature-002 focused scenarios and tracked-file scans from `specs/002-claude-connection-pass-through/quickstart.md`, including absence of ordinary `api.anthropic.com` preflight and generic account-login claims, then record exact candidate-bound results under I4/D1 in `specs/004-safe-upstream-merge/evidence/validation-results.md`.
- [x] T065 [US3] Run the complete focused overlap/invariant selector set in `tests/test_core.py`, `tests/test_platforms.py`, and `tests/test_mxc.py`; require 100% coverage of every manually resolved runtime overlap and BI-CONNECTION, BI-SETTING-SOURCES, BI-WINDOWS-MXC, BI-WSL2-MODE, BI-CLOUD-SHIFT, BI-CONVERSATION, BI-CONFIG-ROOT, BI-ENTRY-MODE, BI-TERMINAL, BI-REPORT-DESK, BI-UNREAD-SCOPE, BI-NOTIFICATION, BI-PROVIDER-COPY, BI-TEST-CLEANUP, BI-DATA, and BI-PLANNING-STATUS in `specs/004-safe-upstream-merge/evidence/validation-results.md`.

### Full Locally Available Suite (Separate Processes)

- [x] T066 [US3] Run `python -m unittest tests.test_core` with `PYTHONUTF8=1`, `STAFF_TEST_OCR=0`, and `PYTHONDONTWRITEBYTECODE=1`; record exact count, failures, skips/reasons, tree ID, and artifact digest under I5 in `specs/004-safe-upstream-merge/evidence/validation-results.md`, treating every expected host check failure as `fail` rather than baseline success.
- [x] T067 [US3] Run `python -m unittest tests.test_channels` in a fresh process with the same isolated environment and record exact count/failures/skips/tree/artifact under I5 in `specs/004-safe-upstream-merge/evidence/validation-results.md`.
- [x] T068 [US3] Run `python -m unittest tests.test_tools` in a fresh process, preserve exact dependency/offline/OCR skip reasons, and record count/failures/skips/tree/artifact under I5 in `specs/004-safe-upstream-merge/evidence/validation-results.md` without converting unavailable live/OCR checks into passes.
- [x] T069 [US3] Run `python -m unittest tests.test_calls` in a fresh process and record exact count/failures/skips/tree/artifact plus listener/audio cleanup under I5 in `specs/004-safe-upstream-merge/evidence/validation-results.md`.
- [x] T070 [US3] Run `python -m unittest tests.test_platforms` in a fresh process and record exact count/failures/skips/tree/artifact under I5/X1 in `specs/004-safe-upstream-merge/evidence/validation-results.md`; unsupported POSIX/WSL/macOS cases stay pending, and near-midnight skips must be rerun.
- [x] T071 [US3] Run `python -m unittest tests.test_mxc` in a fresh process and record exact count/failures/skips/tree/artifact under I5/REL1 in `specs/004-safe-upstream-merge/evidence/validation-results.md`, explicitly stating that fake-executor success is not real-host containment evidence.
- [x] T072 [US3] After every module completes, prove no registered module root, `fake-claude-*`, `orbit-mxc-test-*`, disposable `.claude/projects` slug, full-environment recorder, listener/service child, tracked-file change, or live owner `Staff`/credential change remains; record BI-TEST-CLEANUP/BI-DATA evidence in `specs/004-safe-upstream-merge/evidence/validation-results.md`.

### Guard, Smoke, Platform, and Readiness Evidence

- [x] T073 [US3] Run `claude plugin test` from `core/guard/staff-guard` when the supported CLI is available, require all ten cases including commit-message-as-data behavior, and record G1 as `pass` with tree/artifact or `pending` with exact missing prerequisite in `specs/004-safe-upstream-merge/evidence/validation-results.md`—never infer a pass.
- [x] T074 [US3] Execute representative setup/status, ordinary crew work, main conversation, report delivery/unread, and owner desk smoke flows only in a disposable profile/environment, and record each exact `pass|fail|pending|not_applicable` result plus cleanup in `specs/004-safe-upstream-merge/evidence/validation-results.md`.
- [x] T075 [US3] Compare the exact candidate requirements with every macOS, Ubuntu 24.04, native-Windows unit, and WSL2 job in `.github/workflows/tests.yml`; record unavailable candidate-bound jobs as X1 `pending` in `specs/004-safe-upstream-merge/evidence/validation-results.md` and do not publish a validation branch without the US4 owner decision.
- [x] T076 [US3] Instantiate the Release Compatibility Record in `specs/004-safe-upstream-merge/evidence/validation-results.md`: one record per candidate tree; `feature_003_status` exactly `blocked|pending_evidence|ready` and currently `blocked`; non-empty known blockers; explicit version-line, connection-policy, and Desktop-session conflicts; feature-004 compatibility choices matching R16; and REL1 evidence links, with `ready` forbidden until all applicable evidence passes.
- [x] T077 [US3] Complete D1 by cross-checking every command, prerequisite, connection/account/cost claim, brain/hands/conversation/report/notification/desk claim, platform statement, version, and release-gate statement in `README.md`, `SETUP.md`, `PRODUCT.md`, and `.github/workflows/tests.yml` against source; record zero contradictions or leave D1 `fail` in `specs/004-safe-upstream-merge/evidence/validation-results.md`.
- [x] T078 [US3] Finalize I1 in `specs/004-safe-upstream-merge/evidence/integration-ledger.md`: every regenerated changed path appears exactly once, every entry has a terminal outcome, every high-risk path links passing focused evidence, all fourteen overlap reviews are terminal, and no exclusion lacks explicit owner approval.
- [x] T079 [US3] Record the Integration Candidate's `validated_local` decision in `specs/004-safe-upstream-merge/evidence/validation-results.md` only if I0–I5 and D1 pass: unique candidate ID; verified local/upstream baselines; full tree ID mandatory from `resolved`; revision left empty until local recording; version exactly `0.12.0`; non-negative `unresolved_count=0` and `coverage_pending=0`; independent integration/release states; and evidence links satisfying the gate; otherwise set state `blocked` and stop before US4.

**Checkpoint**: One exact tree is locally validated or explicitly blocked. G1/X1 may remain pending; REL1 remains blocked. No unavailable evidence is presented as passing.

---

## Phase 6: User Story 4 — Recover and Publish Deliberately (Priority: P2)

**Goal**: Preserve recovery, record a genuine two-parent merge, remove temporary history metadata without changing content, and present publication choices while defaulting to no remote mutation.

**Independent Test**: Restore/inspect the baseline in a disposable location within five minutes, prove the local integration revision has parents `366cf73` and `256ed16`, prove its tree survives replacement removal unchanged, prove both inputs are ancestors and recovery remains available, and show that `origin/main` was not written.

### Recovery, Recording, and Cleanup

- [x] T080 [US4] Rehearse recovery without touching the active candidate by checking out `backup-before-sync` in a disposable detached worktree/archive, verify its full revision/tree against `366cf73`, remove only the disposable location, time the operation under five minutes, and record the result in `specs/004-safe-upstream-merge/evidence/history-proof.md`.
- [x] T081 [US4] Refresh the read-only observed remote revision/tree and stale-merge parent/tree comparison, update `specs/004-safe-upstream-merge/evidence/publication-options.md`, and keep the selected posture `hold_local`; if the remote differs from the reviewed `da644db` condition, mark the publication analysis stale and do not write remotely.
- [x] T082 [US4] Stage only the reviewed allowlist from `specs/004-safe-upstream-merge/evidence/integration-ledger.md`, including `.specify/feature.json` and `specs/004-safe-upstream-merge/`; inspect every remaining unstaged/untracked path and use explicit `git add -- <paths>` rather than `git add -A` or broad recursive staging.
- [x] T083 [US4] Run final staged I0–I5/D1 checks, require zero failure and zero unresolved path, write the staged tree, bind every passing evidence record to that exact tree, update/stage `specs/004-safe-upstream-merge/evidence/validation-results.md` and `specs/004-safe-upstream-merge/evidence/history-proof.md`, and stop if any evidence became stale after a content change.
- [x] T084 [US4] Record the genuine integration merge using the existing `.git/MERGE_HEAD` with first parent `366cf73`, second parent `256ed16`, the validated staged tree, and a message naming upstream v0.12.0 plus semantic base `500d772`; do not squash, add `da644db` as a parent, or create an ancestry-only merge.
- [x] T085 [US4] With replacement processing disabled, inspect the new merge's full revision, tree, and exactly two parents and write the result to `%TEMP%\orbit-upstream-merge-final-evidence.md`; require its tree to equal the pre-commit staged tree before touching `.git/refs/replace/93773e055f31ce25bedc30cdc1fe3f73c541a0c7`.
- [x] T086 [US4] Remove only the temporary replacement for `93773e055f31ce25bedc30cdc1fe3f73c541a0c7`, verify `git replace -l` is empty, and append to `%TEMP%\orbit-upstream-merge-final-evidence.md` that the merge tree/parents are unchanged, both authoritative inputs are ancestors, and `backup-before-sync` still resolves to `366cf73`; never delete the recovery ref.
- [x] T087 [US4] Validate a replacement-free checkout/worktree with structural checks and the focused smoke selectors, append exact H1 results/tree/artifacts to `%TEMP%\orbit-upstream-merge-final-evidence.md`, and keep G1/X1/REL1 statuses separate from local recording.
- [x] T088 [US4] Reconfirm the timed recovery route and absence of any remote write after replacement cleanup, then append recovery status and `origin/main` observation to `%TEMP%\orbit-upstream-merge-final-evidence.md`.
- [x] T089 [US4] Generate `%TEMP%\orbit-upstream-merge-publication-handoff.md` with a valid Publication Decision record: candidate revision resolves and matches its tree; freshly observed remote revision; exactly one option from `hold_local|publish_validation_branch|append_corrective_history|replace_remote_with_lease`; collaborator/history consequences; explicit approval required except for `hold_local`; status from `pending|approved|executed|stale|failed`; and result revision only after successful execution; select `hold_local/pending` and ask the owner before any remote action.

**Checkpoint**: The corrected merge exists locally, no replacement metadata remains, recovery is intact, and publication is pending at `hold_local`. A future approved publication operation is a separate gated action, not an automatic task here.

---

## Phase 7: Polish & Cross-Cutting Completion

**Purpose**: Ensure the recorded result and handoff use precise readiness language and leave no task-generation or test residue.

- [x] T090 Verify the committed tree contains no temporary `.specify/scripts/bash/setup-tasks.sh`, `.specify/scripts/bash/common.sh`, or `.specify/templates/tasks-template.md`, no test/temp recorder residue, no unreviewed tracked/untracked candidate file, and no post-commit source edit; append the clean-state result to `%TEMP%\orbit-upstream-merge-final-evidence.md`.
- [x] T091 Produce the final owner report from `%TEMP%\orbit-upstream-merge-final-evidence.md` and `%TEMP%\orbit-upstream-merge-publication-handoff.md`, naming candidate revision/tree/parents, ledger totals/exclusions, all R-* outcomes, I0–I5/G1/D1/H1/X1/REL1/PUB1 statuses, exact pending/blocked evidence, replacement/recovery state, and whether any remote changed; use “locally recorded,” “cross-platform validated,” “release ready,” and “published” only when their contract predicates pass.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 Setup
  -> Phase 2 Foundational inventory
  -> US1 content integration
  -> US2 safety/feature compatibility
  -> US3 validation/readiness
  -> US4 recovery/history/publication handoff
  -> Phase 7 final report
```

- **Setup (Phase 1)**: Starts immediately; read-only Git inspection plus new evidence files.
- **Foundational (Phase 2)**: Depends on T001–T004 and blocks source edits.
- **US1 (Phase 3)**: Depends on the complete inventory/resolution map; owns textual merge resolution and content accounting.
- **US2 (Phase 4)**: Depends on US1's marker-free candidate; tests precede compatibility implementation.
- **US3 (Phase 5)**: Depends on all US2 focused tests passing; no history recording while I0–I5 or D1 fails.
- **US4 (Phase 6)**: Depends on T079 reaching `validated_local`; T084 is the only integration commit task.
- **Polish (Phase 7)**: Read-only verification/reporting after replacement cleanup.

### User Story Dependencies

- **US1 (P1)**: No prior story dependency, but requires Setup + Foundational. Independently proves two-sided content accounting and textual integration.
- **US2 (P1)**: Depends on US1 because it refines the single resolved `core/engine.py` and other shared candidate paths. Independently proves behavioral compatibility.
- **US3 (P2)**: Depends on US2 because evidence must bind to final behavior. Independently reports local/cross-platform/release readiness without conflation.
- **US4 (P2)**: Depends on US3 local validation. Independently proves recovery, two-parent history, tree stability, and no unauthorized publication.

### Critical File Serialization

- `core/engine.py`: T013 -> T014 -> T041 -> T042 -> T043 -> T044 -> focused tests.
- `tests/test_core.py`: T026 -> T033 -> T034 -> T035 -> T038 -> T039 -> T059 -> suite.
- `tests/test_platforms.py`: T027 -> T036 -> T037 -> T038 -> T040 -> T059 -> suite.
- `core/panel/app.js`: T022 -> T049 -> T053 -> T055 -> structural/docs gates.
- Evidence ledger: T001/T004 -> T005–T010 -> story reviews -> T058 -> T078 -> final stage.
- Git index/history: T016 may resolve exact UU files; all broad candidate staging waits for T082; T084–T088 are strictly serial.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001 creates the evidence directory.
- T012 and T015 can run in parallel because they resolve different conflicted files; `core/engine.py` remains serialized.
- T033 and T036 can run in parallel because they write `tests/test_core.py` and `tests/test_platforms.py` respectively.
- T045 and T046 can run in parallel after the shared engine contracts are fixed because they write `core/team.py` and `core/osinfo.py`.
- T060 can run in parallel with T059 because it writes only `.github/workflows/tests.yml` while cleanup work stays under `tests/`.
- No Git staging, commit, replacement cleanup, or remote/publication task is parallelizable.

---

## Parallel Examples

### User Story 1

```text
Task T012: Resolve README cost/account conflict in README.md.
Task T015: Resolve notification conflict in core/osinfo.py.
```

### User Story 2

```text
Task T033: Add launch/session compatibility tests in tests/test_core.py.
Task T036: Add native entry-point mode tests in tests/test_platforms.py.

After T041–T044:
Task T045: Implement scoped unread cursors in core/team.py.
Task T046: Implement platform-owned terminal argv in core/osinfo.py.
```

### User Story 3

```text
Task T059: Close test cleanup gaps under tests/.
Task T060: Add the guard plugin CI invocation in .github/workflows/tests.yml.
```

---

## Implementation Strategy

### MVP: User Story 1 Content Checkpoint

1. Complete Setup and Foundational phases.
2. Resolve the three explicit conflict files semantically.
3. Review all fourteen overlaps and account for the 92-path union.
4. Reach the US1 checkpoint: marker-free, parseable, version 0.12.0, no unapproved content omission.
5. Stop and review. This MVP is a content checkpoint only; it is not safe to commit or publish until US2 and US3 pass.

### Incremental Delivery

1. **US1** -> complete, reviewable content integration.
2. **US2** -> safety-compatible local/upstream behavior with focused tests.
3. **US3** -> exact local validation plus honest pending/blocked platform/release evidence.
4. **US4** -> genuine local merge, replacement cleanup, recovery proof, `hold_local` publication handoff.

### Execution Discipline

- Tests added in US2 must fail for the intended missing behavior before implementation and pass afterward.
- Run Python modules separately; `unittest discover -s tests` is diagnostic only and cannot replace T066–T071.
- Any candidate content change invalidates affected I2–I5/D1 evidence and requires rerunning it before T083.
- A failed mandatory check blocks progress unless the owner explicitly accepts a documented exception with user/safety impact; an exception cannot convert failed security evidence into `pass`.
- Skipped, unavailable, cancelled, timed-out, or uncollected checks remain `pending` or `fail` according to the validation contract.
- Feature 003 remains out of implementation scope and REL1 remains `blocked`; preserving its files is not release evidence.
- Remote publication remains outside automatic execution. After T089, wait for an explicit owner choice and generate a separate approved operation plan.

## Notes

- `[P]` means different files and no incomplete dependency; it is not permission to parallelize shared Git state.
- Every evidence result binds to the exact candidate tree and platform and excludes secrets, owner messages, and unrestricted policy contents.
- Do not use historical feature-001/002 outputs as passes for the merged tree.
- Do not restore `engine.online`/`wait_online`, strip `CLAUDE_CONFIG_DIR`, broaden PowerShell permissions, or allow native employee Desktop sessions to make tests pass.
- Do not delete `backup-before-sync` during this task list.

---

## Phase 8: Convergence

- [x] T092 Execute the five representative smoke flows (setup/status, ordinary crew work, a main conversation, report delivery/unread, and owner desk) in a disposable profile/environment against candidate tree `8448419bfc0790ed74379145222ff2aa51850c1a`, and record each exact `pass|fail|pending|not_applicable` result plus cleanup proof in `specs/004-safe-upstream-merge/evidence/validation-results.md` per SC-006 and task T074 (partial)
