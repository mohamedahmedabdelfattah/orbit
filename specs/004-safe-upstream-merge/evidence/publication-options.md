# Publication Options

## Current posture

| Field | Value |
| --- | --- |
| Decision ID | `PUB-004-001` |
| Candidate revision/tree | Pending local merge recording |
| Observed remote revision | `da644db1159d076b8119ad621ba421f2da8ecbe0` (planning observation; refresh required before any publication action) |
| Observed remote tree | `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` |
| Option | `hold_local` |
| Owner approval | Not required for `hold_local`; no positive remote-write approval has been given |
| Status | `pending` |
| Result remote revision/tree | Empty; no remote command is authorized |

Read-only refresh `git ls-remote origin refs/heads/main` (2026-11-11): the remote still advertises
`da644db1159d076b8119ad621ba421f2da8ecbe0`, so the reviewed topology observation remains current and
the analysis is not stale. No `fetch` was run; no local or remote ref was mutated.

The integration candidate remains local. This document authorizes no `push`, remote branch creation,
force update, pull, or merge of `origin/main`.

## Available options

| Option | Remote effect | Collaborator/history consequences | Approval |
| --- | --- | --- | --- |
| `hold_local` | None | Local candidate and `backup-before-sync` remain available; remote stays at its observed tip | Safe default; no positive approval required |
| `publish_validation_branch` | Create a new non-main branch at the exact candidate | Enables candidate-bound CI/review without changing main; branch name and absence of collision must be checked | Explicit owner approval required |
| `append_corrective_history` | Create a tree-preserving bridge whose first parent is the candidate and second parent is the freshly observed stale remote, then fast-forward main | Keeps every remote commit, including the defective merge; existing clones can fast-forward; history permanently records both sibling merges and the bridge | Explicit owner approval required |
| `replace_remote_with_lease` | Replace the exact freshly observed stale main tip with the candidate under an expected-old-revision lease | Clean main topology, but existing clones/open branches diverge and can reintroduce the defective merge; collaborator and branch-protection impact must be reviewed | Explicit owner approval naming exact old/new revisions required |

## Prohibited implicit choice

`origin/main` is publication topology only. It is not a content input: its parents are the desired local
and upstream commits, but its tree equals stale local baseline `366cf73`. An ordinary merge or pull of
that sibling merge is prohibited because it can repeat conflict resolution or treat omitted upstream
content as an intentional reversion.

Immediately before any later approved remote write, refresh the remote revision/tree. Any difference
from the revision on which the decision was based makes that decision `stale` and stops execution.
