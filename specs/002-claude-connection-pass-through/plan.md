# Implementation Plan: Claude Connection Pass-Through

**Feature**: `002-claude-connection-pass-through` — [spec.md](./spec.md)

**Status**: Plan complete — refined after specification analysis

**Branch**: `main` (planning worktree detached from `main`)

## Technical Context

| Dimension | Decision | Notes |
| --- | --- | --- |
| Runtime | Python 3.9-compatible; plain browser JavaScript; no new dependency | Matches current Orbit runtime. |
| Integration boundary | Installed unmodified Claude Code CLI/application | Claude owns auth, provider, gateway, model resolution, and inference. |
| General readiness | Executable resolution plus version command | No Claude-account or provider probe. |
| Launch classification | Installation, ordinary pass-through, legacy API-key, interactive application, or Cloud Shift | Every production Claude invocation resolves to exactly one class per execution; conditional shared sites (L02–L04) list their permitted class pairs in the launch contract. |
| Settings | `user,project` for employee runs; `user` for onboarding outside legacy API-key mode; none for Cloud Shift checks/launches | Exact user pass-through chosen despite trusted hook/plugin expansion, in ordinary sessions only; legacy isolated sources remain. |
| Environment | Preserve the complete inherited process environment (documented trust decision); remove only `CLAUDECODE`; overlay the enumerated Orbit-owned values | Legacy Orbit API-key mode keeps its current prefix-filter isolation. Unrelated inherited values reach Claude by design and are disclosed in docs (FR-025). |
| Connectivity | No hard-coded Anthropic preflight for ordinary work | Actual Claude invocation is source of truth. |
| Cloud Shift eligibility | Account-only status may be cached for read-only display for at most 60 seconds | Enablement, new-hire defaulting, and every local cloud launch force a fresh check. |
| Cloud Shift environment | Explicit minimal platform bootstrap allowlist; empty user setting sources | Unknown inherited variables are excluded by default, not by recognized provider prefixes. |
| Diagnostics | Preserve process classification and Claude output behavior without copying inherited values into Orbit metadata | Tests distinguish Orbit-generated records from Claude-generated output. |
| Storage | No schema or migration | Existing team data and `staff.json.auth` retained. |
| Tests | `unittest` with fake Claude, launch inventory, argv/env logs, socket traps, lifecycle transitions, and static tracked-file scans | No real inference needed in CI. |
| CI platforms | macOS, Ubuntu 24.04, native Windows unit coverage, and Ubuntu 24.04 under WSL2 | Matches `.github/workflows/tests.yml`; native MXC runtime remains outside this feature. |

**Constitution check**: `.specify/memory/constitution.md` does not exist. No project constitution constraints apply.

## Architecture Decisions

Full rationale: [research.md](./research.md). Transient state model: [data-model.md](./data-model.md). Launch contract: [contracts/claude-launch.md](./contracts/claude-launch.md). Validation guide: [quickstart.md](./quickstart.md).

1. **Claude configuration is trusted external state.** Orbit no longer models providers. User hooks/plugins may load because exact manual-Claude behavior was selected.
2. **One small launch-policy seam.** `core/engine.py` centralizes pass-through versus legacy API-key environment and setting-source choices. Callers consume that policy instead of repeating prefix filters. The enumerated Orbit-owned overlay keys are listed in the launch contract, and conditional shared launch sites resolve to exactly one class per execution.
3. **Command-line safety remains authoritative where supported.** Existing inline sandbox settings, explicit deny rules, guard/plugin dirs, strict MCP, workspace, prompts, model, effort, and session flags stay unchanged.
4. **Optimistic execution replaces endpoint guessing.** Chats and schedules start Claude directly. Claude errors drive transient classification and later routine retry.
5. **Cloud Shift is not general Claude work.** It keeps a sanitized account-only environment and gains a real eligibility check before controls or defaults claim it works.
6. **No connection persistence.** Orbit does not copy shell exports or Claude settings. Owners configure unattended Claude through persistent Claude/OS mechanisms.
7. **No routing claims.** UI and docs report only Claude availability and actual run success, never provider or locality.
8. **Every Claude invocation is classified.** The launch contract inventories all production invocation sites. A regression check rejects a new direct invocation until it is assigned to one behavioral class.
9. **Cloud eligibility caches are advisory.** Read-only status may cache for at most 60 seconds. Manual enablement, new-hire auto-enablement, and every Orbit-initiated Cloud Shift CLI launch bypass the cache. An enabled shift that loses eligibility remains configured but local cloud operations fail with an account-only reason; ordinary work remains available.
10. **Account isolation uses construction, not subtraction.** Cloud account checks and launches start from a documented platform bootstrap allowlist. They never clone the ordinary pass-through environment and try to remove recognized provider prefixes.
11. **Diagnostics preserve provenance.** Orbit-generated state and metadata never copy inherited credential values. Claude stdout/stderr retains existing handling, so tests use a non-echoing fake when asserting Orbit-originated non-serialization.
12. **Repository copy checks are tracked-file checks.** Validation scans production, setup, template, CI, and documentation files. Only historical specifications, test fixtures, and exact Cloud Shift account-only wording are excluded.

## Planned Code Surfaces

| Surface | Planned change |
| --- | --- |
| `core/engine.py` | Central launch env/source policy; preserve ordinary connection config; retain API-key isolation and setting sources; remove ordinary Anthropic preflight/wait; provider-neutral errors; keep logs free of copied env data. |
| `core/onboard.py` | Use shared launch policy; load user settings for structured hiring; generic policy wording. |
| `core/staffd.py`, `core/team.py` | Dispatch model-backed due work without an Anthropic-host precheck; rely on existing transient retry callback; generalize plan-only comments. |
| `orbit` | Make Claude check installation/version-only; remove account gate/copy. |
| `core/panel.py` | Replace account readiness cache/checklist with Claude installation availability; expose Cloud Shift availability separately. |
| `core/panel/app.js` | Provider-neutral Claude/status/budget copy; do not promise Cloud Shift when ineligible. |
| `core/cloud.py`, `core/orders.py` | Read-only eligibility cache; forced fresh checks for state-changing/launch paths; allowlisted account environment; loss-of-eligibility errors; prevent ineligible default-on behavior. |
| `core/guard/staff-guard/hooks/register.js` | Generalize non-cloud plan-usage comments without changing hook behavior. |
| `install.sh`, `setup-windows.ps1`, `SETUP.md`, `README.md` | Remove paid-account prerequisite; explain external persistent Claude config and trusted user customizations. |
| `tests/test_core.py`, `tests/test_platforms.py` | Complete launch inventory, signed-out end-to-end flow, pass-through/legacy matrices, no-preflight behavior, diagnostic provenance, Cloud Shift lifecycle, and unknown-sentinel isolation. |
| Repository tracked files | Static stale-copy, direct-launch, preflight, provider-filter, and forbidden-provider-artifact checks with explicit exceptions. |

## Phase 0: Research

Resolved in [research.md](./research.md):

- Claude auth methods and provider ownership.
- Settings-source behavior and user-config trust expansion.
- Service environment persistence limits.
- Legacy API-key compatibility.
- Provider-neutral execution/error behavior.
- Account-only Cloud Shift boundary.
- Exhaustive production Claude launch classification.
- Cloud eligibility freshness and loss-of-eligibility transitions.
- Platform bootstrap allowlist for account-only commands.
- Orbit-generated versus Claude-generated diagnostic provenance.
- Repository-wide tracked-file validation and supported CI matrix.

No `NEEDS CLARIFICATION` items remain.

## Phase 1: Launch Inventory and Policy Foundation

- Inventory every production Claude invocation and assign one behavioral class in [contracts/claude-launch.md](./contracts/claude-launch.md).
- Define the source-level regression guard that rejects an unclassified direct Claude invocation, then activate it after all launch-site migrations are complete.
- Add tests for ordinary pass-through, unknown inherited sentinels, Orbit overrides, and legacy API-key isolation before changing production code.
- Add a small shared launch-policy helper in `core/engine.py`; do not add a provider module.
- Keep stored-key employee and onboarding setting sources isolated as explicit legacy behavior.
- Preserve all current Orbit safety arguments and assert them after the change.

## Phase 2: Account-Free Setup and Status

- Replace global account status checks with executable/version availability.
- Update setup, doctor, checklist, and Settings response/copy.
- Keep account status logic only behind the Cloud Shift boundary.

## Phase 3: Exact Connection Pass-Through

- Route employee, onboarding, summary, role-processing, chat, routine, follow-up, and guard-plugin administration paths through their assigned launch policy.
- Use `user,project` for employee work and `user` for structured onboarding outside legacy API-key mode.
- Preserve arbitrary inherited values by default, remove only `CLAUDECODE`, and overlay exactly the enumerated Orbit-owned runtime/safety values from the launch contract.
- Run one signed-out fake-Claude flow through setup, structured hiring, and an employee task using one temporary Orbit home.

## Phase 4: Provider-Neutral Execution and Diagnostics

- Remove `api.anthropic.com` gating from employee runs and scheduled dispatch.
- Preserve current resume/new-session safeguards while removing endpoint-based waiting/replay; never add Orbit provider fallback.
- Generalize auth/network/rate-limit messages and routine failure reasons while retaining existing process classification and Claude-output logging.
- Prove Orbit-generated run records, activity data, panel responses, registry data, and employee files never copy inherited credential sentinels.

## Phase 5: Cloud Shift Boundary

- Construct account-only environments from the platform bootstrap allowlist in the launch contract; omit every unlisted inherited value and disable user setting sources.
- Add an account-specific eligibility result with a maximum 60-second read-only display cache.
- Force fresh eligibility for manual enablement, new-hire auto-enablement, and every Orbit-initiated Cloud Shift CLI launch.
- Cover `none`, `third_party`, `api_key`, `api_key_helper`, `oauth_token`, qualifying `claude.ai`, and eligible-to-ineligible transitions.
- Keep an enabled shift configured after eligibility loss, but block subsequent local cloud operations and expose an account-only reason; do not affect ordinary work.
- Render Cloud Shift promises and controls only when eligible; otherwise show the optional account requirement.

## Phase 6: Documentation and Regression

- Rewrite installation requirements and assisted setup instructions.
- Explain persistent service configuration, trusted user hooks/plugins, and non-guarantees.
- Run targeted and full suites on macOS, Ubuntu 24.04, native Windows unit coverage, and WSL2 CI jobs.
- Run tracked-file static checks from [quickstart.md](./quickstart.md), including exact Cloud Shift wording exceptions.

## Requirement Coverage

| Requirements | Planned evidence |
| --- | --- |
| FR-001–004 | Setup/version tests; panel/checklist snapshots; installer/docs checks |
| FR-005–012 | Launch-policy unit tests; command argv/env assertions; legacy API-key regression |
| FR-013–016 | Socket trap; engine/staffd tests; generic error assertions |
| FR-017–019 | Fresh-versus-cached eligibility matrix; manual/new-hire/launch enforcement; account-env allowlist; eligibility-loss transition |
| FR-020–025 | Provenance-aware registry/file/activity/log/UI leak checks; no-schema diff; tracked-file documentation review |
| SC-001–009 | [quickstart.md](./quickstart.md) scenarios A–K |

## Risks

| Risk | Mitigation / accepted boundary |
| --- | --- |
| User hook/plugin executes outside Orbit's intended worker controls | Explicitly accepted owner-trust boundary; disclose in setup docs; keep Orbit CLI controls and guard. |
| User permission/plugin settings widen employee capabilities | Preserve explicit deny rules, strict MCP, sandbox, and tests; document that arbitrary owner extensions remain trusted. |
| Inherited provider credential reaches Claude-launched subprocess | Do not deliberately serialize it; disclose Claude owns subprocess credential and error behavior. Stronger isolation is out of scope. |
| Terminal-only gateway export disappears after reboot | Document persistent user/managed settings or OS service environment requirement. |
| Legacy stored API key gets rerouted by new user settings | Conditional legacy path keeps provider scrub and isolated setting sources. |
| Third-party connection is mistaken for Cloud Shift eligibility | Separate sanitized account check; eligibility matrix tests. |
| A future provider variable bypasses account isolation | Cloud account environment is built from an allowlist; arbitrary unknown sentinels are absent by default. |
| A cached qualifying status authorizes a later state change | Cache is read-only and bounded to 60 seconds; enablement, auto-enablement, and launches force refresh. |
| An enabled shift loses account eligibility | Keep configuration visible, block subsequent Orbit-initiated cloud commands, store/display the account-only reason, and leave local work untouched. Remote schedules already running while Orbit is offline remain an external account behavior Orbit cannot retroactively revoke. |
| A new Claude subprocess bypasses policy | Inventory all current call sites and fail a source-level regression check on an unclassified direct invocation. |
| A credential sentinel appears because fake Claude echoes it | Separate Orbit-originated non-serialization assertions from a dedicated Claude-output compatibility test. |
| Removing network preflight causes one failed invocation while offline | Existing transient result/retry path handles it; avoids blocking healthy alternative connections. |
| User settings choose incompatible model mapping | Keep existing model alias contract; surface Claude's provider-neutral failure. |
| UI implies locality or no fallback | Prohibit such claims in copy/tests. |

## Non-deliverables

- No `core/inference.py` or provider abstraction.
- No provider UI, endpoint field, credential field, relay, discovery, readiness matrix, or local-model qualification.
- No team-data migration or provider run binding.
- No Claude Desktop configuration editing or comparison.
- No guarantee that Orbit can revoke an already-scheduled remote Cloud Shift while this computer is offline or after local account access has already disappeared.

## Post-Design Constitution Check

`.specify/memory/constitution.md` remains absent. The refined design introduces no constitution gate and no unresolved `NEEDS CLARIFICATION` item.
