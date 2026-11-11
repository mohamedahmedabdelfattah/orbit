# History and Recovery Proof

## Recovery point

| Field | Value |
| --- | --- |
| Reference | `backup-before-sync` |
| Revision | `366cf73e7e8f4e62e3604613097a00bafab087df` |
| Tree | `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` |
| Local baseline revision/tree | Same as above |
| Verified at | `2026-11-10T20:51:29+02:00` |
| Status | `available` |

The recovery reference remains available and must not be deleted by feature 004.

## Recovery rehearsal (T080)

| Field | Value |
| --- | --- |
| Method | Disposable detached worktree (`git worktree add --detach`) |
| Location | `C:\Users\Mohamed\AppData\Local\Temp\opencode\orbit-recovery-rehearsal` |
| Resolved revision / tree | `366cf73e7e8f4e62e3604613097a00bafab087df` / `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` |
| Checkout status | `git status --porcelain` empty (worktree equals HEAD) |
| Elapsed | 0.77 s (limit: five minutes) |
| Cleanup | Worktree removed; `git worktree list` back to one entry |
| Recorded at | `2026-11-11` |
| Status | `pass` |

## Temporary history metadata

| Field | Value |
| --- | --- |
| Replaced object | `93773e055f31ce25bedc30cdc1fe3f73c541a0c7` |
| Replacement object | `ec2f0c78eafef5dbe06756b2128bf1d8be720678` |
| Replacement tree | `4ad01869a3bab00059b6d7efe7eb0ff1f5fba790` |
| Synthetic parent | `500d772ae751651c5b6d1f0e2776e7dd5fd3d834` |
| Purpose | Make the verified 0.8.0 product relationship visible while forming the merge |
| Cleanup status | Removed after the merge was recorded (T086); `git replace -l` is empty and the replacement-free identity equals the recorded identity |

## Validated-content vs recorded-tree delta

| Field | Value |
| --- | --- |
| Validated content tree (T1) | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` |
| Staged tree with final evidence records (T2) | `8448419bfc0790ed74379145222ff2aa51850c1a` (T083) |
| Delta proof | `git diff --name-only T1 T2` lists exactly five paths, all under `specs/004-safe-upstream-merge/`: the four evidence records and `verify_candidate.py` (the repository-owned oracle) |
| Meaning | The recorded merge tree equals the tree staged immediately before the commit; its product content is exactly the validated content tree plus final evidence-record text |
| Status | `closed` (T083/T084: the merge tree equals T2 exactly) |

## Recorded merge (H1, T084–T086)

| Field | Value |
| --- | --- |
| Revision | `62552d6d33cb40a07abfd338f5775a5bd604158e` |
| Tree | `8448419bfc0790ed74379145222ff2aa51850c1a` |
| Parents (first, second) | `366cf73e7e8f4e62e3604613097a00bafab087df` (local line), `256ed1626941982d22c5aee7305f5ed3f9852dc4` (upstream v0.12.0) |
| Tree equality | Recorded tree equals pre-commit staged tree T2 exactly; verified before any replacement mutation |
| Replacement-disabled identity | `GIT_NO_REPLACE_OBJECTS=1` yields the identical revision/tree/parents |
| Replacement removal | `refs/replace/93773e055f31ce25bedc30cdc1fe3f73c541a0c7` deleted (T086); `git replace -l` empty afterwards; identity unchanged with and without replacement processing |
| Ancestry | Both authoritative inputs are ancestors of the merge (`merge-base --is-ancestor` exit 0) |
| Recovery | `backup-before-sync` still `366cf73e7e8f4e62e3604613097a00bafab087df`; rehearsal passed (T080) |
| Remote | Read-only `ls-remote` reconfirmed `da644db1159d076b8119ad621ba421f2da8ecbe0` after the merge; nothing pushed |
| Topology note | `origin/main` `da644db` is a sibling merge with a stale tree; it was never a content input to this merge |
| Status | `pass` |

## Ref-mutation baseline

At setup, `HEAD`, `backup-before-sync`, `MERGE_HEAD`, and the observed `origin/main` tracking ref were
read only. No remote command was run and no recovery ref changed. Final H1 proof, replacement cleanup,
ancestor checks, and the no-remote-write reconfirmation remain pending until the local merge exists.

**Closed 2026-11-11:** the local merge exists (`62552d6d33cb40a07abfd338f5775a5bd604158e`, tree
`8448419bfc0790ed74379145222ff2aa51850c1a`), the replacement is removed, both inputs are proven
ancestors, recovery is intact, and the remote was only ever read.
