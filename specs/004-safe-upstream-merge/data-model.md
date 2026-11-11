# Data Model: Safe Upstream Synchronization

## Summary

This feature performs no destructive migration of `staff.json`, owner secrets, employee workspaces, sessions, histories, roles, routines, abilities, or grants. Most entities are maintainer-owned integration and evidence records used to prove that two source lines were combined without losing content or weakening behavioral boundaries.

One additive runtime concept is required to preserve upstream unread semantics after the merge: an optional owner+employee seen cursor layered over the existing owner-global cursor in the current team state file. No new runtime file is introduced, and existing global-only state remains valid.

Integration records may be maintained as Markdown tables and source-control identities. They are planning/validation artifacts, not application state consumed by Orbit at runtime.

## Entities

### Baseline Reference

An immutable identity used to define the integration safety envelope.

| Field | Type / values | Validation |
| --- | --- | --- |
| `baseline_id` | `local`, `upstream`, `local_product_point`, `upstream_product_point`, `recovery`, `remote_current` | Unique within the integration |
| `revision_id` | Full source-control object ID | Must resolve to a commit while the integration is active |
| `tree_id` | Full source-tree object ID | Captured independently from the commit ID |
| `version` | Product version or `not_applicable` | `upstream` must be `0.12.0`; corresponding product points must be 0.8.0-era |
| `role` | Human-readable purpose | Must not imply content integration from ancestry alone |
| `verified_at` | Timestamp | Recorded after both commit and tree resolve successfully |
| `verification_status` | `verified`, `mismatch`, `missing` | Only `verified` references may enter a candidate |

Required identities for this integration:

| Baseline ID | Revision | Role |
| --- | --- | --- |
| `local` | `366cf73` | Pre-synchronization local content |
| `upstream` | `256ed16` | Canonical upstream `v0.12.0` target |
| `local_product_point` | `93773e0` | Local 0.8.0-era product point plus local delta |
| `upstream_product_point` | `500d772` | Canonical upstream 0.8.0-era product point |
| `recovery` | `backup-before-sync` resolving to `366cf73` | Stable local recovery point |
| `remote_current` | `da644db` at planning time | Existing fork synchronization with stale content tree |

The remote reference is observational and must be refreshed before publication. The other planning identities remain fixed for feature 004.

### Change Coverage Entry

Accounts for one tracked path or one inseparable path group from both authoritative content inputs.

| Field | Type / values | Validation |
| --- | --- | --- |
| `entry_id` | Stable identifier | Unique and immutable |
| `path` | Repository-relative path or closed path group | Must exist in at least one authoritative input or be a planned evidence artifact |
| `local_state` | `unchanged`, `added`, `modified`, `deleted`, `absent` | Derived relative to the verified product relationship |
| `upstream_state` | Same enum | Derived independently from canonical upstream |
| `risk_tier` | `security_session`, `control_plane`, `docs_version`, `evidence` | Determines review depth |
| `outcome` | `pending`, `retained_local`, `retained_upstream`, `combined`, `approved_exclusion` | Terminal outcomes exclude `pending` |
| `resolution_ids` | Zero or more Resolution Decision IDs | Required for `combined` and conflicting states |
| `invariant_ids` | Zero or more Behavioral Invariant IDs | Required for every high-risk runtime path |
| `evidence_ids` | Zero or more Validation Evidence IDs | At least one passing evidence item required before completion |
| `rationale` | Concise explanation | Required for all outcomes except an identical unchanged path |
| `owner_approval` | Approval reference or empty | Mandatory for `approved_exclusion`; forbidden as an implied/default value |

#### State transitions

```text
pending
  ├──> retained_local
  ├──> retained_upstream
  ├──> combined
  └──> approved_exclusion  (owner approval required)
```

Terminal entries may return to `pending` if a later audit or test contradicts their rationale. An entry can never transition to `approved_exclusion` automatically.

### Resolution Decision

Describes one genuine semantic overlap and the behavior-preserving union selected for it.

| Field | Type / values | Validation |
| --- | --- | --- |
| `resolution_id` | Stable `R-*` identifier | Unique; referenced by the ledger |
| `path` | Repository-relative file | Must be in the candidate |
| `region` | Function, section, or semantic behavior | Specific enough for focused review |
| `local_intent` | Requirement-level outcome | Must cite local evidence/specification |
| `upstream_intent` | Requirement-level outcome | Must cite upstream behavior or tests |
| `decision` | Combined intended behavior | Must preserve both intents or state an owner-approved incompatibility |
| `rejected_alternatives` | One or more alternatives | Includes whole-side selection where it would lose behavior |
| `invariant_ids` | Behavioral invariants protected | Non-empty for runtime resolutions |
| `evidence_ids` | Focused validation records | Must all pass before `verified` |
| `status` | `proposed`, `applied`, `verified`, `blocked` | `verified` requires clean diff and passing focused evidence |

Required resolution records are `R-ENGINE-COMMAND`, `R-ENGINE-RUN`, `R-OSINFO-NOTIFY`, `R-README-COST`, `R-INTERACTIVE-PLATFORM`, `R-CLAUDE-DATA-ROOT`, `R-UNREAD-SCOPE`, `R-PROVIDER-COPY`, `R-TEST-EVIDENCE`, `R-CLEANUP`, and `R-RELEASE-STATUS`, as defined in [plan.md](./plan.md).

### Behavioral Invariant

An outcome from either input line that must remain true in the integrated candidate.

| Field | Type / values | Validation |
| --- | --- | --- |
| `invariant_id` | Stable `BI-*` identifier | Unique |
| `name` | Short behavior name | Clear to a maintainer/reviewer |
| `source` | Specification, contract, test, or authoritative upstream behavior | Must be reviewable |
| `statement` | Observable required behavior | Testable and provider/platform precise where relevant |
| `affected_paths` | Repository-relative paths | Non-empty |
| `evidence_ids` | Validation evidence | At least one terminal passing item before integration completion |
| `release_scope` | `integration`, `product_release`, `both` | Prevents planning-only release gates from being misreported as implemented |

Minimum invariant catalog:

| ID | Invariant | Scope |
| --- | --- | --- |
| `BI-CONNECTION` | Ordinary work uses Claude's effective configured connection with no provider-specific preflight | `both` |
| `BI-SETTING-SOURCES` | Ordinary/legacy and interactive/unattended setting-source boundaries remain correct | `both` |
| `BI-WINDOWS-MXC` | Native Windows shell work remains behind MXC/fail-closed controls | `both` |
| `BI-WSL2-MODE` | WSL2 fallback is explicit and never becomes uncontained native execution | `both` |
| `BI-CLOUD-SHIFT` | Cloud Shift account eligibility remains separate from ordinary local work | `both` |
| `BI-CONVERSATION` | Upstream one-conversation, chat-window coordination, and session continuity remain | `integration` |
| `BI-CONFIG-ROOT` | Conversation/session discovery follows the effective Claude data root without stripping or persisting it | `integration` |
| `BI-ENTRY-MODE` | Every employee launch surface enforces the same native MXC/WSL2 mode boundary | `both` |
| `BI-TERMINAL` | Terminal launch and copied commands use platform-owned argv/quoting | `integration` |
| `BI-REPORT-DESK` | Upstream reports/unread behavior and Claude-app crew/Orbit chats remain | `integration` |
| `BI-UNREAD-SCOPE` | Filtered views clear only the viewed employee while full-room views clear globally | `integration` |
| `BI-NOTIFICATION` | Mac, Linux, and native-Windows notification behavior uses one normalized message | `integration` |
| `BI-PROVIDER-COPY` | Ordinary UI copy describes configured Claude rather than assuming subscription/provider | `integration` |
| `BI-TEST-CLEANUP` | Validation leaves no recorder/temp/transcript/process residue or live owner-data change | `integration` |
| `BI-DATA` | No owner team data or secret migration/loss occurs | `both` |
| `BI-PLANNING-STATUS` | Feature-003 planning evidence is preserved without being claimed as implemented | `integration` |

### Unread Cursor (Additive Runtime State)

Represents how far one owner has actually viewed crew reports. It extends the existing team-state cursor without replacing it.

| Field | Type / values | Validation |
| --- | --- | --- |
| `owner_key` | Normalized owner name | Same normalization as the existing global cursor |
| `scope` | `global` or `employee` | Closed enum |
| `employee_id` | Employee ID or empty | Required only for employee scope; must identify a current or historically known employee |
| `seen_timestamp` | Existing feed timestamp format or empty | Monotonic within this cursor |
| `seen_ids_at_timestamp` | Set/list of feed record IDs | Covers equal-timestamp ordering; IDs must belong to the cursor's scope |

#### Effective cursor rule

For each incoming employee message, unread evaluation uses the newer of:

1. the owner's existing global cursor; and
2. the owner's cursor for that message's employee, when present.

A full team-room/Today view advances only the global cursor. A filtered employee inbox/chat advances only that employee cursor. Therefore viewing one employee clears that employee's viewed messages from global counts without clearing another employee's unseen report.

#### State transitions

```text
no scoped cursor
  -> employee view records scoped cursor
  -> later employee view advances scoped cursor

global cursor advances
  -> all messages at/before global cursor are seen regardless of older scoped cursors
```

Existing state with only global `seen`/same-timestamp IDs is valid. Scoped keys are created lazily, so no eager migration is required.

### Release Compatibility Record

Separates source-integration completion from feature-003 product-release readiness.

| Field | Type / values | Validation |
| --- | --- | --- |
| `record_id` | Stable identifier | One active record per candidate tree |
| `candidate_tree_id` | Tree ID | Must match Integration Candidate |
| `feature_003_status` | `blocked`, `pending_evidence`, `ready` | Current candidate begins `blocked` because implementation is absent |
| `known_blockers` | Closed list of code/evidence blockers | Non-empty while blocked |
| `design_conflicts` | Version-line, connection-policy, and Desktop-session decisions | All three planning-time conflicts remain explicit until later resolution |
| `merge_compatibility_decisions` | Source-version, pass-through, and native-app gate choices | Must match research R16 |
| `evidence_ids` | REL1 evidence | `ready` requires all applicable evidence passing |

This record is not runtime state and does not change application behavior. It prevents preservation of planning files from being reported as implementation or release proof.

### Integration Candidate

Represents the proposed combined source tree and its independent integration/release states.

| Field | Type / values | Validation |
| --- | --- | --- |
| `candidate_id` | Local stable identifier | Unique for one candidate attempt |
| `local_baseline_id` | Baseline Reference | Must be `local` and verified |
| `upstream_baseline_id` | Baseline Reference | Must be `upstream` and verified |
| `tree_id` | Full tree object ID or empty before resolution | Mandatory from `resolved` onward |
| `revision_id` | Full commit ID or empty before local recording | Mandatory from `locally_recorded` onward |
| `version` | `0.12.0` | Exact unless owner approves a fork version |
| `unresolved_count` | Non-negative integer | Must be zero from `resolved` onward |
| `coverage_pending` | Non-negative integer | Must be zero from `validated_local` onward |
| `integration_state` | State machine below | Independent from release readiness |
| `release_readiness` | `not_evaluated`, `pending`, `blocked`, `ready` | Feature-003 and cross-platform release evidence live here |
| `evidence_ids` | Validation evidence | Must satisfy the selected state gate |

#### Integration state transitions

```text
discovered
  -> aligned
  -> resolving
  -> resolved
  -> validated_local
  -> locally_recorded
  -> validated_cross_platform
  -> awaiting_publication
  -> published
```

Any state may transition to `blocked` when evidence fails or an unapproved incompatibility is found. `blocked` returns only to the immediately preceding non-terminal state after the failure is corrected. It never triggers automatic reset, exclusion, or publication.

`locally_recorded` may precede `validated_cross_platform` when remote CI needs a recorded revision, but the candidate cannot be reported feature-complete or published as a release while mandatory evidence is pending. Recording a local candidate does not imply remote publication.

### Validation Evidence

One result from a structural, behavioral, platform, documentation, history, or release gate.

| Field | Type / values | Validation |
| --- | --- | --- |
| `evidence_id` | Stable `E-*` identifier | Unique |
| `gate_id` | Gate from validation contract | Must exist in [contracts/validation-evidence.md](./contracts/validation-evidence.md) |
| `candidate_tree_id` | Tree object ID | Binds evidence to exact content |
| `platform` | `host`, `macos`, `linux`, `wsl2`, `windows_unit`, `windows_mxc_x64`, `windows_mxc_arm64`, `not_applicable` | Explicit; never inferred from success text |
| `check` | Command, scenario, or review ID | Reproducible or reviewable |
| `status` | `pass`, `fail`, `pending`, `not_applicable` | Closed enum |
| `observed` | Result summary | Cannot contain secrets or owner data |
| `artifact` | Log, digest, workflow run, or review reference | Required for `pass` and `fail` |
| `recorded_at` | Timestamp | Required |
| `blocking_scope` | `integration`, `cross_platform`, `product_release`, `publication` | Determines which transition is blocked |

`pending` is not a weaker form of `pass`. Evidence from a different tree, platform, or check cannot satisfy the gate.

### Recovery Point

Represents the preserved route back to pre-synchronization local content.

| Field | Type / values | Validation |
| --- | --- | --- |
| `reference` | Named immutable-enough local reference | Must resolve to local baseline throughout integration |
| `revision_id` | Commit ID | Must equal local baseline revision |
| `tree_id` | Tree ID | Must equal local baseline tree |
| `verified_at` | Timestamp | Rechecked before candidate recording and cleanup |
| `status` | `available`, `missing`, `mismatch`, `owner_released` | Cleanup allowed only after owner release |

The required recovery point is `backup-before-sync`. No implementation task may delete it.

### Publication Decision

Captures the owner's explicit choice after candidate validation.

| Field | Type / values | Validation |
| --- | --- | --- |
| `decision_id` | Stable identifier | Unique |
| `candidate_revision_id` | Locally recorded candidate | Must resolve and match candidate tree |
| `observed_remote_revision` | Remote revision at decision time | Must be refreshed immediately before execution |
| `option` | `hold_local`, `publish_validation_branch`, `append_corrective_history`, `replace_remote_with_lease` | Closed enum |
| `consequences` | Collaborator/history impact | Must be shown before approval |
| `owner_approval` | Explicit approval reference | Required for every option except default `hold_local` |
| `status` | `pending`, `approved`, `executed`, `stale`, `failed` | `stale` when remote changes after approval |
| `result_revision` | Remote revision or empty | Required only after successful execution |

The default record is `pending` + `hold_local`. No source-integration success automatically changes it.

## Relationships

```text
Baseline Reference (local) ---------+
                                     +--> Integration Candidate --> Publication Decision
Baseline Reference (upstream) ------+
                 |                          |
                 +--> Change Coverage Entry+--> Validation Evidence
                              |             |
                              +--> Resolution Decision --> Behavioral Invariant

Recovery Point ---------------------> local baseline and candidate safety envelope

Unread Cursor ----------------------> existing team feed records by employee/timestamp/record ID

Integration Candidate --------------> Release Compatibility Record --> REL1 evidence
```

## Validation Rules

1. Every local and upstream changed path has exactly one Change Coverage Entry.
2. No entry remains `pending` at `validated_local`.
3. Every `approved_exclusion` has explicit owner approval; absence of approval is a blocker.
4. Every high-risk runtime entry links at least one Behavioral Invariant and passing focused evidence.
5. The candidate tree is captured before temporary history metadata is removed and is identical afterward.
6. Integration and product-release readiness are never collapsed into one Boolean.
7. `pending` platform evidence remains visible and blocks only the scope named by its contract.
8. A publication decision becomes `stale` if the observed remote changes before execution.
9. No record stores owner credentials, unrestricted secret values, or live team content.
10. A filtered unread action may advance only its matching employee cursor; a global action may advance the global cursor.
11. `feature_003_status` cannot become `pending_evidence` until required implementation blockers are removed, and cannot become `ready` until REL1 evidence passes.

## Migration

No destructive or eager migration. Integration/evidence records govern source work only. Existing Orbit owner data remains untouched.

The existing team-state file may gain optional employee-scoped seen keys lazily when an owner views a filtered employee feed. Older installations and records with only the global cursor retain their meaning. No feed row, global cursor, employee workspace, session, secret, or registry record is rewritten during upgrade.
