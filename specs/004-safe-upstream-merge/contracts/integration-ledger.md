# Contract: Integration Ledger and Semantic Resolution

## Purpose

Define the evidence required to claim that local baseline `366cf73` and canonical upstream `256ed16` were combined without silently losing, duplicating, or misclassifying either line's work.

This contract governs a maintainer-owned ledger created during implementation. It is not an Orbit runtime API and contains no owner team data.

## Authoritative Inputs

| Role | Required identity | Contract meaning |
| --- | --- | --- |
| Local baseline | `366cf73` | Complete local content immediately before synchronization |
| Upstream target | `256ed16` | Canonical upstream `v0.12.0` content |
| Upstream semantic base | `500d772` | Canonical 0.8.0-era product point |
| Local product variant | `93773e0` | Local 0.8.0-era tree whose four-path delta from `500d772` remains local work |
| Recovery | `backup-before-sync` -> `366cf73` | Stable pre-synchronization recovery route |
| Observed fork remote | `da644db` at planning time | Publication topology only; never a content input |

The ledger MUST record full commit and tree identities resolved at implementation time. Short IDs above are labels, not sufficient evidence by themselves.

The verified local product variant differs from the upstream semantic base at:

- `README.md`
- `core/grants.py`
- `core/staffd.py`
- `tests/test_platforms.py`

Those differences are local changes and MUST NOT be erased by treating the two 0.8.0-era trees as byte-identical.

## Ledger Header

Every ledger instance starts with:

| Field | Requirement |
| --- | --- |
| `candidate_id` | Stable local identifier for this attempt |
| `created_at` | Timestamp |
| `local_revision` / `local_tree` | Full verified IDs |
| `upstream_revision` / `upstream_tree` | Full verified IDs |
| `semantic_base_revision` / `semantic_base_tree` | Full verified upstream 0.8.0-era IDs |
| `local_variant_revision` / `local_variant_tree` | Full verified local 0.8.0-era IDs |
| `recovery_reference` / resolved IDs | Must match local baseline |
| `initial_unmerged_paths` | Exact list before manual resolution |
| `initial_overlap_paths` | Exact set changed on both input lines |
| `temporary_history_metadata` | Identity and purpose; marked removed only after candidate recording |

At planning time the current merge has 71 local changed paths, 35 upstream changed paths, 14 paths changed by both lines, and a 92-path union relative to the semantic base. Implementation MUST regenerate these counts rather than trusting the planning snapshot. Feature-004 planning/evidence files and the updated active-feature pointer are separately identified as planned candidate additions rather than miscounted as either baseline's historical work.

## Entry Schema

One row is required for every path changed by either authoritative input relative to the semantic base.

| Field | Required content |
| --- | --- |
| `entry_id` | Unique stable identifier |
| `path` | Repository-relative path |
| `local_state` | `unchanged`, `added`, `modified`, `deleted`, or `absent` |
| `upstream_state` | Same closed enum |
| `overlap` | Boolean derived from both states |
| `risk_tier` | `security_session`, `control_plane`, `docs_version`, or `evidence` |
| `outcome` | `pending`, `retained_local`, `retained_upstream`, `combined`, or `approved_exclusion` |
| `resolution_ids` | Resolution records applied, if any |
| `invariant_ids` | Required behavior preserved, if high risk |
| `evidence_ids` | Validation proving the outcome |
| `rationale` | Why the candidate reflects both authoritative inputs |
| `owner_approval` | Mandatory only for an exclusion or incompatible behavior choice |

### Terminal outcome rules

- `retained_local` means upstream has no independent behavior to preserve at that path, or the upstream path is absent and local retention is intentional.
- `retained_upstream` means local has no independent behavior to preserve at that path. It MUST NOT be used merely because upstream is newer.
- `combined` means both lines have intended behavior and the candidate contains a reviewed semantic union.
- `approved_exclusion` requires explicit owner approval and documented consequences. It is never inferred from deletion, an automatic merge, or a passing test.
- `pending` blocks local validation.

## Mandatory Overlap Set

Planning identified these 14 paths as changed on both lines. The implementation ledger MUST include all of them and MUST stop if regeneration produces a different unexplained set:

1. `README.md`
2. `SETUP.md`
3. `core/engine.py`
4. `core/guard/staff-guard/hooks/register.js`
5. `core/onboard.py`
6. `core/orders.py`
7. `core/osinfo.py`
8. `core/panel.py`
9. `core/panel/app.js`
10. `core/staffd.py`
11. `core/team.py`
12. `orbit`
13. `tests/test_core.py`
14. `tests/test_platforms.py`

Only `README.md`, `core/engine.py`, and `core/osinfo.py` are textually unmerged in the current index. The other eleven paths require explicit semantic review precisely because their automatic merge result is not proof of compatibility.

## Resolution Record Schema

Each true semantic overlap uses this structure:

```text
Resolution: R-...
Path / region: ...
Local intent: ... (source evidence)
Upstream intent: ... (source evidence)
Decision: ...
Rejected alternatives: ...
Behavioral invariants: BI-...
Focused evidence: E-...
Status: proposed | applied | verified | blocked
```

### Required resolution records

#### `R-ENGINE-COMMAND`

Must combine:

- local launch-policy setting-source choice, environment policy, platform tool surface, and MXC settings;
- upstream interactive command mode, permission selection, and interactive omission of print/stream-only arguments.

It MUST NOT hard-code project-only setting sources for ordinary pass-through and MUST NOT make interactive mode a separate safety policy.

#### `R-ENGINE-RUN`

Must combine:

- local provider-neutral execution, native-Windows WSL2-mode gate, and process-result failure truth;
- upstream one-running-conversation session selection, job-specific model choice, orientation on new sessions, busy/chat coordination, forked-aside behavior, session memory, and guaranteed marker cleanup.

It MUST NOT restore an `api.anthropic.com` preflight or provider-specific wait/retry before ordinary work.

#### `R-OSINFO-NOTIFY`

Must combine upstream normalized/truncated `body`, optional location context, current Mac notifier, and Linux behavior with local native-Windows tray delivery. All platform branches use the computed `body`. Subprocess failure remains best-effort and non-crashing.

#### `R-README-COST`

Must keep:

- plan limits only when Claude reports them;
- upstream brain/hands token guidance;
- explicit optional Anthropic API-key compatibility wording;
- Cloud Shift as a separate eligibility-gated feature that does not define ordinary local readiness.

The final paragraph cannot duplicate or contradict itself.

#### `R-INTERACTIVE-PLATFORM`

Must prove that one machine-mode boundary governs all employee execution surfaces: unattended run, terminal chat, Claude-app/session opening, panel opening, and refresh/plugin work. Native Windows recorded as WSL2 refuses native-side employee launch. Native MXC terminal chat carries the same PowerShell/MXC/guard/tool policy as unattended work. Native employee Desktop remains gated pending feature 003. The owner desk uses exact platform commands/paths and cannot bypass employee gates.

Terminal opening/display accepts an argv boundary owned by `osinfo`; native Windows MUST NOT receive a POSIX-quoted shell string.

#### `R-CLAUDE-DATA-ROOT`

Must prove transcript lookup, context rollover, window discovery, and idle detection use the effective data root from the exact Claude child environment. An inherited ordinary `CLAUDE_CONFIG_DIR` is preserved but never logged or persisted. Default, custom, legacy/application-owned roots receive focused tests.

#### `R-UNREAD-SCOPE`

Must add lazy owner+employee cursors over the existing global seen cursor. Full-room views mark globally; filtered employee views mark only that employee; unread evaluation applies the newer matching cursor. Existing global-only state must work without migration. Two-employee equal-timestamp cases are mandatory.

#### `R-PROVIDER-COPY`

Must remove universal plan/subscription/provider wording from ordinary onboarding, UI, README, SETUP, and PRODUCT surfaces while keeping brain/hands model roles. Ordinary copy says Claude's configured connection and qualifies usage data when Claude reports it. Only legacy stored-key and Cloud Shift boundaries may use their exact provider/account language.

#### `R-TEST-EVIDENCE`

Must reconcile auto-merged tests with production contracts rather than restore obsolete code: no `engine.online` fixture dependency, upstream brain/ORIENT expectations retained, MXC exec `command`+`args` asserted, final `unittest.main()` placement, new combined-mode/data-root/unread/notification/entry-point matrices, and ten guard tests run via `claude plugin test`.

#### `R-CLEANUP`

Must register `test_mxc` and every fake-Claude recorder under cleanup, remove transcript/temp/process residue, and ensure full inherited environment recordings cannot survive test exit. Python modules run separately. Manual install/OCR smoke uses a disposable profile/environment.

#### `R-RELEASE-STATUS`

Must record feature-003 REL1 as blocked while implementation artifacts are absent and P0 behaviors remain. Current-product docs and workflow comments may not call real-host validation optional/non-gating. The record names the future version-line, connection-policy, and native Desktop design conflicts without solving them inside feature 004.

## Automatic Merge Review Contract

For every automatically combined overlap path, the reviewer records:

1. local and upstream diff summaries relative to the semantic base;
2. symbols, commands, or documentation claims touched by both;
3. whether the merged result creates duplicate definitions, stale branches, lost arguments, contradictory copy, or missing tests;
4. invariant and evidence IDs;
5. terminal outcome and rationale.

Textual cleanliness alone is insufficient. A path cannot be marked terminal until its focused diff and affected behavior are reviewed.

## Candidate Tree Contract

Once all paths are staged and no unmerged entry remains:

1. Record the candidate tree ID before creating the integration revision.
2. Record a genuine two-parent merge with first parent `366cf73` and second parent `256ed16`.
3. Confirm the recorded revision's tree equals the staged candidate tree.
4. Inspect the revision once with replacement handling disabled.
5. Remove the temporary replacement metadata.
6. Confirm the revision's tree and two parent IDs remain unchanged.

The content-integration revision MUST NOT use `da644db` as an input parent. That revision is handled only by the publication contract.

## Completion Predicate

The integration ledger is complete only when:

- every regenerated changed path has exactly one entry;
- both sides' changed-path counts reconcile with the ledger;
- all 14 overlap paths (or the explained regenerated set) have semantic review;
- every entry has a terminal outcome;
- no exclusion lacks explicit owner approval;
- every high-risk entry links passing focused evidence;
- all required resolution records are `verified`;
- no unmerged index path or accidental conflict marker remains;
- the recorded candidate tree survives temporary-history cleanup unchanged.

## Prohibited Shortcuts

- Treating the two 0.8.0-era revisions as identical.
- Choosing all local or all upstream content for a conflicted file without per-behavior review.
- Treating an automatic merge as a terminal ledger outcome without semantic review.
- Using the stale remote merge as a content baseline.
- Broadly staging unrelated worktree content without reviewing the exact path set.
- Counting an unavailable platform or release gate as passing.
- Deleting the recovery reference as part of integration completion.
