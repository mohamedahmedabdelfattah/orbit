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
| Cleanup status | Active; removal is forbidden until the genuine integration merge is recorded and replacement-disabled tree equality passes |

## Validated-content vs recorded-tree delta

| Field | Value |
| --- | --- |
| Validated content tree (T1) | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` |
| Staged tree with final evidence records (T2) | Recorded after final evidence staging (T083) |
| Delta proof | `git diff --name-only T1 T2` must list only paths under `specs/004-safe-upstream-merge/` (final evidence records and the repository-owned oracle) |
| Meaning | The recorded merge tree equals the tree staged immediately before the commit; its product content is exactly the validated content tree plus final evidence-record text |
| Status | pending T2 |

## Ref-mutation baseline

At setup, `HEAD`, `backup-before-sync`, `MERGE_HEAD`, and the observed `origin/main` tracking ref were
read only. No remote command was run and no recovery ref changed. Final H1 proof, replacement cleanup,
ancestor checks, and the no-remote-write reconfirmation remain pending until the local merge exists.
