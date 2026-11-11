# Implementation Plan: Safe Upstream Synchronization

**Branch**: `004-safe-upstream-merge` (Spec Kit feature identifier; active Git branch is `main`) | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-safe-upstream-merge/spec.md`

**Status**: Plan complete; implementation remains the active local merge

## Setup Note

This checkout contains `.specify/feature.json` but does not keep `.specify/scripts/`, a plan template, or `.specify/memory/constitution.md`. To execute the prescribed setup step, the current official Spec Kit `setup-plan.sh`, `common.sh`, and `plan-template.md` were placed temporarily under `.specify/`, run through the installed Git Bash, and then removed. Setup resolved:

- `FEATURE_SPEC`: `specs/004-safe-upstream-merge/spec.md`
- `IMPL_PLAN`: `specs/004-safe-upstream-merge/plan.md`
- `FEATURE_DIR`: `specs/004-safe-upstream-merge`
- `BRANCH`: `004-safe-upstream-merge`

No branch hook was installed, so planning remains on the already-active `main` merge. No extension hooks are registered.

## Summary

Complete the already-started semantic integration of local baseline `366cf73` with canonical upstream `256ed16` (`v0.12.0`) by using the verified 0.8.0 product relationship to avoid false conflicts, resolving the remaining overlaps as behavior-preserving unions, auditing every automatically combined high-risk path, and producing change-coverage and validation evidence before recording the integrated tree.

The design preserves the local native-Windows/MXC, WSL2 fallback, provider-neutral Claude connection pass-through, Cloud Shift account boundary, and feature 001–003 artifacts while retaining upstream's 0.9.0–0.12.0 brain/hands, one-conversation, notification, unread-state, terminal/app-chat, and front-desk behavior. It introduces no destructive team-data migration; the only additive runtime state is an optional employee-scoped unread cursor in the existing team-state file. Remote publication is deliberately separate from local content integration because `origin/main` already contains an ancestry-only merge with stale content.

## Technical Context

| Dimension | Decision | Notes |
| --- | --- | --- |
| Language/Version | Python 3.9-compatible core and CLI; plain browser JavaScript; existing JavaScript/TypeScript guard assets; POSIX shell and PowerShell setup paths | No language or runtime upgrade is part of synchronization |
| Primary Dependencies | Existing Orbit dependencies and installed Git; no new product dependency | Source-history reconciliation is a maintainer operation, not a runtime capability |
| Storage | Repository objects, refs, index, source files, planning/evidence Markdown, and optional scoped-cursor keys in the existing team state | No new runtime file or destructive/eager owner-data migration |
| Testing | Six Python `unittest` modules in isolated processes, platform slices, static contracts, feature gate scripts, `claude plugin test` for the existing guard suite, and the CI matrix | Unavailable platform evidence is pending; feature-003 REL1 is currently blocked, not passing |
| Target Platform | macOS, Ubuntu Linux, Windows through WSL2, native Windows unit coverage, and the existing native Windows 11 MXC evidence environments | Current planning/implementation host is native Windows without WSL |
| Project Type | Cross-platform local CLI/script kit, background service, browser control panel, and Claude-app integration | Single repository; no service split |
| Performance Goals | No runtime performance regression attributable to conflict resolution; validation and recovery remain practical for one maintainer | Existing feature-specific performance criteria remain authoritative |
| Constraints | Active merge; fixed upstream target `v0.12.0`; no reset/discard; no owner-data use; no silent provider preflight; no uncontained Windows fallback; no remote rewrite without approval | Recovery branch and temporary history reconciliation must remain controlled |
| Scale/Scope | One integration candidate; 71 local changed paths, 35 upstream changed paths, 14 shared paths, and three currently unmerged files relative to the verified semantic base (counts regenerated during implementation) | Feature 001–003 planning artifacts are preserved, not implemented by this work |

No planning unknown remains. The feature description, handoff, repository state, and existing feature contracts determine the required behavior.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` does not exist. No formal project constitution gate applies. The following feature-level gates replace it for this integration:

| Gate | Pre-design result | Required design response |
| --- | --- | --- |
| No unapproved local or upstream content loss | Pass | Complete change-coverage ledger with explicit outcome and evidence for every touched path |
| Provider-neutral ordinary Claude work remains provider-neutral | Pass | Preserve local launch policy and omit upstream provider-specific preflight/wait logic |
| Native Windows shell work remains fail-closed | Pass | Preserve MXC hook/settings/tool surface and apply the explicit MXC/WSL2 mode gate to every employee launch surface |
| Upstream 0.9.0–0.12.0 user behavior remains present | Pass | Retain interactive command/session, brain/hands, report, notification, app chat, and desk flows |
| Effective Claude configuration remains authoritative | Pass | Resolve transcripts/sessions through the effective child data root without stripping or persisting it |
| Filtered views do not erase unrelated unread reports | Pass | Add lazy owner+employee cursors while preserving the global cursor and old state |
| Planning artifacts are not presented as implemented security controls | Pass | Keep feature-003 release readiness independent and record REL1 as blocked while implementation is absent |
| Owner team data is not a merge or test fixture | Pass | Use isolated test homes, close cleanup gaps, and retain no environment recorder residue |
| Unavailable evidence is not called passing | Pass | Validation records use distinct `pass`, `fail`, `pending`, and `not-applicable` states |
| Recovery precedes mutation and publication | Pass | Preserve `backup-before-sync`; record candidate locally before removing temporary history metadata |
| Remote history is not rewritten implicitly | Pass | Publication remains an owner-approved post-validation decision |

## Project Structure

### Documentation (this feature)

```text
specs/004-safe-upstream-merge/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── integration-ledger.md
│   ├── validation-evidence.md
│   └── publication-decision.md
└── tasks.md                    # generated later by /speckit-tasks
```

### Source and Validation Surfaces (repository root)

```text
README.md
SETUP.md
PRODUCT.md
VERSION
orbit
core/
├── engine.py                  # launch/session semantic union
├── osinfo.py                  # platform notification semantic union
├── mxc.py                     # retained native containment implementation / REL1 blockers
├── onboard.py
├── panel.py
├── staffd.py
├── team.py
├── update.py
├── claudeapp.py
├── desk.py
├── guard/staff-guard/
└── panel/app.js
tests/
├── _cleanup.py
├── fake_claude.py
├── test_core.py
├── test_channels.py
├── test_tools.py
├── test_calls.py
├── test_platforms.py
└── test_mxc.py
.github/workflows/tests.yml
specs/001-windows-mxc-sandbox/
specs/002-claude-connection-pass-through/
specs/003-close-containment-gaps/
```

**Structure Decision**: Keep the existing single-repository structure. This feature resolves and validates existing source surfaces; it adds only planning, ledger, and evidence documents under `specs/004-safe-upstream-merge/`. No new runtime module is justified.

## Integration Architecture

### Safety Envelope

The integration is bounded by five immutable references/roles:

1. **Local baseline** — `366cf73`, also retained by `backup-before-sync`.
2. **Upstream target** — `256ed16`, canonical `v0.12.0`.
3. **Corresponding product points** — local `93773e0` and upstream `500d772`, both representing the 0.8.0-era product with a small local delta.
4. **Existing fork remote** — `da644db`, whose parents record local plus upstream ancestry but whose tree equals the pre-synchronization local tree.
5. **Integration candidate** — the not-yet-committed index/worktree produced from the verified corresponding product relationship.

A temporary local history reconciliation makes the product relationship visible while the candidate is built. It is not part of published history or product content. The integrated tree is recorded before that metadata is removed, and the tree identity must remain unchanged afterward.

### Semantic Resolution Set

| Resolution ID | Surface | Local intent retained | Upstream intent retained | Required evidence |
| --- | --- | --- | --- | --- |
| R-ENGINE-COMMAND | `core/engine.py::command` | Shared `launch_policy`, platform-specific tool sets, MXC settings, ordinary/legacy setting sources | Interactive mode, permission-mode selection, omission of print/stream flags in a live chat | Command argv/source matrix for unattended, interactive, ordinary, legacy, and native Windows paths |
| R-ENGINE-RUN | `core/engine.py::run` | Claude process result is connection truth; no Anthropic-specific preflight or replay; native WSL2-mode gate | One running conversation, busy/chat coordination, forked aside, orientation on new session, model-by-job, remembered session, guaranteed busy cleanup | Session lifecycle, socket-trap, transient result, chat-window, and cleanup tests |
| R-OSINFO-NOTIFY | `core/osinfo.py::notify` | Native-Windows tray delivery | Upstream normalized/truncated body, optional location text, signed Mac notifier, Linux behavior, broad subprocess failure handling | Platform notification unit cases; Windows receives computed body rather than raw text |
| R-README-COST | `README.md` cost/account section | Limits only when Claude reports them; explicit Anthropic API-key wording; Cloud Shift remains separate and eligibility-gated | Brain/hands token explanation and current upstream usage guidance | Documentation/source cross-check with no duplicated or contradictory paragraph |

The detailed rationale and rejected alternatives are recorded in [research.md](./research.md). No whole-file side selection is allowed for these surfaces.

### Compatibility Resolutions Exposed by Auto-Merge Audit

| Resolution ID | Surfaces | Decision | Required evidence |
| --- | --- | --- | --- |
| R-INTERACTIVE-PLATFORM | `core/engine.py`, `core/osinfo.py`, `core/claudeapp.py`, `core/desk.py`, `core/panel.py`, `orbit`, `core/staffd.py` | Apply one employee MXC/WSL2 mode gate to headless, terminal, app, panel and refresh launches; native MXC terminal uses the same locks; native employee Desktop is gated pending feature 003; owner desk uses exact Windows PowerShell/path rules; terminal launch accepts argv and is platform-owned | Native `mxc`/`wsl2` matrix across every entry point; no POSIX-quoted native command; Mac/Linux/WSL regressions |
| R-CLAUDE-DATA-ROOT | `core/engine.py` transcript/window helpers | Derive transcripts and session-window discovery from the exact effective child Claude data root; preserve but never persist/log inherited `CLAUDE_CONFIG_DIR` | Default/custom-root context rollover, window-open, idle, and session continuity tests |
| R-UNREAD-SCOPE | `core/team.py`, `core/panel.py`, `core/panel/app.js`, `orbit` | Add lazy owner+employee seen cursors; full-room views advance global cursor, filtered views advance only that employee; unread uses the newer applicable cursor | Two-employee same/different-timestamp tests across CLI and panel; old global-only state compatibility |
| R-PROVIDER-COPY | `core/onboard.py`, `core/panel/app.js`, `README.md`, `SETUP.md`, `PRODUCT.md` | Ordinary work says “Claude's configured connection”; usage is conditional on Claude reporting it; brain/hands remains model-role selection; legacy key and Cloud Shift are the only provider/account-specific copy | Static tracked-file scan plus source-backed docs review |
| R-TEST-EVIDENCE | `tests/`, guard tests, `.github/workflows/tests.yml` | Remove obsolete `engine.online` fixture assumptions; update brain/orientation expectations; inspect hook command+args; add combined matrices; move script test entrypoint last; run guard through `claude plugin test`; run modules in separate processes | 280 Python tests subject to platform skips, ten guard tests, exact failure/skip manifest, no disabled assertions |
| R-CLEANUP | `tests/_cleanup.py`, `tests/test_mxc.py`, fake-Claude fixtures | Register every module/recorder root, keep recorders inside cleanup scope, remove transcript/temp/process residue, and avoid live owner data | Before/after disposable-home inventory and zero residual sensitive environment logs |
| R-RELEASE-STATUS | Feature 003 artifacts, `PRODUCT.md`, README/workflow release claims | Preserve planning, label current REL1 blocked, remove optional/non-gating release claims, and record unresolved future version/connection/Desktop design conflicts | Absent feature-003 implementation files and current P0 paths recorded; no “release ready” claim |

### Automatically Combined Surface Audit

Auto-merge success is treated only as a textual result, not semantic proof. Review proceeds in risk tiers:

1. **Launch/security/session tier** — `core/engine.py`, `core/osinfo.py`, `core/onboard.py`, `core/guard/staff-guard/`, `core/staffd.py`, `core/team.py`, `orbit`, effective Claude data-root handling, and all native mode gates.
2. **Control-plane/application tier** — `core/panel.py`, `core/panel/app.js`, `core/update.py`, `core/orders.py`, `core/hire.py`, Claude-app/desk files, unread cursors, and job prompts.
3. **Documentation/version tier** — `README.md`, `SETUP.md`, `PRODUCT.md`, `VERSION`, workflow release comments, handbook and job documentation.
4. **Evidence tier** — `tests/_cleanup.py`, all changed Python test modules, the guard TypeScript suite, workflow definitions, and retained feature 001–003 artifacts.

Every path receives a change-coverage outcome. High-risk paths additionally require a behavioral-invariant mapping and targeted evidence ID.

## Delivery Sequence

1. **Freeze and inventory the candidate**
   - Verify all baseline, target, recovery, remote, merge-head, and temporary-reconciliation identities.
   - Record the initial unresolved set and all staged/unstaged integration paths.
   - Initialize the integration ledger; no exclusions are allowed without owner approval.
2. **Resolve explicit semantic overlaps**
   - Apply R-ENGINE-COMMAND, R-ENGINE-RUN, R-OSINFO-NOTIFY, and R-README-COST.
   - Remove markers and stage each resolved file only after its focused diff matches the contract.
3. **Close auto-merge compatibility gaps**
   - Apply R-INTERACTIVE-PLATFORM and R-CLAUDE-DATA-ROOT before enabling any new employee entry point.
   - Apply R-UNREAD-SCOPE additively; old global state remains valid.
   - Apply R-PROVIDER-COPY without renaming persisted compatibility markers.
   - Apply R-TEST-EVIDENCE and R-CLEANUP before treating any test output as candidate evidence.
   - Record R-RELEASE-STATUS as blocked; feature 004 does not implement feature 003.
4. **Audit automatically combined paths**
   - Review risk tiers in order.
   - Detect duplicate definitions, stale branches, discarded local constraints, and incomplete upstream flows.
   - Add focused regression coverage only where existing evidence does not prove the union.
5. **Prove structure and change coverage**
   - Require zero unresolved index entries, accidental markers, whitespace errors, invalid source, or unintended duplicate behavior.
   - Complete both local and upstream sides of the integration ledger.
   - Verify `VERSION`, all expected upstream additions, and current-product docs including `PRODUCT.md`.
6. **Prove behavior locally**
   - Run targeted conflict/compatibility tests, local feature 001/002 checks, guard tests where Claude CLI is available, cleanup assertions, and all six Python modules in separate processes.
   - Expected host failures remain failures; unavailable platforms/guard runner remain pending.
7. **Record the candidate and remove temporary history metadata**
   - Record the integrated tree with both local and upstream ancestry.
   - Capture its tree identity, remove only the temporary reconciliation metadata, and prove content/tree identity did not change.
   - Re-run a smoke/structural check after cleanup.
8. **Obtain cross-platform evidence**
   - Use the existing macOS, Linux, native-Windows, and WSL2 matrix when an authorized validation ref is available.
   - Add the repository-owned `claude plugin test` gate after Claude Code installation.
   - Keep feature-003 REL1 blocked until implementation exists; later real-host evidence remains non-waivable.
9. **Present publication decision**
   - Default to no remote mutation.
   - Present validation-branch, non-destructive corrective-history, and explicit history-replacement choices under [the publication contract](./contracts/publication-decision.md).
   - Execute only the owner's selected option after checking the remote has not changed.

## Requirement Coverage

| Requirements | Design owner / evidence |
| --- | --- |
| FR-001–007 | Baseline references plus complete integration ledger; fixed `v0.12.0` version check |
| FR-008–015 | Behavioral-invariant catalog; explicit + compatibility resolution sets; all-entry mode gate; effective Claude root; scoped unread; feature 001–003 references |
| FR-016–021 | Explicit resolution records, high-risk auto-merge audit, structural/static checks, documentation review |
| FR-022–028 | Validation-evidence contract; targeted/full suite ladder; distinct pending and release-gate states |
| FR-029–035 | Recovery-point record, candidate tree proof, temporary-metadata cleanup proof, and owner-gated publication contract |

## Success-Criteria Coverage

| Criterion | Planned proof |
| --- | --- |
| SC-001–002 | Two-sided change ledger reaches 100% terminal outcomes with zero unapproved exclusions |
| SC-003 | Index/marker/parse/duplicate-definition structural gates |
| SC-004–005 | Six isolated Python modules, guard CLI suite, and targeted overlap/invariant matrices |
| SC-006 | Version and representative setup/status, work, conversation, report, and desk smoke flows in isolated data |
| SC-007 | Documentation guard against README/SETUP/PRODUCT/workflow source, command, account, platform, release-gate, and version behavior |
| SC-008 | Isolated test-home inventory before/after; no live owner-data touch |
| SC-009 | Every resolution and pending platform check has a requirement/evidence link |
| SC-010 | Timed recovery-point identification and restore rehearsal without changing the active candidate |
| SC-011 | Independent tree/ancestry/content review after temporary metadata removal |
| SC-012 | Publication record remains `pending` until explicit owner approval; remote audit proves no earlier mutation |

## Phase 0: Research

[research.md](./research.md) resolves:

- the correct product baseline despite rewritten/replayed history;
- semantic-union rules for explicit and automatic merges;
- interaction between local connection pass-through and upstream session/connectivity behavior;
- one mode gate for all headless, terminal, app, panel, and refresh employee entry points;
- effective Claude data-root handling for transcripts/window continuity;
- native-Windows argv/terminal/front-desk compatibility and employee Desktop gating;
- scoped unread state, provider-neutral copy, and additive brain/session compatibility;
- test expectation reconciliation, guard runner, and cleanup closure;
- integration-completion versus feature-003 release-readiness evidence;
- candidate commit and temporary-history cleanup ordering;
- safe options for a remote branch that already contains a stale ancestry-only merge.

No clarification remains unresolved before Phase 1.

## Phase 1: Design and Contracts

- [data-model.md](./data-model.md) — baseline references, ledger entries, resolution decisions, invariants, additive scoped unread cursor, release compatibility, candidate state, validation evidence, recovery point, and publication decision.
- [contracts/integration-ledger.md](./contracts/integration-ledger.md) — two-sided change accounting and semantic-resolution completion rules.
- [contracts/validation-evidence.md](./contracts/validation-evidence.md) — structural, behavioral, platform, release, and documentation evidence states and gates.
- [contracts/publication-decision.md](./contracts/publication-decision.md) — default hold, validation publication, corrective-history, and explicit replacement choices.
- [quickstart.md](./quickstart.md) — executable validation sequence from active conflict resolution through local candidate proof and publication handoff.

## Post-Design Constitution Re-check

Pass. Phase 1 design:

- adds no product dependency or new runtime file/service;
- uses only lazy additive unread cursor keys, with no destructive/eager owner-data migration;
- preserves provider-neutral ordinary execution and effective Claude configuration;
- applies the native MXC/WSL2 boundary to every employee entry point and gates unproven native Desktop behavior;
- keeps feature-003 release status explicitly blocked rather than weakening or fabricating evidence;
- closes test cleanup/environment-recorder gaps before evidence is trusted;
- binds validation to an exact candidate tree;
- retains recovery and requires explicit owner approval before any remote rewrite.

No feature-level gate is violated and no unresolved clarification remains.

## Risks and Mitigations

| Risk | Mitigation / completion consequence |
| --- | --- |
| Replayed history creates false conflicts or duplicate upstream work | Use verified product-point relationship and prove two-sided content coverage, not commit-name similarity |
| Whole-side conflict choice drops local or upstream behavior | Closed semantic resolution records with tests for both intents |
| Auto-merged file contains a semantic collision | Risk-tier audit and invariant mapping even when no marker exists |
| Upstream connectivity wait breaks third-party/local Claude connection | Preserve process-result truth and socket-trap evidence; omit provider-specific preflight/replay |
| Interactive/app/refresh entry bypasses local machine mode | One shared employee mode gate across every launch surface; native Desktop remains gated pending feature 003 |
| Custom Claude data root breaks context/window continuity | Derive all transcript/session discovery from the exact effective child environment without logging it |
| Native terminal fallback emits POSIX-quoted text | Platform-owned argv launch/display; native Windows starts the Python+Orbit argv in a new console |
| Native notification displays raw or incomplete text | One computed notification body used by every platform branch |
| Filtered employee view clears another employee's unread report | Lazy employee-scoped cursor combined with the existing global cursor |
| UI reintroduces universal subscription/provider claims | Tracked-file copy scan; “configured connection” for ordinary work; account/provider terms only at their real boundaries |
| Auto-merged tests restore obsolete production behavior | Reconcile fixtures to no-preflight + one-conversation semantics and require focused combined matrices |
| Guard 1.6.1 suite remains orphaned | Run documented `claude plugin test` from the plugin directory and add a CI gate after CLI installation |
| Planning-only security artifacts are mistaken for shipped protection | Separate integration and release-readiness states; explicit plan-only labeling |
| Tests leave full inherited environment or temp roots behind | Register MXC/fake-Claude roots, keep recorders in cleanup scope, use disposable profiles, and inventory residue |
| Removing temporary reconciliation changes interpreted content | Capture candidate tree before cleanup and require identical tree afterward |
| Correct local merge becomes a sibling of stale `origin/main` merge | No automatic push; publication contract offers reviewed choices and remote-change precondition |
| Non-destructive corrective history preserves a confusing stale merge | Record consequence; owner may instead authorize lease-protected replacement after collaborator review |
| Cross-platform or real-host evidence is unavailable | Keep status pending; never weaken the gate or report success |
| Feature 003 is preserved but still unimplemented | Record REL1 blocked with known P0 paths and future version/connection/Desktop design conflicts |

## Complexity Tracking

No constitution violation requires justification. Planning adds only evidence contracts. Runtime compatibility uses existing modules and one lazy optional cursor extension in the existing team-state file; it adds no service, dependency, new data file, or destructive migration.
