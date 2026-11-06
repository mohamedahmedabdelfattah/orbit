# Contract: Claude Launch and Account Boundary

## Purpose

Define how Orbit invokes Claude without owning Claude's inference connection.

## Launch Matrix

| Flow | Connection owner | Environment | Setting sources | Orbit controls |
| --- | --- | --- | --- | --- |
| Setup / doctor | Claude | Inherited enough to resolve executable; no account check | N/A for version check | Installation/version only |
| Ordinary employee work | Claude user configuration | Inherit provider values; remove recursion marker; add Orbit employee values | `user,project` | Inline sandbox settings, guard/plugins, strict MCP, tools, prompt, model, effort, session |
| Structured onboarding | Claude user configuration | Same pass-through base without employee-only values | `user` | No tools, strict MCP, system prompt, schema, model, effort |
| Guard plugin administration | Claude user configuration | Pass-through base | Claude command default | Fixed plugin operation and workspace |
| Legacy Orbit API-key work | Orbit legacy compatibility path | Strip inherited provider values; inject stored key | Existing isolated sources | Existing behavior unchanged |
| Interactive Open in Claude | Claude application | Application-owned | Application-owned plus employee local project settings | Employee workspace and generated Orbit safety settings |
| Cloud Shift | Claude account only | Provider values removed | Empty | Existing cloud-only tools and commands |

## Required Invariants

1. Setup success never depends on `loggedIn` or a Claude-account method.
2. Ordinary work never strips a variable solely because it names an Anthropic, Claude, Bedrock, Vertex, Foundry, gateway, or proxy connection.
3. `CLAUDECODE` is removed before child launch to prevent nested-client refusal.
4. Orbit-owned values override same-named inherited values.
5. Legacy Orbit API-key mode cannot inherit a base URL, auth token, provider-selection flag, or user setting that reroutes its stored key.
6. Ordinary employee and onboarding paths select the setting sources in the matrix.
7. Orbit never deliberately serializes or echoes inherited credential values into `staff.json`, employee files, UI responses, activity logs, or run logs. Claude output/errors keep existing logging behavior.
8. User hooks/plugins are trusted and may execute. Orbit does not describe them as sandboxed or reviewed.
9. Claude's process result, not a socket probe, decides ordinary connection success.
10. Orbit never performs provider fallback. Any provider precedence or fallback inside Claude is Claude configuration behavior.

## Installation Status

Owner-facing status has three provider-neutral states:

| State | Meaning | Action |
| --- | --- | --- |
| `available` | Executable resolved and version command succeeded | None |
| `missing` | No executable resolved | Install Claude Code |
| `broken` | Executable resolved but could not run | Repair/update Claude Code and retry |

Account status is not part of general readiness.

## Error Contract

| Class | Owner-facing wording |
| --- | --- |
| Authentication/provider | Claude could not use its configured connection; verify Claude directly, then retry |
| Network/unreachable | Claude could not reach its configured connection; check that connection, then retry |
| Usage/rate limit | Claude's configured connection reached a usage or rate limit; routine work retries later |
| Other | Existing generic logged-error response |

Messages must not claim a specific provider, endpoint, locality, or required login method.

## Cloud Shift Eligibility

- General Claude availability does not imply Cloud Shift availability.
- Eligibility runs with inherited provider variables removed and user setting sources disabled.
- `third_party`, `api_key`, `api_key_helper`, `oauth_token`, and `none` are ineligible.
- Eligibility requires `loggedIn: true` with `authMethod: "claude.ai"`.
- Ineligible state blocks manual enablement and prevents new-hire auto-enablement.
- Existing enabled shifts must expose loss of eligibility as an error; ordinary local work remains unaffected.

## Explicit Non-contracts

Orbit does not promise:

- which endpoint Claude selects;
- whether inference stays on-device;
- whether Claude falls back;
- whether a configured model supports Orbit's prompts/tools;
- whether provider credentials are hidden from Claude-launched subprocesses;
- whether terminal-only exports survive service restart.
