# Data Model: Claude 3P Local Model Support

Feature: `002-claude-3p-local-models`. Additions preserve Orbit's JSON-file storage model. Provider secrets never enter these records.

## 1. InferenceProviderRegistry *(new block in `~/Staff/staff.json`)*

Machine/team-level provider state.

```json
{
  "inference": {
    "schema": 1,
    "active_profile": "claude-account",
    "generation": 1,
    "profiles": {
      "claude-account": {"kind": "claude_account"},
      "anthropic-api": {
        "kind": "anthropic_api_key",
        "credential_ref": "anthropic_api_key"
      },
      "local": {
        "kind": "local_gateway",
        "revision": 3,
        "lifecycle": "active",
        "base_url": "http://127.0.0.1:11434",
        "credential_style": "none",
        "credential_ref": null,
        "models": {
          "primary": {"id": "local-code-model", "context_tokens": 32768, "source": "discovered"},
          "fallback": {"id": "local-code-model", "context_tokens": 32768, "source": "discovered"}
        },
        "max_parallel_runs": 1,
        "readiness": "rr_..."
      }
    },
    "readiness_results": {
      "rr_...": {"verdict": "ready", "checked_at": "2026-11-06T12:00:00Z"}
    }
  }
}
```

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | integer | `1` for this feature. Unknown future major version blocks provider edits but not read-only diagnostics. |
| `active_profile` | enum/profile ID | `claude-account`, `anthropic-api`, or `local` in v1. Must reference a profile. |
| `generation` | positive integer | Increments only after atomic active-profile switch. Used for optimistic confirmation. |
| `profiles` | object | Built-in account/API profiles plus at most one local draft/profile in v1. |
| `readiness_results` | object | Bounded to newest result per profile revision plus newest failed candidate result. No raw response bodies or secrets. |

### Legacy migration

When `inference` is absent:

| Existing `auth` | Effective profile |
| --- | --- |
| missing or `subscription` | `claude-account` |
| `api_key` | `anthropic-api` |

Reading legacy state performs no write. On the first owner provider edit, Orbit materializes this block and mirrors `auth` as `subscription`/`api_key` while those modes are active. Local mode writes no secret into `auth`; all new routing reads `inference.active_profile` through `core/inference.py`.

## 2. InferenceProviderProfile

Owner-selected route. Built-in profiles have stable IDs; local has revisioned routing data.

| Field | Type | Values/validation |
| --- | --- | --- |
| `kind` | enum | `claude_account`, `anthropic_api_key`, `local_gateway` |
| `revision` | integer | Local only. Increments when endpoint, auth style/ref, model assignment, context, or capacity changes. Readiness/status updates do not increment it. |
| `lifecycle` | enum | `draft`, `checking`, `ready`, `active`, `blocked`, `inactive` |
| `credential_ref` | nullable secret name | Identifier matching `[a-z0-9_]+`; never a credential value. |
| `readiness` | nullable result ID | Must reference a result for this exact profile revision. |

### Profile lifecycle

```text
draft ──check──> checking ──all pass──> ready
  ^                    └──any fail────> draft
  │
inactive <──switch── active ──runtime failure──> blocked
                    blocked ──full recheck pass──> active
```

- `ready → active` requires owner confirmation and unchanged candidate revision/result.
- A different active profile becomes `inactive` only after the switch transaction commits.
- `blocked` remains the active selection but refuses new model work; it does not fall back.
- Removal applies only to inactive `local` with zero live bindings.

## 3. LocalGatewayConnection *(fields on local profile)*

| Field | Type | Validation |
| --- | --- | --- |
| `base_url` | URL string | Canonical `http`/`https`; loopback only; optional safe path prefix; no user info/query/fragment; no redirect. |
| `pinned_address` | ephemeral | Numeric loopback selected during each check/relay start. Never persisted as authority over a changed URL. |
| `credential_style` | enum | `none`, `bearer`, `api_key` |
| `credential_ref` | nullable string | Required for bearer/API key; null for none. Value stored separately under `.secrets`. |
| `discovery` | enum | `available`, `unavailable`, `invalid` from last check. |
| `max_parallel_runs` | integer | `1..16`; default `1`. Advanced owner setting. |
| `health` | derived enum | `unknown`, `ready`, `busy`, `blocked`; derived from readiness/runtime evidence, not owner-editable. |

Secret file names are profile-scoped (for example `local_gateway_credential`). Existing secret protections apply: owner-only mode/ACL, secret directory in deny-read policy, no git tracking.

## 4. ModelAssignment

Two named workload roles on one local gateway.

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | Exact gateway model ID; 1–300 printable characters; no control/NUL characters. |
| `context_tokens` | integer | Verified `>= 32000`; upper bound accepted by installed Claude client. |
| `source` | enum | `discovered`, `manual` |
| `display_name` | optional string | Sanitized discovery label; never used for routing. |
| `capabilities` | object | Last readiness evidence for stream/tool/structured output. Claims from discovery are advisory only. |

Roles:

- `primary`: default for hiring, new employees, normal work.
- `fallback`: explicitly selected lighter/alternate workload model. May equal primary.

`fallback` is **not** an error failover. A runtime failure on either role fails/blocks that bound run on that role.

Employee records gain:

```json
{"model": "sonnet", "local_model_role": "primary"}
```

`model` remains untouched and applies in Claude-account/API-key modes. `local_model_role` applies only in local mode and defaults to `primary` when absent.

## 5. ProviderReadinessResult

Sanitized, persisted evidence for one exact profile revision.

| Field | Type |
| --- | --- |
| `id` | `rr_<random>` |
| `profile_id`, `profile_revision` | binding to candidate/profile |
| `checked_at`, `finished_at`, `duration_ms` | UTC/timing |
| `trigger` | `activation`, `doctor`, `startup_first_run`, `manual_recheck` |
| `claude_version` | parsed version, no path secrets |
| `endpoint` | canonical non-secret base URL |
| `models` | checked exact IDs and context values |
| `checks` | ordered `ReadinessCheck` records |
| `verdict` | `ready`, `blocked` |

`ReadinessCheck`:

```json
{
  "capability": "tool_use",
  "model_role": "primary",
  "status": "pass",
  "code": "ok",
  "message": "Tool call completed",
  "recovery": null,
  "duration_ms": 1830
}
```

Allowed `status`: `pass`, `fail`. Activation has no skipped mandatory checks. `message` and `recovery` are single-line, control-character-free, redacted, and bounded. Raw prompts, responses, headers, credentials, URLs with user info/query, and process arguments are never persisted.

## 6. RunProviderBinding

Immutable route captured when work is accepted.

| Field | Type | Notes |
| --- | --- | --- |
| `run_id` | random stable ID | One per accepted unit of work. |
| `profile_id`, `profile_revision` | string/integer | Routing snapshot. |
| `provider_kind` | enum | For diagnostics and usage copy. |
| `model_role` | enum/null | Local: primary/fallback. |
| `model_id` | string | Exact upstream model selected at acceptance. |
| `context_tokens` | integer/null | Verified local limit. |
| `accepted_at` | UTC timestamp | Defines “new work” for switching. |
| `deadline_at` | UTC timestamp | Existing job timeout converted to an absolute bound. |
| `session_namespace` | string | Hash of provider kind/profile/revision; prevents cross-provider resume. |

The binding contains a credential **reference**, if needed internally, never a credential. The live trusted process resolves that reference just before relay creation. Removal is blocked while a binding exists.

## 7. InferenceRun *(runtime state; sanitized live view + final run log)*

| Field | Type |
| --- | --- |
| `run_id`, `employee`, `job` | identity |
| `binding` | `RunProviderBinding` |
| `state` | state enum below |
| `state_since` | UTC timestamp |
| `queue_position` | optional positive integer |
| `retry` | optional `{attempt, max_retries, retry_delay_ms, error_status}` from Claude stream |
| `result` | success/failure metadata after completion |

State transitions:

```text
accepted
  ├─> waiting_employee
  ├─> waiting_capacity
  └─> checking_provider ─> starting ─> running ─> succeeded
                                  │          ├─> waiting_gateway ─> running
                                  │          └─> failed
                                  └─> failed
any nonterminal state ──deadline──> expired
```

Only one Claude process belongs to a run. `waiting_gateway` is a retry in that process, not a new execution. A partial stream can transition only to `failed`/`expired`, never to a fresh process replay.

## 8. Run Log Extension *(existing `state/runs.jsonl`)*

New optional fields:

```json
{
  "provider": "local_gateway",
  "provider_profile": "local",
  "provider_revision": 3,
  "model_role": "primary",
  "model": "local-code-model",
  "tokens": 812,
  "cost_usd": null,
  "cost_known": false,
  "readiness_result": "rr_..."
}
```

Rules:

- Existing records remain readable.
- Local tokens are measured only; no conversion from estimated Claude-equivalent dollars.
- Local `cost_usd` is null unless a trusted gateway measurement exists; UI says `unknown`.
- `error` uses sanitized provider code/message, never a raw credential-bearing body.

## 9. CloudShiftPreference *(extension to employee/provider state)*

| Field | Type | Meaning |
| --- | --- | --- |
| existing `cloud_shift` | boolean | Owner's desired preference, preserved across local mode. |
| `cloud_shift_suspended_by` | nullable enum | `local_gateway` while local active. |
| cloud state `triggers_disabled_at` | timestamp/null | Evidence that future triggers were disabled before activation. |

Effective cloud shift is `cloud_shift == true` **and** active provider is `claude_account` **and** not suspended. Local activation requires all existing trigger-disable operations to succeed before commit.

## 10. Desktop3PStatus *(derived, never persisted with secrets)*

| Field | Type |
| --- | --- |
| `installed` | boolean |
| `version`, `version_ok` | string/boolean |
| `source` | `local`, `managed_machine`, `managed_user`, `bootstrap`, `admin`, `unknown` |
| `provider` | sanitized enum/unknown |
| `base_url` | canonical non-secret URL/null |
| `auth_scheme` | bearer/x-api-key/unknown |
| `credential_present`, `credential_matches` | boolean/null |
| `models` | sanitized model IDs |
| `match` | `matching`, `mismatch`, `unverified`, `not_configured`, `too_old` |
| `actions` | short guided steps, no secrets |

Only `matching` permits Orbit to claim an interactive session is local and return the employee deep link.

## Global Invariants

1. No provider credential value is present in registry, candidate/readiness records, workspace, session map, run log, activity log, panel response, command argument, or Claude child environment.
2. Exactly one active profile generation accepts new work.
3. Every accepted run keeps its original binding through queues, retries, and provider switches.
4. Local upstream destination is loopback and redirect-free for every request, not only during setup.
5. Local upstream model equals the binding's exact model; all other model IDs fail closed.
6. Existing employees, history, skills, routines, settings, and cloud model choices survive provider switch/removal unchanged.
