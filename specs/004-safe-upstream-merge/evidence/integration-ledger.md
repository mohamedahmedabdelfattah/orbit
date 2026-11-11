# Integration Ledger: Safe Upstream v0.12.0 Synchronization

## Ledger header

| Field | Value |
| --- | --- |
| `candidate_id` | `orbit-v0.12.0-merge-001` |
| `created_at` | `2026-11-10T20:51:29+02:00` |
| `candidate_tree_id` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` (validated content tree; evidence-record staging may add a final delta recorded in `history-proof.md`) |
| `local_revision` / `local_tree` | `366cf73e7e8f4e62e3604613097a00bafab087df` / `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` |
| `upstream_revision` / `upstream_tree` | `256ed1626941982d22c5aee7305f5ed3f9852dc4` / `34c5b3d9c3bccd121d694f0d14adae8c2dff0538` |
| `semantic_base_revision` / `semantic_base_tree` | `500d772ae751651c5b6d1f0e2776e7dd5fd3d834` / `8f95d0d3a96f3e0c952cf47a293faee69cdee490` |
| `local_variant_revision` / `local_variant_tree` | `93773e055f31ce25bedc30cdc1fe3f73c541a0c7` / `4ad01869a3bab00059b6d7efe7eb0ff1f5fba790` |
| `recovery_reference` / resolved IDs | `backup-before-sync` -> local revision/tree above |
| `initial_unmerged_paths` | `README.md`; `core/engine.py`; `core/osinfo.py` |
| `initial_overlap_paths` | The 14-path set under “Regenerated inventories” |
| `temporary_history_metadata` | Replace `93773e0` with synthetic object `ec2f0c78eafef5dbe06756b2128bf1d8be720678`, whose tree is the local-variant tree and parent is `500d772`; active until post-merge proof |

## Baseline references

Commit and tree were resolved independently before admission. A role describes why an identity is
observed; it does not assert content integration merely from ancestry.

| Baseline ID | Revision ID | Tree ID | Version | Role | Verified at | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `local` | `366cf73e7e8f4e62e3604613097a00bafab087df` | `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` | `0.8.0`-era fork | Complete pre-sync local content | `2026-11-10T20:51:29+02:00` | `verified` |
| `upstream` | `256ed1626941982d22c5aee7305f5ed3f9852dc4` | `34c5b3d9c3bccd121d694f0d14adae8c2dff0538` | `0.12.0` | Canonical upstream target | `2026-11-10T20:51:29+02:00` | `verified` |
| `local_product_point` | `93773e055f31ce25bedc30cdc1fe3f73c541a0c7` | `4ad01869a3bab00059b6d7efe7eb0ff1f5fba790` | `0.8.0` | Local product variant; not byte-identical to upstream base | `2026-11-10T20:51:29+02:00` | `verified` |
| `upstream_product_point` | `500d772ae751651c5b6d1f0e2776e7dd5fd3d834` | `8f95d0d3a96f3e0c952cf47a293faee69cdee490` | `0.8.0` | Canonical semantic base | `2026-11-10T20:51:29+02:00` | `verified` |
| `recovery` | `366cf73e7e8f4e62e3604613097a00bafab087df` | `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` | `not_applicable` | `backup-before-sync`; stable recovery route | `2026-11-10T20:51:29+02:00` | `verified` |
| `remote_current` | `da644db1159d076b8119ad621ba421f2da8ecbe0` | `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` | `not_applicable` | Observed fork topology only; stale local tree despite both desired parents | `2026-11-10T20:51:29+02:00` | `verified` |

`origin/main` has parents `366cf73e7e8f4e62e3604613097a00bafab087df` and
`256ed1626941982d22c5aee7305f5ed3f9852dc4`, but its tree equals the local baseline tree. It is not a
content input.

## Initial merge snapshot

The pre-resolution snapshot was captured before source remediation. First-column staged entries were
the automatic merge result; `.specify/feature.json` and feature-004 planning were intentionally
unstaged.

```text
 M .specify/feature.json
UU README.md
M  SETUP.md
M  VERSION
A  core/claudeapp.py
A  core/desk.md
A  core/desk.py
UU core/engine.py
M  core/guard/staff-guard/.claude-plugin/plugin.json
M  core/guard/staff-guard/hooks/register.js
M  core/guard/staff-guard/tests/guard.test.ts
M  core/handbook.md
M  core/hire.py
M  core/jobs/brief.md
M  core/jobs/catchup.md
A  core/jobs/claude_app.md
M  core/jobs/eod.md
M  core/jobs/initiative.md
M  core/jobs/review.md
M  core/jobs/scout.md
M  core/jobs/standup.md
M  core/onboard.py
M  core/orders.py
UU core/osinfo.py
M  core/panel.py
M  core/panel/app.js
M  core/staffd.py
M  core/team.py
M  core/update.py
M  orbit
A  tests/_cleanup.py
M  tests/test_calls.py
M  tests/test_channels.py
M  tests/test_core.py
M  tests/test_platforms.py
M  tests/test_tools.py
?? specs/004-safe-upstream-merge/
```

Expected pre-resolution failures were observed: `git diff --name-only --diff-filter=U` returned the
three paths; markers were at README lines 301/309/314 and engine lines 465/469/474, 722/726/730 and
770/783/807; `core/engine.py` did not parse; and cached diff checking reported the extra blank line at
`core/claudeapp.py:158`. `core/osinfo.py` was marker-free in the worktree but remained `UU` until review.

### Initial index stages

| Path | Stage 1 (semantic base) | Stage 2 (local) | Stage 3 (upstream) |
| --- | --- | --- | --- |
| `README.md` | `d5947e78c5c15058afee26d7ea72bbdaa21eb14f` | `ecc9d23fbdc1e5774176399ecbc79862241c33ac` | `764180b22d1ffb4a789f2a6931cdb472ed415cbe` |
| `core/engine.py` | `bac4258a4d75590d77d78baec3ada13be9264f23` | `efd1d52a86ac036289e8f78e406a18d28c2f77ee` | `ed4eb5a21671dab8270ccd051b7b7ddae2b77ca0` |
| `core/osinfo.py` | `71f94aced6bc2fc9d2ca0c6535ad2a8566dab5ff` | `abc28ab7adfb74777bcdb15aba0b8e1d62cdaf59` | `c36d3cdd10215896dfaf51f84ca9c06732eaa4b6` |

All stage-1 blob IDs independently equal the corresponding `500d772:<path>` blobs. After focused
review, only these three paths were added explicitly; the unmerged path scan and `git ls-files -u` are
now empty.

## Regenerated inventories

`git diff --name-status 500d772 366cf73` and `git diff --name-status 500d772 256ed16` regenerated:

| Set | Count |
| --- | ---: |
| Local changed paths | 71 |
| Upstream changed paths | 35 |
| Changed on both sides | 14 |
| Union | 92 |

The regenerated overlap is exactly:

```text
README.md
SETUP.md
core/engine.py
core/guard/staff-guard/hooks/register.js
core/onboard.py
core/orders.py
core/osinfo.py
core/panel.py
core/panel/app.js
core/staffd.py
core/team.py
orbit
tests/test_core.py
tests/test_platforms.py
```

The local product-point delta `500d772..93773e0` is exactly four modified paths: `README.md` retains
local connection/Cloud Shift wording; `core/grants.py` retains local owner-controlled grants;
`core/staffd.py` retains local scheduler/provider behavior; and `tests/test_platforms.py` retains local
platform/MXC regressions. None is treated as equivalent upstream content.

## Behavioral invariants

| Invariant ID | Name | Reviewable source | Observable statement | Affected paths | Evidence | Scope |
| --- | --- | --- | --- | --- | --- | --- |
| `BI-CONNECTION` | Configured connection | feature 002 contracts | Ordinary work launches Claude directly with its effective configured connection and no provider-specific preflight | `core/engine.py`, `core/onboard.py`, `core/staffd.py` | `E-I4-LAUNCH` | `both` |
| `BI-SETTING-SOURCES` | Setting-source boundary | feature 002 launch contract | Ordinary employee/onboarding use `user,project`/`user`; legacy employee uses `project`; interactive changes no safety source | `core/engine.py`, `core/onboard.py` | `E-I4-LAUNCH` | `both` |
| `BI-WINDOWS-MXC` | Native MXC containment | feature 001 contracts | Native shell-capable work carries the MXC exec-form hook and fails closed | `core/engine.py`, `core/mxc.py`, `tests/test_mxc.py` | `E-I4-PLATFORM`, `E-I5-MXC` | `both` |
| `BI-WSL2-MODE` | Explicit WSL2 fallback | feature 001 contracts | A native process recorded as WSL2 refuses employee work and directs the owner inside WSL | `core/engine.py`, `orbit`, `core/panel.py`, `core/staffd.py` | `E-I4-PLATFORM` | `both` |
| `BI-CLOUD-SHIFT` | Account separation | feature 002 and cloud source | Cloud Shift alone uses qualifying-account evidence; ineligibility never blocks local hire/chat/routines/desk | `core/cloud.py`, `core/orders.py`, `core/panel.py`, `core/panel/app.js` | `E-I4-CLOUD` | `both` |
| `BI-CONVERSATION` | One conversation | upstream tests/source | Routines, chats and follow-ups resume one main session with new-session orientation, rollover, fork and marker cleanup | `core/engine.py`, `core/team.py`, `orbit` | `E-I4-SESSIONS` | `integration` |
| `BI-CONFIG-ROOT` | Effective data root | feature 004 R11 | Transcript, context and window discovery use the exact child `CLAUDE_CONFIG_DIR` without persisting it | `core/engine.py` | `E-I4-DATA-ROOT` | `integration` |
| `BI-ENTRY-MODE` | Shared entry gate | feature 004 R10 | Run, chat, open, panel, app and refresh surfaces enforce one native MXC/WSL2/Desktop decision before setup | `core/engine.py`, `core/claudeapp.py`, `core/panel.py`, `core/staffd.py`, `orbit` | `E-I4-PLATFORM` | `both` |
| `BI-TERMINAL` | Platform-owned argv | feature 004 R12 | Callers pass argv; native Windows starts Python plus Orbit without shell reparsing and displays Windows quoting | `core/osinfo.py`, `core/panel.py`, `orbit` | `E-I4-PLATFORM` | `integration` |
| `BI-REPORT-DESK` | Reports and desk | upstream 0.12 source/tests | Reports reach room/phone/notification; employee/owner chat surfaces retain their platform-appropriate behavior | `core/team.py`, `core/desk.py`, `core/claudeapp.py`, `core/panel.py` | `E-I4-DESK` | `integration` |
| `BI-UNREAD-SCOPE` | Scoped unread | feature 004 R13 | Filtered views advance one employee cursor; full-room views advance global; equal timestamps preserve unseen rows | `core/team.py`, `core/panel.py`, `core/panel/app.js`, `orbit` | `E-I4-UNREAD` | `integration` |
| `BI-NOTIFICATION` | Normalized platform message | merged notify contract | Mac/Linux/native Windows receive the same normalized/truncated body and optional location | `core/osinfo.py`, `core/team.py` | `E-I4-PLATFORM` | `integration` |
| `BI-PROVIDER-COPY` | Provider-neutral ordinary copy | feature 002/004 docs contract | Ordinary UI/docs say configured connection and conditional reported usage; provider/account terms stay at legacy key/Cloud Shift boundaries | `README.md`, `SETUP.md`, `PRODUCT.md`, `core/onboard.py`, `core/panel/app.js` | `E-I4-COPY`, `E-D1-DOCS` | `integration` |
| `BI-TEST-CLEANUP` | Isolated validation | feature 004 R15 | Every module/recorder root and transcript/process residue is removed; no live owner data is used | `tests/_cleanup.py`, `tests/fake_claude.py`, `tests/test_mxc.py` | `E-I5-CLEANUP` | `integration` |
| `BI-DATA` | No owner-data migration | feature 004 spec | Synchronization changes source/evidence only and performs no destructive team/secret/workspace migration | source tree, tests | `E-I0-BASELINES`, `E-I5-CLEANUP` | `both` |
| `BI-PLANNING-STATUS` | Feature-003 remains planning | feature 003 plus REL1 contract | Planning is preserved, native Desktop stays gated, and release status remains blocked rather than claimed ready | `specs/003-close-containment-gaps/**`, `PRODUCT.md`, workflow | `E-REL1-BLOCKED`, `E-D1-DOCS` | `integration` |

## Resolution decisions

All records below are `verified` against the validated content tree
`e90f3edf3a94a29d4c6a47b233a32ff7606e2367`: each focused diff and its passing evidence were rerun on
the fully staged candidate. No rejected alternative is an approved exclusion.

### R-ENGINE-COMMAND

- **Path / region:** `core/engine.py::command`
- **Local intent:** feature 002 launch policy, ordinary/legacy setting sources, full environment policy, platform tool/MXC/guard/MCP controls.
- **Upstream intent:** interactive mode omits print/stream flags and uses `default` unless autonomy requires `bypassPermissions`.
- **Decision:** one command builder; interactive changes only interaction flags while safety/settings remain shared.
- **Rejected:** upstream hard-coded `project`; separate interactive safety policy; local-only headless builder.
- **Invariants / evidence:** `BI-CONNECTION`, `BI-SETTING-SOURCES`, `BI-WINDOWS-MXC`; `E-I4-LAUNCH`, `E-I4-PLATFORM`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-ENGINE-RUN

- **Path / region:** `core/engine.py::run` and conversation helpers.
- **Local intent:** actual Claude result is connection truth; no Anthropic endpoint preflight/replay; native WSL2-mode refusal.
- **Upstream intent:** one session, brain/hands model choice, resume/new fallback, new-session orientation, window wait/fork, persistence and unconditional busy cleanup.
- **Decision:** preserve the upstream lifecycle around the local provider-neutral and platform boundary.
- **Rejected:** restoring `online()`/`wait_online()`; provider wait/replay; dropping conversation continuity.
- **Invariants / evidence:** `BI-CONNECTION`, `BI-CONVERSATION`, `BI-ENTRY-MODE`; `E-I4-LAUNCH`, `E-I4-SESSIONS`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-OSINFO-NOTIFY

- **Path / region:** `core/osinfo.py::notify`.
- **Local intent:** native-Windows tray notification.
- **Upstream intent:** normalized/truncated body, optional `more`, signed Mac notifier, Linux branch and broad subprocess recovery.
- **Decision:** compute one body and pass it to every platform; Windows uses `q(body)`; recover from `OSError`/`SubprocessError`.
- **Rejected:** raw Windows text; platform-specific normalization; dropping a platform.
- **Invariants / evidence:** `BI-NOTIFICATION`; `E-I4-PLATFORM`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-README-COST

- **Path / region:** README cost/account, connection and platform sections.
- **Local intent:** usage limits only when Claude reports them, explicit optional legacy Anthropic key, separate eligible Cloud Shift.
- **Upstream intent:** brain/hands token guidance and 0.12 conversation/desk behavior.
- **Decision:** one provider-neutral ordinary-cost section plus explicit legacy-key and Cloud Shift boundaries; current Desktop/release claims match source.
- **Rejected:** duplicate cost prose; universal subscription claim; omission of upstream model-role guidance.
- **Invariants / evidence:** `BI-PROVIDER-COPY`, `BI-PLANNING-STATUS`; `E-I4-COPY`, `E-D1-DOCS`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-INTERACTIVE-PLATFORM

- **Path / region:** employee launch surfaces in engine, osinfo, claudeapp, desk, panel, staffd and `orbit`.
- **Local intent:** native MXC/explicit WSL2 containment and feature-003 Desktop refusal.
- **Upstream intent:** terminal/app/panel employee chats and owner front desk.
- **Decision:** one gate; MXC allows contained headless/terminal work, WSL2 mode refuses native employee work, native employee Desktop/refresh refuses before files are touched, owner desk gets exact Windows command/path rules, and terminal callers pass argv.
- **Rejected:** uncontained Desktop fallback; POSIX command text on Windows; disabling compatible Mac/Linux/WSL flows.
- **Invariants / evidence:** `BI-WINDOWS-MXC`, `BI-WSL2-MODE`, `BI-ENTRY-MODE`, `BI-TERMINAL`, `BI-REPORT-DESK`; `E-I4-PLATFORM`, `E-I4-DESK`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-CLAUDE-DATA-ROOT

- **Path / region:** `claude_data_root`, transcripts/context/window helpers.
- **Local intent:** preserve arbitrary inherited `CLAUDE_CONFIG_DIR` in the exact child environment.
- **Upstream intent:** conversation rollover and open/idle window discovery.
- **Decision:** all discovery derives from the effective child root, defaulting only when absent; no path is logged/persisted.
- **Rejected:** hard-coded `~/.claude`; stripping or storing the root.
- **Invariants / evidence:** `BI-CONFIG-ROOT`, `BI-CONVERSATION`; `E-I4-DATA-ROOT`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-UNREAD-SCOPE

- **Path / region:** team cursors, panel `/api/seen`, panel client and CLI inbox/chat.
- **Local intent:** retain existing global cursor/state without migration.
- **Upstream intent:** reports/unread counts and filtered employee chat views.
- **Decision:** lazy normalized owner+employee cursors; unread uses newer global/matching cursor; same-timestamp IDs are scope-specific.
- **Rejected:** filtered global clearing; never marking filtered rows; eager schema migration.
- **Invariants / evidence:** `BI-UNREAD-SCOPE`, `BI-REPORT-DESK`; `E-I4-UNREAD`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-PROVIDER-COPY

- **Path / region:** onboarding, panel UI, README, SETUP and PRODUCT.
- **Local intent:** configured-connection ordinary work and account-only Cloud Shift.
- **Upstream intent:** brain/hands model roles and usage UI.
- **Decision:** exact provider-neutral ordinary copy, conditional reported-usage wording, persisted `subscription` treated only as compatibility, legacy key/Cloud Shift retain exact names.
- **Rejected:** global subscription/plan inference; removing model roles; renaming persisted state.
- **Invariants / evidence:** `BI-PROVIDER-COPY`, `BI-CLOUD-SHIFT`; `E-I4-COPY`, `E-D1-DOCS`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-TEST-EVIDENCE

- **Path / region:** Python tests, guard tests and CI workflow.
- **Local intent:** provider-neutral/no-preflight and native containment assertions remain strong.
- **Upstream intent:** brain/orientation/session/desk behavior and guard 1.6.1 commit-message cases.
- **Decision:** reconcile expectations to the combined contract, add data-root/unread/entry/notification/desk matrices, run modules separately, and wire official `claude plugin test` after CLI installation.
- **Rejected:** restoring `engine.online`; weakening hook shape; treating unavailable runner as pass.
- **Invariants / evidence:** all integration invariants; `E-I5-*`, `E-G1-GUARD`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-CLEANUP

- **Path / region:** cleanup helper, fake Claude, MXC/tools/calls tests.
- **Local intent:** no owner-data/test-recorder residue.
- **Upstream intent:** shared transcript/temp cleanup.
- **Decision:** register every module/recorder root, fix documented module import, close file handles, and preserve explicit dependency/platform skips.
- **Rejected:** recorder outside registered roots; broad cleanup of owner paths; hiding missing dependencies as passes.
- **Invariants / evidence:** `BI-TEST-CLEANUP`, `BI-DATA`; `E-I5-CLEANUP`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

### R-RELEASE-STATUS

- **Path / region:** PRODUCT, README, workflow and feature-003 artifacts.
- **Local intent:** retain feature-003 P0 governance and required real-host evidence.
- **Upstream intent:** integrate source version 0.12.0 and app/session additions where compatible.
- **Decision:** source version stays 0.12.0; native Desktop stays gated; docs say release readiness is blocked; feature 003 remains planning-only.
- **Rejected:** calling hosted/fake tests release proof; marking REL1 merely pending; implementing feature 003 inside this merge.
- **Invariants / evidence:** `BI-PLANNING-STATUS`, `BI-WINDOWS-MXC`; `E-REL1-BLOCKED`, `E-D1-DOCS`.
- **Status:** `verified` (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`).

## Change coverage entries (92-path union)

State values are independently derived from each input relative to `500d772`. `absent` means that
side did not change the path. Every outcome is terminal; there are no exclusions and therefore no
owner-approval references.

| Entry | Path | Local | Upstream | Overlap | Risk | Outcome | Resolution IDs | Invariant IDs | Evidence IDs | Rationale | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `C001` | `.github/workflows/tests.yml` | modified | absent | false | evidence | combined | R-TEST-EVIDENCE; R-RELEASE-STATUS | BI-TEST-CLEANUP; BI-PLANNING-STATUS | E-I3-STRUCTURE; E-G1-GUARD; E-D1-DOCS | Retains local matrix/native slices, adds the upstream guard suite runner, and labels real-host proof honestly. | — |
| `C002` | `.gitignore` | modified | absent | false | evidence | retained_local | — | BI-TEST-CLEANUP | E-I1-COVERAGE; E-I3-STRUCTURE | Local ignore rules remain; upstream had no change. | — |
| `C003` | `.specify/feature.json` | added | absent | false | evidence | retained_local | — | BI-PLANNING-STATUS | E-I1-COVERAGE; E-I3-STRUCTURE | Retains the local active-feature mechanism; its feature-004 pointer update is separately reviewed below. | — |
| `C004` | `bin/staff-apify.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C005` | `bin/staff-browse.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C006` | `bin/staff-bus.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C007` | `bin/staff-connectors.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C008` | `bin/staff-docs.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C009` | `bin/staff-fetch.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C010` | `bin/staff-remind.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C011` | `bin/staff-skill.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C012` | `bin/staff-video.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C013` | `bin/staff-watch.cmd` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I5-PLATFORMS | Keeps the local native-Windows gateway shim. | — |
| `C014` | `core/calls.py` | modified | absent | false | control_plane | retained_local | — | BI-DATA | E-I5-CALLS | Retains local cross-platform call/listener behavior; upstream had no change. | — |
| `C015` | `core/claudeapp.py` | absent | added | false | security_session | combined | R-INTERACTIVE-PLATFORM | BI-ENTRY-MODE; BI-REPORT-DESK | E-I4-PLATFORM; E-I4-DESK | Keeps upstream app plans/chats while applying native employee Desktop refusal before setup. | — |
| `C016` | `core/cloud.py` | modified | absent | false | control_plane | retained_local | — | BI-CLOUD-SHIFT; BI-CONNECTION | E-I4-CLOUD | Retains local account-only Cloud Shift implementation, separate from ordinary work. | — |
| `C017` | `core/desk.md` | absent | added | false | control_plane | retained_upstream | — | BI-REPORT-DESK | E-I4-DESK | Keeps upstream front-desk instructions; exact command permissions are enforced by `desk.py`. | — |
| `C018` | `core/desk.py` | absent | added | false | security_session | combined | R-INTERACTIVE-PLATFORM | BI-REPORT-DESK; BI-ENTRY-MODE | E-I4-PLATFORM; E-I4-DESK | Keeps upstream owner desk with exact native-Windows Python+Orbit PowerShell rules and normalized deny paths. | — |
| `C019` | `core/engine.py` | modified | modified | true | security_session | combined | R-ENGINE-COMMAND; R-ENGINE-RUN; R-INTERACTIVE-PLATFORM; R-CLAUDE-DATA-ROOT | BI-CONNECTION; BI-SETTING-SOURCES; BI-WINDOWS-MXC; BI-WSL2-MODE; BI-CONVERSATION; BI-CONFIG-ROOT; BI-ENTRY-MODE | E-I4-LAUNCH; E-I4-SESSIONS; E-I4-DATA-ROOT; E-I4-PLATFORM | Semantic union of local connection/containment and upstream conversations/brain-hands/interactive behavior. | — |
| `C020` | `core/grants.py` | modified | absent | false | security_session | retained_local | — | BI-DATA; BI-WINDOWS-MXC | E-I5-CORE; E-G1-GUARD | Preserves the verified local product-point owner-grant controls. | — |
| `C021` | `core/guard/staff-guard/.claude-plugin/plugin.json` | absent | modified | false | security_session | retained_upstream | R-TEST-EVIDENCE | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-G1-GUARD | Keeps upstream guard version 1.6.1 metadata; official runner evidence remains separately tracked. | — |
| `C022` | `core/guard/staff-guard/hooks/register.js` | modified | modified | true | security_session | combined | R-TEST-EVIDENCE | BI-CONNECTION; BI-WINDOWS-MXC | E-I3-STRUCTURE; E-G1-GUARD | Local provider-neutral usage wording and upstream inert commit-message parsing coexist without weakening deny branches. | — |
| `C023` | `core/guard/staff-guard/tests/guard.test.ts` | absent | modified | false | evidence | retained_upstream | R-TEST-EVIDENCE | BI-WINDOWS-MXC | E-G1-GUARD | Keeps all ten upstream guard cases, including inert versus executable commit-message behavior. | — |
| `C024` | `core/handbook.md` | absent | modified | false | docs_version | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-D1-DOCS | Keeps upstream 0.12 employee operating guidance. | — |
| `C025` | `core/hire.py` | absent | modified | false | control_plane | retained_upstream | R-PROVIDER-COPY | BI-CONVERSATION; BI-PROVIDER-COPY | E-I4-COPY; E-I5-CORE | Keeps additive upstream brain/main-session migration and model-role fields. | — |
| `C026` | `core/jobs/brief.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream routine prompt aligned with one conversation/reporting. | — |
| `C027` | `core/jobs/catchup.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream catch-up prompt. | — |
| `C028` | `core/jobs/claude_app.md` | absent | added | false | control_plane | retained_upstream | — | BI-REPORT-DESK | E-I4-DESK; E-D1-DOCS | Keeps upstream Claude-app routine setup brief on supported platforms. | — |
| `C029` | `core/jobs/eod.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream end-of-day prompt. | — |
| `C030` | `core/jobs/initiative.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream initiative prompt. | — |
| `C031` | `core/jobs/review.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream review prompt. | — |
| `C032` | `core/jobs/scout.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream scout prompt. | — |
| `C033` | `core/jobs/standup.md` | absent | modified | false | control_plane | retained_upstream | — | BI-CONVERSATION; BI-REPORT-DESK | E-I5-CORE; E-D1-DOCS | Keeps upstream standup prompt. | — |
| `C034` | `core/mxc.py` | added | absent | false | security_session | retained_local | R-INTERACTIVE-PLATFORM | BI-WINDOWS-MXC; BI-WSL2-MODE | E-I4-PLATFORM; E-I5-MXC | Preserves the local native-Windows MXC boundary and explicit mode handling. | — |
| `C035` | `core/onboard.py` | modified | modified | true | control_plane | combined | R-ENGINE-COMMAND; R-PROVIDER-COPY | BI-CONNECTION; BI-SETTING-SOURCES; BI-PROVIDER-COPY | E-I4-LAUNCH; E-I4-COPY | Combines local shared launch policy with upstream reusable/normalized interview-card guides. | — |
| `C036` | `core/orders.py` | modified | modified | true | control_plane | combined | R-UNREAD-SCOPE; R-PROVIDER-COPY | BI-CLOUD-SHIFT; BI-CONVERSATION | E-I4-CLOUD; E-I4-SESSIONS | Local hire always completes and fresh eligibility alone enables Cloud Shift; upstream messages use the main conversation. | — |
| `C037` | `core/osinfo.py` | modified | modified | true | security_session | combined | R-OSINFO-NOTIFY; R-INTERACTIVE-PLATFORM | BI-NOTIFICATION; BI-TERMINAL; BI-ENTRY-MODE | E-I4-PLATFORM | Combines native tray delivery with normalized cross-platform body and argv-owned terminal launching. | — |
| `C038` | `core/panel.py` | modified | modified | true | security_session | combined | R-INTERACTIVE-PLATFORM; R-UNREAD-SCOPE; R-PROVIDER-COPY | BI-CONNECTION; BI-CLOUD-SHIFT; BI-ENTRY-MODE; BI-UNREAD-SCOPE; BI-TERMINAL; BI-REPORT-DESK | E-I4-PLATFORM; E-I4-UNREAD; E-I4-CLOUD; E-I4-DESK | Keeps installation-only readiness/Cloud separation and adds gated argv employee/desk sessions plus scoped seen API. | — |
| `C039` | `core/panel/app.js` | modified | modified | true | control_plane | combined | R-INTERACTIVE-PLATFORM; R-UNREAD-SCOPE; R-PROVIDER-COPY | BI-CLOUD-SHIFT; BI-UNREAD-SCOPE; BI-PROVIDER-COPY; BI-REPORT-DESK | E-I4-UNREAD; E-I4-COPY; E-I4-DESK; E-D1-DOCS | Combines local account boundaries with upstream desk/chat/brain-hands UI and employee-scoped seen behavior. | — |
| `C040` | `core/staffd.py` | modified | modified | true | security_session | combined | R-ENGINE-RUN; R-INTERACTIVE-PLATFORM | BI-CONNECTION; BI-CLOUD-SHIFT; BI-CONVERSATION; BI-ENTRY-MODE | E-I4-SESSIONS; E-I4-PLATFORM; E-I5-CORE | Keeps no-preflight scheduling and retry semantics, skips app-owned routines, and gates refresh before workspace changes. | — |
| `C041` | `core/team.py` | modified | modified | true | control_plane | combined | R-UNREAD-SCOPE; R-PROVIDER-COPY | BI-CONNECTION; BI-CONVERSATION; BI-REPORT-DESK; BI-UNREAD-SCOPE | E-I4-SESSIONS; E-I4-UNREAD; E-I4-COPY | Keeps provider-neutral retry/delivery and upstream main-session/report behavior with additive scoped cursors. | — |
| `C042` | `core/update.py` | absent | modified | false | control_plane | retained_upstream | — | BI-DATA | E-I5-PLATFORMS | Keeps upstream update behavior; update tests operate in disposable repositories. | — |
| `C043` | `docs/superpowers/specs/2026-11-06-claude-connection-pass-through-design.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-D1-DOCS | Preserves local accepted connection design evidence. | — |
| `C044` | `docs/wsl2-architecture.md` | added | absent | false | docs_version | retained_local | — | BI-WSL2-MODE | E-D1-DOCS | Preserves local WSL2 architecture documentation. | — |
| `C045` | `install.sh` | modified | absent | false | security_session | retained_local | — | BI-WSL2-MODE; BI-TEST-CLEANUP | E-I3-STRUCTURE; E-X1-LINUX; E-X1-WSL2 | Keeps local install/platform behavior; cross-platform execution remains pending. | — |
| `C046` | `orbit` | modified | modified | true | security_session | combined | R-INTERACTIVE-PLATFORM; R-UNREAD-SCOPE; R-PROVIDER-COPY | BI-CONNECTION; BI-WSL2-MODE; BI-ENTRY-MODE; BI-TERMINAL; BI-UNREAD-SCOPE; BI-REPORT-DESK | E-I4-PLATFORM; E-I4-UNREAD; E-I4-COPY; E-I5-CORE | Combines local platform/readiness commands with upstream chat/open/inbox/desk, applying shared gates and scoped cursors. Integration remediation: Windows process liveness uses `OpenProcess`/`GetExitCodeProcess` (`pid_alive`) because `os.kill(pid, 0)` terminates the target on Windows and would kill the running service during a liveness check. | — |
| `C047` | `PRODUCT.md` | modified | absent | false | docs_version | retained_local | R-PROVIDER-COPY; R-RELEASE-STATUS | BI-PROVIDER-COPY; BI-PLANNING-STATUS | E-D1-DOCS; E-REL1-BLOCKED | Retains local product definition while correcting version, connection roles and blocked release status. | — |
| `C048` | `README.md` | modified | modified | true | docs_version | combined | R-README-COST; R-PROVIDER-COPY; R-RELEASE-STATUS | BI-PROVIDER-COPY; BI-CONVERSATION; BI-REPORT-DESK; BI-PLANNING-STATUS | E-I4-COPY; E-D1-DOCS | Reviewed prose union of local safety/account boundaries and upstream 0.12 behavior, with no native Desktop/release overclaim. | — |
| `C049` | `SETUP.md` | modified | modified | true | docs_version | combined | R-INTERACTIVE-PLATFORM; R-PROVIDER-COPY; R-RELEASE-STATUS | BI-CONNECTION; BI-WSL2-MODE; BI-PROVIDER-COPY; BI-PLANNING-STATUS | E-I4-COPY; E-D1-DOCS | Combines local native/WSL setup and pass-through instructions with upstream app/desk handoff, qualified by platform gate. | — |
| `C050` | `setup-windows.ps1` | added | absent | false | security_session | retained_local | — | BI-WINDOWS-MXC; BI-WSL2-MODE | E-I3-STRUCTURE; E-X1-WINDOWS | Preserves local native-Windows installer; hosted unit evidence cannot satisfy real-host REL1. | — |
| `C051` | `specs/001-windows-mxc-sandbox/checklists/requirements.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 requirement evidence. | — |
| `C052` | `specs/001-windows-mxc-sandbox/contracts/cc-hook.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local MXC hook contract. | — |
| `C053` | `specs/001-windows-mxc-sandbox/contracts/mxc-request.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local MXC request contract. | — |
| `C054` | `specs/001-windows-mxc-sandbox/contracts/service-task.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local Windows service contract. | — |
| `C055` | `specs/001-windows-mxc-sandbox/data-model.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 data model. | — |
| `C056` | `specs/001-windows-mxc-sandbox/GATES.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 gate ledger. | — |
| `C057` | `specs/001-windows-mxc-sandbox/plan.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 plan. | — |
| `C058` | `specs/001-windows-mxc-sandbox/quickstart.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves development validation instructions without treating them as current REL1 proof. | — |
| `C059` | `specs/001-windows-mxc-sandbox/research.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 research. | — |
| `C060` | `specs/001-windows-mxc-sandbox/spec.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 specification. | — |
| `C061` | `specs/001-windows-mxc-sandbox/tasks.md` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves local feature-001 task history. | — |
| `C062` | `specs/001-windows-mxc-sandbox/verify_gates.py` | added | absent | false | evidence | retained_local | — | BI-WINDOWS-MXC | E-I3-STRUCTURE; E-I4-PLATFORM | Preserves the implemented feature-001 validator for candidate-bound reruns. | — |
| `C063` | `specs/002-claude-connection-pass-through/checklists/requirements.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves accepted feature-002 checklist. | — |
| `C064` | `specs/002-claude-connection-pass-through/contracts/claude-launch.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION; BI-SETTING-SOURCES | E-I1-COVERAGE; E-I4-LAUNCH | Preserves the authoritative launch inventory. | — |
| `C065` | `specs/002-claude-connection-pass-through/data-model.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves feature-002 data model. | — |
| `C066` | `specs/002-claude-connection-pass-through/plan.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves feature-002 plan. | — |
| `C067` | `specs/002-claude-connection-pass-through/quickstart.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I4-LAUNCH; E-D1-DOCS | Preserves candidate-focused pass-through validation scenarios. | — |
| `C068` | `specs/002-claude-connection-pass-through/research.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves feature-002 research. | — |
| `C069` | `specs/002-claude-connection-pass-through/spec.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves accepted provider-neutral requirements. | — |
| `C070` | `specs/002-claude-connection-pass-through/tasks.md` | added | absent | false | evidence | retained_local | — | BI-CONNECTION | E-I1-COVERAGE; E-I3-STRUCTURE | Preserves feature-002 implementation history. | — |
| `C071` | `specs/003-close-containment-gaps/checklists/requirements.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves planning-only feature-003 requirements. | — |
| `C072` | `specs/003-close-containment-gaps/contracts/containment-hook.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS; BI-WINDOWS-MXC | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves planned stronger hook/Desktop contract without claiming implementation. | — |
| `C073` | `specs/003-close-containment-gaps/contracts/gateway-invocation.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS; BI-WINDOWS-MXC | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves planned gateway contract and known blocker. | — |
| `C074` | `specs/003-close-containment-gaps/contracts/mxc-runtime.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS; BI-WINDOWS-MXC | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves planned runtime/broker contract. | — |
| `C075` | `specs/003-close-containment-gaps/contracts/readiness-evidence.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves release evidence contract and blocked status. | — |
| `C076` | `specs/003-close-containment-gaps/contracts/trusted-policy.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS; BI-WINDOWS-MXC | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves planned trusted-policy authority rules. | — |
| `C077` | `specs/003-close-containment-gaps/data-model.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves planning-only feature-003 model. | — |
| `C078` | `specs/003-close-containment-gaps/GATES.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves unresolved feature-003 gates. | — |
| `C079` | `specs/003-close-containment-gaps/plan.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves feature-003 plan without executing it here. | — |
| `C080` | `specs/003-close-containment-gaps/quickstart.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves future real-host procedure; no candidate pass is inferred. | — |
| `C081` | `specs/003-close-containment-gaps/research.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves feature-003 findings and known blockers. | — |
| `C082` | `specs/003-close-containment-gaps/spec.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves feature-003 requirements as planning. | — |
| `C083` | `specs/003-close-containment-gaps/tasks.md` | added | absent | false | evidence | retained_local | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-REL1-BLOCKED; E-I3-STRUCTURE | Preserves the unimplemented task inventory. | — |
| `C084` | `tests/_cleanup.py` | absent | added | false | evidence | combined | R-CLEANUP | BI-TEST-CLEANUP; BI-DATA | E-I5-CLEANUP | Keeps upstream shared cleanup and applies it to all module/recorder roots. | — |
| `C085` | `tests/fake_claude.py` | added | absent | false | evidence | retained_local | R-CLEANUP; R-TEST-EVIDENCE | BI-CONNECTION; BI-TEST-CLEANUP | E-I4-LAUNCH; E-I5-CLEANUP | Preserves local deterministic Claude seam with registered sensitive recorder cleanup. | — |
| `C086` | `tests/test_calls.py` | absent | modified | false | evidence | retained_upstream | R-CLEANUP | BI-DATA; BI-TEST-CLEANUP | E-I5-CALLS; E-I5-CLEANUP | Keeps upstream call tests and closes transcript handles so cleanup evidence is warning-free. | — |
| `C087` | `tests/test_channels.py` | absent | modified | false | evidence | retained_upstream | — | BI-REPORT-DESK; BI-DATA | E-I5-CHANNELS | Keeps upstream channel/report tests. | — |
| `C088` | `tests/test_core.py` | modified | modified | true | evidence | combined | R-ENGINE-COMMAND; R-ENGINE-RUN; R-CLAUDE-DATA-ROOT; R-UNREAD-SCOPE; R-PROVIDER-COPY; R-TEST-EVIDENCE | BI-CONNECTION; BI-SETTING-SOURCES; BI-CONVERSATION; BI-CONFIG-ROOT; BI-CLOUD-SHIFT; BI-UNREAD-SCOPE; BI-PROVIDER-COPY; BI-REPORT-DESK | E-I4-LAUNCH; E-I4-SESSIONS; E-I4-DATA-ROOT; E-I4-UNREAD; E-I4-COPY; E-I5-CORE | Reconciles local safety/pass-through tests with upstream conversation/brain/desk tests and adds focused combined-contract cases. | — |
| `C089` | `tests/test_mxc.py` | added | absent | false | evidence | retained_local | R-CLEANUP; R-TEST-EVIDENCE | BI-WINDOWS-MXC; BI-TEST-CLEANUP | E-I5-MXC; E-I5-CLEANUP | Preserves local fake-executor coverage and makes documented module execution import shared cleanup correctly. | — |
| `C090` | `tests/test_platforms.py` | modified | modified | true | evidence | combined | R-OSINFO-NOTIFY; R-INTERACTIVE-PLATFORM; R-PROVIDER-COPY; R-TEST-EVIDENCE; R-CLEANUP | BI-WINDOWS-MXC; BI-WSL2-MODE; BI-ENTRY-MODE; BI-TERMINAL; BI-NOTIFICATION; BI-PROVIDER-COPY; BI-TEST-CLEANUP | E-I4-PLATFORM; E-I4-COPY; E-I5-PLATFORMS; E-I5-CLEANUP | Retains extensive local native/WSL tests, upstream platform features, and adds all-entry/notification/argv/desk/doc matrices with explicit host skips. | — |
| `C091` | `tests/test_tools.py` | absent | modified | false | evidence | retained_upstream | R-CLEANUP; R-TEST-EVIDENCE | BI-DATA; BI-TEST-CLEANUP | E-I5-TOOLS; E-I5-CLEANUP | Keeps upstream toolbelt tests; missing host packages become one explicit dependency skip rather than import failure or fake pass. | — |
| `C092` | `VERSION` | absent | modified | false | docs_version | retained_upstream | R-RELEASE-STATUS | BI-PLANNING-STATUS | E-I3-STRUCTURE; E-D1-DOCS | Keeps upstream source version `0.12.0`, separately from blocked product-release readiness. | — |

Totals: 92 entries; 71 local-present; 35 upstream-present; 14 overlaps; 0 `pending`; 0
`approved_exclusion`; 0 owner approvals required.

## Semantic overlap reviews

| Path | Local diff intent | Upstream diff intent | Candidate semantic review | Resolution / invariants / focused evidence | Outcome |
| --- | --- | --- | --- | --- | --- |
| `README.md` | Provider-neutral connection, conditional usage, explicit key and Cloud Shift boundaries, native platform claims | Brain/hands, one conversation, reports, app chats and desk | One cost section; app behavior is platform-qualified; version/REL1 are honest; no duplicate/contradictory account claim | R-README-COST, R-PROVIDER-COPY, R-RELEASE-STATUS / BI-PROVIDER-COPY, BI-REPORT-DESK / E-I4-COPY, E-D1-DOCS | combined |
| `SETUP.md` | Native/WSL setup, installation-only readiness, complete environment trust disclosure | Claude-app employee/desk handoff | Setup commands remain source-backed; ordinary connection is unchanged; employee Desktop handoff excludes native Windows | R-INTERACTIVE-PLATFORM, R-PROVIDER-COPY / BI-WSL2-MODE, BI-PROVIDER-COPY / E-I4-COPY, E-D1-DOCS | combined |
| `core/engine.py` | Shared launch policy, no preflight, MXC/WSL2 boundaries | Interactive command, brain/hands, one main conversation/window coordination | No duplicate command/run authority; session lifecycle wraps exact local launch policy; effective data root and all-entry gate added | R-ENGINE-COMMAND, R-ENGINE-RUN, R-INTERACTIVE-PLATFORM, R-CLAUDE-DATA-ROOT / BI-CONNECTION, BI-CONVERSATION, BI-ENTRY-MODE / E-I4-LAUNCH, E-I4-SESSIONS, E-I4-DATA-ROOT, E-I4-PLATFORM | combined |
| `core/guard/staff-guard/hooks/register.js` | “Claude usage” provider-neutral comment | Commit messages treated as data unless executable substitution remains | `withoutCommitMessages` feeds existing deny loop only; all deny/masking/grant branches remain single; syntax clean; ten official-runner cases retained | R-TEST-EVIDENCE / BI-CONNECTION, BI-WINDOWS-MXC / E-I3-STRUCTURE, E-G1-GUARD | combined |
| `core/onboard.py` | `launch_policy("onboarding")`, pass-through/legacy sources | Shared ASK/CARD guides and normalized desk-written cards | `_ask` remains the sole Claude launch using policy; upstream normalization follows response; ordinary prompt says configured connection | R-ENGINE-COMMAND, R-PROVIDER-COPY / BI-CONNECTION, BI-SETTING-SOURCES, BI-PROVIDER-COPY / E-I4-LAUNCH, E-I4-COPY | combined |
| `core/orders.py` | Local hire always succeeds; Cloud Shift enables only on fresh eligible account | Panel messages use the one main conversation | Hire occurs before the account-only optional branch; message session key is main; no eligibility leak into local work | R-PROVIDER-COPY / BI-CLOUD-SHIFT, BI-CONVERSATION / E-I4-CLOUD, E-I4-SESSIONS | combined |
| `core/osinfo.py` | Native Windows identity, paths, terminal/platform containment, tray notify | Normalized notify body and Mac/Linux notifier behavior | Windows gets computed body; failures remain best effort; argv display/launch is owned once by platform code | R-OSINFO-NOTIFY, R-INTERACTIVE-PLATFORM / BI-NOTIFICATION, BI-TERMINAL / E-I4-PLATFORM | combined |
| `core/panel.py` | Installation-only readiness and separate Cloud account status | Brain field, unread count, employee/desk sessions | Native WSL2 blocks; MXC panel uses contained terminal argv; Desktop gate remains; optional employee `/api/seen` is validated | R-INTERACTIVE-PLATFORM, R-UNREAD-SCOPE, R-PROVIDER-COPY / BI-ENTRY-MODE, BI-UNREAD-SCOPE, BI-CLOUD-SHIFT / E-I4-PLATFORM, E-I4-UNREAD, E-I4-CLOUD | combined |
| `core/panel/app.js` | Eligibility-only Cloud UI and installed/configured ordinary readiness | Desk/employee session UI, brain/hands, unread UI | Ordinary strings are configured-connection/conditional; scoped chat marks do not zero unrelated counts; native errors come from server gate | R-INTERACTIVE-PLATFORM, R-UNREAD-SCOPE, R-PROVIDER-COPY / BI-PROVIDER-COPY, BI-UNREAD-SCOPE, BI-REPORT-DESK / E-I4-COPY, E-I4-UNREAD, E-I4-DESK | combined |
| `core/staffd.py` | Due work starts without provider preflight; transient results re-arm | App-owned routines skip service and session/desk plans refresh | No `online()` branch restored; app-owned routines are skipped; shared Desktop/mode gate now runs before workspace/plugin/session changes | R-ENGINE-RUN, R-INTERACTIVE-PLATFORM / BI-CONNECTION, BI-CONVERSATION, BI-ENTRY-MODE / E-I4-SESSIONS, E-I4-PLATFORM | combined |
| `core/team.py` | Provider-neutral connection/usage retry words | Main conversation, window wait, room notification and unread | Delivery/retry remains actual-result based; notification adds location; scoped cursors are additive over old global state | R-UNREAD-SCOPE, R-PROVIDER-COPY / BI-CONVERSATION, BI-REPORT-DESK, BI-UNREAD-SCOPE / E-I4-SESSIONS, E-I4-UNREAD | combined |
| `orbit` | Native platform setup/status/sandbox, installation-only readiness | Chat/open/inbox/desk and one-conversation CLI | Chat/open call shared gate; copied commands use platform display; filtered inbox/chat mark only employee; no stale account gate | R-INTERACTIVE-PLATFORM, R-UNREAD-SCOPE, R-PROVIDER-COPY / BI-ENTRY-MODE, BI-TERMINAL, BI-UNREAD-SCOPE / E-I4-PLATFORM, E-I4-UNREAD, E-I4-COPY | combined |
| `tests/test_core.py` | Launch policy/no-preflight/MXC/Cloud separation and extensive local regressions | Brain/session/orientation/unread/app/desk tests | Obsolete `engine.online` assumptions removed; Opus/ORIENT expectations apply only where intended; DataRoot, ScopedUnread and static provider contracts added; `unittest.main()` remains last | R-TEST-EVIDENCE / BI-CONNECTION, BI-CONVERSATION, BI-CONFIG-ROOT, BI-UNREAD-SCOPE / E-I4-*, E-I5-CORE | combined |
| `tests/test_platforms.py` | Native/WSL/MXC/service/call/cloud/platform suite | App/desk/asleep/update additions | Exec hook asserts command+args; native all-entry matrix, notifications, argv, exact desk rules and docs added; POSIX/audio dependencies use explicit platform skips without weakening production checks | R-TEST-EVIDENCE, R-INTERACTIVE-PLATFORM, R-CLEANUP / BI-WINDOWS-MXC, BI-ENTRY-MODE, BI-NOTIFICATION, BI-TEST-CLEANUP / E-I4-PLATFORM, E-I5-PLATFORMS | combined |

No overlap contains duplicate active definitions, an unexplained whole-side choice, or an unapproved
incompatibility. Guard CLI and cross-platform execution remain visible as pending evidence, not content
coverage omissions.

## Feature-004 planned candidate additions

These are deliberate integration records, not part of the 92 historical input-path union:

| Path/group | Purpose | Review status |
| --- | --- | --- |
| `.specify/feature.json` worktree update | Point active feature tooling at feature 004; its historical local add remains `C003` | Reviewed; stage explicitly |
| `specs/004-safe-upstream-merge/spec.md` | Accepted behavior and success criteria | Reviewed |
| `specs/004-safe-upstream-merge/plan.md` | Integration architecture and delivery sequence | Reviewed |
| `specs/004-safe-upstream-merge/research.md` | Source-backed decisions and rejected alternatives | Reviewed |
| `specs/004-safe-upstream-merge/data-model.md` | Closed evidence/runtime entity schemas | Reviewed |
| `specs/004-safe-upstream-merge/quickstart.md` | Maintainer validation/recording sequence | Reviewed |
| `specs/004-safe-upstream-merge/tasks.md` | Dependency-ordered implementation ledger | Reviewed |
| `specs/004-safe-upstream-merge/checklists/requirements.md` | Requirements-quality check | Reviewed |
| `specs/004-safe-upstream-merge/contracts/*.md` | Ledger, validation and publication contracts | Reviewed |
| `specs/004-safe-upstream-merge/GATES.md` | Completion gates for the active task | Reviewed |
| `specs/004-safe-upstream-merge/evidence/*.md` | Candidate-bound integration, validation, history and publication records | Bound to the validated tree; H1 closes after merge recording |
| `specs/004-safe-upstream-merge/verify_candidate.py` | Repository-owned structural/evidence/history oracle | Reviewed; `structural` and `tests` passed on the staged candidate |
| `core/tools/remind.py` | Validation remediation: reminder state read/write now closes its file handles (fixes `ResourceWarning`-as-error evidence) | Reviewed |
| `core/tools/skill.py` | Validation remediation: saved-skill path is reported with `/` separators on every platform instead of native `os.sep` | Reviewed |
| `specs/001-windows-mxc-sandbox/verify_gates.py` | Oracle update: the `ci` gate now requires the workflow to separate hosted unit coverage from required real-host x64/ARM64 evidence and to keep product readiness blocked | Reviewed |
| `tests/test_platforms.py` `NativeService` | Restored fake-only scheduled-task and native-doctor coverage so feature-001's `phase39` oracle selects real tests again | Reviewed |

Final staging uses this ledger's reviewed allowlist and explicit `git add -- <paths>` calls. No
untracked file or exclusion enters implicitly.
