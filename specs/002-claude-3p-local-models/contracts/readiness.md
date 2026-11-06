# Contract: Provider Readiness

**Producer**: `core/inference.py` readiness runner.

**Consumers**: activation, doctor, first run after startup/profile change, Settings/checklist, automated tests.

Readiness checks one exact profile revision. It never changes the active provider.

## Triggers

| Trigger | Scope | Cache allowed |
| --- | --- | --- |
| `activation` | full candidate/destination suite | no |
| `doctor` | full active suite | no |
| `startup_first_run` | full active suite once per service process/revision | coalesce concurrent first runs only |
| `manual_recheck` | full active/candidate suite | no |
| later ordinary run | health gate | recent successful same-revision result allowed; runtime failure invalidates immediately |

Activation result is fresh for 10 minutes. Any candidate routing edit invalidates it immediately.

## Check Order

Fast/static failures run before model work so owner gets the most specific action quickly.

### C0 — Claude client

- Resolve official `claude` executable.
- Parse `claude --version`; require v2.1.259+ for local headless mode.
- Verify required flags/stream protocol with a no-inference startup seam where version parsing is inconclusive.

Failure: `claude_missing` or `claude_too_old`. Recovery for old client: `claude update`.

### C1 — Endpoint safety

- Parse/canonicalize URL per [gateway-relay.md](./gateway-relay.md).
- Resolve every address; all must be loopback.
- Open direct connection without redirect following.

Failures: `endpoint_invalid`, `destination_unsafe`, `redirect_refused`.

### C2 — Reachability and authentication

- Send smallest valid `POST /v1/messages` request through candidate relay.
- Distinguish socket/timeout, 401/403, model error, capacity, malformed success.
- A model-not-found response proves reach/auth but does not pass model availability.

Failures: `gateway_unreachable`, `credential_rejected`, `gateway_saturated`, `response_incompatible`.

### C3 — Discovery and selected-model availability

- Best-effort `GET /v1/models?limit=1000`, three-second timeout, no redirects.
- Discovery absence is not fatal because manual IDs are allowed.
- For each distinct selected model, send a minimal inference request and require successful model load/selection.
- A discovery entry alone never passes availability.

Failures: `model_unavailable`, `model_loading`, `model_id_invalid`.

### C4 — Streaming

For each distinct model:

- request `stream: true`;
- require at least one increment before completion;
- require parseable ordered Anthropic SSE events and final `message_delta` + `message_stop`;
- reject full-response buffering beyond probe deadline, early EOF, duplicate/invalid block lifecycle, HTML/non-API body.

Failure: `stream_incompatible`.

### C5 — Tool use through Claude

For each distinct model, run actual supported `claude -p` through candidate relay in a fresh temporary workspace:

- exact synthetic model binding;
- only one harmless canary tool available/allowed;
- `--permission-prompts none`;
- prompt requires writing a nonce to one canary file, then reading/reporting it;
- verify stream contains tool use/result and file contains exact nonce once.

Failures: `tool_use_missing`, `tool_input_invalid`, `tool_result_incompatible`.

Cleanup always removes temporary workspace and local Claude config.

### C6 — Hiring structured response

For each distinct model, invoke the same launch helper and representative hiring JSON Schema used by `onboard._ask()`:

- no tools;
- `--output-format json --json-schema <schema>`;
- require process success, `structured_output`, schema-valid required fields/types, and bounded strings/arrays.

Failures: `structured_output_missing`, `structured_output_invalid`.

This checks the actual Orbit/Claude path, not only raw gateway JSON mode.

### C7 — Context capacity

For each distinct model:

1. Read advisory `max_input_tokens`/equivalent discovery metadata when present.
2. If manual, require owner-provided configured value.
3. Build deterministic non-sensitive input; use token-count endpoint when available to size to at least 32,000 input tokens, otherwise use conservative generated size.
4. Send with one output token through candidate relay under a 30-second capability deadline.
5. Require no context rejection and valid completion. Record verified lower bound, not an unproven larger claim.

Failures: `context_too_small`, `context_probe_timeout`, `context_response_invalid`.

## Deadlines

- Static/discovery/connect failures: report as soon as observed, at most 30 seconds.
- Each mandatory capability probe: 30-second blocker deadline unless an earlier specific response arrives.
- Whole suite may span multiple models but stops launching dependent probes for a model after a definitive blocker.
- Owner can cancel; cancellation returns `check_cancelled` and no ready verdict.

## Verdict

`ready` only when every mandatory C0–C7 check passes for every distinct assigned model. Discovery can be unavailable; every other capability is mandatory.

`blocked` contains every independently observed failed capability, not only the first. UI highlights first recovery action but can expand all rows.

## Stable Failure Taxonomy

| Code | Owner message | Direct action |
| --- | --- | --- |
| `claude_missing` | Claude client is not installed | Install from documented Claude client URL |
| `claude_too_old` | Claude client is too old for local gateway mode | Run `claude update` |
| `endpoint_invalid` | Gateway address is not a valid loopback URL | Enter `http://127.0.0.1:<port>` or valid local URL |
| `destination_unsafe` | Address resolves outside this computer | Use same-computer loopback endpoint |
| `redirect_refused` | Gateway redirected; Orbit will not send credentials there | Enter final loopback address directly |
| `gateway_unreachable` | Nothing answered at local gateway | Start gateway/check port |
| `credential_rejected` | Gateway rejected selected credential | Replace credential/check style |
| `model_unavailable` | Selected model is absent/unloaded/renamed | Load or reselect exact model |
| `model_loading` | Model is not ready yet | Wait for load, then recheck |
| `stream_incompatible` | Gateway did not provide complete live stream | Enable Anthropic-compatible streaming/update gateway |
| `tool_use_missing` | Model did not use required tool | Choose tool-capable model/config |
| `structured_output_missing` | Model did not return hiring structure | Choose structured-output-capable model/config |
| `context_too_small` | Model context is below 32K | Raise runtime context or choose another model |
| `context_probe_timeout` | 32K context probe did not finish in time | Preload/tune model or choose faster compatible model |
| `gateway_saturated` | Local model is busy | Stop other work/wait, then recheck |
| `response_incompatible` | Gateway response is not valid Anthropic Messages output | Update/reconfigure gateway |

No local code/message contains `claude auth login`.

## Persistence and Redaction

Persist:

- capability, model role/ID, pass/fail code, owner message/action, timestamps/duration, safe endpoint, Claude version;
- successful verified context lower bound.

Never persist:

- prompts/responses/tool payloads, auth/header values, raw URLs with user info/query, raw error body, temporary paths containing owner identity, subprocess env/argv dumps.

All error input passes common redaction for known secret values, authorization forms, URL credentials/query, control characters, and length.

## Runtime Blocking

A detected active-run failure in reach/auth/model/response/context classes immediately:

1. marks active local health `blocked` with sanitized code;
2. fails current run on its bound provider;
3. prevents new process start on that profile;
4. does not change active profile or fall back;
5. offers full recheck/recovery.

`gateway_saturated` is transient `busy`, not profile-blocking while retries/deadline remain.
