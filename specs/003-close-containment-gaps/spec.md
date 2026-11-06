# Feature Specification: Fail-Closed Native Windows Containment

**Feature ID**: `003-close-containment-gaps`

**Created**: 2026-11-06

**Status**: Draft

**Priority**: P0 security fix

**Input**: User description: "Resolve the P0 issue: containment hook omits Claude Code `onFailure: \"block\"`; current default is continue on hook crash/timeout. Missing hook can run shell uncontained. Security defect found during trace: hook trusts `<employee workspace>/state/mxc-policy.json` when present. Employee file tools can write workspace, so policy self-widening is possible. Also review uncontained gateway pass-through and the exact MXC release contract."

Native Windows employee shells are intended to run inside Microsoft Execution Containers (MXC). Two paths currently break that promise. First, Claude Code continues a tool action when Orbit's containment hook crashes or times out because the hook does not request blocking failure behavior. Second, the hook accepts a policy cache from the employee's writable workspace, allowing the workload being restricted to widen its own restrictions. Gateway commands intentionally run on the host and therefore need an equally strict exception contract. Orbit must also prove that the installed Claude Code, MXC runtime, schema, Windows build, and effective settings support the behavior on which containment depends.

The security invariant for this feature is: **no model-proposed shell command reaches the Windows host unless it is one exact, currently authorized Orbit gateway invocation; every other shell command is either executed through verified MXC containment or denied. Any missing, malformed, stale, unsupported, or uncertain security state denies execution.**

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Shell Commands Fail Closed (Priority: P0)

An owner gives an employee a task on native Windows. Every shell action is contained. If the containment hook is absent, disabled, incompatible, crashes, returns malformed output, exits unsuccessfully, or exceeds its deadline, the proposed command does not run on the host. Orbit reports one useful recovery action instead.

**Why this priority**: Hook execution is the containment boundary. Continuing after hook failure turns any reliability fault into arbitrary host command execution.

**Independent Test**: Use a harmless host-marker command and trigger each hook failure class separately: missing registration, unsupported client, disabled hooks, missing handler, non-zero exit, crash, timeout, empty output, malformed JSON, missing input fields, and containment-helper failure. Verify that no marker is created and that each attempt is reported as blocked.

**Acceptance Scenarios**:

1. **Given** a supported native Windows MXC installation, **When** an employee requests an ordinary PowerShell command, **Then** the command runs only through the verified containment path.
2. **Given** the containment hook process crashes, exits unsuccessfully, or times out, **When** Claude Code handles the tool call, **Then** the tool call is blocked and the original command is never executed.
3. **Given** the hook emits empty, partial, malformed, or semantically invalid output, **When** a shell event matches the containment hook, **Then** Orbit denies the event rather than returning no decision.
4. **Given** the installed Claude Code does not support blocking hook failures, ignores Orbit's hook settings, or has hooks disabled by effective policy, **When** Orbit prepares an employee run, **Then** the run is refused before employee work begins and the owner receives an exact upgrade or settings action.
5. **Given** the hook succeeds but the MXC helper or executor later cannot start, **When** the rewritten command runs, **Then** the original command is not retried on the host and the tool result states that containment could not start.
6. **Given** a contained command exceeds its execution budget, **When** Orbit returns control to Claude Code, **Then** the workload and helper are terminated with no surviving child process.

---

### User Story 2 - Employees Cannot Widen Their Policy (Priority: P0)

An employee can write ordinary work files in its workspace but cannot influence the containment policy, hook configuration, gateway authorization, or runtime requests through those files. Owner-approved changes still take effect through an owner-controlled path.

**Why this priority**: A policy controlled by the subject of that policy is not a security boundary.

**Independent Test**: Pre-seed and modify workspace files with permissive policy data, including the legacy `state/mxc-policy.json`, profile security fields, project settings, and hook-bearing content. Attempt a secret read, an out-of-scope write, private-network access, and an unapproved public destination. Verify that every attempt remains denied and that trusted policy evidence is unchanged.

**Acceptance Scenarios**:

1. **Given** an employee creates a workspace policy cache granting full-disk writes, no denied reads, unrestricted domains, and no timeout, **When** the next shell command is evaluated, **Then** Orbit ignores the workspace file and enforces the owner-controlled policy.
2. **Given** an existing installation already contains a legacy workspace policy cache, **When** Orbit is upgraded, **Then** that file is never used as authorization and cannot preserve an older, wider policy.
3. **Given** an employee changes profile or workspace metadata that resembles a security setting, **When** containment policy is generated, **Then** only owner-controlled security fields can grant access.
4. **Given** an owner narrows allowed paths or domains during a run, **When** the next command is evaluated, **Then** no stale snapshot can retain the removed access.
5. **Given** trusted policy state is missing, unreadable, malformed, mismatched to the employee, or changed during evaluation, **When** a command is requested, **Then** the command is denied with no fallback to workspace data or defaults that are broader.
6. **Given** employee-controlled project settings, skills, or other workspace content declares a host-side hook, **When** an employee session starts or that content is loaded, **Then** it cannot register or execute an untrusted host process.

---

### User Story 3 - Gateway Host Execution Is Narrow and Auditable (Priority: P0)

An employee with an owner-enabled gateway can use that gateway as before. Only a single, exact invocation of an Orbit-owned gateway launcher may run outside MXC. Shell composition, path spoofing, disabled abilities, and ambiguous syntax never inherit the exception.

**Why this priority**: A broad command-pattern exception can turn a limited gateway into a general host-shell escape.

**Independent Test**: Run a corpus containing valid gateway calls plus command chaining, pipelines, redirects, command substitution, environment prefixes, aliases, relative and absolute path variants, executable-name suffixes, case variants, quoted metacharacters, PATH shadowing, and disabled abilities. Verify that only canonical authorized calls reach the host gateway.

**Acceptance Scenarios**:

1. **Given** the owner enabled a gateway and its trusted launcher is intact, **When** the employee makes one canonical gateway call with valid arguments, **Then** the gateway runs under its own URL, method, budget, local-network, and secret controls.
2. **Given** a command combines a gateway call with another command through chaining, a pipeline, redirection, substitution, or shell expression, **When** the hook evaluates it, **Then** the whole command is contained or denied; no part receives host pass-through.
3. **Given** an employee places a same-named executable earlier on `PATH`, uses a relative path, or invokes an alternate wrapper, **When** the command is evaluated, **Then** Orbit does not grant the gateway exception.
4. **Given** the owner disables a gateway ability after the session starts, **When** the employee next invokes it, **Then** current owner state wins and the call is denied.
5. **Given** gateway classification or trusted-launcher verification fails, **When** a command is evaluated, **Then** Orbit denies it rather than treating it as an ordinary uncontained command.

---

### User Story 4 - Setup and Release Prove the Exact Security Contract (Priority: P0)

An owner cannot enter native MXC mode with an unsupported or unverified dependency combination. Maintainers can identify exactly which Claude Code hook semantics, MXC artifact, schema, architecture, Windows build, and runtime capabilities were tested for a release.

**Why this priority**: A security design based on assumed dependency behavior can fail open even when Orbit's own code is correct.

**Independent Test**: Exercise supported and unsupported combinations of Claude Code version and effective hook settings; MXC package, executable, schema, and architecture; and Windows release/build. Tamper with each artifact or contract value. Verify that only a fully verified combination becomes ready and that the recorded evidence identifies every accepted component.

**Acceptance Scenarios**:

1. **Given** Claude Code predates support for blocking hook failures, **When** setup or doctor checks containment, **Then** native MXC mode is blocked with one exact upgrade action.
2. **Given** the MXC package, executor signature, architecture, version, or schema differs from the reviewed contract, **When** setup or doctor validates it, **Then** employee work remains blocked until the verified runtime is restored.
3. **Given** a nominally supported Windows release is below MXC's documented minimum servicing build, **When** setup evaluates it, **Then** Orbit reports it as unsupported rather than relying on the release name alone.
4. **Given** the installed runtime passes basic discovery but cannot enforce Orbit's actual filesystem and proxy policy, **When** Orbit probes the exact request shape, **Then** MXC mode is rejected.
5. **Given** a release candidate, **When** its containment evidence is reviewed, **Then** it includes real-client hook-failure results and real-host MXC positive and negative results for every Windows architecture shipped by Orbit.

### Edge Cases

- The hook reaches its deadline immediately before producing a valid decision; timeout still blocks the action.
- The hook writes valid JSON and then exits unsuccessfully; failure still blocks.
- The hook receives an event with an unexpected tool name, missing command, non-string command, unknown fields, or a changed input schema.
- Several matching hooks exist. No other hook result, workspace setting, plugin, skill, or user setting may override a containment denial or execute employee-controlled code on the host.
- Enterprise policy permits only managed hooks, globally disables hooks, or rejects command hooks.
- An employee creates a permissive cache before upgrade, replaces it during a run, uses a symlink or junction, or races policy generation.
- An owner tightens policy while commands are queued or while a policy snapshot is being created.
- A gateway name appears after an environment assignment, inside a quoted string, in a nested shell, after another command, or as an argument to another executable.
- A gateway launcher is missing, modified, shadowed, replaced by a junction, or no longer matches the installed Orbit release.
- A gateway's own validation fails after host pass-through was approved; it must fail without invoking a fallback shell or leaking a secret.
- Claude Code is newer than the reviewed minimum but changes hook parsing or failure semantics.
- The MXC package hash is correct but the selected architecture is wrong, a required companion is absent, or Authenticode trust cannot be established offline.
- Windows reports a supported feature release but lacks the servicing update or runtime capability required for deny paths or the identity-less loopback proxy.
- MXC discovery succeeds without a request, but the exact Orbit request is unsupported.
- The owner deliberately selects WSL2 fallback. Existing WSL2 containment remains available and must not inherit native-Windows exceptions.

## Requirements *(mandatory)*

### Functional Requirements

#### Fail-Closed Hook Boundary

- **FR-001**: In native Windows MXC mode, every shell-capable tool call MUST receive exactly one terminal disposition before execution: contained, approved as a canonical gateway call, or denied. A new or renamed shell tool that is not covered by the verified hook contract MUST remain unavailable.
- **FR-002**: Orbit's Claude Code command-hook configuration MUST set `onFailure: "block"` on every containment-critical handler. Leaving the field unset or setting it to continue is forbidden.
- **FR-003**: Orbit MUST require a Claude Code release that supports blocking command-hook failures and MUST verify effective behavior before accepting employee work. Version text alone is insufficient if effective settings disable or exclude the hook.
- **FR-004**: A missing handler, spawn error, non-zero exit, crash, timeout, empty output, malformed output, invalid decision, or incompatible event payload MUST block the triggering shell action.
- **FR-005**: A matched shell event MUST NOT use a successful empty response as "no decision." Missing or invalid required input MUST produce an explicit denial.
- **FR-006**: If request construction, trusted-policy loading, helper launch, proxy launch, executor launch, or contained execution setup fails, Orbit MUST NOT execute or retry the original command on the host.
- **FR-007**: Hook and workload deadlines MUST terminate their child process trees. A timeout MUST leave no hook, helper, proxy, executor, or workload process running.
- **FR-008**: Only Orbit-owned, release-verified handlers MAY execute as host-side hooks in employee sessions. Employee-writable settings, skills, plugins, or other content MUST NOT add, replace, disable, or influence host-side handlers.
- **FR-009**: Every employee session MUST establish that its effective client configuration registered the containment hook before any shell-capable tool becomes available. Orbit MUST repeat the full proof that the hook rewrites a normal command and blocks a synthetic failure and timeout after install, upgrade, Claude Code change, effective-policy change, or containment repair.
- **FR-010**: Hook denial and readiness messages MUST identify the failed boundary and one recovery action without exposing commands, secrets, credentials, unrestricted paths, or policy contents beyond what support needs.

#### Trusted Policy Boundary

- **FR-011**: Orbit MUST treat the complete employee workspace and all model-produced content as untrusted for containment, hook, gateway, and readiness decisions.
- **FR-012**: `<employee workspace>/state/mxc-policy.json` and every other employee-writable cache MUST NOT be read as an authorization source. Existing copies MUST be ignored regardless of apparent validity.
- **FR-013**: Access-granting policy fields MUST come only from owner-controlled state and Orbit's verified base policy. Employee-editable profile or workspace fields MAY provide non-security metadata but MUST NOT widen filesystem, network, timeout, gateway, or execution rights.
- **FR-014**: If policy snapshots are used, they MUST live outside all employee write scopes; be bound to the intended employee, run, policy source state, Orbit release, and contract version; and reject missing, extra, malformed, stale, or mismatched data.
- **FR-015**: Owner policy tightening MUST take effect no later than the next command. A stale snapshot MAY cause denial but MUST NOT preserve removed access.
- **FR-016**: The policy used for a command MUST remain stable from authorization through request creation. A detected race or source change MUST deny the command and rebuild from trusted state.
- **FR-017**: Diagnostics and audit logs MAY live in an employee workspace only as non-authoritative output. Editing or deleting them MUST have no effect on future security decisions.

#### Gateway Exception Boundary

- **FR-018**: Host execution MUST be denied by default. Gateway status MUST be a narrow exception, never a property inferred from a command-name substring or broad wildcard.
- **FR-019**: A gateway exception MUST require current owner authorization, an exact gateway identity from Orbit's verified catalog, and an intact Orbit-owned launcher outside employee write scopes.
- **FR-020**: Only one simple gateway invocation MAY qualify. Commands containing additional commands, syntactically active shell operators, redirections, substitutions, aliases, functions, environment prefixes, or ambiguous parsing MUST NOT qualify. Metacharacters proven to be literal argument data do not become shell control syntax.
- **FR-021**: Canonical gateway calls MUST preserve each gateway's existing URL, method, budget, local/private-network, secret, and owner-consent restrictions. Pass-through MUST NOT expose gateway credentials to the employee shell.
- **FR-022**: Unknown, malformed, disabled, or unverifiable gateway calls MUST be contained when containment is valid and compatible, or denied otherwise. They MUST never run uncontained by default.
- **FR-023**: Gateway identity MUST NOT depend on employee-controlled `PATH`, current directory, file extension resolution, alias state, shell profile, symlink, or junction resolution.
- **FR-024**: Failure in gateway classification or dispatch MUST block the command. It MUST NOT fall back to normal host-shell execution.
- **FR-025**: Every approved host gateway invocation and every rejected gateway-like invocation MUST produce an audit record containing employee, gateway identity, policy version, decision, and non-secret reason.

#### Dependency and Release Contract

- **FR-026**: The minimum Claude Code contract for this feature is version `2.1.295`, the first documented release supporting command-hook `onFailure: "block"`. Newer releases MAY be accepted only after the effective-behavior proof in FR-009 passes.
- **FR-027**: The reviewed MXC baseline is runtime package `1.0.1` with immutable stable request schema `1.0.0`. Any runtime or schema change MUST be treated as a new security-contract review, not a compatible patch by assumption.
- **FR-028**: Orbit MUST obtain MXC only from a pinned official release source and MUST verify package digest, selected-architecture payload digest, Microsoft Authenticode publisher, and required runtime companions before installation or repair. Any mismatch MUST leave MXC mode blocked.
- **FR-029**: Every emitted MXC request MUST validate against the exact published schema before use. Unknown, retired, experimental, or release-incompatible fields MUST fail closed.
- **FR-030**: Readiness MUST run MXC's request-aware probe against Orbit's actual containment and proxy request shape, then run positive and negative containment workloads. A generic host probe alone is insufficient.
- **FR-031**: Windows support MUST follow MXC's exact servicing-build and runtime-capability contract, including required host preparation. Product-name checks such as "Windows 11 24H2" alone are insufficient.
- **FR-032**: Setup and doctor output MUST show the effective Claude Code version and hook proof, MXC runtime and schema versions, artifact verification state, Windows build, request-aware probe result, last positive/negative proof, and one recovery action for each blocker.
- **FR-033**: A release containing native Windows containment MUST NOT ship until the hook failure matrix, policy-tampering matrix, gateway bypass corpus, exact-schema validation, and real-host MXC proof pass for every Windows architecture that release supports.
- **FR-034**: This P0 release gate supersedes prior statements that real-host MXC validation is optional or non-gating. The evidence MAY be automated or produced by a repeatable signed run, but it MUST be reviewable and tied to the release candidate.
- **FR-035**: macOS, Linux, and WSL2 behavior MUST remain unchanged. WSL2 fallback MUST remain contained and MUST NOT reuse native-Windows gateway or hook exceptions.
- **FR-036**: Existing native Windows installations MUST stop accepting employee shell work after upgrade until the new hook, trusted-policy, gateway, and dependency proofs pass. Existing team data MUST remain intact.

### Exact External Contract Baseline

The following values define the reviewed baseline. They are security inputs, not floating examples:

| Contract | Reviewed value |
| --- | --- |
| Claude Code command-hook behavior | `onFailure: "block"`, supported in Claude Code `2.1.295+`; unset defaults to continuing the triggering action after handler failure |
| MXC release | `microsoft/mxc` tag `v1.0.1`, commit `fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2` |
| MXC package | `@microsoft/mxc-sdk` `1.0.1`; official npm tarball SHA-256 `416D9607C9D4652395D95C3D9C5F5605F1F2F845DA1A63228BEE41B7392CEF49` |
| MXC executor, x64 | `package/bin/x64/wxc-exec.exe`; SHA-256 `090F5D1F7BB93104AB08DCD4E8034EF954AEEFCDAF6658DDE5F7DFF4CFC12F3A`; valid Microsoft Corporation Authenticode signature |
| MXC executor, ARM64 | `package/bin/arm64/wxc-exec.exe`; SHA-256 `91AA4171E8809F33F19622C381116188EAB7D8C8CFFAD231230A31B58146EE77`; valid Microsoft Corporation Authenticode signature |
| MXC host preparation, x64 | `package/bin/x64/wxc-host-prep.exe`; SHA-256 `C18783AD3DD62C0A54530B25192B7C4015706B3F518CD9619259AE9750D4AB6E`; valid Microsoft Corporation Authenticode signature |
| MXC host preparation, ARM64 | `package/bin/arm64/wxc-host-prep.exe`; SHA-256 `74CCAE215A9C5E81215BC7124AA31CDD7A0B2215A79B5CF8865865BBDAAF93E2`; valid Microsoft Corporation Authenticode signature |
| Stable schema | `schemas/stable/mxc-config.schema.1.0.0.json`; SHA-256 `207254FA94966A800FA70F01A2DA73AE813D27FE8847200C92F4DD0E219649C2` |
| Native executor forms used by Orbit | Request-aware `wxc-exec.exe <request> --probe` and one-shot `wxc-exec.exe <request>`; no-request probe is discovery only; audit mode never handles employee work |
| Minimum Process Isolation servicing builds | Windows 11 24H2 `26100.9278`; 25H2 `26200.9278`; 26H2 `26300.9550`; 26H1 `28000.2804`, followed by runtime capability probing |

### Scope Boundaries

**In scope**:

- Native Windows shell-command containment through Claude Code's hook boundary.
- Fail-closed behavior for hook registration, execution, output, timeout, and downstream containment startup.
- Removal of employee-writable policy and hook inputs from the trusted computing boundary.
- A strict, auditable contract for gateways that intentionally run outside MXC.
- Exact Claude Code, MXC, schema, artifact, architecture, and Windows compatibility verification.
- Upgrade handling, diagnostics, regression coverage, and release evidence for the P0 fix.

**Out of scope**:

- Whole-agent containment; the existing owner decision to contain shell commands rather than the Claude agent process remains unchanged.
- New employee abilities, gateways, network destinations, filesystem grants, or broader autonomy.
- Replacing MXC with another native Windows sandbox backend.
- Upgrading beyond MXC `1.0.1` or schema `1.0.0` as part of this fix; a later upgrade requires its own reviewed contract change.
- Redesigning gateway business behavior beyond proving and narrowing the host-execution boundary.
- Changes to macOS, Linux, or existing WSL2 containment behavior.

### Key Entities

- **Containment Hook Contract**: Effective Claude Code configuration and behavior that intercepts every native-Windows shell call and blocks on any handler failure.
- **Trusted Policy Source**: Owner-controlled registry state plus Orbit's verified base rules. Employee workspaces are never part of this entity.
- **Trusted Policy Snapshot**: Optional derived, read-only command policy bound to one employee and source state, stored outside employee write scopes.
- **Gateway Exception**: Current owner authorization for one canonical Orbit-owned gateway invocation to run on the host under that gateway's own controls.
- **Containment Readiness Result**: Time-stamped evidence covering effective hook behavior, dependency identity, request-aware MXC support, positive execution, and negative denials.
- **Release Evidence Bundle**: Results tied to one release candidate, dependency set, Windows build, and architecture that prove all P0 matrices passed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across 100 repetitions of every hook failure class in User Story 1, zero host-marker commands execute and zero hook, helper, proxy, executor, or workload processes survive the deadline.
- **SC-002**: Across the policy-tampering matrix, including pre-existing and raced workspace caches, profile fields, settings, skills, symlinks, and junctions, 100% of secret reads, out-of-scope writes, private-network connections, and unapproved-domain connections remain blocked.
- **SC-003**: In a gateway corpus containing every enabled gateway's valid forms and at least 50 bypass variants per gateway, 100% of canonical calls reach only the intended trusted gateway and zero non-canonical calls execute on the host.
- **SC-004**: On each supported Windows architecture, a clean compatible installation and an upgraded installation both prove hook failure blocking, one allowed contained action, secret-read denial, outside-write denial, non-allowlisted-network denial, and timeout cleanup before accepting employee work.
- **SC-005**: Every accepted native Windows run has a readiness result tied to the current employee-policy source, Orbit release, Claude Code behavior proof, MXC artifact/schema, architecture, and Windows build; stale or mismatched evidence results in zero employee shell executions.
- **SC-006**: For each unsupported or tampered dependency case, setup or doctor identifies the blocker and one exact recovery action within 30 seconds, without exposing secret or sensitive policy data.
- **SC-007**: All existing macOS, Linux, and WSL2 containment and gateway tests pass unchanged, and team data survives native-Windows blocking, repair, and fallback with zero loss.
- **SC-008**: Independent security review of the release candidate finds zero path by which employee-controlled workspace content or a containment-hook failure can cause an arbitrary host process to execute.
- **SC-009**: At least 9 of 10 non-technical owners shown a blocked-run message can identify that work did not run, name the failing prerequisite, and follow the displayed recovery action without separate documentation.

## Assumptions

- Employee workspace contents are attacker-controlled for security design, even when ordinary permission rules discourage edits to particular files.
- Claude Code `2.1.295+` preserves documented `onFailure: "block"` behavior, but runtime proof remains required because settings and later releases can alter effective behavior.
- MXC `1.0.1` and stable schema `1.0.0` remain the only accepted native runtime contract for this feature.
- Gateway programs still need host execution to access owner-held credentials and enforce their existing controls. This feature narrows that exception; it does not assume broad shell pass-through is safe.
- WSL2 remains the safe fallback when native prerequisites cannot satisfy this contract. Orbit never falls back to an uncontained native shell.
- The prior shell-only containment decision remains in force. File and web tools continue under Claude Code and Orbit permission controls, but they cannot modify inputs that govern host execution or containment.

### Dependencies

- Claude Code hook support with command-hook exec form, timeout, `PreToolUse`, input rewriting, explicit deny decisions, and `onFailure: "block"`.
- Official Microsoft MXC `v1.0.1` runtime artifacts, stable schema `1.0.0`, request-aware probe, ProcessContainer support, and required host-preparation tooling.
- Orbit's owner-controlled registry, ability catalog, verified installation files, diagnostics, setup, doctor, and WSL2 fallback.
- Access to supported x64 and ARM64 Windows 11 hosts for release-candidate evidence while Orbit ships both architectures.
