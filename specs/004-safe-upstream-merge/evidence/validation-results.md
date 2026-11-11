# Validation Results

## Integration Candidate decision (T079)

| Field | Value |
| --- | --- |
| Candidate ID | `orbit-v0.12.0-merge-001` |
| State | `validated_local` |
| Candidate tree | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` |
| Candidate revision | `62552d6d33cb40a07abfd338f5775a5bd604158e` (recorded locally in US4/T084) |
| Local baseline | `366cf73e7e8f4e62e3604613097a00bafab087df` / tree `323afbf24aa42ed55be78d924a6a6da3d2cbfadc` — `verified` |
| Upstream baseline | `256ed1626941982d22c5aee7305f5ed3f9852dc4` (v0.12.0) / tree `34c5b3d9c3bccd121d694f0d14adae8c2dff0538` — `verified` |
| Semantic base | `500d772ae751651c5b6d1f0e2776e7dd5fd3d834` / tree `8f95d0d3a96f3e0c952cf47a293faee69cdee490` — `verified` |
| Version | `0.12.0` |
| Unresolved count | `0` |
| Coverage pending | `0` |
| Integration state | `validated_local` (I0–I5, D1 pass) |
| Release state | `blocked` (REL1) |
| Publication state | `pending`, posture `hold_local` |
| Evidence links | `E-I0-BASELINES` … `E-I5-CLEANUP`, `E-D1-DOCS`, `E-G1-GUARD`, `E-X1-*`, `E-REL1-BLOCKED`, `E-PUB1-HOLD` |

After this decision, the only index changes permitted before recording are final evidence-record
staging; the delta is proven evidence-only in `history-proof.md`.

## Gate summary

| Gate | Status | Blocking scope | Result |
| --- | --- | --- | --- |
| `I0` | `pass` | integration | All baseline commit/tree/recovery/stage-1 identities reconcile; replacement active by design |
| `I1` | `pass` | integration | 92-path ledger complete (71/35/14/92), terminal outcomes only, zero exclusions |
| `I2` | `pass` | integration | Eleven R-* resolutions `verified` against the validated tree |
| `I3` | `pass` | integration | `SAFE_MERGE_STRUCTURAL_OK`: zero unresolved index paths, zero markers, clean diff checks, sources parse, structured files valid, version `0.12.0` |
| `I4` | `pass` | integration | Focused matrices for every invariant passed on the staged candidate |
| `I5` | `pass` | integration | Six modules in separate processes, 298 tests, only documented dependency/platform skips, zero residue |
| `G1` | `pending` | cross_platform | `claude` CLI absent on this host; official `claude plugin test` runs in CI after installation; no pass inferred |
| `D1` | `pass` | integration | Source-backed docs review: zero contradictions remain |
| H1 | `pass` | integration | Merge recorded `62552d6d33cb40a07abfd338f5775a5bd604158e` (tree `8448419b…` = pre-commit staged T2); replacement removed; recovery rehearsal passed (T080) |
| `X1` | `pending` | cross_platform | Candidate-bound macOS/Linux/native-Windows/WSL2 CI requires an owner-approved remote action |
| `REL1` | `blocked` | product_release | Feature-003 implementation and required real-host evidence absent |
| `PUB1` | `pending` | publication | `hold_local`; no remote write authorized |

## Final candidate-bound runs (tree `e90f3edf3a94a29d4c6a47b233a32ff7606e2367`)

Interpreter for the six modules: the disposable dependency-complete virtual environment
`C:\Users\Mohamed\AppData\Local\Temp\opencode\orbit-validate-venv\Scripts\python.exe`, with
`PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, `STAFF_TEST_OCR=0`; each module in its own process.
Logs: `C:\Users\Mohamed\AppData\Local\Temp\opencode\orbit-final-logs\<module>.log`.

| Check | Result | Skips (all documented) | Artifact SHA-256 |
| --- | --- | --- | --- |
| `tests.test_core` | 82 tests OK | 15: POSIX-only fixtures/commands unavailable on Windows | `4aa2b1beeddbab23f54c0581c3511b89e4e2ea2e7c3695d4ff99928b7e729f1a` |
| `tests.test_channels` | 20 tests OK | 0 | `055c65073097bcee78067623dae0581edcd7ef44385e8a78e53663f14bc16303` |
| `tests.test_tools` | 49 tests OK | 7: offline live smoke; POSIX executable/symlink fixtures | `6c741ae301f42391f4bfc54547b0813c20187918b0490afd8f4e9080f08293ad` |
| `tests.test_calls` | 10 tests OK | 0 (audio via fake soundcard; `ResourceWarning`-as-error run passed earlier) | `42042372b8fd68d402135856c872c7ca16916fba4e77d4787effb2d6ff78f58a` |
| `tests.test_platforms` | 106 tests OK | 5: WSL2/macOS-only service and audio paths | `7a98e533efaa16f1035cc1682da4b23dccb7d594b7ec56a3395ba717269a9a70` |
| `tests.test_mxc` | 31 tests OK | 0 (fake executor; not real-host containment evidence) | `0eac3da6f51240e8d945b5895a848510eea651d13a159c0d319e0b5538ed9007` |
| Oracle summary | `SAFE_MERGE_TESTS_OK test_core=82 test_channels=20 test_tools=49 test_calls=10 test_platforms=106 test_mxc=31`; zero residue | — | Session record |
| Structural oracle | `SAFE_MERGE_STRUCTURAL_OK` | — | Session record |

Recorded: 2026-11-11. Zero leaked temp roots after the final runs (before/after residue inventory).

## Representative smoke flows (T092 / SC-006)

Executed against the recorded merge's production sources: since commit `62552d6d33cb40a07abfd338f5775a5bd604158e`
only `specs/004-safe-upstream-merge/**` files changed, so the production tree these flows exercised is exactly the
recorded candidate tree `8448419bfc0790ed74379145222ff2aa51850c1a`. Interpreter: the disposable dependency-complete
virtual environment `C:\Users\Mohamed\AppData\Local\Temp\opencode\orbit-validate-venv\Scripts\python.exe`, with
`PYTHONUTF8=1`. Disposable profile/environment: `STAFFROOM_HOME` pointed at a fresh temp dir for every run; `claude`
resolved to the deterministic fake driver (`tests/fake_claude.py`) launched through a compiled `claude.exe` shim (see
host findings below); no real Claude, no network, no owner data. Transcript:
`C:\Users\Mohamed\AppData\Local\Temp\opencode\orbit-smoke-transcript.txt`.

| Flow | Step | Status | Observed |
| --- | --- | --- | --- |
| Setup/status | `orbit setup --no-start` (the real flow; piped answers) | fail | Blocks forever at the interactive Telegram-token `getpass`; killed by tree at 240 s; evidence-only blocker (below) |
| Setup/status | Disposable-home init replicating setup's post-gate engine calls (registry owner `local-alex`/`Alex`, team `Smoke Team`, `team/ABOUT.md`) | pass | Home initialized; the blocked interactive setup never reached this stage, so the harness performed the identical engine calls it performs after its checks |
| Setup/status | `orbit status` | pass | "Service: stopped (`orbit start`)" |
| Setup/status | `orbit list` | pass | exit 0; empty registry prints nothing |
| Ordinary crew work | `orbit hire --name Tess --role "Research assistant" --scope … --supervisor Alex` | pass | "Hired Tess: /tess. They start within a minute." |
| Ordinary crew work | `orbit run tess "Say hello and list what you can do for me."` (turn 1) | pass | The fake's reply returned verbatim; fake's `calls.jsonl` shows the full contained argv (MXC PreToolUse hook, sandbox blob, denied tools) |
| Main conversation | `orbit run tess "And what files do you see in your workspace?"` (turn 2) | pass | Reply returned; same running conversation (continuity below) |
| Main conversation | `orbit chat tess --show` | pass | Prints the interactive claude command for the same session (`--resume <session id>`, hook and sandbox settings visible) |
| Report delivery/unread | Report job delivery via the report path's `team.feed('tess', 'Tess', owner, …, 'job')` | pass | Delivered to owner Alex |
| Report delivery/unread | `orbit status` | pass | "New from your crew: 1 (orbit inbox)" (the unread banner is printed by `status`, not `list`) |
| Report delivery/unread | `orbit inbox` | pass | Shows the report ("End of day: smoke report delivered."); marks it seen |
| Report delivery/unread | `orbit status` after inbox | pass | Unread banner gone |
| Report delivery/unread | `orbit inbox --all` | pass | Report shown again from history |
| Owner desk | `orbit desk --show` | pass | `claude://code/new?folder=…desk&q=…` link printed |
| Owner desk | `orbit open tess --show` | pass | Exact gate refusal: "Crew member Desktop sessions aren't available on this native Windows PC yet. Use `orbit chat <handle>` for a contained terminal conversation." |

Conversation continuity (the fake's own recording, `calls.jsonl`): exactly 2 conversation calls; call 1 carries
`--session-id <uuid>`, call 2 carries `--resume <the same uuid>`; `employees/tess/state/sessions.json` remembers `main`.
Cleanup proof: disposable home removed, fake-claude dir removed, zero temp/probe residue afterwards, and the real
`~/Staff` was never created or touched.

Host findings recorded as evidence only — production stays untouched so the recorded tree and all bound evidence remain
valid; these feed the REL1 real-host blocker list:

1. Setup blocker: `orbit setup` blocks forever at the interactive Telegram-token `getpass` (orbit, setup flow). The
   prompts before it consume piped answers normally, then `getpass.getpass` on Windows reads the console
   (`msvcrt.getwch`) and can never proceed when stdin is piped. Reproduced three times (600 s, 420 s, 240 s kills,
   unbuffered `-u` showing the exact stall point). A real-host/CI run needs a TTY or a secret-skip path.
2. Claude `.BAT` spawn: `engine.stream` spawning the fake through `claude.bat` fails with cmd.exe's "The filename,
   directory name, or volume label syntax is incorrect." CreateProcess routes a `.BAT` through `cmd.exe /c`, whose
   quoting mangles the inline-JSON `--settings` value (`settings_json`, core/engine.py). Bisected: dropping only
   `--settings` makes the same `.BAT` spawn succeed; the guard probe's simple `claude --version` spawn succeeds. A
   real npm-style `claude.cmd` shim install would hit the same path; the smoke harness therefore launches the fake
   through a compiled `claude.exe` shim that forwards argv verbatim. Feeds REL1 real-host blockers.
3. `mxc.probe()` on this host: discovery ok (`vendor\mxc\wxc-exec.exe`), verdict `usable` in 2.1 s (Windows build
   10.0.26300 ≥ the updated-24H2 gate); all probe cases (positive write, outside-write, denied read, network, timeout)
   behaved as designed on the real sandbox runtime.
4. Minor pre-existing UX gap observed: `orbit open <unknown-handle>` raises a KeyError traceback instead of an
   owner-readable line (`engine.employee` used directly rather than the crew-member lookup).

## Implementation diagnostics (pre-binding history)

| Check | Observed result | Artifact |
| --- | --- | --- |
| T034–T038 focused core selectors | 11 tests, OK | Host console; `DataRoot`, `ScopedUnread`, `StaticContracts` |
| T036–T038 focused platform selectors | 9 tests, OK | Host console; `EmployeeEntryMode`, `PlatformMessagesAndDesk` |
| Core module (system interpreter) | 82 tests, OK, 15 documented skips | `orbit-test-core.txt` |
| Channels module (system interpreter) | 20 tests, OK | `orbit-test-channels.txt` |
| Tools module (system interpreter) | One explicit module skip: missing `requests`/`beautifulsoup4` | Host console |
| Calls module (system interpreter) | 10 tests, OK under `ResourceWarning`-as-error | Host console |
| MXC module (system interpreter) | 31 tests, OK after documented-module import fix | Host console |
| Feature-001 gates | `planning`, `ci`, `phase2`, `phase4`, `phase5`, `phase57`, `phase39`, `full` pass; full selected 44 native-host tests | Host console |
| Feature-002 focused core | 30 tests, OK, 8 POSIX-shim skips | Host console |
| Feature-002 focused platform | 12 tests, OK, 1 POSIX-shim skip | Host console |
| Feature-002 tracked-file scans | No ordinary account-login wording; `api.anthropic.com` only in Cloud Shift connect probe; env/resolve sites match the launch contract | `git grep` session record |
| Guard CLI | Not run: `claude` command is absent | Host command lookup; remains `pending` |
| Service-liveness defect found and fixed | `Service.test_stop_ends_the_background_service` failed in the first full candidate run: on Windows `os.kill(pid, 0)` terminates the target and still "succeeds" on a freshly dead PID, so `service_pid()` could kill the running service and `stop_service_run()` could leave the stale PID file. Fixed with an `OpenProcess`/`GetExitCodeProcess` `pid_alive()` probe in `orbit`; `Service` + `NativeService` (5 tests) and the single stop test pass | Host console plus isolated `os.kill(pid, 0)` semantics probe (child exited 0xC000013A; second probe raised no error) |
| Cleanup-at-exit defect found and fixed | `verify_candidate.py tests` residue check caught leaked temp roots: employee workspaces are real git repositories whose loose objects are read-only, so `shutil.rmtree(ignore_errors=True)` could not delete them on Windows. `tests/_cleanup.py` now clears the read-only attribute and retries; 254 stale roots purged; two full-module reruns and the final oracle run left zero residue | Oracle failure output plus before/after residue inventory |

## Validation evidence records

| Evidence ID | Gate ID | Candidate tree ID | Platform | Check/scenario | Status | Observed | Artifact | Recorded at | Blocking scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `E-I0-BASELINES` | `I0` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Full commit/tree/recovery/replacement/stage-1 identity reconciliation | pass | All identities match `integration-ledger.md`; recovery resolves to `366cf73` | `integration-ledger.md`; `history-proof.md` | 2026-11-11 | integration |
| `E-I1-COVERAGE` | `I1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Regenerate and validate 92 union entries/14 reviews | pass | 92 entries, 71/35/14/92, 0 pending, 0 exclusions | `integration-ledger.md` | 2026-11-11 | integration |
| `E-I2-RESOLUTIONS` | `I2` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Review all eleven R-* decisions | pass | All `verified` against the validated tree | `integration-ledger.md` | 2026-11-11 | integration |
| `E-I3-STRUCTURE` | `I3` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Structural oracle | pass | `SAFE_MERGE_STRUCTURAL_OK` | `verify_candidate.py structural` | 2026-11-11 | integration |
| `E-I4-LAUNCH` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Ordinary/legacy and interactive/unattended launch matrix | pass | Focused core selectors pass in the bound module runs | `test_core.log` | 2026-11-11 | integration |
| `E-I4-SESSIONS` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Main session resume/new/orient/fork/busy cleanup | pass | Focused core selectors pass in the bound module runs | `test_core.log` | 2026-11-11 | integration |
| `E-I4-DATA-ROOT` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Default/custom/inherited Claude data root | pass | `DataRoot` cases pass in the bound module runs | `test_core.log` | 2026-11-11 | integration |
| `E-I4-UNREAD` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Equal-timestamp two-employee CLI/panel scoped unread | pass | `ScopedUnread` cases pass in the bound module runs | `test_core.log` | 2026-11-11 | integration |
| `E-I4-PLATFORM` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | MXC/WSL2 all-entry gate, notifications, argv, desk permissions, service liveness | pass | `EmployeeEntryMode`, `PlatformMessagesAndDesk`, `Service`, `NativeService` pass in the bound module runs | `test_platforms.log` | 2026-11-11 | integration |
| `E-I4-COPY` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Provider-neutral static copy/model-role contract | pass | `StaticContracts` passes in the bound module runs | `test_core.log` | 2026-11-11 | integration |
| `E-I4-CLOUD` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Local hire and Cloud Shift eligibility separation | pass | Feature-002 focused cases pass in the bound module runs | `test_core.log`; `test_platforms.log` | 2026-11-11 | integration |
| `E-I4-DESK` | `I4` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Reports, employee chat and owner desk flows | pass | Core/platform desk cases pass in the bound module runs | `test_core.log`; `test_platforms.log` | 2026-11-11 | integration |
| `E-I5-CORE` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `python -m unittest tests.test_core` (own process) | pass | 82 tests OK, 15 documented skips | `test_core.log` `4aa2b1be…729f1a` | 2026-11-11 | integration |
| `E-I5-CHANNELS` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `python -m unittest tests.test_channels` (own process) | pass | 20 tests OK | `test_channels.log` `055c6507…16303` | 2026-11-11 | integration |
| `E-I5-TOOLS` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `python -m unittest tests.test_tools` (own process, dependency-complete) | pass | 49 tests OK, 7 documented offline/POSIX-fixture skips | `test_tools.log` `6c741ae3…08293ad` | 2026-11-11 | integration |
| `E-I5-CALLS` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `python -m unittest tests.test_calls` (own process) | pass | 10 tests OK | `test_calls.log` `42042372…ff78f58a` | 2026-11-11 | integration |
| `E-I5-PLATFORMS` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `python -m unittest tests.test_platforms` (own process) | pass | 106 tests OK, 5 documented platform skips | `test_platforms.log` `7a98e533…69a9a70` | 2026-11-11 | integration |
| `E-I5-MXC` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `python -m unittest tests.test_mxc` (own process) | pass | 31 tests OK (fake executor only) | `test_mxc.log` `0eac3da6…ed9007` | 2026-11-11 | integration |
| `E-I5-CLEANUP` | `I5` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Temp/recorder/transcript/live-data cleanup | pass | Zero residue before/after the final runs; 254 stale roots purged after the fix | `verify_candidate.py tests` session record | 2026-11-11 | integration |
| `E-G1-GUARD` | `G1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | `claude plugin test` from guard plugin | pending | CLI missing on this host; no pass inferred. CI invokes the official runner after Claude Code installation and asserts exactly ten cases | `.github/workflows/tests.yml` | 2026-11-11 | cross_platform |
| `E-D1-DOCS` | `D1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | host | Source-backed README/SETUP/PRODUCT/workflow review | pass | Version 0.12.0 stated; Desktop gating and blocked release status honest; connection/cost/account wording matches source; zero contradictions found in the final review | `test_core.log` (`StaticContracts`); `test_platforms.log` (docs matrix) | 2026-11-11 | integration |
| `E-H1-HISTORY` | `H1` | `8448419bfc0790ed74379145222ff2aa51850c1a` | host | Two-parent/tree/replacement-free/recovery proof | pass | Merge `62552d6d33cb40a07abfd338f5775a5bd604158e` with parents `366cf73…` + `256ed16…`; recorded tree equals staged T2; identity stable under `GIT_NO_REPLACE_OBJECTS=1`; replacement removed; both inputs ancestors; `SAFE_MERGE_HISTORY_OK` | `history-proof.md`; `verify_candidate.py history` | 2026-11-11 | integration |
| `E-X1-MACOS` | `X1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | macos | macOS workflow job | pending | No candidate-bound remote CI run | workflow URL pending | 2026-11-11 | cross_platform |
| `E-X1-LINUX` | `X1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | linux | Ubuntu 24.04 workflow job | pending | No candidate-bound remote CI run | workflow URL pending | 2026-11-11 | cross_platform |
| `E-X1-WINDOWS` | `X1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | windows_unit | Native-Windows workflow job | pending | Local host evidence passes; exact candidate workflow run absent | workflow URL pending | 2026-11-11 | cross_platform |
| `E-X1-WSL2` | `X1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | wsl2 | Ubuntu 24.04 under WSL2 workflow job | pending | No candidate-bound remote CI run | workflow URL pending | 2026-11-11 | cross_platform |
| `E-REL1-BLOCKED` | `REL1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | not_applicable | Feature-003 implementation/readiness inspection | fail | Required implementation/harness/workflows/evidence validator absent; known P0 paths remain | feature-003 plans and source inspection | 2026-11-11 | product_release |
| `E-PUB1-HOLD` | `PUB1` | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` | not_applicable | Publication decision | pending | `hold_local`; remote still at reviewed `da644db` per read-only `ls-remote`; no remote write authorized | `publication-options.md` | 2026-11-11 | publication |
| `E-SC6-FLOWS` | `SC-006` | `8448419bfc0790ed74379145222ff2aa51850c1a` | host | Five representative smoke flows in a disposable profile/environment (T092; completes T074) | pass | 14 of 15 steps `pass`; setup `fail` (Telegram-token `getpass` blocker, evidence-only); conversation continuity (`--session-id` → `--resume`, same id) and cleanup proven | `orbit-smoke-transcript.txt` | 2026-11-11 | integration |

## Release Compatibility Record (T076)

| Field | Value |
| --- | --- |
| Record ID | `REL-004-001` |
| Candidate tree | `e90f3edf3a94a29d4c6a47b233a32ff7606e2367` |
| `feature_003_status` | `blocked` |
| Known blockers | No `native/orbit-containment-broker/`, no `core/windows_shell_identity.py`, no feature-003 Windows proof harnesses/build workflows/evidence validator; the current hook lacks the planned failure contract; workspace policy remains an authority; malformed/no-decision and gateway pass-through blockers remain |
| Version-line conflict | Feature 004 integrates source `0.12.0`; feature 003 proposed `0.8.0-sec.N`; future release design unresolved |
| Connection-policy conflict | Feature 004 retains accepted provider-neutral pass-through; feature 003 proposed a native restricted relay/empty-source model; future design unresolved |
| Desktop-session conflict | Upstream adds employee app sessions; feature 004 gates them on native Windows pending feature 003 |
| Feature-004 compatibility choices | Keep 0.12.0 source, retain feature-002 ordinary behavior, block native employee Desktop, preserve feature-003 planning |
| REL1 evidence | `E-REL1-BLOCKED` |

This record cannot become `pending_evidence` until the implementation blockers are removed, and cannot
become `ready` until every applicable real-client/real-host architecture gate passes.
