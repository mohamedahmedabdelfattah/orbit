# Claude Connection Pass-Through Design

**Date:** 2026-11-06

**Status:** Approved

## Intent

Orbit must require an installed Claude Code client, not a Claude account sign-in. Claude Code remains responsible for authentication, provider selection, gateway configuration, model routing, and inference. Orbit remains responsible for employee workflows, prompts, workspaces, tools, sandboxing, and safety controls.

## Goals

- Allow setup and normal employee work when `claude auth status` reports no Claude account but the installed Claude client can use another configured connection.
- Make Orbit-launched local Claude processes use the owner's effective Claude user configuration.
- Keep existing Claude-account and Orbit-managed Anthropic API-key paths working.
- Keep account-only Cloud Shift separate and unavailable without a qualifying Claude account session.
- Make setup, status, and errors provider-neutral.

## Non-goals

- Provider selection, endpoint entry, model discovery, gateway readiness probes, or provider-specific diagnostics in Orbit.
- An Orbit inference client, relay, credential broker, model runtime, or cloud fallback.
- Claims that a connection is local, private, compatible, or incapable of fallback; Claude owns those behaviors.
- Isolation from owner-installed Claude hooks, plugins, skills, or other user settings. Exact pass-through treats that configuration as trusted.

## Constraints

- Orbit background services do not reliably inherit ephemeral shell exports after login or restart. Persistent Claude user or managed settings, native credential state, or OS service environment must hold configuration needed by unattended work.
- Loading `user` settings also loads owner customizations. Claude exposes no documented provider-only settings source.
- Existing Orbit safety flags, inline sandbox settings, guard plugin, strict MCP configuration, and deny rules stay in place. They do not turn arbitrary owner hooks into Orbit-controlled code.
- Legacy `auth = "api_key"` installations retain their isolated stored-key behavior.

## Approaches Considered

1. **Remove only the sign-in gate.** Rejected: Orbit would still strip backend variables, exclude user settings, preflight `api.anthropic.com`, and emit account-specific errors.
2. **Exact Claude pass-through.** Selected: load Claude user settings and preserve connection environment for ordinary local work. Smallest approach matching manual Claude behavior.
3. **Selective provider import or Orbit relay.** Rejected: adds provider knowledge, credential handling, and ongoing inference compatibility work outside the requested scope.

## Design

- Setup and doctor verify that Claude Code is installed and executable. They do not require `loggedIn: true` and never block on Claude account state.
- Ordinary employee runs load `user,project` settings. Structured onboarding calls load `user` settings. Orbit continues supplying its own higher-precedence command flags and inline settings.
- Ordinary runs inherit Claude/provider environment values. Orbit removes only narrowly required recursion markers, then adds employee and Orbit runtime variables.
- Legacy Orbit API-key mode keeps its current sanitized environment, stored key injection, and isolated settings sources.
- Orbit removes Anthropic-host connectivity as a prerequisite for local work. It invokes Claude and classifies the returned error; transient failures retain existing later-retry behavior.
- Generic status and failure copy refers to Claude's configured connection. Account sign-in language appears only on Cloud Shift controls.
- Cloud Shift performs its own account-specific eligibility check and never auto-enables for third-party or unconfigured Claude connections.
- Interactive **Open in Claude** continues to open the employee workspace. The Claude application owns its connection and user configuration.
- Tests use fake Claude executables and settings/environment sentinels. No real provider or model is required in CI.

## Accepted Trust Boundary

Owner Claude user configuration is trusted input. User hooks and plugins may execute in Orbit-launched Claude sessions. Orbit does not copy inherited credential values into its registry, workspace files, logs, or UI, but does not add a new credential-isolation layer beyond Claude's own behavior.
