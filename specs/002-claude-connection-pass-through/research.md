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
- Existing process classification and Claude-provided output/error handling remain unchanged.
- Orbit-generated registry data, run metadata, activity records, files, and UI responses never copy values from inherited connection environment or settings.
- No message claims which provider was used, whether inference stayed local, or whether Claude can fall back.

**Rationale**: This deliberately gives up provider-specific advice. Specific diagnosis belongs in Claude itself (`claude doctor`, `/status`, or a direct manual run). Separating Orbit-originated metadata from Claude output avoids both credential copying and an accidental promise that Orbit redacts arbitrary model/client output.

**Alternatives considered**:

- Redact every Claude output/error: changes existing logging semantics and cannot reliably identify secrets in arbitrary text.
- Log inherited environment keys or values for support: violates the pass-through privacy boundary.

## D8 — Cloud Shift Is a Separate Account Contract

**Decision**: Cloud Shift qualifies only for `loggedIn: true` with `authMethod: "claude.ai"`. `third_party`, `api_key`, `api_key_helper`, `oauth_token`, and `none` remain outside Orbit's supported Cloud Shift contract; ordinary local work is unaffected.

Read-only display may cache eligibility in memory for at most 60 seconds. Manual enablement, new-hire auto-enablement, and every Orbit-initiated Cloud Shift Claude command force a fresh account check. If an enabled shift loses eligibility, Orbit keeps its configured flag visible but blocks subsequent local cloud commands and records an account-only reason.

**Rationale**: A short display cache avoids repeated one-second status calls while rendering the panel. A cached result must never authorize a state change or launch. Keeping the enabled flag preserves owner intent and makes lost eligibility visible instead of silently rewriting configuration.

**Alternatives considered**:

- Use the same cache for enablement and launches: stale positive status can cross the account-only boundary.
- Disable the shift automatically after one failed check: destroys owner intent and obscures why work stopped.
- Promise cancellation of already-scheduled remote work while Orbit is offline: Orbit cannot retroactively revoke an external schedule without a working account connection.

## D9 — No New Persisted Data Model

No persisted provider profile, endpoint, credential reference, readiness result, run binding, or migration is needed. Existing `staff.json.auth` stays for backward compatibility with Orbit's stored API key. Team and employee records are untouched. Transient launch classification, availability, eligibility, and diagnostic-provenance concepts are documented in [data-model.md](./data-model.md).

## D10 — Test Strategy

- Fake Claude executable records argv, selected setting sources, and environment sentinels.
- One temporary Orbit installation completes setup, hiring, and an employee run while account status is signed out.
- An enumerated source inventory covers every production Claude invocation; a regression assertion rejects unclassified direct launches.
- Employee, onboarding, and guard-plugin paths assert exact environment, setting-source, and safety behavior.
- Socket trap fails any `api.anthropic.com` probe while fake Claude succeeds.
- Cloud tests cover every known auth method, fresh-versus-cached checks, manual and automatic enablement, each cloud launch wrapper, and eligible-to-ineligible transitions.
- Account isolation tests add an arbitrary future-provider sentinel and prove it is excluded without naming its prefix.
- Existing legacy API-key tests assert both environment and employee/onboarding setting-source isolation.
- Diagnostic tests use a non-echoing fake for Orbit-originated leak assertions and a separate marker-output case to prove Claude output handling is unchanged.
- Static checks scan tracked production, setup, template, CI, and documentation files, allowing only exact account-only Cloud Shift wording.

## D11 — Exhaustive Launch Classification

**Decision**: Maintain the production invocation inventory in [contracts/claude-launch.md](./contracts/claude-launch.md). Every direct use of the resolved Claude executable in `orbit` or `core/` must correspond to one named inventory entry and one of five behavioral classes: installation check, ordinary pass-through, legacy API-key, interactive application, or Cloud Shift.

All employee chats, routines, summaries, role processing, scheduled follow-ups, and similar work converge through `engine.run()`/`engine.stream()` and therefore share the employee launch policy. Structured hiring uses `onboard._ask()`. Guard plugin administration is a separate non-inference invocation. Cloud Shift has five direct command families in `core/cloud.py`.

**Rationale**: Testing representative calls is not evidence for “100%.” An explicit inventory plus a source-level regression assertion makes a newly added bypass visible before implementation ships.

**Alternatives considered**:

- Rely only on the shared helper: a future direct `subprocess` call can bypass it silently.
- Search for the text `claude`: produces many documentation/UI false positives and misses resolved executable variables.
- Add a provider/inference wrapper module: unnecessary; the inventory classifies process launches without making Orbit own inference.

## D12 — Cloud Account Environment Allowlist

**Decision**: Build the Cloud Shift account environment from an empty mapping plus a documented platform bootstrap allowlist. Force the default owner home/profile used by Claude's native credentials, a known executable search path, and platform temporary directories. Copy only basic locale and OS process-bootstrap values. Set controlled `TERM` only for the interactive cloud-session bootstrap. Omit every unlisted variable, including `CLAUDECODE`, `CLAUDE_CONFIG_DIR`, provider/endpoint/token/API-key variables, proxy variables, and unknown future connection variables. Cloud inference commands explicitly use empty setting sources.

The contract lists the allowed POSIX/macOS and Windows keys. Account status uses the same environment; `auth status` does not create a model session or load a user setting source.

**Rationale**: Prefix subtraction can never prove absence of future provider variables. Official authentication documentation places the default login in the macOS Keychain or the default home/profile credential file, while `CLAUDE_CONFIG_DIR` selects a different credential/config set. A minimal allowlist therefore retains executable resolution, the default owner home/profile, temporary files, locale, and Windows process bootstrap without inheriting unrelated session variables.

**Alternatives considered**:

- Keep the current `ANTHROPIC_`/`CLAUDE_CODE_` denylist: misses unrelated or future provider names.
- Use a completely empty environment: can break shebang resolution, owner-home account state, temporary files, Windows process startup, and native credential stores.
- Reuse ordinary pass-through then clear selected values: violates isolation by default.

## D13 — Repository-Wide Copy and Configuration Checks

**Decision**: Validate all tracked production, setup, template, CI, and user-documentation files. Exclude historical feature artifacts and deliberate test fixtures. Treat account-login wording as valid only at exact allowlisted Cloud Shift messages. Also inventory hard-coded Anthropic host checks, provider-variable filtering, and direct Claude executable calls.

**Rationale**: A hand-picked path list cannot satisfy a repository-wide success criterion and allows stale installer/template copy to survive.

**Alternatives considered**:

- Search only currently planned files: misses future and less-visible owner surfaces.
- Ban every login phrase globally: rejects tests and legitimate account-only Cloud Shift guidance.

## D14 — Supported Validation Platforms

**Decision**: Use the repository's existing CI matrix: macOS, Ubuntu 24.04, native Windows unit coverage, and Ubuntu 24.04 under WSL2. Feature tests use fake Claude and no provider credentials on every job. Native Windows MXC runtime validation remains governed by feature 001 and is not added here.

**Rationale**: This names the actual automated platform contract instead of leaving “supported CI platforms” undefined.

**Alternatives considered**:

- Require local execution on every operating system: not reproducible for one implementation session.
- Add live Claude/provider checks to CI: consumes credentials/resources and contradicts the fake-only test boundary.

## Primary Sources

- Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference
- Claude Code settings and precedence: https://code.claude.com/docs/en/settings
- Claude Code settings reference: https://code.claude.com/docs/en/settings-reference
- Claude Code authentication: https://code.claude.com/docs/en/authentication
- Claude Code environment variables: https://code.claude.com/docs/en/env-vars
- Claude Code third-party integrations: https://code.claude.com/docs/en/third-party-integrations
- Claude Code LLM gateways: https://code.claude.com/docs/en/llm-gateway
