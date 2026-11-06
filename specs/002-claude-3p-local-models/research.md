# Research: Claude 3P Local Model Support

Feature: `002-claude-3p-local-models`. Research checked against official documentation on 2026-11-06. Each decision records rationale and rejected alternatives.

## D1 — Supported Claude integration surfaces

**Decision**: Use Claude Code's documented LLM-gateway path for Orbit's headless processes:

- `ANTHROPIC_BASE_URL` selects an Anthropic Messages-compatible endpoint.
- `ANTHROPIC_AUTH_TOKEN` supplies bearer auth; `ANTHROPIC_API_KEY` supplies `x-api-key` auth.
- A non-empty harmless placeholder is supplied to Claude even when the upstream gateway needs no auth.
- Every run names an exact model with `--model`.
- Local mode sets `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` and `skipWebFetchPreflight: true`; owner-enabled external tools remain separately disclosed.

Claude Desktop's interactive 3P mode is a different surface. It reads `inferenceProvider: "gateway"`, `inferenceGatewayBaseUrl`, credential/auth-scheme, and `inferenceModels` from its own supported configuration. It does **not** use Orbit's CLI environment variables.

Headless activation requires Claude Code **v2.1.259+**. That floor includes gateway retry events, custom-context handling used here, and `--permission-prompts none` for deterministic unattended readiness checks. Older clients get one action: `claude update`. Interactive support additionally checks that installed Claude Desktop exposes gateway configuration and `x-api-key`/bearer selection; an old app blocks only `Open in Claude`, not P1 headless operation.

**Rationale**:

- Official docs state a gateway credential takes precedence over a saved claude.ai login and can start without account sign-in.
- Official Desktop 3P docs explicitly support local per-user configuration and an account-free "start using provider configuration" path.
- Cloud sessions, Remote Control, and Claude-plan limits are not part of an LLM-gateway deployment, matching the feature's cloud-shift boundary.

**Alternatives considered**:

- Reimplement the agent loop against a local API: rejected; scope keeps the official unmodified Claude client.
- Treat CLI and Desktop configuration as one mechanism: rejected; official docs define separate sources and precedence.
- Trust any installed Claude version: rejected; older builds lack controls needed for deterministic, safe account-free runs.

## D2 — One provider boundary and legacy migration

**Decision**: Add `core/inference.py` as the only module that interprets provider state. It owns:

- lazy migration from legacy `staff.json.auth` (`subscription` or `api_key`);
- candidate local profile storage and readiness;
- activation/switch/removal transactions;
- run bindings, selected model, launch settings, connectivity, status, errors, usage labels, and redaction.

`engine.run()` and `onboard._ask()` call this module. `rolebook.distill()` already delegates to onboarding. `cloud.py` remains explicitly subscription-only. No other module builds inference credentials or endpoint settings.

Existing registries with no `inference` block are read exactly as today and are not rewritten on upgrade. The block is materialized only when an owner edits provider settings. The legacy `auth` field remains mirrored during the compatibility period, but routing code never reads it directly after the refactor.

**Rationale**: Current routing assumptions are duplicated in `engine.clean_env`, `onboard._ask`, `panel.claude_auth`, `orbit.claude_status`, `engine.online`, model/usage UI, and cloud shift. Centralization is needed to prove FR-009 and FR-014.

**Alternatives considered**:

- Add local branches in each current caller: rejected; easy to miss role sharing, hiring, diagnostics, or a future flow.
- Reuse `auth = "local"` alone: rejected; cannot represent endpoint, credential reference, model assignments, readiness, or revision safely.

## D3 — Keep the local provider credential away from employees

**Decision**: For every local Claude process, Orbit starts a short-lived loopback relay in the same trusted parent process:

1. Real credential is read from `~/Staff/.secrets/<credential_ref>` into parent memory only.
2. Claude gets a protected temporary settings file containing an Orbit relay URL and fixed non-secret placeholder.
3. Relay accepts only supported Claude API paths, strips incoming `Authorization`, `x-api-key`, cookies, user info, and custom routing credentials.
4. Relay inserts no upstream auth, `Authorization: Bearer <secret>`, or `x-api-key: <secret>` according to the profile.
5. Relay streams the upstream response and closes when the Claude process exits.

Local runs also use an Orbit-owned `CLAUDE_CONFIG_DIR` scoped by profile revision and employee. This prevents a saved Claude account credential or user gateway setting from participating and keeps local transcripts/sessions separate from account/API modes. The runtime directory and temporary settings are in the deny-read set.

**Rationale**:

- Claude settings `env` values reach subprocesses Claude starts. Passing a provider key directly would let a generated shell command or stdio MCP server read it, violating FR-015.
- `apiKeyHelper` returns one value in both auth headers and exposes a callable credential-producing command. It cannot express exact `none`/bearer/API-key behavior as cleanly.
- Relay also provides one enforceable point for destination pinning, model mapping, redaction, status classification, and no-fallback evidence.

**Alternatives considered**:

- Put the gateway credential in `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY`: rejected; child-process exposure.
- Put the key in inline `--settings`: rejected; process arguments and employee-readable settings risk.
- Store provider settings in employee workspaces: rejected; employees can edit/read them.
- Ask owners to configure shell profiles globally: rejected; unrelated inherited settings would influence Orbit and switching would be unsafe.

## D4 — Loopback address and redirect safety

**Decision**: Accept only `http` or `https` URLs whose host is a loopback literal or `localhost` resolving entirely to loopback. Allow a normalized path prefix because gateways may mount the API below one. Reject:

- user info (`user:pass@host`), query strings, fragments, control characters, encoded authority tricks;
- missing/invalid ports and non-loopback IPs;
- a hostname with any non-loopback resolution;
- every redirect, including loopback-to-loopback redirects.

At readiness time Orbit selects a responding numeric loopback address. Each relay re-resolves, confirms loopback, connects to the pinned numeric address, and preserves only the safe host/port/path contract. It never follows redirects. Owner-visible status renders the canonical non-secret base URL only.

**Rationale**: This handles loopback-to-remote redirect, DNS rebinding, stale validation, credential-bearing URLs, and host confusion without creating a general-purpose SSRF proxy.

**Alternatives considered**:

- Allow RFC1918/LAN hosts: rejected by v1 scope.
- Rely on `urllib` defaults: rejected; redirects are followed by default.
- Validate only when settings are saved: rejected; destination can change before a run.

## D5 — Readiness must prove behavior, not branding

**Decision**: A full readiness check runs for each distinct primary/fallback model and records separate outcomes for:

1. Claude installation/version.
2. Safe endpoint and loopback pin.
3. Reachability and credential acceptance.
4. Selected model availability/loading state.
5. complete, incremental SSE streaming sequence.
6. model-driven tool call executed in a temporary workspace with a checked canary result.
7. valid output through Orbit's actual hiring JSON schema path.
8. at least 32,000 input tokens through a bounded one-token-output challenge.

Raw protocol checks run first for fast diagnosis; real `claude -p` checks run through the exact relay/settings/model path Orbit will use. Activation requires every mandatory capability. Doctor always runs a full check. The first crew run after service startup or profile revision runs a full recheck once per process. A runtime failure immediately records a blocked health state.

Failed capability records use stable codes and one direct recovery action; raw gateway bodies are redacted and truncated. Candidate settings remain stored; active provider remains unchanged.

**Rationale**: "Anthropic-compatible" implementations vary. A text-only ping cannot prove streaming, tools, current request fields, structured hiring output, or context.

**Alternatives considered**:

- Trust `/v1/models` capability fields: rejected; fields are optional and don't prove the selected model follows them.
- Probe only the raw API: rejected; misses Claude Code request-shape and parsing incompatibility.
- Probe only Claude: rejected; errors become hard to classify and model discovery/manual correction is poorer.

## D6 — Model discovery, roles, and context

**Decision**:

- Query `GET /v1/models?limit=1000` with selected auth and a three-second discovery timeout. Refuse redirects. Preserve arbitrary model IDs; do not apply Claude Code's interactive discovery filter that keeps only IDs containing `claude`/`anthropic`.
- When discovery is absent/empty, accept manual exact IDs. A manual model must also declare its configured context window for the 32K challenge.
- Store `primary` and `fallback` as workload roles. Each employee gets `local_model_role`; default `primary`. Existing `model` remains the Claude-family preference used after switching back.
- Never change from primary to fallback because of an error or saturation. Fallback is used only when work/employee is explicitly assigned that role.
- Give Claude a synthetic `orbit-local-<role>-<revision>` model ID. Relay rewrites it to the exact selected gateway ID and rejects every unbound ID. Set all Claude background/default model variables to that same synthetic ID for the process.
- Set `CLAUDE_CODE_MAX_CONTEXT_TOKENS` to the verified assigned-model window (bounded to the client-supported range) and test the real path. At minimum, a 32K assignment must complete the generated context probe.

**Rationale**: Synthetic IDs prevent Claude from inferring a 200K/1M window or capabilities from a gateway model name. Separate local/cloud employee preferences preserve team data and make switching reversible.

**Alternatives considered**:

- Pass `sonnet`/`haiku` aliases: rejected; aliases move across releases and can request an unserved model.
- Reuse employee `model` for local exact IDs: rejected; destroys existing cloud-mode preference and validation assumptions.
- Automatic primary→fallback on error: rejected; violates owner visibility and fail-closed intent.

## D7 — Binding, capacity, and retries

**Decision**: Define the start of an inference run as owner work acceptance, before waiting on employee/provider locks. Capture an immutable provider binding then.

Local profiles have `max_parallel_runs` (default `1`). Accepted work waits FIFO with a visible `waiting_capacity` state. One Claude process is launched when admitted. During a process, `system/api_retry` events with `429`/`529` or equivalent gateway errors change the visible state to `waiting_gateway`; Claude's own same-request retry resumes it. The existing task timer remains the hard deadline.

Orbit does not start a second process for a partial/malformed/dropped stream. It permits only Claude's documented pre-response retry behavior. A known capacity response before any response body may continue on the same process; everything else fails closed.

Provider switching changes the active revision for subsequently accepted work only. Profile removal is blocked while any accepted binding references it.

**Rationale**: This preserves pending work, prevents duplicate tools/commands, handles single-slot local runtimes, and gives deterministic switch semantics.

**Alternatives considered**:

- Keep current routine-only semaphore: rejected; chats and background flows can still saturate the model.
- Kill/reroute queued work on switch: rejected; silently changes provider after acceptance.
- Orbit-level replay after every network error: rejected; can duplicate tool effects after a partial response.

## D8 — Cloud shift and usage semantics

**Decision**:

- Local activation first disables each existing cloud trigger while the old subscription path is still active. If any trigger cannot be disabled, activation does not commit.
- Preserve desired `cloud_shift` preference and mark it `suspended_by_local`. Local status explains that a local model cannot work while the computer/gateway is off. New local hires do not default cloud shift on.
- Switching back to a validated subscription mode clears suspension and rearms desired shifts; failures remain visible per employee without changing team data.
- Local run logs store measured input/output/cache tokens when present. They never infer tokens from Anthropic list-price cost and never treat Claude's client-side `total_cost_usd` estimate as local cost. Cost is `unknown` unless the selected gateway returns an explicit trusted measurement.
- Hide Claude plan meters and high-plan-usage model switching in local mode. Weekly token budgets can remain as owner work limits, relabeled as local token budgets.

**Rationale**: Existing cloud triggers are external state and must be stopped before claiming inference is local. Claude's client-side dollar estimate is not proof of local cost.

**Alternatives considered**:

- Set all cloud preferences to false: rejected; loses reversible owner settings.
- Leave triggers enabled but hide controls: rejected; cloud inference could continue after local activation.
- Show `total_cost_usd` as local spend: rejected; can be an Anthropic-equivalent estimate unrelated to local billing.

## D9 — Interactive Claude Desktop 3P

**Decision**: Add `core/desktop3p.py` to inspect supported effective configuration sources:

- local config library (`Claude-3p/configLibrary`) on macOS/Windows/Linux;
- Windows machine/user policy, respecting machine precedence;
- macOS managed preferences;
- Linux root-managed JSON.

It returns only sanitized facts: source, provider, canonical base URL, auth scheme, credential presence/match boolean, model IDs, app version, and verification state. Secret comparison, when readable, is constant-time in memory; values are never returned or logged. Bootstrap/admin-managed configurations that cannot be proven locally are `unverified`, never assumed matching.

V1 does not write these global settings. Orbit shows the exact official in-app path (enable Developer Mode → Configure Third-Party Inference → Gateway → apply/restart), values without the credential, and asks the owner to enter/approve the credential in Claude. After restart Orbit re-inspects. `Open in Claude` proceeds only on `matching`; then the existing employee workspace, guard, tools, memory, and deep link are used.

**Rationale**: Official docs say Desktop ignores CLI gateway env and applies provider config at host level. Directly editing undocumented config-library metadata would risk another application's global state. Guided supported UI is safer and meets explicit-consent requirements.

**Alternatives considered**:

- Write Desktop config files/registry automatically: rejected for v1; unsupported and global.
- Put gateway env in `.claude/settings.local.json`: rejected; Desktop-managed provider routing takes precedence.
- Open and merely trust the app: rejected; Orbit could falsely claim a cloud session is local.

## D10 — Test and qualification strategy

**Decision**:

- Unit/integration seam: local `ThreadingHTTPServer` fake gateways for healthy, auth reject, missing model, redirect, malformed stream, low context, and saturation; fake `claude` executable emits stream-json/retry/tool/result events.
- Security seam: socket/HTTP trap fails any local-mode attempt to contact non-loopback or an Anthropic inference host; spawned-command/env assertions search for real secrets and credential-bearing URLs.
- Existing subscription/API-key tests remain unchanged and run on every OS job.
- Real qualification: same standard task suite against at least two independent current Anthropic-compatible local servers (initial targets: Ollama 0.14+ and LM Studio 0.4.1+, or qualified replacements) on each supported OS. A product/version is evidence, not an allowlist; it must pass Orbit readiness that day.
- Benchmark relay start/first-forward against direct gateway calls for 20 prompts; median Orbit-added delay must stay under SC-007.

**Rationale**: CI cannot assume GPU/model availability. Fake seams prove Orbit's routing/safety deterministically; real qualification catches model/gateway interoperability and quality regressions.

**Alternatives considered**:

- Download a model in CI: rejected; heavy, hardware-sensitive, and outside feature scope.
- Declare one gateway supported by name: rejected; SC-006 requires independent implementations and behavior can change by version.

## Primary Sources

- Claude Code: [Connect to an LLM gateway](https://code.claude.com/docs/en/llm-gateway-connect)
- Claude Code: [Gateway compatibility guide](https://code.claude.com/docs/en/llm-gateway-protocol)
- Claude Code: [Model configuration](https://code.claude.com/docs/en/model-config)
- Claude Code: [Environment variables](https://code.claude.com/docs/en/env-vars)
- Claude Code: [Authentication](https://code.claude.com/docs/en/authentication)
- Claude Code: [Programmatic/headless mode](https://code.claude.com/docs/en/headless)
- Claude Desktop 3P: [Overview](https://claude.com/docs/third-party/claude-desktop/overview)
- Claude Desktop 3P: [Gateway deployment](https://claude.com/docs/third-party/claude-desktop/gateway)
- Claude Desktop 3P: [In-app configuration](https://claude.com/docs/third-party/claude-desktop/in-app-configuration)
- Claude Desktop 3P: [Configuration implementation](https://claude.com/docs/third-party/claude-desktop/configuration-format)
- Claude Desktop 3P: [Code integration](https://claude.com/docs/third-party/claude-desktop/code)
- Claude Desktop 3P: [Telemetry and egress](https://claude.com/docs/third-party/claude-desktop/telemetry)
- Ollama: [Anthropic compatibility](https://docs.ollama.com/api/anthropic-compatibility)
- LM Studio: [Claude Code integration](https://lmstudio.ai/blog/claudecode)
