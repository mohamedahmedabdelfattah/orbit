# Contract: Integration and Release Validation Evidence

## Purpose

Define the closed evidence states and gates used to distinguish:

1. a textually resolved merge;
2. a locally validated integration candidate;
3. a candidate validated across the repository's supported CI platforms;
4. a product release satisfying independent native-Windows containment release gates;
5. an owner-approved remote publication.

These states MUST NOT collapse into one Boolean. In particular, preserving feature-003 planning artifacts does not implement them, and unavailable real-host evidence is not a pass.

## Evidence Record

```text
Evidence ID: E-...
Gate ID: ...
Candidate revision/tree: ...
Platform: host | macos | linux | wsl2 | windows_unit | windows_mxc_x64 | windows_mxc_arm64 | not_applicable
Check/scenario: ...
Status: pass | fail | pending | not_applicable
Observed result: ...
Artifact/log/digest/review: ...
Recorded at: ...
Blocking scope: integration | cross_platform | product_release | publication
```

### Status rules

- `pass`: The exact check completed successfully against the exact candidate tree on the named platform.
- `fail`: The check completed and violated its expected outcome. The named scope is blocked.
- `pending`: Evidence is required but could not yet be executed or reviewed. It remains visible and blocks only the scope defined by the gate.
- `not_applicable`: The contract explicitly excludes this check for this candidate/platform. A rationale is mandatory.

Skipped, unavailable, timed-out, cancelled, or uncollected checks are `pending` or `fail` according to their gate; they are never inferred as `pass`.

## Gate Catalog

### I0 — Baseline and Recovery Integrity

**Scope**: integration

Required evidence:

- local, upstream, semantic-base, local-variant, recovery, and observed-remote commit/tree identities;
- recovery reference resolves to the local baseline;
- current merge parents are the authoritative local and upstream inputs;
- temporary reconciliation identity and purpose are recorded;
- stage-1 blobs for unresolved paths match the semantic base.

Pass condition: all identities resolve and match the integration ledger with no unexplained difference.

### I1 — Two-Sided Change Coverage

**Scope**: integration

Required evidence:

- regenerated local/upstream changed-path sets;
- complete integration ledger;
- all overlap paths reviewed;
- zero `pending` entries;
- no exclusion without owner approval.

Pass condition: 100% of both changed-path sets have one terminal ledger outcome.

### I2 — Explicit Semantic Resolutions

**Scope**: integration

Required evidence for:

- `R-ENGINE-COMMAND`;
- `R-ENGINE-RUN`;
- `R-OSINFO-NOTIFY`;
- `R-README-COST`;
- `R-INTERACTIVE-PLATFORM`;
- `R-CLAUDE-DATA-ROOT`;
- `R-UNREAD-SCOPE`;
- `R-PROVIDER-COPY`;
- `R-TEST-EVIDENCE`;
- `R-CLEANUP`;
- `R-RELEASE-STATUS`.

Pass condition: each record is applied, focused diff is reviewed, both input intents are traceable, and focused evidence passes.

### I3 — Structural Integrity

**Scope**: integration

Required evidence:

- zero unmerged index paths;
- zero accidental conflict markers outside deliberate fixtures;
- clean whitespace/error checks for staged content;
- source parsing/compilation succeeds for changed source;
- JSON and other structured assets parse;
- no unintended duplicate active definitions;
- `VERSION` equals `0.12.0`;
- expected upstream additions and local feature artifacts exist.

Pass condition: every structural check is clean against the staged candidate tree.

### I4 — Targeted Behavioral Invariants

**Scope**: integration

Required evidence covers:

- ordinary versus legacy launch policy;
- interactive versus unattended command construction;
- no provider-specific ordinary connectivity preflight;
- one-conversation session/fork/orientation/busy cleanup;
- effective Claude data-root transcript/window continuity;
- native-Windows MXC and explicit WSL2-mode gate across every employee entry point;
- native terminal argv/quoting and exact owner-desk PowerShell/path rules;
- Mac/Linux/native-Windows notification behavior;
- Cloud Shift separation;
- brain/hands alias behavior without provider routing;
- scoped unread and Claude-app desk/report flows;
- test cleanup and owner-data isolation.

Pass condition: every Behavioral Invariant affected by an overlap has at least one passing focused check bound to the candidate tree.

### I5 — Complete Locally Available Suite

**Scope**: integration

Required evidence:

- every repository unit module expected on the implementation host runs without failure;
- any pre-existing host-specific failure is identified by exact test ID and comparison evidence, but remains `fail` unless an existing authoritative platform contract classifies that exact check as not applicable;
- no test is disabled, weakened, or removed merely to obtain a pass;
- `test_mxc` and fake-Claude recorder roots are registered for cleanup;
- no temp root, transcript slug, full-environment recorder, listener/service child, or live owner-data change remains.

Pass condition: all checks that are expected to run on this host pass. A known failure is diagnostic context, not a pass. Platform-inapplicable checks are recorded separately and do not satisfy X1.

### G1 — Guard Plugin Test Suite

**Scope**: cross_platform

Required evidence:

- run `claude plugin test` from `core/guard/staff-guard` using the repository's supported Claude Code CLI;
- all ten current TypeScript tests pass, including the guard 1.6.1 commit-message-as-data cases;
- the CI workflow owns an executable invocation after installing Claude Code;
- no account sign-in or network inference is required by the test.

Pass condition: the exact candidate's plugin and test files pass through the official plugin test runner. Missing CLI/runner evidence is `pending`, not `pass`.

### D1 — Documentation and Version Consistency

**Scope**: integration

Required evidence:

- commands and setup prerequisites match source;
- ordinary Claude connection and Cloud Shift account language match their contracts;
- brain/hands, conversation, report, notification, and desk claims match the integrated source;
- native-Windows and WSL2 claims match platform behavior;
- cost/use wording is non-duplicated and consistent;
- version references use 0.12.0 where this candidate is the subject;
- `PRODUCT.md`, README, SETUP, and workflow comments agree on current version and release-gate status;
- planning-only security artifacts remain labeled as planning and REL1-blocking rather than implemented/shipped.

Pass condition: source-backed review finds zero contradictory or unverifiable current-product claim.

### H1 — Recorded Tree and Temporary-Metadata Cleanup

**Scope**: integration

Required evidence:

- integration revision has exactly local baseline and upstream target as parents;
- revision tree equals the staged validated tree;
- replacement-disabled inspection sees the same revision/tree;
- temporary replacement ref is removed;
- tree and parent identities remain unchanged after removal;
- both authoritative inputs are ancestors of the recorded integration revision;
- recovery reference remains available.

Pass condition: all identity checks pass and a replacement-free checkout validates structurally.

### X1 — Supported Cross-Platform CI Matrix

**Scope**: cross_platform

Required evidence follows `.github/workflows/tests.yml`:

- macOS full selected module suite;
- Ubuntu 24.04 full selected module suite plus existing installation/sandbox/OCR/service checks;
- native-Windows unit slices for MXC, Windows, and mode behavior;
- Ubuntu 24.04 under WSL2 full selected module suite plus existing integration checks.

Pass condition: every mandatory matrix job passes against the exact candidate tree. Local Windows evidence cannot substitute for macOS, Linux, or WSL2 evidence.

### REL1 — Native-Windows MXC Release Evidence

**Scope**: product_release

Required evidence is governed by `specs/003-close-containment-gaps/` and any later accepted implementation/release contract.

Pass condition: the applicable real-client/real-host evidence is complete for every architecture the release claims to support.

Current planning state is `blocked`, not merely `pending`, because the implementation modules/harnesses/workflows are absent and current code retains the known hook-failure, workspace-policy, malformed/no-decision, and gateway pass-through blockers. Once implementation exists and unit/design blockers are cleared, missing real-host evidence may become `pending`.

The REL1 record also retains three unresolved future release-design conflicts rather than hiding them: integrated version `0.12.0` versus the proposed `0.8.0-sec.N` line, provider-neutral ordinary pass-through versus the proposed native restricted relay, and upstream native employee app sessions versus the planned native Desktop refusal. Feature 004 selects source-integration compatibility outcomes but does not declare the long-term release design resolved.

Important distinctions:

- Feature 004 preserves this gate; it does not implement feature 003.
- Hosted Windows Server unit coverage does not prove real MXC enforcement.
- Missing real-host evidence remains `pending` and blocks the corresponding product-release claim, not the act of recording a source-integration candidate.

### PUB1 — Owner-Approved Publication

**Scope**: publication

Required evidence:

- selected option from [publication-decision.md](./publication-decision.md);
- explicit owner approval where required;
- fresh remote identity;
- candidate/published tree equality;
- post-publication fetch/clone verification;
- no lease or remote-state mismatch.

Pass condition: the selected operation completed without changing the validated tree and its remote result is independently verified.

## Readiness Predicates

| State | Required passing gates | Allowed pending gates |
| --- | --- | --- |
| `resolved` | I0, I2, I3 | I1, I4, I5, G1, D1, H1, X1, REL1, PUB1 |
| `validated_local` | I0–I5, D1 | G1, H1, X1, REL1, PUB1 |
| `locally_recorded` | I0–I5, D1, H1 | G1, X1, REL1, PUB1 |
| `validated_cross_platform` | I0–I5, G1, D1, H1, X1 | REL1, PUB1 |
| `release_ready` | I0–I5, G1, D1, H1, X1, REL1 | PUB1 |
| `published` | All gates applicable to the owner's selected publication/release scope | None within selected scope |

A `fail` in a required gate blocks the state. Owner acceptance of an exception must be represented as an explicit specification/publication decision; it cannot convert failed security evidence into passing evidence.

## Existing Test Mapping

Static planning inventory finds approximately 280 Python tests across the six modules (runtime counts vary through platform/dependency skips) and ten guard plugin tests. The repository's authoritative Python sequence runs each module in a fresh process:

1. `tests.test_core`
2. `tests.test_channels`
3. `tests.test_tools`
4. `tests.test_calls`
5. `tests.test_platforms`
6. `tests.test_mxc`

Focused class/method selections may run first for diagnosis, but they do not replace the full applicable sequence. Existing gate scripts and static scans from features 001–003 remain additional evidence where applicable.

`unittest discover -s tests` is diagnostic only because modules mutate process-global home configuration and imports retain the first binding. It MUST NOT replace separate-process module evidence. The guard suite is separate G1 evidence through the Claude plugin test runner.

## Evidence Binding

Every passing evidence record MUST bind to the candidate tree. If source content changes afterward:

- I2–I5 and D1 evidence affected by changed paths becomes stale;
- H1 must be rerun for a newly recorded revision;
- G1/X1/REL1 runs from another tree cannot be reused;
- publication approval becomes stale if either candidate or remote identity changes.

## Redaction and Data Safety

Evidence MUST NOT contain:

- API keys, tokens, passwords, native credential material, or inherited connection values;
- owner message contents or unrestricted team files;
- full security policy contents where a digest/reason code suffices.

Tests use isolated homes and existing cleanup helpers. Any observed modification to live owner data is a failed I5 check.

## Completion Report Contract

The implementation completion report lists:

- candidate revision and tree;
- input/recovery identities;
- integration ledger totals and exclusions;
- explicit resolution outcomes;
- I0–I5, G1, D1, H1, X1, REL1, and PUB1 statuses;
- exact failures and pending platforms;
- replacement cleanup status;
- recovery-point status;
- publication decision status.

The report uses “locally recorded,” “cross-platform validated,” “release ready,” and “published” only when the corresponding predicate above is met.

## Planning-Time Gate Snapshot (2026-11-09)

This snapshot is diagnostic and MUST be replaced by candidate-bound implementation evidence:

| Gate | Status | Reason |
| --- | --- | --- |
| I0 | `pending` | Identities observed, but no final evidence record exists |
| I1 | `pending` | 92-path union/14-overlap counts observed; no instantiated complete ledger |
| I2 | `fail` | Three index-unmerged files and unresolved compatibility records |
| I3 | `fail` | Conflict markers/parse failure plus `core/claudeapp.py` EOF whitespace issue |
| I4 | `pending` | Combined behavior not yet implemented or tested |
| I5 | `pending` | Suite not run; cleanup gaps remain in MXC/fake-Claude fixtures |
| G1 | `pending` | Ten tests exist; repository CI invocation is absent |
| D1 | `fail` | README conflict and stale PRODUCT/release-gate/current-platform copy |
| H1 | `pending` | Corrected integration revision not recorded; replacement still active |
| X1 | `pending` | No candidate-bound macOS/Linux/native-Windows/WSL2 matrix |
| REL1 | `blocked` | Feature 003 unimplemented; known P0 code paths and absent evidence harnesses |
| PUB1 | `pending` | Default hold-local; no owner publication decision |
