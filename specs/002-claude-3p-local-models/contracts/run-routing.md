# Contract: Inference Run Routing

**Producer**: Orbit work acceptance/queue (`team.py`) and inference launcher (`engine.py` + `core/inference.py`).

**Consumer**: every Orbit model-backed flow, live status, run logs, provider switching/removal.

## Covered Flows

This contract applies to:

- setup/hiring questions and card;
- employee chats from panel/terminal/channels;
- first day, routines, catch-up, reminders/follow-ups, plans and summaries;
- team bus work;
- role-share/distillation;
- meeting minutes and other `engine.run()` work;
- future Orbit-initiated model calls.

Cloud shift management calls are deliberately outside local inference: they are disabled/suspended while local mode is active.

## Acceptance-Time Binding

Before waiting on an employee lock or provider capacity, create one immutable `RunProviderBinding`:

```json
{
  "run_id": "run_example",
  "profile_id": "local",
  "profile_revision": 3,
  "provider_kind": "local_gateway",
  "model_role": "primary",
  "model_id": "local-code-model",
  "context_tokens": 32768,
  "accepted_at": "2026-11-06T12:00:00Z",
  "deadline_at": "2026-11-06T12:30:00Z",
  "session_namespace": "local-r3"
}
```

Binding rules:

1. Resolution occurs once.
2. No registry reread may change provider/model for this run.
3. Credential value is never part of binding; trusted launcher resolves reference at relay start.
4. Profile revision stays retained until all bindings end.
5. A provider switch affects only work accepted after switch commit.

## Model Resolution

| Active mode | Selection |
| --- | --- |
| Claude account | existing employee `model` and plan-usage fallback logic unchanged |
| Anthropic API key | existing employee `model` and fallback behavior unchanged |
| Local gateway | employee `local_model_role` (`primary` default) → exact profile assignment; no usage/error fallback |

Hiring and provider-independent internal setup use local primary. Within one local process, all Claude background/default model aliases are pinned to the same bound synthetic model, preventing hidden cross-model requests.

## Launch Environment

Common: start from scrubbed provider environment; only Orbit-selected launch material is added.

### Claude account

Current behavior unchanged: default Claude config/keychain; no `ANTHROPIC_API_KEY` inserted by Orbit.

### Anthropic API key

Current behavior unchanged: Orbit's saved Anthropic key supplied exactly as before. This feature does not retrofit its credential handling.

### Local gateway

- remove all inherited `ANTHROPIC_*`, `CLAUDE_CODE_*`, provider selectors, and conflicting gateway variables before adding approved values;
- set isolated `CLAUDE_CONFIG_DIR` for profile revision/employee;
- use protected temporary `--settings` file, not inline JSON with sensitive values;
- settings pin relay `ANTHROPIC_BASE_URL`, fixed non-secret placeholder credential, safe model/context values, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, and `skipWebFetchPreflight: true`;
- set `NO_PROXY/no_proxy` for loopback and prevent proxy routing of relay traffic;
- start relay, then Claude; tear both down together.

Real upstream credential is absent from Claude process and descendants.

## Session Namespace

Existing logical chat key becomes:

```text
<provider kind>:<profile id>:<revision>:<logical session key>
```

- Switching provider/revision starts a fresh Claude conversation; it never resumes a transcript created for another endpoint/model.
- Switching back to unchanged prior revision may resume its existing namespace.
- Employee memory/workspace remains shared as today, so continuity comes from Orbit files, not silent transcript migration.

## Queue and Capacity

Order:

1. accepted/bound;
2. employee lock (one run per employee);
3. local profile FIFO capacity gate (`max_parallel_runs`, default 1), if local;
4. first-run readiness gate for process/revision;
5. process start/run.

Live states are exposed through existing `DOING`/`LIVE` surfaces with run ID:

- `Waiting for <employee>`;
- `Waiting for local model (N ahead)`;
- `Checking local gateway`;
- `Local model is busy; retrying in <time>`;
- ordinary working/tool steps.

Acquiring a queue slot never launches a second run. Deadline continues while waiting; expiration removes exactly that queue item.

## Retry Rules

Claude stream `system/api_retry` event:

- 429/529/capacity: state `waiting_gateway`; same process/request continues.
- reachability before any response: Claude's documented in-process retry may continue, bounded by run deadline.
- authentication/model/context/invalid request: terminal; profile blocked where applicable.

Orbit-level restart/replay:

- never after any assistant/tool/partial stream content;
- never for unknown network failure;
- never onto another model/provider/gateway;
- only a future owner resubmission or existing routine retry creates a new run ID.

This keeps tool effects at-most-once from Orbit's process-launch perspective.

## Failure and Owner Text

Local failures call provider-specific formatter. Result includes stable code, safe model/endpoint label, and recovery action. It never:

- says Claude account sign-in expired;
- says internet loss when loopback alone failed;
- claims plan limit/billing;
- falls back silently.

Routine retry semantics remain, but retry retains or reconstructs the intended provider rule explicitly:

- retry scheduled before a provider switch retains original run's failure record;
- when retry becomes newly accepted later, it binds the provider active then and is a visibly new run. It does not masquerade as continuation of old run.

## Usage Record

Every final record adds provider profile/revision and model role. Local rules:

- use actual CLI/gateway token counts when present;
- unknown count stays unknown (no cost conversion estimate);
- ignore client-side Anthropic-equivalent dollar estimate;
- cost null/unknown unless explicit trusted gateway measurement;
- no Claude plan rate-limit fields in local UI.

## Switching

Provider activation transaction does not acquire/kill run processes. After commit:

- old bindings continue against old revision;
- new bindings use new generation;
- local profile/secret remains retained while referenced;
- Settings shows count of work still using previous provider;
- profile removal returns conflict until count reaches zero.

## Fail-Closed Invariants

1. No request without a valid binding.
2. Local relay accepts only bound destination/model.
3. Local unavailable/blocked never invokes account/API mode.
4. No cross-provider session resume.
5. Partial responses never trigger a fresh Orbit process automatically.
6. Existing sandbox, guard, ability, connector, workspace, and approval settings are generated identically regardless of provider.
