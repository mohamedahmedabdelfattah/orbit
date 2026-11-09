# Contract: Claude Launch and Account Boundary

## Purpose

Define how Orbit invokes Claude without owning Claude's inference connection.

## Behavioral Classes

| Class | Connection owner | Environment | Setting sources | Authorization |
| --- | --- | --- | --- | --- |
| Installation check | None | Enough to resolve and execute the installed client | N/A | Successful version invocation only |
| Ordinary pass-through | Claude user configuration | Inherit arbitrary values, remove `CLAUDECODE`, then overlay Orbit-owned values | `user,project` for employee work; `user` for structured onboarding | Actual Claude result |
| Legacy Orbit API-key | Orbit compatibility path | Existing provider isolation; inject only Orbit's stored key where inference needs it | Existing isolated employee/onboarding sources | Existing stored-key behavior |
| Interactive application | Claude application | Application-owned | Application-owned plus generated employee-local project settings | Application-owned |
| Cloud Shift | Qualifying Claude account | Minimal account bootstrap allowlist; no inherited connection/routing values | Empty for every inference launch | Fresh qualifying account status before every Orbit-initiated launch |

## Production Invocation Inventory

| ID | Source/function after implementation | Purpose | Class | Required evidence |
| --- | --- | --- | --- | --- |
| L01 | Shared installation helper used by `orbit` and `core/panel.py` | Setup, doctor, checklist, and Settings availability | Installation check | Missing, broken, and successful-version cases; no account command |
| L02 | `core/engine.py` employee command via `run()`/`stream()` | Chats, routines, summaries, role processing, follow-ups, and all other employee model work | Ordinary pass-through or legacy API-key | Every caller converges here; argv/env/safety/session matrix |
| L03 | `core/onboard.py:_ask()` | Structured hiring and role output | Ordinary pass-through or legacy API-key | User source in pass-through; isolated source in legacy mode; no-tools/schema controls |
| L04 | `core/engine.py:claude_session()` plugin administration | Install/update Orbit's guard plugin | Ordinary pass-through (no overlays; full inheritance beyond `CLAUDECODE` removal) or legacy isolated non-key environment | Fixed plugin operation/workspace; no model call; no stored key in either mode |
| L05 | `core/engine.py:claude_session()` application link | Open an interactive employee session | Interactive application | No headless inference child; generated project safety settings remain |
| L06 | Account-status helper in `core/cloud.py` | Determine Cloud Shift eligibility | Cloud Shift | Minimal account environment; exact auth-method matrix; read cache/fresh modes |
| L07 | `core/cloud.py:trigger()` | Create/update remote routine triggers | Cloud Shift | Fresh eligibility, account environment, empty sources |
| L08 | `core/cloud.py:send()` | Send state/instructions to a cloud session | Cloud Shift | Fresh eligibility, account environment, empty sources |
| L09 | `core/cloud.py:environment()` | Resolve the owner's cloud environment | Cloud Shift | Fresh eligibility, account environment, empty sources |
| L10 | `core/cloud.py:new_session()` | Bootstrap a cloud desk/session | Cloud Shift | Fresh eligibility and controlled interactive `TERM` |
| L11 | `core/cloud.py:_transcript()` | Bring a cloud transcript back | Cloud Shift | Fresh eligibility, account environment, empty sources |

The inventory regression guard examines production direct uses of the resolved Claude executable in `orbit` and `core/`. A new direct `subprocess`/`exec` launch fails validation until its containing function and class are added here. Calls routed through `engine.run()` are represented once by L02; their business callers do not create Claude processes themselves.

Classes are resolved per execution, not assigned once per site. L02–L04 are conditional sites: each row's Class column names the permitted pair, and the entry resolves to ordinary pass-through when the team is not in legacy stored-key mode and to legacy Orbit API-key when it is. The regression guard rejects a launch site with no declared class and any resolved pair outside the contract.

## Environment Contracts

### Ordinary pass-through

1. Start with Orbit's complete inherited process environment; there is no prefix filtering. Unrelated and unrecognized values, including any secrets present in Orbit's service environment, reach Claude by design. This is the documented trust decision behind FR-005 and FR-025.
2. Remove only `CLAUDECODE` as the recursion marker.
3. Overlay exactly the enumerated Orbit-owned values below; each wins over a same-named inherited value:
   - Execution/platform: `HOME` resolved to the actual owner home, `PATH` containing Orbit's binary directory, the resolved Claude executable directory, and Orbit's system path directories, and `SSL_CERT_FILE`/`CURL_CA_BUNDLE` defaults when the platform CA bundle exists.
   - Runtime/safety: `CLAUDE_CODE_FORK_SUBAGENT=0`; `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` on native Windows; `STAFF_EMPLOYEE`, `STAFF_WORKSPACE`, `STAFFROOM_HOME`, `STAFFROOM_KIT`, `STAFF_ABILITIES`, and `STAFF_BROWSER_SITES`.
   - Legacy Orbit API-key mode only: `ANTHROPIC_API_KEY` injected under the existing legacy behavior, on top of the legacy prefix-filtered isolation.
   - Structured onboarding adds no runtime keys beyond these; guard-plugin administration adds none and never receives the stored inference key in either mode.
4. Do not persist or log the inherited mapping.

### Legacy API-key compatibility

Keep the existing provider isolation and setting sources. Employee inference injects only the stored Orbit Anthropic key. Structured onboarding retains its existing isolated source behavior. Guard plugin administration remains isolated and does not receive the stored inference key.

### Cloud Shift account environment

Build from an empty mapping. Values not listed below are absent even when present in Orbit's process environment.

- **Generated/forced on every platform**: the resolved executable directory plus Orbit's known system path, the actual owner home, and the platform temporary directory.
- **POSIX/macOS bootstrap keys that may be copied**: `USER`, `LOGNAME`, `LANG`, `LC_ALL`, and `LC_CTYPE`.
- **Windows bootstrap keys that may be copied**: `SYSTEMROOT`, `WINDIR`, `COMSPEC`, `PATHEXT`, `USERNAME`, `USERDOMAIN`, `APPDATA`, `LOCALAPPDATA`, and `PROGRAMDATA`; `USERPROFILE`, `HOMEDRIVE`, and `HOMEPATH` must resolve to the actual owner home.
- **Command-specific controlled value**: `TERM=xterm-256color` only for the interactive session bootstrap.
- **Always absent**: `CLAUDECODE`, `CLAUDE_CONFIG_DIR`, proxy variables, provider/endpoint/token/API-key variables, and every unknown/unlisted inherited variable.

Cloud inference commands explicitly disable setting sources. Account status uses the same environment but creates no inference session and loads no user setting source.

## Required Invariants

1. Setup success never depends on `loggedIn` or a Claude-account method.
2. Ordinary work never strips a variable solely because it names an Anthropic, Claude, Bedrock, Vertex, Foundry, gateway, or proxy connection.
3. `CLAUDECODE` is removed before child launch to prevent nested-client refusal.
4. Orbit-owned values override same-named inherited values.
5. Legacy Orbit API-key mode cannot inherit a base URL, auth token, provider-selection flag, or user setting that reroutes its stored key.
6. Every production Claude invocation appears exactly once in the inventory or routes through an inventoried shared launch.
7. Ordinary employee and onboarding paths select the setting sources in the class contract; legacy employee and onboarding paths retain their isolated sources.
8. Orbit never deliberately serializes or echoes inherited credential values into `staff.json`, employee files, UI responses, activity records, diagnostic metadata, or Orbit-generated logs. Claude output/errors keep existing logging behavior.
9. User hooks/plugins are trusted and may execute. Orbit does not describe them as sandboxed or reviewed.
10. Claude's process result, not a socket probe, decides ordinary connection success.
11. Orbit never performs provider fallback. Any provider precedence or fallback inside Claude is Claude configuration behavior.
12. Unknown future environment-variable names pass through ordinary work and fail closed at the Cloud Shift boundary.

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

Orbit-generated diagnostics retain the existing process result and failure class but never add inherited environment/settings values—credential values or otherwise—except values Orbit itself computes for the session, such as session identifiers, workspace paths, and run timings. Tests asserting this use a fake Claude that does not echo the sentinel. A separate compatibility case may emit a harmless marker from fake Claude to prove Claude-output handling itself is unchanged.

## Cloud Shift Eligibility

- General Claude availability does not imply Cloud Shift availability.
- Eligibility uses the account environment allowlist and no user setting source.
- `third_party`, `api_key`, `api_key_helper`, `oauth_token`, and `none` are ineligible.
- Eligibility requires `loggedIn: true` with `authMethod: "claude.ai"`.
- Read-only status may cache the result in memory for at most 60 seconds.
- Manual enablement, new-hire auto-enablement, and L07–L11 bypass the cache and refresh eligibility.
- Ineligible state blocks manual enablement, auto-enablement, and all later Orbit-initiated cloud launches.
- Existing enabled shifts retain their configured flag but expose loss of eligibility as an account-only error; ordinary local work remains unaffected.
- Orbit does not promise to revoke a remote schedule that was already created before eligibility disappeared while Orbit was offline.

## Explicit Non-contracts

Orbit does not promise:

- which endpoint Claude selects;
- whether inference stays on-device;
- whether Claude falls back;
- whether a configured model supports Orbit's prompts/tools;
- whether provider credentials are hidden from Claude-launched subprocesses;
- whether terminal-only exports survive service restart.
