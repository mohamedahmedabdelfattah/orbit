# Feature Specification: Claude Connection Pass-Through

**Target Branch**: `main` (planning worktree currently detached)

**Created**: 2026-11-05

**Revised**: 2026-11-06

**Status**: Approved design and implementation tasks; ready for analysis

**Input**: "Bypass the Claude sign-in requirement. Orbit should accept the installed Claude client and use whatever inference or connection Claude already has, without Orbit adding inference support."

Orbit currently treats a Claude account session as a general prerequisite even though Claude Code supports other configured authentication and provider paths. Orbit also removes Claude/provider environment values, excludes Claude user settings from headless work, checks Anthropic connectivity before runs, and translates failures into account-login instructions. This feature makes Orbit transparent to Claude's connection rather than adding a provider system.

## User Scenarios & Testing

### User Story 1 - Set Up Orbit Without Claude Account Sign-In (Priority: P1)

An owner has Claude Code installed and configured to work through a connection Claude supports. They can set up Orbit without signing in to a Claude account. Orbit checks the client installation, then lets Claude handle the connection when actual work begins.

**Why this priority**: The current account gate blocks every later flow even when Claude itself can work.

**Independent Test**: Use a fake Claude executable whose account status is signed out but whose print-mode invocation succeeds. Complete Orbit's mandatory Claude check without any login instruction.

**Acceptance Scenarios**:

1. **Given** Claude Code is installed but `claude auth status` reports no Claude account, **When** the owner runs setup, **Then** the Claude check passes based on installation and setup does not request account login.
2. **Given** Claude Code is absent or cannot execute, **When** setup or doctor runs, **Then** Orbit blocks with one installation or executable-repair action.
3. **Given** Claude is installed but its configured connection is broken, **When** setup runs, **Then** setup does not mislabel that state as missing account sign-in; the first actual Claude call reports a connection failure.

---

### User Story 2 - Use Claude's Existing Connection Everywhere (Priority: P1)

The owner configures Claude itself. Orbit's hiring interview, employee chats, routines, summaries, role processing, and other local model-backed work use that same effective Claude connection without storing or selecting a provider in Orbit.

**Why this priority**: Removing setup's gate has no value if later Orbit subprocesses erase the connection.

**Independent Test**: Put sentinel connection values in Claude user settings and the process environment, run fake-Claude hiring and employee paths, and verify each process sees them together with unchanged Orbit safety arguments.

**Acceptance Scenarios**:

1. **Given** connection configuration exists in Claude user settings, **When** an employee run starts, **Then** Claude receives `user,project` setting sources plus Orbit's project, sandbox, guard, tool, and MCP controls.
2. **Given** connection configuration exists in Claude user settings, **When** Orbit generates structured hiring output, **Then** Claude receives the `user` setting source while onboarding's no-tools and strict-MCP controls remain.
3. **Given** relevant Claude/provider variables exist in Orbit's process environment, **When** ordinary local work starts, **Then** Orbit preserves them except for narrowly documented recursion markers.
4. **Given** an existing Orbit installation explicitly uses Orbit's stored Anthropic API key, **When** work starts, **Then** its previous isolated environment and stored-key behavior remain unchanged.
5. **Given** owner user settings include hooks or plugins, **When** Orbit starts ordinary local work, **Then** Claude may load them as trusted owner configuration; Orbit does not claim to isolate them.

---

### User Story 3 - Avoid Anthropic-Specific Blocking and Guidance (Priority: P2)

Local Orbit work starts without an `api.anthropic.com` preflight. Claude's actual result determines whether its configured connection works. Errors and status do not assume a particular provider.

**Why this priority**: A healthy non-Anthropic or same-computer connection may work while Anthropic is unreachable.

**Independent Test**: Make every socket attempt to `api.anthropic.com` fail while fake Claude succeeds. Verify an employee task starts immediately and completes.

**Acceptance Scenarios**:

1. **Given** Anthropic is unreachable but Claude's configured connection works, **When** a chat or routine starts, **Then** Orbit invokes Claude without waiting for Anthropic connectivity.
2. **Given** Claude reports a connection, authentication, or provider error, **When** Orbit presents the failure, **Then** the message refers to Claude's configured connection and directs the owner to verify Claude, not necessarily to `claude auth login`.
3. **Given** Claude reports a transient network or rate-limit failure, **When** a scheduled routine fails, **Then** Orbit retains its existing later-retry behavior without selecting another provider.

---

### User Story 4 - Keep Account-Only Features Honest (Priority: P2)

Cloud Shift remains an Anthropic-account feature. Owners using another Claude connection can use local Orbit work, but Cloud Shift stays off and explains its separate account requirement.

**Why this priority**: Removing the global account requirement must not make an account-only feature appear available or auto-enable it for new hires.

**Independent Test**: Return `third_party`, `api_key`, `none`, and `claude.ai` account methods from fake account checks. Verify Cloud Shift is available only for the qualifying account method and only that path can auto-enable it.

**Acceptance Scenarios**:

1. **Given** Claude uses a third-party connection and has no qualifying Claude account session, **When** an employee is hired, **Then** local work starts normally and Cloud Shift is not enabled.
2. **Given** a qualifying Claude account session exists, **When** the owner enables Cloud Shift, **Then** existing Cloud Shift behavior remains unchanged.
3. **Given** no qualifying account exists, **When** the owner views or enables Cloud Shift, **Then** Orbit explains that this optional feature needs a Claude account without treating local work as broken.

### Edge Cases

- A stale or absent Claude account exists beside a working third-party connection.
- Claude user settings are malformed or a user hook fails before inference.
- The connection exists only in an ephemeral shell export that Orbit's login service does not inherit.
- A gateway or provider accepts Claude's selected model aliases differently; Claude owns mapping and errors.
- User settings add hooks, plugins, permission rules, models, or environment values that change session behavior.
- Provider credentials in inherited settings or environment become available according to Claude's own subprocess behavior.
- Claude's configured connection changes while Orbit work is queued or a session is resumable.
- Anthropic is offline while a local connection is healthy, or Anthropic is healthy while another configured connection is not.
- A saved Claude account and another configured credential coexist; Claude decides precedence and fallback.
- Cloud Shift was previously enabled, then account eligibility disappears.

## Requirements

### Functional Requirements

#### Setup and Status

- **FR-001**: Orbit MUST require an installed, executable Claude Code client for non-demo operation.
- **FR-002**: Orbit MUST NOT require a Claude account, a successful Claude account login, or `loggedIn: true` to complete setup or pass the mandatory Claude installation check.
- **FR-003**: Setup, doctor, onboarding checklist, and Settings MUST describe general Claude availability, not equate availability with Claude account sign-in.
- **FR-004**: Generic setup, status, and recovery messages MUST NOT instruct the owner to run `claude auth login`; account-login guidance MAY appear only for an explicitly account-only feature.

#### Claude Pass-Through

- **FR-005**: For ordinary local work outside legacy Orbit API-key mode, Orbit MUST preserve Claude/provider environment values inherited by its process. It MAY remove `CLAUDECODE` to permit a child Claude process and MUST override same-named Orbit runtime/safety values.
- **FR-006**: Ordinary employee runs MUST load Claude's user and project setting sources. Structured onboarding calls MUST load Claude's user setting source.
- **FR-007**: Orbit MUST apply the same pass-through policy to every local model-backed flow, including hiring, chats, routines, summaries, role processing, and plugin preparation where applicable.
- **FR-008**: Orbit MUST keep its explicit command-line sandbox, guard, allowed/disallowed tool, strict-MCP, workspace, prompt, and session controls in place.
- **FR-009**: Owner Claude user settings, including hooks and plugins, MUST be treated as trusted configuration and MAY run in Orbit-launched Claude sessions.
- **FR-010**: Orbit MUST NOT add provider profiles, endpoint configuration, provider credentials, model discovery, provider readiness probes, a relay, or a replacement inference client.
- **FR-011**: Orbit MUST continue passing its selected employee model alias and effort to Claude; Claude remains responsible for resolving them against its configured connection.
- **FR-012**: Existing installations using Orbit's stored Anthropic API-key mode MUST retain their current isolated environment and key-injection behavior.

#### Execution and Failures

- **FR-013**: Ordinary local work MUST NOT depend on a successful connection to `api.anthropic.com` before Claude is invoked.
- **FR-014**: Claude's actual process result MUST be the source of truth for connection readiness and failure.
- **FR-015**: Connection, authentication, provider, network, and rate-limit failures MUST use provider-neutral owner-facing language while preserving safe diagnostic detail in existing logs.
- **FR-016**: Existing transient-failure scheduling and retry behavior MUST remain, but Orbit MUST NOT route a failed request to another provider.

#### Account-Only Boundary

- **FR-017**: Cloud Shift MUST remain unavailable unless a separate account-specific check, run without inherited provider configuration or user setting sources, returns `loggedIn: true` with `authMethod: "claude.ai"`.
- **FR-018**: New hires MUST NOT auto-enable Cloud Shift when that account-specific check fails, even when ordinary Claude work is available.
- **FR-019**: Cloud Shift's account-only environment and routing MUST remain isolated from third-party Claude user settings.

#### Privacy, Compatibility, and Documentation

- **FR-020**: Orbit MUST NOT deliberately serialize or echo inherited Claude connection credential values into its registry, employee files, UI, activity records, or logs. Claude-generated output and errors remain subject to Orbit's existing logging behavior.
- **FR-021**: Orbit MUST NOT claim that an inherited connection is local, private, provider-pinned, compatible, or unable to fall back; those properties remain Claude/configuration responsibilities.
- **FR-022**: Existing employee data, sessions, histories, roles, routines, abilities, connector grants, and safety settings MUST require no migration.
- **FR-023**: Documentation MUST describe Claude account sign-in as one supported Claude configuration, not a global Orbit prerequisite.
- **FR-024**: Documentation MUST state that unattended Orbit work needs connection configuration available to the background service, normally through persistent Claude user/managed settings, native credentials, or OS service environment rather than an ephemeral shell export.
- **FR-025**: Documentation MUST disclose that exact pass-through trusts owner Claude hooks and plugins and does not add credential isolation beyond Claude's behavior.

### Scope Boundaries

**In scope**:

- Removing Claude-account sign-in as an Orbit-wide prerequisite.
- Loading the owner's effective Claude user configuration for ordinary local work.
- Preserving inherited provider environment where the Orbit process has it.
- Removing Anthropic-specific preflight blocking from ordinary work.
- Provider-neutral status/errors and account-specific Cloud Shift gating.
- Regression tests and corrected setup/user documentation.

**Out of scope**:

- Configuring, detecting, validating, naming, or supporting any specific third-party provider or gateway.
- Persisting ephemeral shell environment into Orbit services.
- Guaranteeing endpoint choice, locality, privacy, fallback behavior, model compatibility, context size, streaming, or tool quality.
- Hiding provider credentials from Claude or from processes Claude itself launches.
- Installing or operating a gateway, model runtime, or model weights.
- Making Cloud Shift work without a qualifying Claude account.
- Replacing or modifying the Claude client.

### Key Entities

No new persisted Orbit entity is introduced. Relevant external state is Claude Code's effective configuration and native credential state. Existing `staff.json.auth` remains only for backward compatibility with Orbit's stored API-key path.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A test installation with Claude account status signed out but a successful fake Claude connection completes setup, hiring, and one employee task without an account-login instruction.
- **SC-002**: Automated tests prove 100% of ordinary local Claude launch paths preserve connection sentinels and select the required user setting source.
- **SC-003**: With `api.anthropic.com` unreachable and fake Claude healthy, an employee run starts without the former connectivity wait and completes successfully.
- **SC-004**: Existing sandbox, guard, tool-deny, MCP, workspace, and session command assertions remain passing after user settings are enabled.
- **SC-005**: Existing Orbit-managed Anthropic API-key tests remain passing with no routing or credential-source change.
- **SC-006**: Automated Cloud Shift tests prove `third_party`, `api_key`, `oauth_token`, and `none` methods cannot enable or auto-enable Cloud Shift, while `loggedIn: true` with `authMethod: "claude.ai"` retains existing behavior.
- **SC-007**: Repository-wide searches find no generic setup, checklist, Settings, installer, or error text that states Claude account sign-in is required for ordinary Orbit work.
- **SC-008**: Implementation adds no provider schema, provider module, gateway endpoint field, credential store, relay, inference dependency, or team-data migration.

## Assumptions and Dependencies

- A supported Claude Code release is installed and can use the owner's chosen connection without Orbit configuring it.
- Connection configuration required after reboot is available to the service user persistently; terminal-only exports are not assumed to survive.
- Claude user configuration is owner-controlled and trusted, including hooks and plugins.
- Claude accepts Orbit's existing employee model aliases and effort values, or returns its own useful failure.
- Managed settings continue to apply according to Claude's own precedence rules.
- The existing Orbit guard, sandbox, and explicit CLI arguments remain compatible with user settings; owner customizations outside those controls remain owner responsibility.
- Official Claude Code behavior referenced by this spec includes `third_party` authentication status, provider environment settings, and `--setting-sources user,project`.
