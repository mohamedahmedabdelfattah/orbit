# Feature Specification: Claude 3P Local Model Support

**Feature Branch**: `main` (no branch hook configured)

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Why does the project require Claude sign-in, and plan support for using Claude 3P gateway with local models without signing in to a Claude account?"

Orbit currently treats a Claude account session or Anthropic API key as a prerequisite. Setup, readiness checks, status messages, connectivity checks, model names, and cloud features all assume one of those two paths. Orbit also prevents inherited gateway settings from reaching employee runs. These choices protect credentials and make subscription use predictable, but they make a local Claude 3P gateway impossible to select. This feature adds a distinct local inference mode rather than weakening those protections.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Orbit on a Local Model (Priority: P1)

An owner already running a compatible local model gateway chooses **Local gateway** during Orbit setup. They select or enter a model, pass a readiness check, hire their first crew member, and complete a real crew task without creating or signing in to a Claude account.

**Why this priority**: This is the requested outcome and the smallest useful release. Configuration without a successful crew task has no user value.

**Independent Test**: Start from a clean Orbit home on a supported computer. Install the Claude client but do not sign in. Start a compatible gateway and local model on the same computer. Complete setup, hiring, and one employee task using only the local model.

**Acceptance Scenarios**:

1. **Given** Claude is installed but has never been signed in, and a compatible local gateway is ready, **When** the owner selects Local gateway and supplies valid connection and model details, **Then** Orbit completes setup without asking for a Claude account or Anthropic API key.
2. **Given** Local gateway mode is ready, **When** Orbit performs the hiring interview and the new crew member completes a task, **Then** every model request uses the selected local gateway and model.
3. **Given** the local gateway does not require authentication, **When** the owner configures it, **Then** Orbit can connect without asking for a provider account credential.
4. **Given** the gateway cannot provide a capability Orbit needs, **When** the owner runs the readiness check, **Then** Orbit refuses to mark the provider ready and names the missing capability and next action.
5. **Given** the computer has no internet connection but the local gateway is healthy, **When** a crew member runs a task that needs no external site, **Then** Orbit treats inference as available and completes the task locally.

---

### User Story 2 - See, Diagnose, and Switch Inference (Priority: P2)

An owner can see that the crew uses a local model, inspect readiness without exposing secrets, recover from an unloaded model or stopped gateway, and deliberately switch between local, subscription, and API-key modes without losing team data.

**Why this priority**: Local model servers stop, unload models, and vary in capability. Clear status and reversible provider choice prevent silent failures or accidental cloud use.

**Independent Test**: Configure Local gateway mode, stop and restart the gateway, change to an unavailable model, restore it, then switch to another inference mode. Verify status, diagnostics, routing, and existing team data at each step.

**Acceptance Scenarios**:

1. **Given** Local gateway mode is active, **When** the owner opens setup status, Settings, or doctor diagnostics, **Then** each surface identifies Local gateway, the selected model, and ready or blocked state without showing a Claude sign-in warning.
2. **Given** the gateway stops before or during a task, **When** Orbit detects the failure, **Then** it reports a local-gateway problem, preserves pending work, and does not retry against Anthropic or another provider.
3. **Given** the owner chooses a different inference mode, **When** that mode passes its own readiness check and the owner confirms the switch, **Then** new work uses it while employees, history, skills, routines, and settings remain intact.
4. **Given** Local gateway mode is active, **When** the owner views cloud-shift controls or Claude-plan usage, **Then** Orbit explains that cloud shift and plan limits do not apply instead of offering controls that cannot work.
5. **Given** an existing subscription or API-key installation, **When** Orbit is upgraded without selecting Local gateway, **Then** its provider, behavior, and stored team data remain unchanged.

---

### User Story 3 - Open a Crew Member in Claude 3P Mode (Priority: P3)

An owner opens a crew member's interactive Claude session and uses the same local gateway and model, with the crew member's job, memory, tools, and Orbit safety controls, without a Claude account sign-in.

**Why this priority**: Headless crew work delivers the core value. Interactive sessions complete the current Orbit experience but depend on the installed Claude application's 3P capabilities and explicit user consent.

**Independent Test**: On a computer with no Claude account session, configure Local gateway mode, open a crew member from Orbit, complete a tool-using task, and verify both inference routing and Orbit controls.

**Acceptance Scenarios**:

1. **Given** Orbit and the Claude application have matching local 3P settings, **When** the owner selects Open in Claude, **Then** the session opens in the employee workspace, responds through the local model, and retains Orbit's job, memory, tools, and safety controls.
2. **Given** the Claude application is not yet configured for the selected local gateway, **When** the owner tries to open a crew member, **Then** Orbit gives a short guided setup and verification path rather than directing them to Claude account sign-in.
3. **Given** applying 3P settings would change another application's configuration, **When** Orbit offers to help, **Then** it explains the change and requires explicit owner approval before any change is made.
4. **Given** the interactive session is pointed at a different provider than Orbit, **When** Orbit verifies the session path, **Then** it reports the mismatch and does not claim the session is local.

### Edge Cases

- Claude is installed but has no saved account session, or a stale account session still exists.
- A saved Claude account or Anthropic API key exists alongside Local gateway mode; neither may be sent or used as fallback.
- The gateway is reachable but the selected model is missing, still loading, or renamed.
- The gateway answers ordinary text prompts but cannot stream, use tools, produce the structured hiring response, or support the required context size.
- Model discovery is unavailable or returns no usable models; the owner needs a manual model-name path.
- A no-auth local gateway still needs a non-empty client credential placeholder; that value must not be presented as a real account secret.
- The configured address resolves outside the same computer, redirects elsewhere, changes after validation, or uses an unsafe transport for a non-loopback destination.
- The gateway stops during a streamed response or returns a partial or malformed response.
- Several crew members request work while the local model can serve only one request at a time.
- The local model's context or output limit is lower than a task needs.
- The computer is offline while the local model is healthy, or online while the local gateway is down.
- The owner switches inference mode while work is running or queued.
- The owner removes Local gateway configuration while an interactive session remains open.
- Cloud shift was enabled before the owner switched to Local gateway mode.
- Claude application 3P settings differ from Orbit's local provider profile.
- A credential, endpoint query value, or custom header appears in an error, activity record, process listing, or control-panel response.

## Requirements *(mandatory)*

### Functional Requirements

#### Provider Selection and Readiness

- **FR-001**: Orbit MUST offer three explicit inference choices: Claude account, Anthropic API key, and Local gateway. Existing installations MUST keep their current choice until the owner changes it.
- **FR-002**: Local gateway mode MUST allow setup and normal local crew operation with no Claude account, Claude account session, or Anthropic API key.
- **FR-003**: The owner MUST be able to configure a same-computer gateway address, credential style (none, bearer token, or API key), optional gateway credential, primary model, and fallback model. One model MAY serve both model roles.
- **FR-004**: This release MUST accept loopback gateway addresses and MUST reject non-loopback addresses with a clear scope message. Redirects from a loopback address to a non-loopback destination MUST fail validation.
- **FR-005**: Orbit MUST list usable gateway models when discovery is available and MUST provide manual model entry when it is not.
- **FR-006**: Before activation, Orbit MUST verify gateway reachability, credential acceptance, selected-model availability, streamed responses, tool use, the structured response needed by hiring, and a context capacity of at least 32,000 input tokens.
- **FR-007**: A failed readiness check MUST identify each failed capability separately, preserve the proposed settings for correction, and leave the previously active provider unchanged.
- **FR-008**: Orbit MUST recheck readiness during doctor diagnostics and before the first crew run after startup or a provider change. Later runs MAY use a recent successful result, but a detected failure MUST immediately mark the provider blocked.

#### Routing, Privacy, and Secret Safety

- **FR-009**: In Local gateway mode, every Orbit-initiated local inference flow MUST use the selected gateway profile. This includes setup and hiring, chats, routines, plans, summaries, role sharing, and other background crew work.
- **FR-010**: Local gateway requests MUST NOT contain a saved Claude account credential or Anthropic API key.
- **FR-011**: Orbit MUST fail closed when the selected local gateway is unavailable or rejects a request. It MUST NOT silently fall back to a Claude account, Anthropic API, cloud session, or another gateway.
- **FR-012**: Local mode MUST prevent model prompts, model responses, and employee workspace content from being sent to Anthropic inference endpoints. It MUST disable nonessential external client traffic by default and clearly disclose any remaining non-inference network dependency.
- **FR-013**: Gateway credentials and generated placeholders MUST be stored with the same protection as other Orbit secrets and MUST be masked in settings, diagnostics, logs, errors, activity records, and process details.
- **FR-014**: Only the owner-selected provider profile MAY influence Orbit-launched inference. Unrelated inherited provider or gateway settings MUST NOT override it.
- **FR-015**: Employee tools and model-generated commands MUST NOT be able to read or alter the provider profile or its credential.

#### Operation and Owner Experience

- **FR-016**: Setup, Settings, onboarding checklist, and doctor diagnostics MUST show the effective inference mode, non-secret gateway address, selected model or models, last readiness result, and a direct recovery action.
- **FR-017**: Local mode MUST test connectivity against the configured gateway rather than an Anthropic host. Lack of internet access alone MUST NOT block local-only work.
- **FR-018**: Local gateway failures MUST use provider-specific messages for unreachable gateway, rejected credential, missing or unloaded model, incompatible response, context limit, and saturation. Messages MUST NOT direct the owner to `claude auth login`.
- **FR-019**: If the local gateway is busy, Orbit MUST keep each accepted task in a visible waiting state, avoid duplicate execution, and resume it when capacity returns or the normal task deadline expires.
- **FR-020**: Local mode MUST report measured work and token use when available, but MUST NOT show Claude-plan limits or imply Anthropic billing. Unknown local cost MUST be labeled unknown rather than estimated as a Claude charge.
- **FR-021**: Cloud shift MUST be unavailable while Local gateway mode is active. Orbit MUST turn off future cloud-shift triggers during activation, preserve prior cloud-shift preferences for a possible later switch back, and explain that local models cannot work while the computer and gateway are off.
- **FR-022**: Open in Claude MUST support a matching Claude 3P local session where the installed application supports it. Orbit MUST preserve the employee workspace, role, memory, granted tools, and safety controls in that session.
- **FR-023**: Orbit MUST guide and verify Claude application's 3P configuration without silently changing global third-party application settings. Any automated configuration change MUST show its effect and require explicit owner approval.
- **FR-024**: Switching inference modes MUST require owner confirmation, validate the destination first, apply only to new work, let running work finish on its original provider, and preserve all team data.
- **FR-025**: The owner MUST be able to remove a local provider profile and its stored credential after switching away. Removal MUST NOT delete employees, work history, skills, or model files owned by another application.

#### Compatibility and Safety

- **FR-026**: Claude account and Anthropic API-key modes MUST retain their current setup, routing, model selection, usage reporting, cloud-shift behavior, and error handling unless the owner selects Local gateway.
- **FR-027**: Local gateway mode MUST work on every operating system Orbit supports, subject to the installed Claude client's 3P support on that operating system.
- **FR-028**: Orbit MUST detect an installed Claude client that is too old for required 3P behavior and provide one exact upgrade action before accepting Local gateway mode.
- **FR-029**: Existing sandbox, guard, ability, connector, workspace-isolation, and owner-approval rules MUST apply unchanged in Local gateway mode and interactive local sessions.
- **FR-030**: User documentation MUST distinguish Claude account sign-in, Anthropic API-key use, and local 3P inference; state what remains local; state what can still access external sites; and provide setup, verification, recovery, switching, and removal paths.

### Scope Boundaries

**In scope**:

- A local model exposed through a same-computer gateway compatible with Claude 3P inference.
- Account-free Orbit setup, hiring, background work, diagnostics, usage presentation, and provider switching.
- Guided configuration and verification for an interactive Claude 3P crew session.
- Preservation of all existing Orbit safety controls and existing inference modes.

**Out of scope**:

- Installing, downloading, updating, or operating a model runtime, model weights, or gateway product.
- Remote, public, or cloud-hosted third-party gateways.
- Direct support for gateways that are not compatible with Claude 3P inference.
- Making cloud shift run on the local model while the owner's computer is off.
- Guaranteeing answer quality, tool-use reliability, or speed beyond the readiness checks; these depend on the chosen model and hardware.
- Removing the requirement to install a supported Claude client or modifying that client.
- Making connectors, web research, chat channels, or other owner-enabled external tools operate offline.

### Key Entities

- **Inference Provider Profile**: The owner's active inference choice. Holds mode, non-secret connection details, credential reference, model assignments, and activation state.
- **Local Gateway Connection**: A same-computer inference destination with a credential style, safe address, discovery capability, and current health.
- **Model Assignment**: The gateway model selected for Orbit's primary or fallback workload role, including its advertised capabilities and context capacity.
- **Provider Readiness Result**: Time-stamped outcome for reachability, authentication, model availability, streaming, tool use, structured output, context capacity, and any recovery actions.
- **Provider Credential**: Optional secret or generated placeholder used only to authenticate the Claude client to the selected gateway.
- **Inference Run**: One model-backed unit of Orbit work, bound to the provider profile that was active when the run started so a later mode switch cannot reroute it silently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With a compatible gateway and model already running, a first-time owner completes Local gateway setup, hires one crew member, and finishes one task in 10 minutes or less without a Claude account sign-in or Anthropic API key.
- **SC-002**: In end-to-end routing tests covering hiring, chat, a scheduled routine, a summary, and an interactive crew session, 100% of model requests reach the selected local gateway and zero reach an Anthropic inference endpoint.
- **SC-003**: For every readiness failure class in FR-018, Orbit identifies the specific blocker and a recovery action within 30 seconds, starts no employee work, and makes zero fallback model requests.
- **SC-004**: At least 9 of 10 non-technical usability participants connect an already-running compatible local model on their first attempt without external documentation.
- **SC-005**: Switching from Local gateway to either existing inference mode, and back again, takes no more than 3 minutes per switch and causes zero loss or modification of employees, work history, routines, skills, or owner settings.
- **SC-006**: Across at least two independently implemented compatible local gateways on each supported operating system, at least 95% of the standard Orbit task suite completes without an Orbit-specific routing, parsing, or tool-control failure.
- **SC-007**: For 20 representative prompts, Orbit adds no more than 2 seconds median delay before the selected local gateway begins handling the request, compared with using that same gateway directly.
- **SC-008**: Security verification finds zero provider credentials or credential-bearing URLs in owner-visible pages, logs, diagnostics, activity records, employee-readable files, and spawned-command arguments.
- **SC-009**: All existing automated acceptance tests for Claude account and Anthropic API-key modes pass unchanged, plus new tests prove those modes are never selected as Local gateway fallback.
- **SC-010**: In a comprehension check, at least 90% of participating owners can correctly identify which model provider is active, whether inference leaves their computer, why cloud shift is unavailable, and how to switch or recover.

## Assumptions

- "Claude P3 gateway" means Claude **3P (third-party inference) gateway**. If P3 names a different product or protocol, this specification needs clarification before planning.
- The official, unmodified Claude client remains installed and provides the agent interface. This feature removes Claude account sign-in as an Orbit prerequisite; it does not replace that client.
- The installed Claude client permits the chosen local model through its documented 3P mode. Anthropic may not support non-Claude model behavior; Orbit does not patch the client, bypass its controls, or claim vendor support for the selected model.
- The owner starts and maintains a compatible local gateway and model before connecting Orbit. Orbit validates them but does not install or administer them.
- Version 1 supports gateways on the same computer only. Loopback HTTP is acceptable because traffic does not leave the host; any future network gateway support requires a separate security and trust design.
- A compatible gateway can stream responses, support model-driven tool use, produce Orbit's structured hiring output, and expose or document enough model capacity for readiness validation.
- If only one model is available, using it for both primary and fallback work is an acceptable default.
- Local inference means prompts and responses remain on the owner's computer. Owner-enabled connectors, websites, chat channels, update checks, and research tools can still use the network and must remain clearly distinguished from inference.
- Local model quality and speed depend on model choice and hardware. Readiness proves compatibility, not output quality equivalent to a hosted Claude model.
- Cloud shift remains tied to a Claude account and is unavailable in Local gateway mode.
- Existing Orbit sandbox and guard controls remain the authority for employee access. Local inference does not relax them.

### Dependencies

- A supported Claude client release with account-free 3P gateway behavior for headless runs and, where used, interactive application sessions.
- A running local gateway compatible with Claude 3P inference and a loaded model meeting FR-006.
- Existing Orbit secret storage, sandbox, guard, provider status, task queue, and control-panel surfaces.
- Platform-specific support for opening or guiding an interactive Claude 3P session; headless local crew operation remains the required cross-platform baseline.
