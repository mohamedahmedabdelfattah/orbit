# Research: Claude Connection Pass-Through

Feature: `002-claude-connection-pass-through`

Checked against current official Claude Code documentation on 2026-11-06.

## D1 — Claude, Not Orbit, Owns the Connection

**Decision**: Orbit treats the installed `claude` executable as its inference boundary. Orbit does not identify, configure, validate, or route providers.

Claude Code already supports several authentication/provider methods. Its current `auth status` output can classify `claude.ai`, `oauth_token`, `api_key`, `api_key_helper`, and `third_party`. Therefore, `loggedIn` as a Claude-account test is not a valid global Orbit readiness gate.

**Rejected**:

- Add a Local gateway mode: duplicates connection ownership and contradicts requested scope.
- Reimplement inference: unnecessary and significantly larger.
- Remove only setup's `sys.exit`: later environment, setting-source, connectivity, and error assumptions would still break the connection.

## D2 — Installation Check, Actual-Call Readiness

**Decision**: Setup and doctor require a resolvable executable and successful version invocation. They do not perform account readiness. Actual hiring and employee calls are the connection readiness check.

**Rationale**:

- A setup inference probe consumes provider resources and still cannot establish long-term readiness.
- Claude owns connection-specific validation and error text.
- Installation is the only provider-independent prerequisite Orbit can prove without implementing provider support.

## D3 — Load User Settings Exactly

**Decision**:

- Ordinary employee runs use `--setting-sources user,project`.
- Structured onboarding uses `--setting-sources user`.
- Orbit's existing inline `--settings`, command flags, guard plugin, explicit plugin bundle, strict MCP config, prompts, and model/effort arguments remain.

Claude settings precedence puts command-line settings above project and user settings, but some list values merge. Loading user settings can activate owner hooks, plugins, skills, permission rules, credential helpers, model overrides, and environment values. The owner explicitly selected this trust model because it is the only minimal path matching manual Claude behavior.

**Rejected**:

- Keep `--setting-sources project`: blocks common persistent user configuration and fails the "whatever Claude uses" goal.
- `--safe-mode`: preserves authentication/model selection but disables plugins and hooks, including Orbit's own guard/plugin behavior.
- `--bare`: disables customization needed by Orbit.
- Parse only provider-related settings: creates an evolving provider-settings compatibility layer.

## D4 — Preserve Connection Environment, Keep Legacy API-Key Isolation

**Decision**: Centralize Claude launch environment construction in `core/engine.py`.

For ordinary pass-through mode:

- start from the process environment;
- remove `CLAUDECODE`, which otherwise prevents nested Claude invocation;
- override only Orbit-owned runtime values such as employee/workspace paths and `CLAUDE_CODE_FORK_SUBAGENT=0`;
- retain `ANTHROPIC_*`, provider-specific `CLAUDE_CODE_*`, cloud-provider variables, proxy values, and `CLAUDE_CONFIG_DIR` if present.

For legacy `staff.json.auth == "api_key"`:

- preserve current provider-variable stripping;
- inject only Orbit's stored `anthropic_api_key`;
- retain current isolated setting sources so user config cannot reroute the stored key.

**Rationale**: Existing API-key installations are an explicit Orbit-owned path and must not silently change. Default/legacy subscription state becomes provider-transparent because it never represented connection details beyond an account assumption.

## D5 — Persistent Service Configuration

Orbit services on macOS, Linux, WSL, and Windows do not reliably inherit terminal-only exports after reboot. They do run as the owner and can read persistent Claude user/managed settings and native credential state.

**Decision**: Do not capture or persist shell environment in Orbit. Documentation tells owners to place unattended connection configuration where Claude can read it from the background service: user/managed settings, native credentials, or OS service environment.

Capturing all shell values would persist unrelated secrets. Selecting only provider values would make Orbit provider-aware.

## D6 — No Anthropic Preflight for Ordinary Work

**Decision**: Remove `api.anthropic.com` connectivity as a prerequisite from `engine.run()` and scheduler dispatch. Start Claude optimistically. Classify its actual result and keep existing delayed retry callbacks for transient routine failures.

The hard-coded socket probe cannot represent local gateways, Bedrock, Vertex, Foundry, custom gateways, proxies, or future Claude-supported paths. It can also cause a ten-minute delay before a healthy local connection is tried.

Cloud Shift may retain a separate Anthropic/account-specific check because it is explicitly an Anthropic cloud feature.

## D7 — Provider-Neutral Status and Errors

**Decision**:

- Panel and checklist show Claude installed/available, not signed in/out.
- Generic auth/network/rate errors refer to "Claude's configured connection."
- Raw safe detail remains in existing run logs.
- No message claims which provider was used, whether inference stayed local, or whether Claude can fall back.

This is deliberate loss of provider-specific advice. Specific diagnosis belongs in Claude itself (`claude doctor`, `/status`, or a direct manual run).

## D8 — Cloud Shift Is a Separate Account Contract

**Decision**: `cloud.available()` performs a cached, account-only status check with provider variables and user setting sources excluded. Cloud Shift qualifies only for `loggedIn: true` with `authMethod: "claude.ai"`. `third_party`, `api_key`, `api_key_helper`, `oauth_token`, and `none` remain outside Orbit's supported Cloud Shift contract; ordinary local work is unaffected.

Cloud Shift commands keep their current sanitized environment and empty setting sources. New-hire defaulting already calls `cloud.available()`; strengthening that function prevents accidental enablement.

## D9 — No New Data Model

No provider profile, endpoint, credential reference, readiness result, run binding, or migration is needed. Existing `staff.json.auth` stays for backward compatibility with Orbit's stored API key. Team and employee records are untouched.

## D10 — Test Strategy

- Fake Claude executable records argv, selected setting sources, and environment sentinels.
- Setup test returns signed-out account status but successful version/print behavior.
- Employee and onboarding tests assert exact setting-source and safety arguments.
- Socket trap fails any `api.anthropic.com` probe while fake Claude succeeds.
- Cloud tests cover account, third-party, API-key, and no-auth methods.
- Existing legacy API-key, sandbox, guard, MCP, session, and platform suites remain regression gates.
- Static copy checks reject global account-sign-in requirements outside the Cloud Shift boundary.

## Primary Sources

- Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference
- Claude Code settings and precedence: https://code.claude.com/docs/en/settings
- Claude Code settings reference: https://code.claude.com/docs/en/settings-reference
- Claude Code authentication: https://code.claude.com/docs/en/authentication
- Claude Code environment variables: https://code.claude.com/docs/en/env-vars
- Claude Code third-party integrations: https://code.claude.com/docs/en/third-party-integrations
- Claude Code LLM gateways: https://code.claude.com/docs/en/llm-gateway
