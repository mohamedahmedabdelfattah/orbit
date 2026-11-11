# Contract: Publication Decision for a Stale Ancestry-Only Remote Merge

## Purpose

Define how a validated local integration candidate may be reconciled with the fork remote without silently discarding collaborator work, re-running an unsafe sibling-merge calculation, or rewriting history without explicit owner approval.

Local content integration and remote publication are separate operations. Successful local integration defaults to **no remote mutation**.

## Observed Topology

At planning time:

- local baseline is `366cf73`;
- canonical upstream target is `256ed16`;
- existing `origin/main` is `da644db`;
- `da644db` has parents `366cf73` and `256ed16`;
- `da644db`'s tree equals `366cf73`'s tree, so it records upstream ancestry without upstream content.

The corrected content-integration revision (`F`) will also have parents `366cf73` and `256ed16`, but its tree will contain the validated semantic union. Therefore `F` and `da644db` are sibling merges with the same parents and different trees.

An ordinary recursive/`ort` merge between those siblings is prohibited by this contract. Their multiple best common ancestors create a criss-cross-style calculation that may repeat conflict resolution or interpret omitted upstream content as intentional reversion.

## Preconditions Shared by Every Publication Option

Before any remote write:

1. The integration ledger is complete.
2. The local candidate revision exists and has exactly the two authoritative parents.
3. Temporary replacement metadata has been removed.
4. The candidate tree ID remains identical before and after metadata removal.
5. Required local structural/behavioral evidence passes.
6. Cross-platform evidence is either passing or explicitly recorded as pending under the validation contract; no pending evidence is called passing.
7. A fresh remote read records the exact current remote revision and tree.
8. If the remote no longer equals the revision on which the owner's decision was based, the decision becomes `stale` and no write occurs.
9. The recovery branch remains available.
10. The owner sees collaborator/history consequences and explicitly approves every option except `hold_local`.

## Decision Record

```text
Decision ID: ...
Candidate revision/tree: ...
Observed remote revision/tree and timestamp: ...
Option: hold_local | publish_validation_branch | append_corrective_history | replace_remote_with_lease
Validation summary: ...
Pending evidence: ...
Collaborator/history consequences shown: ...
Owner approval: ...
Status: pending | approved | executed | stale | failed
Result remote revision/tree: ...
```

## Option A — Hold Locally (Default)

**Behavior**: Keep the validated candidate and recovery reference local. Perform no remote write.

**Use when**:

- validation is incomplete;
- collaborator status is unknown;
- branch protection/publication policy is unknown;
- the owner has not chosen a history outcome.

**Approval**: No positive approval required; this is the safe default.

**Result**: Local integration may be recorded, but publication status remains pending.

## Option B — Publish a Validation Branch

**Behavior**: Publish the candidate under a new, non-main reference for review and CI while leaving `origin/main` unchanged.

**Use when**:

- remote CI or collaborator review is required before choosing main-history treatment;
- branch creation is allowed;
- pending platform evidence can run from the validation reference.

**Required controls**:

- explicit owner approval for the remote branch name;
- fresh remote check before write;
- no overwrite of an existing unrelated branch;
- CI evidence bound to the exact candidate tree;
- clear statement that validation-branch success does not itself update main.

**Result**: Safest first remote action when remote status or collaborator impact is uncertain.

## Option C — Append Tree-Preserving Corrective History

**Behavior**: Create a deliberate bridge revision (`R`) with:

- first parent: final validated candidate `F`;
- second parent: the exact freshly observed stale remote tip;
- tree: exactly `F^{tree}`.

This makes the stale remote tip an ancestor of `R`, allowing a normal fast-forward update while preserving every remote commit.

**Use when**:

- remote history must not be rewritten;
- the freshly observed remote still has no unique content beyond the known ancestry-only merge;
- preserving the validated candidate as first-parent history is desired.

**Required controls**:

1. Do not ask the ordinary merge strategy to calculate content between sibling merges.
2. Construct/record the bridge with the candidate tree as an explicit invariant.
3. Verify `R^{tree} == F^{tree}` before any push.
4. Verify the stale remote is an ancestor of `R` and `F` remains its first parent.
5. Stop if the remote has advanced or contains any unique content.
6. Use a normal fast-forward update only.
7. Fetch or clone afterward without local replacement refs and verify the remote tree equals the validated tree.

**Consequences shown to owner**:

- no remote commit disappears;
- existing clones at the stale tip can fast-forward;
- history permanently retains the defective merge plus a corrective bridge;
- future readers need the integration record to understand why two sibling merges exist.

### Simpler non-destructive variant

A single-parent corrective commit on top of the stale remote with tree equal to `F` is allowed only if `F` is retained by a durable separate reference. It simplifies topology but otherwise drops `F` from published ancestry, so the bridge form is preferred when preserving the genuine integration revision matters.

## Option D — Replace the Defective Remote with a Lease

**Behavior**: Replace the exact known stale remote tip with the validated candidate, guarded by an expected-old-revision lease.

**Use when**:

- the owner explicitly chooses the clean topology;
- collaborator, open-review, automation, branch-protection, and audit impacts have been checked;
- no dependent work would be lost or unexpectedly diverge.

**Required controls**:

1. Explicit owner approval naming the exact old and new revisions.
2. Fresh remote read immediately before the write.
3. A lease that fails unless the remote still equals the approved old revision.
4. Optional archival remote reference for the old revision when audit policy requires it.
5. Collaborator communication explaining that existing clones must realign and must not merge the old tip back.
6. Post-write fetch/clone verification of candidate commit, parents, and tree.

**Consequences shown to owner**:

- cleaner main history with one genuine content integration;
- defective merge no longer reachable from main unless archived;
- existing clones/branches at the old tip diverge;
- open work and automation may require repair;
- an old clone can reintroduce the defective sibling merge later.

## Prohibited Publication Operations

- Ordinary merge or pull of stale `origin/main` into `F`.
- `-X ours` as a content-preservation guarantee; it affects conflicting hunks only.
- Unqualified force push.
- Any remote update based on a stale observed remote identity.
- Treating the existing ancestry-only merge as proof that upstream content is present.
- Deleting the recovery reference during publication.
- Publishing while the candidate tree differs from the validated tree.

## Post-Publication Evidence

For any option that writes remotely, record:

- selected option and owner approval;
- old and new remote revision IDs;
- candidate and published tree IDs;
- proof that published tree equals validated tree;
- proof no replacement refs are required to interpret the published revision;
- fresh-clone or replacement-disabled structural validation;
- CI/platform evidence associated with the published tree;
- recovery reference status.

Publication is successful only when the remote tree equals the exact validated tree. History shape alone is not sufficient.
