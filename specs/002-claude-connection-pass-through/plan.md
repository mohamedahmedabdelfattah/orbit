# Implementation Plan: Claude Connection Pass-Through

**Feature**: `002-claude-connection-pass-through` — [spec.md](./spec.md)

**Status**: Plan complete

**Branch**: `main` (planning worktree detached from `main`)

## Technical Context

| Dimension | Decision | Notes |
| --- | --- | --- |
| Runtime | Python 3.9-compatible; plain browser JavaScript; no new dependency | Matches current Orbit runtime. |
| Integration boundary | Installed unmodified Claude Code CLI/application | Claude owns auth, provider, gateway, model resolution, and inference. |
| General readiness | Executable resolution plus version command | No Claude-account or provider probe. |
| Settings | `user,project` for employee runs; `user` for onboarding | Exact user pass-through chosen despite trusted hook/plugin expansion. |
| Environment | Preserve inherited connection values; remove only recursion marker; overlay Orbit values | Legacy Orbit API-key mode keeps current isolation. |
| Connectivity | No hard-coded Anthropic preflight for ordinary work | Actual Claude invocation is source of truth. |
| Cloud Shift | Separate account-only eligibility and sanitized launch path | Third-party/local work does not imply cloud eligibility. |
| Storage | No schema or migration | Existing team data and `staff.json.auth` retained. |
| Tests | `unittest` with fake Claude, argv/env logs, socket traps, and existing regression suites | No real inference needed in CI. |

**Constitution check**: `.specify/memory/constitution.md` does not exist. No project constitution constraints apply.

## Architecture Decisions

Full rationale: [research.md](./research.md). Launch contract: [contracts/claude-launch.md](./contracts/claude-launch.md).

1. **Claude configuration is trusted external state.** Orbit no longer models providers. User hooks/plugins may load because exact manual-Claude behavior was selected.
2. **One small launch-policy seam.** `core/engine.py` centralizes pass-through versus legacy API-key environment and setting-source choices. Callers consume that policy instead of repeating prefix filters.
3. **Command-line safety remains authoritative where supported.** Existing inline sandbox settings, explicit deny rules, guard/plugin dirs, strict MCP, workspace, prompts, model, effort, and session flags stay unchanged.
4. **Optimistic execution replaces endpoint guessing.** Chats and schedules start Claude directly. Claude errors drive transient classification and later routine retry.
5. **Cloud Shift is not general Claude work.** It keeps a sanitized account-only environment and gains a real eligibility check before controls or defaults claim it works.
6. **No connection persistence.** Orbit does not copy shell exports or Claude settings. Owners configure unattended Claude through persistent Claude/OS mechanisms.
7. **No routing claims.** UI and docs report only Claude availability and actual run success, never provider or locality.

## Planned Code Surfaces

| Surface | Planned change |
| --- | --- |
| `core/engine.py` | Central launch env/source policy; preserve ordinary connection config; retain API-key isolation; remove ordinary Anthropic preflight/wait; provider-neutral errors/comments. |
| `core/onboard.py` | Use shared launch policy; load user settings for structured hiring; generic policy wording. |
| `core/staffd.py`, `core/team.py` | Dispatch model-backed due work without an Anthropic-host precheck; rely on existing transient retry callback; generalize plan-only comments. |
| `orbit` | Make Claude check installation/version-only; remove account gate/copy. |
| `core/panel.py` | Replace account readiness cache/checklist with Claude installation availability; expose Cloud Shift availability separately. |
| `core/panel/app.js` | Provider-neutral Claude/status/budget copy; do not promise Cloud Shift when ineligible. |
| `core/cloud.py`, `core/orders.py` | Cached account-only eligibility; keep cloud launch isolated; prevent ineligible default-on behavior. |
| `core/guard/staff-guard/hooks/register.js` | Generalize non-cloud plan-usage comments without changing hook behavior. |
| `install.sh`, `setup-windows.ps1`, `SETUP.md`, `README.md` | Remove paid-account prerequisite; explain external persistent Claude config and trusted user customizations. |
| `tests/test_core.py`, `tests/test_platforms.py` | Launch matrix, setup, no-preflight, error, cloud-boundary, and legacy regressions. |

## Phase 0: Research

Resolved in [research.md](./research.md):

- Claude auth methods and provider ownership.
- Settings-source behavior and user-config trust expansion.
- Service environment persistence limits.
- Legacy API-key compatibility.
- Provider-neutral execution/error behavior.
- Account-only Cloud Shift boundary.

No `NEEDS CLARIFICATION` items remain.

## Phase 1: Launch Policy Foundation

- Add tests for pass-through and legacy API-key environments before changing production code.
- Add a small shared launch-policy helper in `core/engine.py`; do not add a provider module.
- Switch employee and onboarding command construction to explicit source policies.
- Preserve all current Orbit safety arguments and assert them after the change.

## Phase 2: Account-Free Setup and Status

- Replace global account status checks with executable/version availability.
- Update setup, doctor, checklist, and Settings response/copy.
- Keep account status logic only behind the Cloud Shift boundary.

## Phase 3: Provider-Neutral Execution

- Remove `api.anthropic.com` gating from employee runs and scheduled dispatch.
- Preserve current resume/new-session safeguards while removing endpoint-based waiting/replay; never add Orbit provider fallback.
- Generalize auth/network/rate-limit messages and routine failure reasons.

## Phase 4: Cloud Shift Boundary

- Add a cached account-specific status helper using sanitized environment/settings.
- Make `cloud.available()` require a qualifying account method.
- Ensure new hires do not default Cloud Shift on when ineligible.
- Render Cloud Shift promise/control only when eligible; otherwise show optional account requirement.

## Phase 5: Documentation and Regression

- Rewrite installation requirements and assisted setup instructions.
- Explain persistent service configuration, trusted user hooks/plugins, and non-guarantees.
- Run targeted and full suites on supported CI platforms.
- Run static copy/config searches from [quickstart.md](./quickstart.md).

## Requirement Coverage

| Requirements | Planned evidence |
| --- | --- |
| FR-001–004 | Setup/version tests; panel/checklist snapshots; installer/docs checks |
| FR-005–012 | Launch-policy unit tests; command argv/env assertions; legacy API-key regression |
| FR-013–016 | Socket trap; engine/staffd tests; generic error assertions |
| FR-017–019 | Cloud eligibility matrix; new-hire and enablement tests |
| FR-020–025 | Env/log/UI leak checks; no-schema diff; documentation review |
| SC-001–008 | [quickstart.md](./quickstart.md) scenarios A–H |

## Risks

| Risk | Mitigation / accepted boundary |
| --- | --- |
| User hook/plugin executes outside Orbit's intended worker controls | Explicitly accepted owner-trust boundary; disclose in setup docs; keep Orbit CLI controls and guard. |
| User permission/plugin settings widen employee capabilities | Preserve explicit deny rules, strict MCP, sandbox, and tests; document that arbitrary owner extensions remain trusted. |
| Inherited provider credential reaches Claude-launched subprocess | Do not deliberately serialize it; disclose Claude owns subprocess credential and error behavior. Stronger isolation is out of scope. |
| Terminal-only gateway export disappears after reboot | Document persistent user/managed settings or OS service environment requirement. |
| Legacy stored API key gets rerouted by new user settings | Conditional legacy path keeps provider scrub and isolated setting sources. |
| Third-party connection is mistaken for Cloud Shift eligibility | Separate sanitized account check; eligibility matrix tests. |
| Removing network preflight causes one failed invocation while offline | Existing transient result/retry path handles it; avoids blocking healthy alternative connections. |
| User settings choose incompatible model mapping | Keep existing model alias contract; surface Claude's provider-neutral failure. |
| UI implies locality or no fallback | Prohibit such claims in copy/tests. |

## Non-deliverables

- No `core/inference.py` or provider abstraction.
- No provider UI, endpoint field, credential field, relay, discovery, readiness matrix, or local-model qualification.
- No team-data migration or provider run binding.
- No Claude Desktop configuration editing or comparison.
