# Quickstart: Validate and Record the Safe Upstream Synchronization

## Purpose

Provide a runnable maintainer sequence that proves the current local/upstream integration contains both lines' intended content, preserves local safety boundaries and upstream 0.12.0 behavior, records one genuine integration revision, and leaves remote publication pending for an explicit owner decision.

Use this guide with:

- [integration ledger contract](./contracts/integration-ledger.md)
- [validation evidence contract](./contracts/validation-evidence.md)
- [publication decision contract](./contracts/publication-decision.md)
- [data model](./data-model.md)

This is a validation/run guide, not permission to reset, abort, force-push, delete recovery refs, or touch live owner data.

## Prerequisites

- Work from the Orbit repository root.
- The intended local baseline is `366cf73`.
- The intended upstream target is `256ed16` (`v0.12.0`).
- `backup-before-sync` resolves to `366cf73`.
- The active merge has `MERGE_HEAD=256ed16`.
- The temporary replacement for local product point `93773e0` remains active until the integration revision is recorded.
- No remote write is part of this guide unless the owner later selects a publication option.
- Tests must use their temporary homes/cleanup helpers, never the owner's live `~/Staff` data.

Recommended Windows test environment:

```powershell
$env:PYTHONUTF8 = "1"
$env:STAFF_TEST_OCR = "0"
$env:PYTHONDONTWRITEBYTECODE = "1"
```

## Phase A — Prove the Safety Envelope

Record outputs as I0 evidence:

```powershell
git rev-parse HEAD
git rev-parse MERGE_HEAD
git rev-parse backup-before-sync
git rev-parse upstream/main
git rev-parse origin/main
git merge-base HEAD MERGE_HEAD
git replace -l
git status --short
git diff --name-only --diff-filter=U
```

Expected at the start of this feature's implementation:

- `HEAD` and `backup-before-sync` resolve to `366cf73...`;
- `MERGE_HEAD` and `upstream/main` resolve to `256ed16...`;
- semantic merge base resolves to `500d772...` while replacement processing is active;
- exactly `README.md`, `core/engine.py`, and `core/osinfo.py` are index-unmerged;
- the replacement list contains only the planned local product-point replacement.

Verify the existing remote's content/history mismatch without using it as an input:

```powershell
git rev-list --parents -n 1 origin/main
git rev-parse "origin/main^{tree}"
git rev-parse "366cf73^{tree}"
```

Expected: the remote merge has both authoritative parents but its tree equals the pre-synchronization local tree.

Stop if any identity differs unexpectedly. Refresh the plan/ledger rather than guessing.

## Phase B — Build the Two-Sided Change Ledger

Generate independent path inventories:

```powershell
git diff --name-status 500d772 366cf73 > "$env:TEMP\orbit-local-paths.txt"
git diff --name-status 500d772 256ed16 > "$env:TEMP\orbit-upstream-paths.txt"
git diff --name-only 500d772 366cf73 > "$env:TEMP\orbit-local-names.txt"
git diff --name-only 500d772 256ed16 > "$env:TEMP\orbit-upstream-names.txt"
```

Populate the implementation ledger using the schema in `contracts/integration-ledger.md`. Regenerate the overlap set and compare it with the 14-path planning set in that contract.

For each overlap path, inspect all three views:

```powershell
git diff 500d772 366cf73 -- <path>
git diff 500d772 256ed16 -- <path>
git diff --cached -- <path>
```

Do not mark an automatically combined path complete until the candidate diff has a rationale, invariant IDs, and evidence IDs.

## Phase C — Resolve the Explicit Semantic Set

Apply the four resolution records from the ledger contract:

1. `R-ENGINE-COMMAND`
2. `R-ENGINE-RUN`
3. `R-OSINFO-NOTIFY`
4. `R-README-COST`

Review focused diffs before staging:

```powershell
git diff -- README.md
git diff -- core/engine.py
git diff -- core/osinfo.py
```

Required outcomes:

- interactive and unattended commands share local launch/sandbox/tool policy but retain their different interaction flags;
- one-conversation session continuity and chat coordination remain, with no ordinary Anthropic-host preflight or provider-specific wait/replay;
- native Windows notifications use the normalized computed body while current Mac/Linux behavior remains;
- README has one coherent cost/account paragraph and a separate accurate Cloud Shift bullet.

Stage only reviewed paths, never the whole worktree by default:

```powershell
git add -- README.md core/engine.py core/osinfo.py
```

Then confirm:

```powershell
git diff --name-only --diff-filter=U
```

Expected: no output.

## Phase D — Audit Automatically Combined Overlaps

Review, at minimum:

```text
SETUP.md
core/guard/staff-guard/hooks/register.js
core/onboard.py
core/orders.py
core/panel.py
core/panel/app.js
core/staffd.py
core/team.py
orbit
tests/test_core.py
tests/test_platforms.py
```

For each path:

- compare local and upstream intent from Phase B;
- inspect the staged candidate;
- check for duplicated branches/definitions, stale provider assumptions, dropped settings, changed tool/sandbox surface, or incomplete upstream session/desk flow;
- add its terminal ledger outcome and evidence mapping.

The audit MUST also resolve these cross-file compatibility records:

- `R-INTERACTIVE-PLATFORM`: all employee entry points share the native `mxc`/`wsl2` mode gate; native terminal launch/display uses argv, native employee Desktop stays gated pending feature 003, and owner desk uses exact Windows permissions;
- `R-CLAUDE-DATA-ROOT`: transcript/window helpers follow effective `CLAUDE_CONFIG_DIR` without logging it;
- `R-UNREAD-SCOPE`: filtered employee views advance only that employee's unread cursor;
- `R-PROVIDER-COPY`: onboarding/panel/docs ordinary-work copy says configured connection, not subscription;
- `R-TEST-EVIDENCE`: tests do not restore `engine.online` or pre-brain/pre-orientation behavior;
- `R-CLEANUP`: every module/recorder leaves no sensitive residue;
- `R-RELEASE-STATUS`: feature-003 REL1 remains explicitly blocked.

Also review every other staged path according to its risk tier. An absent textual conflict is not a review result.

## Phase E — Stage Planning/Evidence Artifacts Deliberately

Review the active feature pointer and feature-004 documents, then stage only their exact paths if they are intended in the integration revision:

```powershell
git diff -- .specify/feature.json
git status --short -- specs/004-safe-upstream-merge
git add -- .specify/feature.json specs/004-safe-upstream-merge
```

Confirm no unrelated untracked path will enter the revision:

```powershell
git status --short
```

## Phase F — Structural Gates

Run I3 and D1 checks:

```powershell
git diff --name-only --diff-filter=U
git diff --check
git diff --cached --check
rg -n "^(<<<<<<<|=======|>>>>>>>)" .
git grep --cached -n -E "^(<<<<<<<|=======|>>>>>>>)"
python -m py_compile orbit core/engine.py core/osinfo.py core/onboard.py core/panel.py core/staffd.py core/team.py core/orders.py core/hire.py core/update.py core/claudeapp.py core/desk.py
node --check core/panel/app.js
node --check core/guard/staff-guard/hooks/register.js
Get-Content VERSION
git diff --cached --stat
```

Expected:

- no unresolved paths;
- no whitespace errors;
- no accidental conflict lines (document and exclude only deliberate fixtures);
- changed Python entry points parse;
- `VERSION` is exactly `0.12.0`;
- expected upstream additions such as `core/claudeapp.py`, `core/desk.py`, and `core/jobs/claude_app.md` are staged;
- local `core/mxc.py`, feature 001–003 artifacts, tests, and Windows setup assets remain present.

Current planning identified an extra blank line at EOF in `core/claudeapp.py`; structural validation must correct it rather than accepting a known `diff --check` failure.

Inspect the complete staged candidate rather than only unstaged changes:

```powershell
git diff --cached -- README.md core/engine.py core/osinfo.py core/onboard.py core/panel.py core/panel/app.js core/staffd.py core/team.py core/update.py orbit tests/test_core.py tests/test_platforms.py
```

Record the staged tree for later identity proof:

```powershell
$stagedTree = git write-tree
$stagedTree
```

## Phase G — Focused Behavioral Evidence

Run existing focused classes/methods that cover the changed launch, session, platform, panel, cloud, notification, and cleanup behavior. Derive exact selectors from the merged test source; do not delete or weaken a failing assertion.

At minimum, evidence must prove:

- ordinary/legacy launch-policy matrix;
- interactive/unattended argv matrix;
- no ordinary Anthropic-host socket gate;
- one-session resume/new/fork/orientation behavior;
- default and custom Claude data-root context/window behavior;
- native-Windows MXC settings and WSL2-mode refusal across run/chat/open/panel/refresh;
- native terminal argv formatting and closed Windows front-desk permissions;
- native employee Desktop gating pending feature 003;
- Cloud Shift eligibility separation;
- notification body behavior per platform;
- Claude-app desk and platform-appropriate employee chat paths;
- two-employee filtered/global unread behavior;
- provider-neutral onboarding/UI/docs copy with brain/hands retained;
- test cleanup leaves no real team data change.

Use `specs/002-claude-connection-pass-through/quickstart.md` for pass-through scenarios and `specs/001-windows-mxc-sandbox/verify_gates.py` for currently implemented feature-001 gates. Keep `specs/003-close-containment-gaps/` release requirements separate. REL1 is currently blocked because its implementation/evidence does not exist and known P0 paths remain.

Auto-merged upstream fixtures that read or monkeypatch `engine.online` must be rewritten to assert the no-preflight contract. Do not restore that symbol. Update old Sonnet/default-prompt assertions only where upstream brain/ORIENT semantics now apply, and keep their original pass-through/no-fallback assertions.

## Phase H — Full Locally Available Suite

Run the repository sequence used by CI:

```powershell
python -m unittest tests.test_core
python -m unittest tests.test_channels
python -m unittest tests.test_tools
python -m unittest tests.test_calls
python -m unittest tests.test_platforms
python -m unittest tests.test_mxc
```

If this native-Windows host has known baseline failures:

1. record exact test IDs;
2. compare with the documented pre-integration baseline for diagnosis only;
3. run affected feature selectors separately where shared global test state could mask results;
4. keep any expected host check as `fail` until corrected; a pre-existing failure is not a pass;
5. mark genuinely unsupported POSIX/WSL/macOS checks `pending`, not passing;
6. do not alter assertions solely to make the suite green.

The authoritative cross-platform commands remain in `.github/workflows/tests.yml`.

After each module, verify that registered module roots, `fake-claude-*`, `orbit-mxc-test-*`, disposable Claude transcript slugs, and listener/service children are gone. `tests/test_mxc.py` and every external fake-Claude recorder must use the shared cleanup mechanism before I5 can pass. A recorder containing the full inherited environment is sensitive test output and cannot remain on disk.

## Phase H2 — Guard Plugin Evidence

When the supported Claude Code CLI is available, run the existing TypeScript suite through its official runner:

```powershell
Push-Location core\guard\staff-guard
claude plugin test
$guardResult = $LASTEXITCODE
Pop-Location
if ($guardResult -ne 0) { exit $guardResult }
```

Expected: all ten guard tests pass, including commit-message-as-data cases. No sign-in or model call is required. If the CLI is unavailable locally, record G1 as pending and require the same command in CI after Claude Code installation; do not count it as a pass.

## Phase I — Documentation and Coverage Review

Complete D1 and the ledger:

- verify every command/field named in README/SETUP exists in source;
- verify ordinary Claude connection language matches feature 002;
- verify Cloud Shift remains separately eligibility-gated;
- verify brain/hands, one-conversation, notifications, reports/unread state, and desk claims match upstream-integrated code;
- verify native-Windows/WSL2 language matches the actual platform paths;
- verify feature-003 artifacts remain planning-only and REL1-blocking rather than claimed shipped;
- verify `PRODUCT.md` identifies the integrated product accurately and no README/workflow comment calls feature-003 real-host evidence optional/non-gating;
- record REL1 as blocked with the known hook failure, workspace policy, malformed/no-decision, gateway pass-through, and absent harness/workflow blockers;
- require zero pending ledger entry and zero unapproved exclusion.

Do not proceed to recording while I0–I5 or D1 fails.

## Phase J — Record the Genuine Integration Revision

Immediately before recording:

```powershell
git rev-parse backup-before-sync
git diff --name-only --diff-filter=U
git status --short
git write-tree
```

Expected: recovery is intact, no unresolved path remains, the intended path set is staged, and the tree equals `$stagedTree` unless an evidence-backed correction changed it and invalidated/re-ran affected tests.

Record the merge with the existing merge metadata and a message that identifies upstream `v0.12.0` and the semantic 0.8.0 base. Do not squash it and do not use `origin/main` as a content parent.

After recording:

```powershell
$candidate = git rev-parse HEAD
$treeBeforeCleanup = git rev-parse "HEAD^{tree}"
git rev-list --parents -n 1 HEAD
$env:GIT_NO_REPLACE_OBJECTS = "1"
git rev-parse "HEAD^{tree}"
git rev-list --parents -n 1 HEAD
Remove-Item Env:GIT_NO_REPLACE_OBJECTS
```

Expected: exactly two parents, local baseline first and upstream target second; replacement-disabled tree equals the tested tree.

## Phase K — Remove Temporary History Metadata and Re-Prove

Only after Phase J succeeds:

```powershell
git replace -d 93773e055f31ce25bedc30cdc1fe3f73c541a0c7
git replace -l
$treeAfterCleanup = git rev-parse "HEAD^{tree}"
git rev-list --parents -n 1 HEAD
git merge-base --is-ancestor 366cf73 HEAD
git merge-base --is-ancestor 256ed16 HEAD
$treeBeforeCleanup -eq $treeAfterCleanup
git rev-parse backup-before-sync
```

Expected:

- replacement list is empty;
- tree is unchanged;
- both inputs are ancestors;
- recovery remains available.

Re-run structural validation and a focused smoke subset after cleanup. For final confidence, validate a clean checkout or clone that has no local replacement refs.

## Phase L — Cross-Platform and Release Evidence

When the owner authorizes a validation branch, run the exact `.github/workflows/tests.yml` matrix for the candidate tree:

- macOS selected full suite;
- Ubuntu 24.04 selected full suite and installation checks;
- native-Windows unit slices;
- Ubuntu 24.04 under WSL2 selected full suite and integration checks.

Record each job under X1 and run G1 in a job with Claude Code installed. Real Windows 11 MXC x64/ARM64 evidence remains governed by feature 003 under REL1. REL1 remains blocked until implementation exists; after implementation, unavailable host evidence remains pending. Report the integration candidate separately from product-release readiness.

## Phase M — Publication Handoff

Do not merge or pull stale `origin/main` into the corrected candidate through the ordinary merge strategy.

Follow `contracts/publication-decision.md`:

1. default to `hold_local`;
2. preferably publish a validation branch first when collaborator status is unknown;
3. after validation, present tree-preserving corrective history versus lease-protected remote replacement;
4. refresh the remote identity immediately before any approved write;
5. verify the published tree in a replacement-free fetch/clone.

## Expected Final Report

Report independently:

- local candidate revision/tree and parents;
- integration ledger totals and any approved exclusions;
- explicit resolution outcomes;
- I0–I5, G1, D1, H1, X1, REL1, and PUB1 status;
- exact pending platforms/evidence;
- temporary replacement cleanup status;
- recovery branch status;
- publication decision and whether any remote changed.

Do not use “fully validated,” “release ready,” or “published” unless the corresponding predicate in `contracts/validation-evidence.md` passes.
