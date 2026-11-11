# Research: Safe Upstream Synchronization

**Feature**: `004-safe-upstream-merge`

**Date**: 2026-11-09

**Status**: Complete; no unresolved clarification remains

## Evidence Reviewed

- Active repository state and merge index for local `366cf73` plus upstream `256ed16`.
- Local/canonical 0.8.0-era product points `93773e0` and `500d772`.
- Existing fork remote merge `da644db` and its commit/tree identities.
- [Git replacement objects](https://git-scm.com/docs/git-replace), [merge behavior](https://git-scm.com/docs/git-merge), [merge-base selection](https://git-scm.com/docs/git-merge-base), and tree/commit identity rules.
- Current handoff at `%TEMP%/orbit-upstream-merge-handoff.md`.
- Feature 001–003 specifications, plans, contracts, gates, quickstarts, and tests.
- Current `core/`, `orbit`, `tests/`, documentation, and `.github/workflows/tests.yml` integration surfaces.
- Official [Claude Code mod test runner contract](https://code.claude.com/docs/en/plugins/mods/test) for the existing `claude-code/testing` suite.

## R1 — Use the Verified Product Relationship, Not the Accidental Graph Base

**Decision**: Treat canonical upstream `500d772` as the semantic 0.8.0 product base and local `93773e0` as a local variant immediately after that base. Use the current temporary replacement only while forming and recording the integration candidate.

**Rationale**: Without the temporary relationship, the graph selects `ae3df83`, making replayed upstream/local releases through 0.8.0 look like independent work and producing 23 misleading conflicts. With the verified product relationship, the current index uses `500d772` as stage 1 and exposes three real conflicted paths. This retains the small local 0.8.0 delta instead of pretending the two product-point trees are identical.

The local variant differs from canonical upstream at four paths: `README.md`, `core/grants.py`, `core/staffd.py`, and `tests/test_platforms.py`. Those differences remain local work.

**Alternatives considered**:

- Merge from accidental base `ae3df83`: rejected because it re-merges equivalent release history and creates false conflicts.
- Declare local/upstream 0.8.0 byte-identical: rejected because their trees differ at four paths.
- Rebase all local work: rejected because it rewrites useful history without improving content safety.
- Cherry-pick upstream releases: rejected because it duplicates canonical history and loses direct upstream ancestry.

## R2 — Record One Genuine Two-Parent Content Integration

**Decision**: The corrected integration revision has first parent `366cf73`, second parent `256ed16`, and the semantically reviewed candidate tree. It is recorded before temporary replacement metadata is removed.

**Rationale**: A real merge gives future upstream updates direct ancestry and stores the candidate tree plus explicit parents independently of the merge base used to form it. Removing the replacement after the revision exists cannot change its stored tree or parents. A tree-identity check before and after cleanup proves this.

The integration record should retain the otherwise-temporary facts: semantic base `500d772`, local variant `93773e0`, authoritative inputs, and confirmation that the four-path local variant was retained.

**Alternatives considered**:

- Squash upstream into local: rejected because future synchronization loses canonical upstream ancestry.
- Use `da644db` as a content parent: rejected because it contains no integrated upstream content despite its ancestry.
- Create another ancestry-only merge: rejected because it repeats the existing defect.
- Remove the replacement before recording the candidate: rejected because it changes the history interpretation under which the current index was formed before a durable tree exists.

## R3 — Resolve Runtime Conflicts as Explicit Behavior Unions

**Decision**: Resolve each genuine overlap at behavior/symbol granularity rather than selecting one file side.

Required unions:

1. `core/engine.py::command` keeps local launch-policy/settings/platform safety behavior and upstream interactive command construction.
2. `core/engine.py::run` keeps local provider-neutral process-result truth and native mode gate while adopting upstream one-running-conversation, chat-window coordination, fork/orientation/session memory, job-specific model, and busy cleanup behavior.
3. `core/osinfo.py::notify` keeps local native-Windows tray delivery and upstream normalized body/location plus current Mac/Linux behavior.
4. `README.md` keeps local account/Cloud Shift accuracy and upstream brain/hands usage guidance without duplicate prose.

**Rationale**: The two lines changed orthogonal concerns in the same regions. Whole-side selection would either lose the local connection/containment contract or lose upstream 0.9.0–0.12.0 application behavior.

The provider-neutral contract specifically prohibits restoring an `api.anthropic.com` preflight or provider-specific retry before ordinary work. Upstream session coordination can be retained without that endpoint assumption.

**Alternatives considered**:

- Choose local for all conflicts: rejected because it omits upstream session/front-desk behavior.
- Choose upstream for all conflicts: rejected because it weakens local provider-neutral and native-Windows behavior.
- Keep both run loops as alternate branches: rejected because it duplicates authority and creates divergent session semantics.
- Treat documentation conflict as wording-only: rejected because it expresses product account, billing, and eligibility boundaries.

## R4 — Audit Every Shared Path, Including Clean Automatic Merges

**Decision**: Build a two-sided change ledger and semantically inspect all paths changed on both lines. Planning found 71 local changed paths, 35 upstream changed paths, and 14 overlaps relative to the semantic base. Only three overlap paths conflicted textually; the other eleven still require review.

The 14 planning-time overlaps are listed in [contracts/integration-ledger.md](./contracts/integration-ledger.md). Implementation regenerates the set and stops on unexplained drift.

**Rationale**: Automatic merge success only proves that text edits did not overlap according to the merge algorithm. It does not detect duplicate definitions, contradictory conditions, lost argument semantics, stale documentation, or tests that independently encode different behavior.

**Alternatives considered**:

- Review only unmerged paths: rejected because eleven shared paths auto-merged without semantic proof.
- Trust a green parser/compiler: rejected because many collisions are behaviorally wrong but syntactically valid.
- Compare candidate only to upstream: rejected because local omissions would be invisible.

## R5 — Separate Integration Readiness from Product-Release Readiness

**Decision**: Track local integration, cross-platform validation, feature-003 native-Windows release evidence, and remote publication as separate states under [contracts/validation-evidence.md](./contracts/validation-evidence.md).

**Rationale**: Feature 004 preserves feature-003 plans and release gates but does not implement them. Hosted Windows Server and fake executors cannot prove real MXC containment. Conversely, pending real-host evidence does not prevent recording a source-integration candidate whose purpose is to preserve planning and current behavior. Collapsing these facts would either misrepresent unimplemented security work as shipped or make content integration impossible to record.

The candidate may become `locally_recorded` after all locally required integration gates pass. It becomes cross-platform validated, release ready, and published only when each corresponding evidence predicate passes.

**Alternatives considered**:

- One pass/fail readiness flag: rejected because it hides which scope is actually proven.
- Count unavailable platforms as pass: rejected by the specification and existing gate ledgers.
- Drop old P0 gates during synchronization: rejected because update work must not weaken security governance.
- Require feature-003 implementation as part of feature 004: rejected as explicitly out of scope; planning preservation is not implementation.

## R6 — Bind Evidence to the Candidate Tree and Protect Owner Data

**Decision**: Every passing validation record binds to the exact candidate tree, platform, and check. Tests use existing temporary-home and cleanup mechanisms. Any live owner-data change is a failed integration gate.

**Rationale**: Evidence from a different tree cannot prove the final candidate. Orbit's tests manipulate registry, session, secret, and workspace-like state, so cleanup is a product-safety requirement rather than test hygiene alone. Upstream `tests/_cleanup.py` and per-module cleanup updates are part of the candidate and must be semantically audited.

**Alternatives considered**:

- Reuse earlier branch test results without tree binding: rejected because merge resolution changes the tested content.
- Use the owner's real team for smoke tests: rejected because the feature requires zero data migration/loss.
- Skip a host-specific failure without exact baseline evidence: rejected because it can hide a merge regression.

## R7 — Treat the Existing Remote Merge as Publication Topology Only

**Decision**: Do not ordinary-merge or pull `origin/main` into the corrected candidate. After validation, default to no remote write. When collaborator status is unknown, publish a validation branch first. For main, present either a deliberate tree-preserving corrective bridge or an explicit lease-protected replacement.

**Rationale**: Existing `da644db` and the corrected merge will be siblings with the same two parents but different trees. An ordinary merge has multiple best common ancestors and may synthesize a virtual base, repeat conflicts, or interpret the stale merge's missing upstream content as intentional reversion.

A non-destructive bridge preserves every remote commit and uses the validated candidate tree by definition. A remote replacement produces cleaner history but disrupts existing clones/branches and therefore requires explicit owner/collaborator review.

**Alternatives considered**:

- Merge upstream into `da644db`: rejected because upstream is already its parent, so Git sees nothing to add.
- Revert `da644db`: rejected because its tree equals its first parent and the revert is content-empty.
- Ordinary sibling merge with `-X ours`: rejected because the option affects only conflicting hunks and does not guarantee the validated tree.
- Unqualified force push: rejected because it can overwrite remote changes and lacks owner authorization.

## R8 — Use Tree Identity as the Content Invariant, Not as Semantic Proof

**Decision**: Capture one validated candidate tree ID and require it to remain unchanged through integration recording, replacement cleanup, any tree-preserving bridge, and post-publication verification.

**Rationale**: A tree ID proves byte-for-byte tracked content, modes, paths, and symlink targets. It is the strongest compact invariant that temporary history metadata or publication topology did not alter content.

Tree identity does not prove that the content is correct. Semantic completeness additionally requires the two-sided ledger, overlap rationale, structural checks, targeted tests, full enabled suites, documentation review, and explicit pending platform evidence.

**Alternatives considered**:

- Compare commit IDs only: rejected because different commits can have identical trees and the current defect demonstrates that correct ancestry can carry stale content.
- Compare file counts/statistics only: rejected because equal counts do not establish equal bytes or modes.
- Treat tree equality as full validation: rejected because a stable but semantically wrong tree remains wrong.

## R9 — Keep Planning Artifacts in the Candidate but Stage Deliberately

**Decision**: Include feature-004 specification/design artifacts and the active feature pointer only after reviewing their exact paths. Do not broadly stage the entire worktree.

**Rationale**: Planning is part of the requested work and provides the audit trail for conflict decisions. However, the active merge also contains staged auto-merge output, unstaged feature state, and untracked planning files. Broad staging could accidentally include disposable previews or unrelated work.

**Alternatives considered**:

- Leave design artifacts permanently untracked: rejected because future implementation/tasks would lose their governing contracts.
- Stage all changes recursively: rejected because it violates deliberate path accounting.
- Commit planning in an unrelated pre-merge revision: rejected because a merge is already active and no destructive history surgery is justified.

## R10 — Put Every Employee Entry Point Behind One Platform/Mode Boundary

**Decision**: Apply the native-Windows mode gate to every employee execution surface, not only headless `engine.run()`:

- terminal chat and its command builder;
- Claude-app employee session creation/opening;
- panel employee-session opening;
- session/plugin refresh work;
- any other path that can start an employee Claude process.

When a native-Windows installation is recorded as `wsl2`, all native-side employee launch surfaces refuse and direct the owner to the WSL side. In native MXC mode, terminal interactive chat uses the same PowerShell tool selection, MXC hook, guard, settings, MCP, and deny boundaries as unattended work.

Native-Windows employee Claude-app/Desktop sessions remain gated until feature 003's stronger effective-settings contract is implemented and proven. Mac, Linux, and actual WSL behavior remains available. The owner front desk is a control-plane surface and may remain available only with exact Windows PowerShell/path permissions that cannot launch an employee outside the mode gate.

**Rationale**: Upstream added `chat_window`, `claude_session`, `orbit chat`, `orbit open`, panel opening, and refresh paths after the local native-mode gate was designed. Gating only `run()` creates a direct bypass of the machine's explicit MXC/WSL2 mode and conflicts with feature 003's reviewed Desktop-session restriction.

**Alternatives considered**:

- Gate only headless work: rejected because interactive/app launch still starts employee work natively.
- Allow native Desktop because generated settings contain a hook: rejected because feature 003 documents why folder/Desktop settings cannot yet establish the required boundary.
- Disable all new upstream app/terminal flows on every platform: rejected because Mac/Linux/WSL behavior is compatible and part of upstream 0.12.0.
- Treat the owner desk as an employee session: rejected because it is a control plane, but it still needs closed platform permissions.

## R11 — Resolve Session/Transcript State Through the Effective Claude Data Root

**Decision**: One helper derives Claude's effective configuration/data root from the exact child launch environment. Transcript context, window discovery, idle detection, and session continuity use that root. Ordinary pass-through preserves an inherited `CLAUDE_CONFIG_DIR`; no value is persisted or copied into logs. Paths that intentionally use application-owned or isolated configuration pass their own effective root.

**Rationale**: Local feature 002 deliberately preserves arbitrary connection/configuration environment, including `CLAUDE_CONFIG_DIR`, while upstream one-conversation helpers hard-code `~/.claude/projects` and `~/.claude/sessions`. Hard-coding silently reads the wrong location for a valid configured connection. Removing or overwriting the environment value would violate exact pass-through.

**Alternatives considered**:

- Strip `CLAUDE_CONFIG_DIR`: rejected by the pass-through contract.
- Document default-location-only support: rejected because the product already promises Claude's effective configured connection and a reasonable deterministic path is available.
- Read the parent process environment independently in each helper: rejected because it may differ from the actual child policy and duplicates sensitive path handling.
- Persist the resolved root in team state: rejected because it is launch configuration, not Orbit-owned data.

## R12 — Make Terminal Launch/Quoting Platform-Owned

**Decision**: Callers pass an argument vector for an Orbit terminal chat; `osinfo` owns display formatting and terminal launch for each platform. Native Windows uses the current Python executable plus the Orbit script in a new console without reparsing a POSIX-quoted shell string. Mac/WSL/Linux keep their platform launch behavior with quoting contained inside `osinfo`.

**Rationale**: Upstream `open_terminal()` has Mac, WSL, and Linux branches only. Panel and CLI callers currently build command text with POSIX `_sh()`, producing unusable or unsafe copied commands on native Windows. A platform-owned argv boundary avoids shell-text composition and makes both launch and fallback display testable.

**Alternatives considered**:

- Add Windows quoting in panel/CLI callers: rejected because quoting would drift across call sites.
- Reparse a single command string through `cmd.exe` or PowerShell: rejected because shell composition expands the injection/quoting surface unnecessarily.
- Leave native Windows as copy-only with a Unix command: rejected because feature 001 requires first-class native flows.

## R13 — Use Additive Employee-Scoped Unread Cursors

**Decision**: Extend the existing owner seen state with optional per-employee cursors:

- a full team-room view advances the existing global owner cursor;
- a filtered employee inbox/chat advances only that owner+employee cursor;
- unread evaluation uses the newer of the global cursor and the matching employee cursor for each message;
- existing global-only state remains valid without migration.

The panel `/api/seen` request accepts an optional employee identity. Employee Chat sends it; full Today/team-room views omit it. `orbit inbox <handle>` and the pre-chat display mark only that employee.

**Rationale**: Current filtered views call global `mark_seen()`, so reading one employee can clear an unseen report from another. This contradicts upstream's “nothing gets lost” promise. Merely avoiding marking would leave an employee's viewed messages unread forever. Additive scoped cursors preserve both accurate global counts and filtered-view UX.

**Alternatives considered**:

- Keep one global cursor from every view: rejected because filtered views clear unseen messages.
- Never mark from filtered views: rejected because viewed employee messages never clear.
- Replace global state with a wholly new database/schema: rejected as unnecessary and destructive.
- Store one record per message: rejected because bounded timestamp+same-timestamp IDs already solve ordering efficiently.

## R14 — Keep Brain/Hands and UI Language Provider-Neutral

**Decision**: Preserve upstream brain/hands model-role selection, defaults, fallback-on-reported-usage, and additive `brain_v1`/main-session compatibility. Continue passing model aliases to Claude without probing compatibility or routing providers. Rewrite ordinary-work UI/onboarding/docs copy to “Claude's configured connection” and qualify plan/usage data with “when Claude reports it.”

The legacy stored-key path may name an Anthropic API key. Cloud Shift alone may require a qualifying Claude account. Existing `staff.json.auth == "subscription"` remains a backward-compatibility marker and MUST NOT be rendered as proof that the owner has a subscription.

**Rationale**: The merged code largely preserves provider-neutral execution, but several upstream UI strings universally call ordinary work a plan/subscription. Brain/hands describes model roles, not provider or billing selection.

**Alternatives considered**:

- Restore account/subscription terminology globally: rejected by feature 002.
- Remove brain/hands to avoid provider assumptions: rejected because aliases are already Claude-owned and upstream behavior is compatible.
- Rename persisted compatibility values during the merge: rejected because no destructive migration is needed.

## R15 — Reconcile Tests to the Combined Contract and Close Cleanup Gaps

**Decision**: Update tests to prove the semantic union rather than restoring obsolete production behavior:

- remove upstream fixture reads/monkeypatches of absent `engine.online`;
- update default chat expectations from hands/Sonnet to brain/Opus where upstream semantics apply;
- expect `ORIENT` only for a new main conversation;
- inspect the MXC hook's exec `command` plus `args`, not only `command`;
- move `unittest.main()` after all appended test classes;
- add matrices for interactive/headless × ordinary/legacy, all employee mode gates, custom Claude data root, native notification body, Windows terminal/desk settings, and scoped unread cursors.

All Python modules run in separate processes, as CI does. `test_mxc.py` and every external fake-Claude recorder gain registered cleanup; recorders live under registered temporary roots and never persist full inherited environments after exit. Manual install/OCR smoke runs only in disposable accounts/VMs. Validation may set `PYTHONDONTWRITEBYTECODE=1` to avoid source-tree cache residue.

The existing guard test suite runs through the documented [`claude plugin test`](https://code.claude.com/docs/en/plugins/mods/test) command from `core/guard/staff-guard`; no package manifest is required. Add a repository-owned CI invocation after Claude Code installation. If the required CLI is unavailable locally, guard evidence is `pending`, not passing.

**Rationale**: Auto-merged upstream tests still encode the removed provider preflight and old model/prompt expectations. Reintroducing production code to satisfy them would violate accepted local behavior. Cleanup gaps currently leave temporary roots and full environment recordings behind, preventing a clean data-safety claim. The guard 1.6.1 change otherwise has an orphaned ten-test suite.

**Alternatives considered**:

- Restore `engine.online` for fixtures: rejected because it violates feature 002 and creates dead/unsafe authority.
- Accept known native test failure as a passing baseline: rejected; expected checks must pass.
- Use `unittest discover` as the authoritative run: rejected because modules mutate process-global home bindings; CI's separate processes are authoritative.
- Ignore guard tests because no package exists: rejected; Claude Code itself provides the test runner.

## R16 — Mark Feature 003 Release Readiness Blocked, Not Merely Pending

**Decision**: Feature 004 may record and cross-platform validate a source-integration candidate, but native-Windows containment product-release status (`REL1`) is currently `blocked` because feature 003 is planning-only and known P0 code paths remain. Preserve all feature-003 artifacts and prevent new entry-point bypasses, but do not claim its implementation or evidence.

The release record explicitly carries three future design conflicts:

1. feature 004's integrated application version `0.12.0` versus feature 003's proposed legacy-invisible `0.8.0-sec.N` release line;
2. feature 002 provider-neutral user-setting pass-through versus feature 003's proposed native-Windows restricted/relay/empty-source model;
3. upstream native Claude-app employee sessions versus feature 003's native Desktop refusal.

For feature 004, the chosen compatibility outcomes are: keep source version 0.12.0, retain feature 002 ordinary behavior, gate native-Windows employee Desktop surfaces, and report `REL1=blocked`. A later feature-003 implementation/design reconciliation owns the long-term release choices.

**Rationale**: Current code still lacks `onFailure: "block"`, accepts workspace policy authority, can emit no decision for malformed/empty hook input, and retains broad gateway pass-through. Planned feature-003 test modules, Windows harnesses, build workflows, and evidence validator do not exist. “Real host unavailable” is not the only missing evidence.

**Alternatives considered**:

- Mark `REL1` pending only: rejected because required implementation is absent and known blockers exist.
- Opportunistically implement feature 003 during synchronization: rejected as a large P0 redesign outside this feature.
- Drop/supersede feature 003 because upstream is newer: rejected because upstream does not close the local security findings.
- Call hosted fake-MXC unit tests release proof: rejected by feature 003 and workflow comments.

## Resolved Design Summary

All planning unknowns are resolved:

- semantic base: canonical upstream `500d772`, preserving local `93773e0` delta;
- content integration: genuine merge of `366cf73` + `256ed16`;
- conflict policy: explicit semantic unions, no whole-side shortcut;
- auto-merge policy: two-sided ledger and review of every overlap;
- content invariant: exact candidate tree before/after temporary metadata cleanup;
- readiness: integration, cross-platform, product release, and publication tracked independently;
- publication: default hold/validation branch, then owner-approved bridge or lease-protected replacement;
- employee surfaces: one mode gate; native MXC terminal allowed under existing controls; native Desktop gated pending feature 003;
- session discovery: effective Claude data root, never hard-coded default or persisted value;
- terminal/desk: platform-owned argv/permissions with exact native-Windows PowerShell rules;
- unread state: additive per-employee cursor layered over the existing global cursor;
- copy/model roles: brain/hands retained without subscription/provider claims;
- tests: combined-contract expectations, module-isolated execution, guard CLI gate, and complete temporary-data cleanup;
- release: feature-003 `REL1` is blocked and its cross-spec conflicts are explicit;
- data: no destructive migration and no live owner-data testing.
