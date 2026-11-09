# Data Model: Claude Connection Pass-Through

## Summary

This feature adds no persisted provider, credential, endpoint, readiness, or run-binding entity and requires no migration. It introduces explicit transient concepts used to keep launch behavior and Cloud Shift eligibility testable. Existing `staff.json`, employee workspaces, sessions, histories, routines, roles, abilities, grants, and cloud state files retain their formats.

## Transient Concepts

### Launch Classification

Represents the behavioral contract assigned to each Orbit-owned Claude invocation.

| Field | Values | Validation |
| --- | --- | --- |
| `launch_id` | Stable inventory ID `L01`–`L11` | Unique within the launch contract |
| `class` | `installation`, `ordinary`, `legacy_api_key`, `interactive`, `cloud_shift` | Exactly one resolved class per execution; conditional sites `L02`–`L04` declare their permitted ordinary/legacy pair |
| `source` | Module and containing function | Must correspond to a production invocation or shared launch seam |
| `setting_sources` | `user,project`, `user`, empty, application-owned, or not applicable | Must match the selected class and flow |
| `environment_policy` | Ordinary pass-through, legacy isolation, application-owned, or cloud allowlist | Must match the selected class |

The inventory is a design/test artifact, not runtime-persisted team data. See [contracts/claude-launch.md](./contracts/claude-launch.md). Conditional launch sites resolve their class per execution; the inventory records the permitted pair, not a single fixed class.

### Claude Availability

Provider-neutral installation state used by setup, doctor, the checklist, and Settings.

| Field | Values | Meaning |
| --- | --- | --- |
| `state` | `available`, `missing`, `broken` | Version invocation succeeded, executable was not found, or executable could not run |
| `detail` | Provider-neutral owner message | Installation/repair guidance only; never an account-login instruction |

Availability is computed on demand and is not persisted as connection readiness.

### Cloud Eligibility Result

Transient result from the account-only status check.

| Field | Type | Validation |
| --- | --- | --- |
| `checked_at` | Monotonic timestamp | Used only for an in-memory read cache |
| `eligible` | Boolean | True only when `loggedIn` is true and `authMethod` is `claude.ai` |
| `auth_method` | String or empty | Never treated as general Claude readiness |
| `reason` | Provider-neutral account-only message | Empty only when eligible |

Read-only consumers may reuse a result for at most 60 seconds. Manual enablement, new-hire auto-enablement, and every Orbit-initiated Cloud Shift command request a fresh result. No eligibility result or credential value is added to `staff.json` or employee data.

### Diagnostic Provenance

Distinguishes data Orbit creates from content Claude emits.

| Provenance | Existing handling | New restriction |
| --- | --- | --- |
| Orbit-generated registry, employee, UI, activity, and run metadata | Existing fields and storage locations remain | Must never copy inherited settings/environment credential values |
| Claude-generated output and errors | Existing output/error logging behavior remains | No new inspection or redaction guarantee |

Tests use a non-echoing fake Claude when proving Orbit-originated non-serialization. A separate harmless marker case proves Claude-output behavior was not changed.

## Existing Persisted State

### `staff.json.auth`

Existing values continue to distinguish the legacy Orbit-managed API-key path from pass-through operation. No new auth/provider value is added.

### `employees.<id>.cloud_shift`

Existing Boolean owner intent remains the persisted Cloud Shift switch.

- Eligibility loss does not silently clear the switch.
- Ineligible state blocks subsequent Orbit-initiated cloud commands.
- Read-only status exposes the account-only reason.
- Ordinary local work remains independent of the switch and eligibility result.

### Existing cloud state file

Existing session, slot, schedule, sent-hash, and error fields remain. Loss of account eligibility may use the existing error field; it introduces no new stored credential, auth method, or provider field.

## State Transitions

| Current state | Event | Eligibility source | Result |
| --- | --- | --- | --- |
| Cloud Shift off | Read status | Cache allowed, maximum 60 seconds | Report eligible/ineligible; no persisted change |
| Cloud Shift off | Manual enable | Fresh | Enable only if eligible; otherwise remain off with account-only reason |
| New employee | Auto-enable decision | Fresh | Set existing switch only if eligible |
| Cloud Shift on | Orbit initiates cloud command | Fresh | Launch only if eligible |
| Cloud Shift on | Eligibility becomes ineligible | Fresh at next local cloud operation | Keep switch configured; block operation and expose/store reason |
| Cloud Shift on or off | Ordinary local work starts | Not consulted | Local work proceeds using ordinary or legacy launch policy |
| Cloud Shift on | Owner disables | No positive eligibility required for local switch-off | Clear local switch; any remote cleanup remains best-effort under available account access |

Remote schedules already created before eligibility disappears while Orbit is offline are external account state. This feature does not claim that local state can retroactively revoke them without account access.

## Migration

None. Existing installations, including stored API-key mode and enabled Cloud Shifts, keep their current records.
