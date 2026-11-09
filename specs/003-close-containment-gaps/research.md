# Research: Fail-Closed Native Windows Containment

**Feature**: `003-close-containment-gaps`
**Date**: 2026-11-06
**Status**: Complete; no unresolved clarification remains

## Evidence reviewed

- Current implementation: `core/mxc.py`, `core/engine.py`, `core/abilities.py`, `core/abilities.json`, `core/hire.py`, `core/staffd.py`, `core/update.py`, `orbit`, `setup-windows.ps1`, `.github/workflows/tests.yml`, `tests/test_mxc.py`, and `tests/test_platforms.py`.
- Prior design: `specs/001-windows-mxc-sandbox/` research, plan, data model, contracts, quickstart, and gates.
- Claude Code: [hooks](https://code.claude.com/docs/en/hooks), [settings precedence](https://code.claude.com/docs/en/settings), [permissions](https://code.claude.com/docs/en/permissions), [CLI flags](https://code.claude.com/docs/en/cli-reference), and release notes beginning with [2.1.295](https://github.com/anthropics/claude-code/releases/tag/v2.1.295).
- Claude managed-policy delivery: [managed settings](https://code.claude.com/docs/en/managed-settings) and [server-managed fetch/caching](https://code.claude.com/docs/en/server-managed-settings), including non-default `ANTHROPIC_BASE_URL` fetch suppression and `policyHelper` precedence.
- MXC baseline: `microsoft/mxc` tag `v1.0.1`, commit `fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2`; especially the [stable schema](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/schemas/stable/mxc-config.schema.1.0.0.json), [schema guide](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/schema.md), [host preparation](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/backends/process-container/host-prep.md), and [Windows build support](https://github.com/microsoft/mxc/blob/fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2/docs/backends/process-container/os-version-support.md).
- Open MXC `1.0.1` risks incorporated as release blockers: [BaseContainer/LPAC incompatibility #1496](https://github.com/microsoft/mxc/issues/1496), [DNS proxy-mode leakage #1666](https://github.com/microsoft/mxc/issues/1666), [owner HKCU environment visibility #1670](https://github.com/microsoft/mxc/issues/1670), and [readwrite delete/rename compatibility #1676](https://github.com/microsoft/mxc/issues/1676).

## Current-state conclusions

1. `core/mxc.py::hook_settings()` omits `onFailure: "block"`. Claude Code normally continues a `PreToolUse` action after handler spawn failure, crash, unexpected exit, or timeout when that field is absent.
2. Exit-zero empty output, `{}`, plain text, a JSON string/array, and some partial text are successful no-decision outputs. `onFailure` alone therefore cannot fix `decision({}) == {}` or malformed stdin becoming `{}`.
3. `Bash`, `PowerShell`, and `Monitor` are current shell-capable built-ins. `--allowedTools` approves tools but does not restrict availability; `--tools` does. `Monitor` cannot safely participate in a rewrite-based boundary and must remain unavailable.
4. Headless runs load employee project settings. Folder/Desktop sessions put critical settings inside the employee workspace. Hooks from settings, plugins, skills, and agents can merge and execute in parallel. An Orbit denial does not stop an untrusted sibling handler from producing host effects.
5. `<workspace>/state/mxc-policy.json` overrides computed policy. `profile.json` supplies access-granting `network_domains`, and its generic merge can also supply `extra_tools`, `extra_denied`, and `add_dirs`.
6. Gateway matching is raw `fnmatch` over shell text and returns no decision. Production receives bare catalog names while its test substitutes a wildcard. Fixing only that mismatch would turn command composition into a host escape.
7. MXC discovery accepts `PATH`, missing metadata, same-major schemas, generic signatures, and a no-request probe. Final proxy-bearing requests are not schema validated.
8. No persisted readiness result gates `engine.run()`, service scheduling, interactive sessions, updates, or gateway classification.
9. `tests/test_platforms.py` contained a committed `=======` marker; it was removed in `b310ae7` and the module now parses. The remaining baseline task is aligning platform expectations with the documented hook exec form before cross-platform evidence is trusted.
10. Feature 001's optional real-host validation rule is incompatible with FR-033 and FR-034.

## R1 — Isolate the real Claude client instead of trusting workspace settings

**Decision**: Native-Windows employee runs use Claude Code `--restricted`, `--setting-sources ""`, `--strict-mcp-config`, and an explicit `--tools` list. `PowerShell` is the only enabled shell tool. `Bash` remains matched and denied as defense in depth. `Monitor` is omitted from `--tools`, explicitly denied, and required absent from the live tool inventory. User, project, local, auto-discovered plugin, skill-hook, and agent-hook sources do not participate. Explicit Orbit plugins and sanitized instruction-only skills are release-verified before loading; employee/team skill text is copied into an immutable per-run bundle with no link back to writable source. Native MCP config admits only strict owner-state remote connectors or release-verified non-shell servers whose tools cannot write security/runtime/install state.

The containment hook is delivered through an Orbit-owned managed-policy bootstrap, not ordinary `--settings`. Windows setup (with owner-approved elevation) installs one exact HKLM document whose `policyHelper.path` is an absolute release-verified native `orbit-policy-helper.exe`; Claude invokes it with no arguments as required on Windows. The helper reads only fixed inherited variables `ORBIT_POLICY_SESSION_ID` and a 256-bit base64url `ORBIT_POLICY_TOKEN`, then connects to fixed owner-side named pipe `\\.\pipe\OrbitPolicyV1`. Pipe DACL, client PID/image/hash verification, one-use expiring token, and parent process-tree binding authenticate both sides. For a valid Orbit launch it emits `{"managedSettings": {...}}` containing complete managed hooks/locks. When Orbit variables are absent (unrelated owner session), it emits `{}`—the `managedSettings` key is omitted so lower owner/admin policy is not suppressed. Invalid/expired Orbit credentials exit nonzero. The parent records protected receipt with exact emitted digest. Changed helper/document applies only next launch; independent watchers terminate employee sessions on mutation.

Remote/server-managed policy is made inapplicable by using an Orbit-owned `CLAUDE_CONFIG_DIR` with a closed layout and no remote-policy cache, routing employee Claude API traffic through a release-verified local loopback relay, and setting a non-default `ANTHROPIC_BASE_URL`; Claude's documented behavior then skips server-managed fetches. The config root permits only enumerated authentication/session/transcript state needed by Orbit and rejects user settings/plugins/remote-policy cache. The relay forwards only the reviewed Claude API protocol to `api.anthropic.com`, never falls back direct, never serves managed settings, and never logs credentials/content. Readiness verifies the layout/cache absence and fetch skip through real-client diagnostics, verifies the exact HKLM helper is the selected local source, and rejects MDM/HKLM replacement, source merging, policy-helper failure, remote-cache/unexpected configuration creation, or any foreign managed handler. Lower managed files and HKCU are ignored because the exact HKLM admin document is present and `first-wins`.

Every run checks the real client's `system/init` stream for version, session identity, active tool names, MCP servers, and plugin errors, plus the policy-helper receipt and real hook behavior, before sending employee work. A source mutation stops the process tree; no claim relies on `ConfigChange`, which does not cover server-managed or registry-policy refreshes.

Native `claude://`/Desktop employee sessions are blocked in MXC mode. The documented `--desktop` path cannot carry `--restricted`, `--settings`, or tool restrictions, while the current alternative relies on employee-writable `.claude/settings.local.json`. Owners retain headless/control-panel runs and explicit WSL2 fallback. macOS, Linux, and WSL2 session behavior does not change.

**Rationale**: `system/init` cannot prove managed-source absence and ordinary command-line hooks can be filtered. An exact managed helper plus remote-fetch suppression gives Orbit an externally inspectable source, puts the critical hook in the effective managed tier, and makes HKCU/project/plugin hooks inapplicable. Restricted mode and explicit tools remain defense in depth.

**Alternatives considered**:

- Keep `--setting-sources project`: rejected because project hooks run with host authority in `-p` sessions.
- Put the hook in workspace local settings: rejected because the employee can pre-seed, race, replace, or disable that file.
- Check `/status`, `system/init`, `resolveSettings()`, or `ConfigChange` for absence: rejected because none is an authoritative continuous oracle for every managed source.
- Install a static global hook: rejected because it affects unrelated sessions. Conditional `policyHelper` output is selected only for a protected Orbit launch nonce.
- Connect employee sessions directly to the default Anthropic API endpoint: rejected because eligible credentials can fetch/poll higher-priority server-managed settings; the no-fallback local relay is part of readiness.
- Trust version text or generated JSON alone: rejected; neither proves the client registered or honored the handler.

## R2 — One strict hook evaluator, one terminal result

**Decision**: Configure synchronous exec-form command handlers with absolute executable and handler paths, explicit short timeouts, no async mode, and `onFailure: "block"`. A small Orbit supervisor owns the evaluator process tree and accepts only one complete, schema-valid terminal result:

- contained: rewrite to an opaque one-use containment ticket;
- gateway: rewrite to an opaque one-use gateway ticket;
- denied: explicit `permissionDecision: "deny"`.

Malformed stdin, unknown or missing tool/event names, missing or non-string commands, incompatible event schema, empty output, partial output, plain text, `{}`, arrays, strings, extra output, evaluator failure, and serialization failure can never become a successful no-decision response. The input schema accepts the complete documented common fields and exact-version PowerShell fields (`description`, `timeout`, `run_in_background`) while rejecting unknown semantics. Observational fields are ignored for authority. Rewritten `tool_input` is constructed from an allowlist: fixed helper command, fixed safe description, policy-derived foreground timeout, and `run_in_background: false`; model-selected execution controls are never copied. Invalid input produces explicit denial; inability to emit denial exits nonzero/2 so the verified client blocks through `onFailure`.

`SessionStart` produces an owner-side receipt. `onFailure` is not treated as a SessionStart gate: the parent-held prompt and receipt are the gate. The parent waits for real initialization, policy-helper receipt, and SessionStart receipt before writing the employee prompt. Independent registry/file watchers terminate the process on managed-source mutation; `ConfigChange` is supplemental only.

**Rationale**: Claude Code treats several exit-zero outputs as successful silence. Orbit must validate its own bytes, not infer that `onFailure` covers them. Waiting before the prompt prevents employee work from racing session registration.

**Alternatives considered**:

- Add only `onFailure`: rejected because empty/plain/partial exit-zero output still continues.
- Return no decision for gateways: rejected because FR-001 requires a terminal disposition and sibling permission behavior is not authorization.
- Depend on exit code 2 for normal decisions: rejected for ordinary operation; structured decisions provide auditable intent. Exit 2 remains the last-resort failure path.

## R3 — Split trusted security policy from employee metadata

**Decision**: Introduce a strict owner-controlled security subtree in `staff.json`, with schema version and monotonic revision. Access-granting fields and explicit owner-deny fields—employee identity and workspace binding, abilities/gateway grants, connectors/MCP server identities and URLs, network domains, denied resources/channels, additional directories/tools, timeout overrides, and native mode—come only from that subtree, release-owned catalogs, and the verified base policy. Connector grant/revoke and deny paths move into this typed API; their digests participate in policy, readiness, and session invalidation. A measured MXC leak is advisory unless it intersects an explicit owner deny. An intersecting leak blocks native shell workflows for that employee because Orbit cannot prove selective enforcement; WSL2 remains the recovery path.

`profile.json`, workspace settings, skills, logs, and all model-produced files are metadata/instructions only. `state/mxc-policy.json` is never opened for authorization. Existing files remain untouched as non-authoritative data.

Existing profile-based grants are not auto-imported. Upgrade records them as requiring owner review, installs the narrower base policy, and keeps native work blocked until the owner confirms the desired grants into trusted state.

**Rationale**: Provenance cannot be recovered from a file the employee could already modify. A conservative reconfirmation is the only safe migration.

**Alternatives considered**:

- Move the current cache unchanged outside the workspace: rejected because it remains stale and unbound.
- Sign or hash a workspace cache: rejected because the hook still needs trusted freshness and key state; direct trusted-state derivation is simpler.
- Auto-copy profile domains during upgrade: rejected because attacker-written and owner-written values are indistinguishable.

## R4 — Stable command policy and one-use execution tickets

**Decision**: Read trusted registry bytes through one no-follow, regular-file operation; validate a closed schema; derive one canonical policy and fingerprint; build the request; then recheck the source fingerprint before issuing a disposition. The helper/dispatcher rechecks it again when atomically claiming a short-lived, single-use ticket. Any mismatch, replacement, reparse point, stale ticket, duplicate claim, missing field, or extra field denies the command.

Tickets live under owner runtime state outside employee workspaces and bind employee, session, command/tool-use ID, disposition, policy fingerprint, Orbit release/contract epoch, creation/expiry, payload digest, and exact launcher/runtime identities. Original commands and gateway arguments stay in the protected ticket, not in the rewritten host-shell string or ordinary logs. Claimed tickets are removed or tombstoned; support evidence contains hashes only.

**Rationale**: Rechecking at dispatch closes the gap between hook authorization and actual launch, including queued commands after owner tightening. Opaque rewritten commands remove quoting and secret leakage from the host shell.

**Alternatives considered**:

- Reusable per-run snapshot: rejected; it can preserve revoked access.
- Put raw command/request paths in `updatedInput`: rejected; it exposes replayable state and expands shell parsing.
- Retry silently after a race: rejected; current action denies, next action rebuilds from trusted state.

## R5 — Whitelist one PowerShell AST shape and always rewrite

**Decision**: Gateway status is explicit catalog metadata, not a wildcard. A fixed release-verified parser helper runs `System.Management.Automation.Language.Parser` under absolute Windows PowerShell with `-NoProfile -NonInteractive`; the proposed command arrives only as stdin data and is never evaluated. The helper runs inside the hook supervisor's Job Object and returns a structured argument vector or a closed rejection code.

Native Windows accepts only an AST with no parse error, exactly one statement, exactly one pipeline element, one `CommandAst`, no redirection/background/chain/call/dot-source form, and an exact lowercase unquoted catalog command as its first element. Every remaining element must be a static bare option/token or static literal string. Variables, splatting, subexpressions, expandable strings with nested expressions, script blocks, here-strings, backticks, comments/control characters, aliases, paths, extensions, functions, assignments, and nested shells are rejected. Input and argument counts/sizes are bounded.

This AST whitelist distinguishes quoted literal `&`, `|`, `;`, `>`, or JSON data from active operators without implementing a second PowerShell parser. The hook resolves current owner authorization and catalog identity, then rewrites to an absolute verified Orbit dispatcher plus a safe opaque ticket ID. It never runs the original command. The dispatcher revalidates authorization, policy revision, catalog/launcher/shared-module/dependency-lock digests, and invokes the gateway module through a dedicated versioned Python environment with an argument vector and minimal environment—never `shell=True`, `.cmd`, `PATH`, a floating user-site dependency, or the employee's PowerShell profile.

The final v1 host catalog is exactly `staff-apify` and `staff-compute`, the two gateways that require owner-held credentials/owner cloud control. `staff-fetch`, `staff-browse`, `staff-watch`, `staff-video`, `staff-connectors`, `staff-docs`, and `staff-skill` are contained; incompatibility means denial, not host promotion. Host gateways may not install or spawn descendant executables. `staff-apify` uses only the dedicated hash-locked Python environment and fresh trusted-state authorization. `staff-compute` is rewritten to use the GitHub HTTPS API in-process for Git data, workflow dispatch/status/artifacts, and ref deletion; it no longer resolves or launches `gh`, `git`, shells, or user configuration on the host. Approved and rejected gateway-like attempts write owner-side, non-secret audit records. A preallocated audit WAL plus Windows Event Log fallback records audit-storage failures; inability to reserve either sink blocks readiness before a gateway event.

**Rationale**: Full PowerShell parsing is unnecessary if the accepted language is intentionally smaller. Rewrite-to-dispatch preserves gateway behavior without granting the employee's shell a host exception.

**Alternatives considered**:

- `fnmatch`, prefix, or substring checks: rejected as composition bypasses.
- Regex, `shlex`, or a hand-written tokenizer: rejected because it would not authoritatively distinguish PowerShell's active and literal forms.
- Allow an absolute employee-supplied launcher path: rejected because path spelling, links, and quoting remain attacker inputs.
- Execute `.cmd` wrappers: rejected because `%*`, `PATH`, and shell reparsing reopen injection.
- Keep fetch/browser/video/watch/connectors on host: rejected because none requires owner credentials and their browsers/downloaders create a large descendant-executable boundary.
- Contain every gateway: rejected because Apify and owner-connected compute require protected owner credentials/control unavailable to the contained employee shell.

## R6 — One release-owned external security manifest

**Decision**: Add one closed JSON manifest consumed by Python and PowerShell. It pins the containment contract epoch, Claude capability floor, managed helper/relay/worker identities, MXC tag/commit/package URL and digest, exact schema and digest, per-architecture executor and host-prep paths/digests, Microsoft publisher requirement, Windows build map, release-owned handler/gateway file digests, and absolute hash/publisher records for every preinstalled browser/media/OCR/tool binary reachable inside MXC. Runtime installation is forbidden.

Setup stages the package, rejects unknown architecture, verifies tarball, selected payload hashes, PE architecture, Authenticode trust and Microsoft Corporation publisher, required/feature-reachable companions, separately vendored schema bytes, and package metadata, then atomically activates a versioned install. The npm tarball does not contain the published JSON Schema, so Orbit vendors/fetches it only from the pinned commit and verifies its exact digest. Runtime accepts only the active versioned path; `PATH` fallback and self-asserted marker defaults are removed. Any repair starts by invalidating readiness.

`wxc-host-prep.exe` is installed and verified but not run unconditionally. Orbit's identity-less proxy request must select `base-container` with `needsDaclAugmentation == false`; AppContainer+DACL Tier 3 cannot satisfy that request and is rejected. Host prep remains verified recovery tooling and becomes active only under a separately reviewed future request contract. Conditional `--audit` companions must be installed/verified or that diagnostic mode is disabled.

**Rationale**: Duplicated Python/PowerShell constants drift. A manifest gives setup, runtime, doctor, tests, and evidence one reviewable source.

**Alternatives considered**:

- Trust package digest alone: rejected; wrong-architecture selection or post-extraction replacement remains possible.
- Trust any valid Authenticode signer: rejected; publisher identity is part of the baseline.
- Keep version text files as authority: rejected; observed bytes, signatures, and architecture are authority.

## R7 — Validate the final request and probe the exact request shape

**Decision**: Install the exact stable schema artifact and verify its digest. A Windows-only, hash-locked [`jsonschema` `4.25.1`](https://pypi.org/project/jsonschema/4.25.1/) dependency (the reviewed line supporting Python 3.9) uses `Draft7Validator` against those exact bytes; its wheel and transitive lock are release inputs. Orbit's builder emits only the fixed `1.0.0` one-shot ProcessContainer subset and rejects unknown fields before serialization. Both the base document and final proxy-bearing wire request are validated, with the final bytes validated again immediately before use. `wxc-exec.exe <request> --probe` then supplies the pinned runtime's semantic parser and request-aware capability decision; no-request `--probe` remains discovery only.

The accepted proxy request removes the current unnecessary `processContainer.capabilities: ["internetClient"]`. It explicitly applies the most restrictive UI policy compatible with noninteractive PowerShell: `clipboard: none`, `injection: false`, container handle/atom isolation, no desktop/system-setting control, and IME disabled; request-aware proof records every corresponding `uiCapabilities` bit. Readiness requires probe exit zero, valid JSON, absent `error`, `tier == "base-container"`, `needsDaclAugmentation == false`, and completed capability measurements. Identity-less loopback proxying remains the reviewed feature baseline; real tests measure direct public/private sockets, non-proxy host-loopback, and an authoritative unique DNS-query canary. A measured leak enters `ready-with-warnings` and work continues unless the owner explicitly denied that channel, in which case that employee's native shell remains blocked.

Readiness starts the same helper path, checks `error == null` and usable tier, then first runs structural timeout/process-tree cleanup, which must pass with zero survivors. It separately runs create/read/update/delete/rename compatibility plus filesystem, owner-hive, network/DNS, and UI side-channel probes. Side effects are inspected directly; denial-looking prose is not evidence. Only completed enumerated data/access enforcement gaps become warnings. Explicit owner-deny intersections block; other eligible leaks and compatibility limitations are highlighted while workflows continue.

Every command revalidates final request shape and current artifact/readiness identity before one-shot execution. Audit mode never handles employee work.

**Rationale**: `_with_proxy()` changes security-relevant fields after the current request is built. Only the final bytes and actual request-aware probe establish compatibility.

**Alternatives considered**:

- Schema-major compatibility: rejected; released contracts are immutable.
- Generic host probe: rejected; it says nothing about Orbit's filesystem/proxy request.
- Use only the executor parser: rejected because schema validity and backend semantic compatibility are distinct checks under the contract.
- Use a floating/latest JSON-schema dependency: rejected; `4.25.1` is the last reviewed line supporting Python 3.9 and is installed from a complete hash lock.

## R8 — Own Windows child trees with Job Objects

**Decision**: Add one Windows process supervisor based on a Job Object with kill-on-close and no permitted breakaway where MXC permits it. Assign children before they can spawn unowned descendants. Layer deadlines: evaluator inside hook timeout, MXC process timeout inside helper watchdog, and Claude run timeout outside both. Timeout terminates the job, waits boundedly, and records cleanup outcome.

Setup also installs a signed native Windows service `OrbitContainmentBroker` from `native/orbit-containment-broker/`. It runs in Session 0 as LocalSystem with restricted service SID and exact service required-privilege set `{SeAssignPrimaryTokenPrivilege, SeIncreaseQuotaPrivilege, SeChangeNotifyPrivilege}`; `SeTcbPrivilege` and every other optional privilege are absent. It has no network and accepts only closed `\\.\pipe\OrbitContainmentBrokerV1` protocol from owner-side verified helper. Pipe DACL, client PID/image/session-token checks, one-use ticket ID, and release/readiness digests authenticate requests; raw commands are never IPC arguments.

The broker owns a dedicated non-admin local `OrbitMxcWorker` identity. Setup grants only batch logon, explicitly denies local/remote interactive and network logon, stores random credential as LSA private data readable only by broker service SID/System, and applies exact ACLs. For each command broker calls `LogonUserW(LOGON32_LOGON_BATCH)` and requires returned token already reports `TokenSessionId == 0`; it never calls `SetTokenInformation(TokenSessionId)` and therefore never needs `SeTcbPrivilege`. It does not load persistent profile/hive, creates private per-command window station/desktop and disposable profile directories, then calls `CreateProcessAsUserW` with `CREATE_SUSPENDED|CREATE_UNICODE_ENVIRONMENT|CREATE_NO_WINDOW`, exact env/std handles/executable/argv. It assigns suspended executor to outer Job before resume and destroys token, private desktop/window station, profile directories, and handoff files after drain. There is no `CreateProcessWithLogonW`, interactive-logon exception, owner-token fallback, conditional privilege set, or “reviewed equivalent.”

The contained process therefore has no intended owner HKCU, owner interactive session/window station, or reusable worker HKCU persistence. Readiness addresses `HKEY_USERS\<owner-SID>\Environment` and `...\SOFTWARE\Policies\ClaudeCode` explicitly (not worker `HKCU`), attempts owner hive-file loading/access, and tests screen capture, raw input, low-level hooks, and foreground control across Session 0/private window station. Broker privilege/protocol/service, token, launch, or measurement failure blocks. A completed canary that observes access is advisory unless the owner explicitly denied that resource/channel; an explicit-deny breach blocks that employee's native shell.

Use the supervisor for hook evaluator/fault probes, Claude runs, Orbit helper/proxy/executor paths, and host gateway budgets as applicable. MXC already creates its contained root suspended, assigns it to an inner kill-on-close Job Object before resume, and terminates that job on timeout/normal teardown; Orbit treats those controls as the workload owner while its outer supervisor owns Orbit-side processes. Real-host compatibility tests verify alternate-user/nested-job behavior, spawn grandchildren, and require absent delayed markers plus no surviving PIDs.

**Rationale**: Python `Popen.kill()` and `subprocess.run(timeout=...)` do not prove Windows descendant cleanup. Claude documents cancellation, not tree termination.

**Alternatives considered**:

- `taskkill /T` after timeout: rejected because ownership and PID-reuse races are weaker than assigning a job before execution.
- Trust MXC timeout alone: rejected; it does not own the hook, helper, proxy, or Claude client.
- Run the contained workload as the owner's Windows identity: rejected because MXC `1.0.1` does not provide a registry-deny policy and known behavior exposes owner HKCU values.

## R9 — Readiness is a security state machine, not a doctor message

**Decision**: Persist strict owner-side machine and per-employee readiness records with states `blocked`, `proving`, `ready`, and `ready-with-warnings`. They bind contract epoch, Orbit candidate identity, Claude executable/version/hash, effective source/config/handler/tool/plugin fingerprints, hook behavior proof, MXC package/payload/schema identities, architecture, exact Windows build, host preparation, request-aware probe, measured leaks, explicit owner denials, employee/policy fingerprint, timestamps, and non-secret evidence digests.

State transitions are `blocked -> proving -> ready|ready-with-warnings`; missing, failed, inconclusive, or mismatched measurement returns to `blocked`. A completed leak without explicit owner deny yields `ready-with-warnings`; adding/tightening an owner deny that intersects it returns to `blocked`. Every headless session waits for live initialization, policy-helper receipt, and SessionStart receipt. Every hook/gateway rechecks current readiness key. Setup, repair, upgrade, client/helper/relay/runtime/worker/host/policy/connector/deny change requires new proof. Independent watchers stop a run on mutation; ConfigChange is supplemental.

The service and panel may remain available for repair while employee scheduling, runs, and native folder sessions remain blocked. Doctor and setup consume the same structured report and show one recovery action per blocker without commands, credentials, policy contents, or unrestricted paths.

**Rationale**: A check that is not bound and enforced at launch is diagnostic, not authorization.

**Alternatives considered**:

- Probe on setup only: rejected because dependencies and settings change afterward.
- Version-only cache: rejected because effective settings and artifacts matter.
- Automatically fall back to native uncontained execution: rejected. Explicit WSL2 is the only fallback.

## R10 — Upgrade invalidates before work and never trusts legacy grants

**Decision**: Increment a containment contract epoch. New code treats missing/old readiness as blocked before any employee work. The first transition from legacy `0.8.0` cannot use old `update.apply()` because that code merges before quiescing. Feature 003 is therefore installed through a full-trust Microsoft Store package whose Package/Identity/Name is exactly `BasemTarekkamal.OrbitSecurityBootstrap`; Microsoft Store assigns a separate alphanumeric Store Product ID during registration. Before release, that assigned ID, exact Publisher, Package Family Name, and version are populated into the externally pinned trust document and release-owned setup text; placeholder/unregistered values fail publication. Acquisition uses exact assigned Store ID/version with `winget --source msstore`. Store/package-signing validation is the independent initial trust channel legacy Orbit lacks; bootstrap refuses unpackaged execution and verifies Store package family/publisher through Windows APIs. Signed package payload embeds offline release key and expected `windows-evidence-trust-v1.json` digest. Secure releases use a legacy-invisible namespace whose first three numeric components remain `0.8.0` (for example `0.8.0-sec.1`), so old `_key()` never offers them in-app even if GitHub marks one latest; every later secure-line release preserves that property indefinitely while any legacy install is supported. Bootstrap stops/disables scheduled service, terminates employee Claude/helper processes, writes machine-level `blocked-before-update` marker outside kit, stages/verifies candidate, atomically activates it, and starts only repair control plane. It refuses source mutation unless package identity, quiescence, and marker persistence are proven.

Bootstrap contract pins initial Store package version `1.0.0.0`; install command uses exact product ID, exact version, and `--source msstore`. Any different version requires a trust-root rotation/review or prior secure-release authorization.

The legacy in-app update path is not allowed to target a feature-003 tag and a release test executes old `_key()` against every secure-line version to prove `newer == false`. After bootstrap installation, all later updates go through its external stop-the-world launcher, which uses the full secure-line version and invalidates evidence before replacement. Manual Git pulls are unsupported for native P0 migration; startup sees bootstrap/epoch mismatch and remains blocked, but owners must run bootstrap to obtain pre-mutation quiescence.

Team data, workspaces, logs, skills, and legacy cache/profile files remain intact. Legacy authorization is ignored. Owner-approved security data is rebuilt in the trusted registry through explicit review. The secure-line suffix/version is advanced by the external updater while its first three numeric components remain `0.8.0` for legacy invisibility.

**Rationale**: Safe migration preserves data, not stale authority.

**Alternatives considered**:

- Restart and prove lazily on first shell command: rejected because gateway and session surfaces could race the proof.
- Let old `update.apply()` install the first secure release: rejected because old code cannot execute new quiescing logic before source replacement.
- Use a normal greater-than-`0.8.0` version while legacy updater remains in the field: rejected because every old client would offer the unsafe merge path; secure-line versions must compare equal under old `_key()` and be installed externally.
- Delete legacy files: rejected as unnecessary and contrary to data preservation.

## R11 — Real-client and real-host evidence blocks release

**Decision**: Hosted CI keeps deterministic fake/unit matrices. Release candidates additionally require authenticated, reviewable evidence from native Windows 11 x64 and ARM64 hosts, each covering clean and upgraded installations. The bundle is tied to candidate commit/tree, manifest digest, test harness digest, exact Claude/MXC/schema identities, architecture, build/UBR, and policy/catalog fingerprints.

Required matrices are hook failure/output bytes, policy tampering/races, at least 50 gateway bypasses per enabled host gateway, exact schema/artifact tampering, registry/DNS/UI side channels, proxy behavior, advisory continuation, explicit-owner-deny blocking, and structural zero-survivor process-tree cleanup. Each hook failure class runs 100 times. Release passes when every structural gate/cleanup passes, every eligible leak is measured/classified/warned, advisory cases continue, and every explicit-owner-deny case blocks. Missing ARM64 evidence removes ARM64; it cannot be waived.

The trust root is a separately versioned `windows-evidence-trust-v1.json` whose SHA-256 is pinned by the Microsoft Store bootstrap and prior secure release, not by the candidate under test. It contains RSA-2048-PSS-SHA256 public key IDs for protected native x64 and ARM64 runner roles, an offline Ed25519 release-approver key, architecture/role constraints, validity windows/revocations, and exact release workflow identity. Runner private keys are non-exportable keys in the Microsoft Platform Crypto Provider (TPM); PSS uses MGF1-SHA256 and 32-byte salt. Each host bundle is signed by matching architecture key. Aggregate candidate index is signed by distinct offline Ed25519 key after validation. Key rotation requires a domain-separated, RFC 8785-canonical rotation envelope signed by old and new roots plus contract-epoch update.

All signed payloads use UTF-8 RFC 8785 JSON Canonicalization Scheme bytes, including sorted artifact maps and canonical number encoding, prefixed by an exact ASCII domain string plus NUL (`Orbit Windows Containment Host Evidence v1\0`, `... Aggregate v1\0`, or `... Trust Root Rotation v1\0`). Runner signatures cover SHA-256 of those domain-separated bytes using RSA-PSS parameters above; offline Ed25519 signs domain-separated canonical bytes directly. Signature fields are omitted from bytes they authenticate and encoded base64url without padding.

The only publication job lives in `.github/workflows/windows-containment-release.yml`, is pinned by workflow digest in the trust document, runs `tests/validate_windows_release_evidence.py`, verifies all host and aggregate signatures against the external root, and publishes through a protected `windows-containment-release` GitHub Environment only when the validator emits the current candidate digest. Ordinary test/release jobs have no publication credential. GitHub OIDC/artifact attestations are supplemental, not the sole trust root.

**Rationale**: Windows Server hosted runners and fake executors cannot establish client hook semantics or ProcessContainer enforcement.

**Alternatives considered**:

- Preserve feature 001's optional quickstart: rejected by FR-033/034.
- Prose attestation: rejected; it is not candidate-bound or reproducible.
- Trust any signature/attestation presented by the candidate: rejected as circular; authorized keys/workflow and revocation must come from the externally pinned prior trust root.
- Emulated ARM64: rejected; payload architecture and native runtime behavior differ.

## R12 — Keep native exceptions behind an exact platform gate

**Decision**: New hook, gateway, readiness, installer, broker, managed-policy, relay, worker, and pinned-dependency behavior executes only when `osinfo.KIND == "windows"` and owner mode is `mxc`. Shared tool files may gain native-only resolution branches, but existing POSIX/WSL PATH/runtime-install and command behavior remains byte/behavior-equivalent outside that exact branch. Native Windows recorded as `wsl2` exposes no native employee execution surface. macOS, Linux, and actual WSL2 retain existing sandbox, `failIfUnavailable`, gateways, settings, service, and tool dependency behavior.

The syntax-broken platform test was repaired in `b310ae7`. Add byte/structure regression tests around non-Windows command/settings generation and per-tool dependency/launcher behavior, then run existing suites unchanged.

**Rationale**: FR-035 forbids sharing native host exceptions with WSL2 or changing established non-Windows behavior.

**Alternatives considered**:

- Refactor all platforms through the new gateway path now: rejected as out of scope and higher regression risk.

## Resolved design summary

All planning unknowns are resolved:

- trusted policy: strict owner registry, no workspace cache;
- snapshots: no reusable policy snapshot; one-use protected tickets only;
- client isolation: restricted headless CLI, Orbit HKLM policy helper, no-fallback local API relay; native Desktop blocked;
- hook proof: policy-helper/live-init/session receipts every run, external source watchers, full real-client proof on any bound change;
- shell surface: PowerShell only; Bash denied; Monitor unavailable;
- gateway parsing: PowerShell AST whitelist, final host set `{staff-apify, staff-compute}`, childless verified dispatcher targets;
- process/registry isolation: alternate low-privilege shell identity plus preassigned Windows Job Objects;
- MXC validation: exact manifest/schema, request-aware probe, registry/DNS/UI/filesystem/functionality canaries, real helper/proxy path;
- readiness: bound machine/per-policy evidence with fail-closed invalidation;
- first upgrade: externally signed stop-the-world bootstrap, never legacy in-app merge;
- release proof: x64 and ARM64, clean and upgrade, externally rooted per-host/offline signatures and publication gate.
