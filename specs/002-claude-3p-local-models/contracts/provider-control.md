# Contract: Provider Control and Owner Surfaces

**Producer**: Orbit provider service (`core/inference.py`) and panel/CLI adapters.

**Consumer**: setup, Settings, onboarding checklist, doctor, CLI owners, and tests.

This contract defines owner-visible provider state and the staged mutation flow. Secret values are write-only.

## Modes

Stable external values:

| Value | Owner label | Credential |
| --- | --- | --- |
| `claude_account` | Claude account | Claude's saved account session |
| `anthropic_api_key` | Anthropic API key | Orbit secret `anthropic_api_key` |
| `local_gateway` | Local gateway | None, bearer, or API key stored under local credential ref |

An upgraded registry with no new provider block derives its value from legacy `auth` and reports `migrated: false` until an owner edit.

## Sanitized Read Contract

`GET /api/inference` and internal `inference.view()` return:

```json
{
  "generation": 4,
  "active": {
    "mode": "local_gateway",
    "profile_id": "local",
    "revision": 3,
    "label": "Local gateway",
    "state": "ready",
    "base_url": "http://127.0.0.1:11434",
    "credential_style": "none",
    "credential_present": false,
    "models": {
      "primary": {"id": "local-code-model", "context_tokens": 32768},
      "fallback": {"id": "local-code-model", "context_tokens": 32768}
    },
    "last_readiness": {
      "id": "rr_example",
      "verdict": "ready",
      "checked_at": "2026-11-06T12:00:00Z",
      "recovery": null
    }
  },
  "candidate": null,
  "can_remove_local": false,
  "running_bindings": 1
}
```

Rules:

- No credential value, secret file path, raw header, raw response, query, URL user info, or temporary relay data.
- `base_url` is canonical and non-secret or omitted.
- `state` is one of `unknown`, `checking`, `ready`, `busy`, `blocked`.
- `recovery` is one direct owner action derived from the first failed mandatory check; full per-check results are available without secrets.

## Write Contracts

All panel calls use existing localhost cookie/origin protections. Bodies are bounded JSON. Credential strings are accepted only over the authenticated panel or hidden CLI input and are never echoed.

### 1. Stage local settings

`POST /api/inference/stage`

```json
{
  "mode": "local_gateway",
  "base_url": "http://localhost:11434",
  "credential_style": "none",
  "credential": null,
  "primary_model": "local-code-model",
  "primary_context_tokens": 32768,
  "fallback_model": "local-code-model",
  "fallback_context_tokens": 32768,
  "max_parallel_runs": 1
}
```

Result: sanitized candidate with a new revision. A non-empty credential is saved immediately under owner-only secret storage and replaced in memory with its reference. An omitted credential means “keep existing”; an explicit remove action is separate.

Static validation failure returns HTTP 400 and field errors; no active state changes.

### 2. Discover models

`POST /api/inference/discover`

Input: candidate revision (or staged connection fields during initial setup). Output:

```json
{
  "discovery": "available",
  "models": [
    {"id": "local-code-model", "display_name": "Local Code Model", "context_tokens": 32768}
  ],
  "manual_entry": true
}
```

`manual_entry` is always true. Discovery timeout, 404, or empty list returns `discovery: "unavailable"` with a recovery note, not a fatal panel error. Unsafe URL, redirect, auth rejection, or malformed successful response returns a specific error.

### 3. Check candidate/destination

`POST /api/inference/check`

```json
{"profile_id": "local", "revision": 3, "trigger": "activation"}
```

Returns a sanitized full `ProviderReadinessResult`. It never activates. Concurrent duplicate checks for the same revision coalesce; a changed revision invalidates the old result.

### 4. Activate/switch

`POST /api/inference/activate`

```json
{
  "profile_id": "local",
  "revision": 3,
  "readiness_result": "rr_example",
  "expected_generation": 4,
  "confirm": true
}
```

Preconditions:

1. `confirm` is true.
2. Candidate revision and readiness-result binding match.
3. Result is `ready` and is within activation freshness window.
4. `expected_generation` equals current generation.
5. For local activation, every existing cloud trigger is disabled successfully.

Success atomically changes active profile, increments generation, and returns new sanitized view. Failure returns HTTP 409 (`stale_candidate`, `stale_generation`, `readiness_expired`, `cloud_suspend_failed`) or HTTP 400; old active profile remains.

Built-in destination modes use the same stage/check/confirm flow. Claude-account check validates installed client + account status; API-key check validates the saved key without exposing it.

### 5. Recheck active

`POST /api/inference/recheck`

Runs full readiness for active revision. A failed result marks active state blocked but does not switch providers. A passing result clears blocked state.

### 6. Remove local profile

`POST /api/inference/remove`

```json
{"profile_id": "local", "expected_generation": 6, "confirm": true}
```

Allowed only when local is inactive and no accepted run binding references it. Removes profile, its readiness records, local Claude config/session runtime, and provider credential. It does not touch employees, workspaces, logs/history, skills, routines, gateway/model runtime files, or Claude Desktop config.

An open Claude Desktop session is outside Orbit's process ownership. Response warns that it remains open with its current app configuration; Orbit does not alter it.

## CLI Contract

```text
orbit provider status
orbit provider use claude-account|api-key|local
orbit provider local
orbit provider check
orbit provider remove-local
```

- `status`: same sanitized view in plain owner language; optional `--json` may expose the same fields, never more.
- `use`: stage/check, show effect, ask explicit confirmation, then activate.
- `local`: hidden credential prompt; model discovery + manual path.
- `check`: full active readiness; nonzero on blocked.
- `remove-local`: explicit confirmation and removal preconditions.

`orbit setup` uses these same functions before business/hiring setup. It asks for one of the three modes; local setup never calls `claude auth login`.

## Surface Copy Invariants

Every setup/Settings/checklist/doctor surface states:

1. effective mode;
2. safe endpoint for local mode;
3. selected model(s);
4. ready/busy/blocked and last-check time;
5. one direct recovery action;
6. whether inference content leaves the computer;
7. local-mode cloud-shift limitation.

No local failure message recommends Claude account sign-in.
