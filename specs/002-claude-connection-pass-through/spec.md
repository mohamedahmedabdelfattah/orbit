# Feature Specification: Claude Connection Pass-Through

**Target Branch**: `main` (planning worktree currently detached)

**Created**: 2026-11-05

**Revised**: 2026-11-07 (remediation of specification analysis findings)

**Status**: Specification, plan, and tasks remediated; ready for implementation

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

**Independent Test**: Inventory every production Claude invocation, put sentinel connection values in Claude user settings and the process environment, and verify every ordinary fake-Claude path receives them together with unchanged Orbit safety arguments and the required setting sources.

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
4. **Given** Orbit inherits a connection credential that Claude does not print, **When** a Claude call fails, **Then** Orbit retains the process result and failure classification without copying that inherited value into Orbit-generated diagnostics.

---

### User Story 4 - Keep Account-Only Features Honest (Priority: P2)

Cloud Shift remains an Anthropic-account feature. Owners using another Claude connection can use local Orbit work, but Cloud Shift stays off and explains its separate account requirement.

**Why this priority**: Removing the global account requirement must not make an account-only feature appear available or auto-enable it for new hires.

**Independent Test**: Return `third_party`, `api_key`, `api_key_helper`, `oauth_token`, `none`, and `claude.ai` account methods from fake account checks. Verify only a fresh qualifying account result can manually enable, auto-enable, or launch Cloud Shift, and that losing eligibility blocks the next cloud operation without affecting ordinary local work.

**Acceptance Scenarios**:

1. **Given** Claude uses a third-party connection and has no qualifying Claude account session, **When** an employee is hired, **Then** local work starts normally and Cloud Shift is not enabled.
2. **Given** a qualifying Claude account session exists, **When** the owner enables Cloud Shift, **Then** existing Cloud Shift behavior remains unchanged.
3. **Given** no qualifying account exists, **When** the owner views or enables Cloud Shift, **Then** Orbit explains that this optional feature needs a Claude account without treating local work as broken.
4. **Given** Cloud Shift was enabled while a qualifying account existed and that eligibility is later removed, **When** the next Cloud Shift run starts, **Then** the cloud run is blocked with an account-only explanation while ordinary local work remains available.
5. **Given** a read-only availability result is cached as eligible and eligibility is then removed, **When** the owner attempts manual enablement, new-hire auto-enablement, or a cloud launch, **Then** Orbit performs a fresh account-specific check and rejects the operation.

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

- **FR-005**: For ordinary local work outside legacy Orbit API-key mode, Orbit MUST preserve the complete process environment inherited by its process, including Claude/provider values and unrecognized future values, instead of filtering by provider-name prefixes; the only inherited value Orbit MUST delete is the `CLAUDECODE` recursion marker. Orbit MUST override same-named inherited values with exactly the enumerated Orbit-owned runtime and safety values defined in the launch contract. This whole-environment inheritance is an explicit documented trust decision: values unrelated to Claude, including any secrets present in Orbit's service environment, reach Claude by design, and documentation MUST disclose this (FR-025).
- **FR-006**: Ordinary employee runs MUST load Claude's user and project setting sources. Structured onboarding calls MUST load Claude's user setting source.
- **FR-007**: Every production Claude invocation owned by Orbit MUST resolve to exactly one behavioral class per execution: installation check, ordinary pass-through, legacy Orbit API-key, interactive application, or Cloud Shift. Every ordinary local model-backed flow—including hiring, chats, routines, summaries, role processing, and plugin preparation—MUST use the ordinary pass-through policy when the team is not in legacy Orbit API-key mode. Shared launch sites whose behavior depends on that mode MUST resolve to exactly one class per execution (ordinary pass-through when the stored key is absent, legacy Orbit API-key when it governs), and the launch inventory MUST list each such site's permitted class pair. No production Claude invocation may execute without a resolved class or bypass an assigned class.
- **FR-008**: Orbit MUST keep its explicit command-line sandbox, guard, allowed/disallowed tool, strict-MCP, workspace, prompt, and session controls in place.
- **FR-009**: In ordinary pass-through sessions only, owner Claude user settings, including hooks and plugins, MUST be treated as trusted configuration and MAY run in Orbit-launched Claude sessions. Legacy Orbit API-key sessions, Cloud Shift account checks, and all Cloud Shift launches MUST NOT load Claude user setting sources; their existing isolation is unchanged.
- **FR-010**: Orbit MUST NOT add provider profiles, endpoint configuration, provider credentials, model discovery, provider readiness probes, a relay, or a replacement inference client.
- **FR-011**: Orbit MUST continue passing its selected employee model alias and effort to Claude; Claude remains responsible for resolving them against its configured connection.
- **FR-012**: Existing installations using Orbit's stored Anthropic API-key mode MUST retain their current isolated environment and key-injection behavior.

#### Execution and Failures

- **FR-013**: Ordinary local work MUST NOT depend on a successful connection to `api.anthropic.com` before Claude is invoked.
- **FR-014**: Claude's actual process result MUST be the source of truth for connection readiness and failure.
- **FR-015**: Connection, authentication, provider, network, and rate-limit failures MUST use provider-neutral owner-facing language. Orbit MUST preserve the existing process result, failure classification, and Claude-provided output/error logging behavior. Orbit-generated diagnostics MUST NOT copy values originating in inherited Claude user settings or the inherited process environment—credential values or otherwise—into failure records, and MUST NOT add guessed provider details; values Orbit already computes itself for the session (such as session identifiers, workspace paths, and run timings) remain permitted.
- **FR-016**: Existing transient-failure scheduling and retry behavior MUST remain, but Orbit MUST NOT route a failed request to another provider.

#### Account-Only Boundary

- **FR-017**: Cloud Shift availability, manual enablement, new-hire auto-enablement, and every Cloud Shift launch MUST require `loggedIn: true` with `authMethod: "claude.ai"` from an account-specific check run without inherited provider configuration or user setting sources. Read-only status displays MAY cache the result for no more than 60 seconds. Manual enablement, auto-enablement, and Cloud Shift launches MUST use a fresh check. If an already-enabled shift loses eligibility, its next cloud launch MUST be blocked with an account-only explanation while ordinary local work remains available. Owner disablement clears the local switch without requiring eligibility; any remote cleanup it attempts is best-effort and, when attempted, MUST itself satisfy the fresh eligibility check and the account-environment rules of FR-017 and FR-019.
- **FR-018**: (Normative restatement of FR-017's auto-enablement rule, retained as a separately tested safety invariant.) New hires MUST NOT auto-enable Cloud Shift when the FR-017 account-specific check fails, even when ordinary Claude work is available. FR-017 governs; FR-018 exists so this single behavior can be tested on its own.
- **FR-019**: Cloud Shift account checks and launches MUST receive only the operating-system environment needed to execute Claude, access its native account state, and use temporary files. They MUST NOT inherit ordinary provider routing, endpoint, token, API-key, proxy, arbitrary connection values, or Claude user setting sources. Isolation MUST remain effective for unrecognized future provider variable names, not only a fixed list of known prefixes.

#### Privacy, Compatibility, and Documentation

- **FR-020**: Orbit MUST NOT deliberately serialize or echo inherited Claude connection credential values into Orbit-generated registry data, employee files, UI responses, activity records, diagnostic metadata, or logs. This prohibition applies to data Orbit obtains from settings or its process environment. It does not require Orbit to inspect or redact values that Claude itself emits in output or errors; Claude-generated content retains its existing logging behavior.
- **FR-021**: Orbit MUST NOT claim that an inherited connection is local, private, provider-pinned, compatible, or unable to fall back; those properties remain Claude/configuration responsibilities.
- **FR-022**: Existing employee data, sessions, histories, roles, routines, abilities, connector grants, and safety settings MUST require no migration.
- **FR-023**: Documentation MUST describe Claude account sign-in as one supported Claude configuration, not a global Orbit prerequisite.
- **FR-024**: Documentation MUST state that unattended Orbit work needs connection configuration available to the background service, normally through persistent Claude user/managed settings, native credentials, or OS service environment rather than an ephemeral shell export.
- **FR-025**: Documentation MUST disclose that exact pass-through trusts owner Claude hooks and plugins and does not add credential isolation beyond Claude's behavior, and that ordinary pass-through forwards Orbit's complete inherited service environment—Claude/provider values and any unrelated values present—to Claude and to processes Claude itself launches.

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

- **SC-001**: One automated validation uses the same temporary Orbit installation and fake Claude executable to complete the mandatory setup check, structured hiring, and one employee task while account status is `loggedIn: false`; no step invokes or presents `claude auth login`.
- **SC-002**: An enumerated launch inventory covers 100% of production Claude invocation sites. Automated validation proves every ordinary local invocation uses pass-through behavior, preserves an arbitrary inherited connection sentinel, removes the recursion marker, applies Orbit-owned overrides, and selects its required setting sources. Validation fails when a new production invocation has no behavioral classification.
- **SC-003**: With `api.anthropic.com` unreachable and fake Claude healthy, an employee run starts without the former connectivity wait and completes successfully.
- **SC-004**: Existing sandbox, guard, tool-deny, MCP, workspace, and session command assertions remain passing after user settings are enabled.
- **SC-005**: Existing Orbit-managed Anthropic API-key tests remain passing with no routing or credential-source change.
- **SC-006**: Automated Cloud Shift validation proves `third_party`, `api_key`, `api_key_helper`, `oauth_token`, and `none` methods cannot manually enable, auto-enable, or launch Cloud Shift. A fresh qualifying `claude.ai` result retains existing behavior, while a transition from eligible to ineligible blocks the next cloud operation without blocking ordinary local work.
- **SC-007**: A repository-wide scan of all tracked production, setup, template, and documentation files finds no generic statement that Claude account sign-in is required for ordinary Orbit work. Historical specifications, test fixtures, and exact allowlisted Cloud Shift account-only messages MAY be excluded.
- **SC-008**: Implementation adds no provider schema, provider module, gateway endpoint field, credential store, relay, inference dependency, or team-data migration.
- **SC-009**: Failure validation proves Orbit retains the process result and failure classification while no inherited credential sentinel enters Orbit-generated registry data, employee files, UI responses, activity records, diagnostic metadata, or logs. Claude-generated output/error behavior remains unchanged.

## Assumptions and Dependencies

- A supported Claude Code release is installed and can use the owner's chosen connection without Orbit configuring it.
- Connection configuration required after reboot is available to the service user persistently; terminal-only exports are not assumed to survive.
- Claude user configuration is owner-controlled and trusted, including hooks and plugins.
- Claude accepts Orbit's existing employee model aliases and effort values, or returns its own useful failure.
- Managed settings continue to apply according to Claude's own precedence rules.
- The existing Orbit guard, sandbox, and explicit CLI arguments remain compatible with user settings; owner customizations outside those controls remain owner responsibility.
- Official Claude Code behavior referenced by this spec includes `third_party` authentication status, provider environment settings, and `--setting-sources user,project`.
