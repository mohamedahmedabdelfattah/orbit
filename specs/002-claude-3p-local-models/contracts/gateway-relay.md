# Contract: Local Gateway and Orbit Relay

**Producer**: Orbit local inference relay (`core/inference.py`).

**Consumers**: Claude Code process (downstream/client side) and owner-selected local gateway (upstream side).

The relay is a short-lived credential and routing boundary. One relay belongs to one immutable run binding or readiness probe.

## Upstream Gateway Minimum

Required:

- Anthropic Messages-compatible `POST <base>/v1/messages`.
- Non-streaming and `stream: true` responses.
- Complete ordered SSE sequence through `message_delta` and `message_stop`.
- Model-driven `tool_use` and accepted `tool_result` continuation.
- Orbit hiring structured-output path.
- Selected model accepts at least 32,000 input tokens.

Optional:

- `GET <base>/v1/models?limit=1000` for discovery.
- `POST <base>/v1/messages/count_tokens` for exact context accounting.
- Prompt caching/usage detail. Missing caching may reduce performance but is not a v1 activation gate.

The gateway may implement more endpoints; relay exposes only those Claude needs. Orbit does not install, operate, or patch it.

## Accepted Base URL

1. Scheme: `http` or `https`.
2. Host: numeric loopback (`127.0.0.0/8`, `::1`) or `localhost` resolving only to loopback.
3. Port: explicit valid port or scheme default.
4. Path: empty or normalized prefix; no `..`, backslash authority trick, or encoded separator that changes authority/path interpretation.
5. Forbidden: user info, query, fragment, NUL/control characters.
6. Redirects: every 3xx is an error. Owner must enter final URL directly.

The validator canonicalizes display form. Each connection revalidates resolution and uses a numeric loopback destination. Any non-loopback change fails before a credential is read/sent.

## Relay Lifecycle

```text
validate profile revision
  → resolve/pin loopback
  → load credential into parent memory
  → bind random loopback port
  → write protected temporary Claude settings (safe relay URL + fixed placeholder)
  → spawn one Claude process
  → stream requests/responses
  → terminate relay, zero/drop credential refs, delete temp settings
```

- Bound interface is loopback only.
- Relay has no reusable external URL and no stored upstream secret.
- Temporary path is under Orbit runtime, owner-only, deny-read for employee tools, and absent from run/activity output.
- Relay closes on normal exit, timeout, process spawn failure, or parent teardown.

## Downstream Authentication

Claude receives a fixed documented non-secret value such as `orbit-local-placeholder`. It exists only because Claude requires an active credential source to skip account sign-in. It is not generated, not an upstream credential, and grants nothing to the gateway.

Relay never forwards it.

## Header Transformation

Before upstream forwarding, remove case-insensitively:

- `Authorization`
- `x-api-key`
- `Cookie` / `Set-Cookie` request equivalents
- proxy auth headers
- owner-specified/custom credential or routing headers not declared by this profile
- hop-by-hop headers (`Connection`, `Proxy-Connection`, `Transfer-Encoding`, etc.)

Then add exactly one selected upstream authentication shape:

| Profile style | Upstream addition |
| --- | --- |
| `none` | no credential header |
| `bearer` | `Authorization: Bearer <provider secret>` |
| `api_key` | `x-api-key: <provider secret>` |

Preserve protocol fields needed by Anthropic Messages, including `anthropic-version`, compatible `anthropic-beta` values, content type, Claude session/agent IDs, and safe user agent. Do not add saved Claude OAuth/API credentials.

## Allowed Paths and Methods

| Method/path | Purpose |
| --- | --- |
| `POST /v1/messages` | inference |
| `POST /v1/messages/count_tokens` | optional token count |
| `GET /v1/models` | optional discovery/readiness |
| `HEAD /api/hello` | optional Claude connection warm-up; may return upstream result or local no-content success without leaving loopback |

Path is appended below configured base path. Every other path/method returns local 404/405 and is not forwarded.

## Model Binding and Rewrite

Claude receives one synthetic ID for the selected role, for example `orbit-local-primary-r3`. Relay parses JSON request body and applies:

1. Request `model` must equal the binding's synthetic ID (or an explicitly registered same-process background alias).
2. Rewrite it to the exact bound upstream model ID.
3. Reject any other model locally with `model_binding_mismatch`; never pass it upstream.
4. Do not rewrite prompts, tools, system blocks, messages, cache controls, output format, or other model content.

For discovery requests, no model rewrite occurs. Response model IDs may be normalized back to the synthetic client ID for Claude parsing; Orbit run logs always use the exact upstream ID from the binding.

## Streaming

- Forward response status and safe headers, including `content-type`, `retry-after`, `x-should-retry`, and usage/rate metadata.
- Stream bytes/chunks as received. No full-response buffering, content logging, or semantic rewrite.
- Preserve SSE ordering, ping events, final delta, and stop event.
- If upstream ends early/malformed, close downstream with a sanitized relay diagnostic; do not synthesize success.
- Request body may be buffered only up to the documented Claude API request bound so model ID can be validated/rewritten. Body is never persisted/logged.

## Error Mapping

Relay preserves safe upstream status while recording only sanitized class:

| Evidence | Orbit code |
| --- | --- |
| connect refused/timeout | `gateway_unreachable` |
| upstream 401/403 | `credential_rejected` |
| model missing/unloaded error | `model_unavailable` |
| 429/529 or retryable capacity response | `gateway_saturated` |
| context/token-limit rejection | `context_too_small` or `context_limit` |
| invalid/malformed response | `response_incompatible` |
| redirect | `redirect_refused` |
| destination no longer loopback | `destination_unsafe` |

Raw upstream bodies are bounded, secret-redacted, and retained only long enough to classify. Owner-facing text comes from stable code, not echoed raw body.

## Security Invariants

1. Upstream credential exists only in secret storage and trusted parent memory/header write.
2. No upstream credential in Claude argv/env/settings, child tools, panel/API, logs, errors, activity, or process command line.
3. Relay cannot connect to non-loopback or follow a redirect.
4. Relay cannot select a provider/model outside immutable binding.
5. A saved Claude login/API key cannot pass through the relay.
6. Failure is terminal for this route; no direct Anthropic or alternate gateway retry.
7. Relay timing metrics contain durations/status/classes only, never content or header values.
