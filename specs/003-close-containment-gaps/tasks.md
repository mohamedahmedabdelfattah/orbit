# Tasks: Fail-Closed Native Windows Containment

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md), [GATES.md](./GATES.md)

**Tests**: Required. The spec defines an independent test per user story, `quickstart.md` makes every matrix release-gating, and `plan.md` names the test and evidence harnesses as planned components. Test tasks below implement that coverage; real-client/real-host evidence tasks must never be satisfied by fake executors.

**Phase order**: All four stories are P0. Phases follow `plan.md`'s required delivery sequence — trusted state (US2) before the hook boundary (US1) — because shipping the hook without the strict-policy surfaces would reopen the widening defect. Task IDs run in execution order.

**Terminology** (per `plan.md`): *policy helper* = `orbit-policy-helper.exe` managed-policy emitter; *ticket helper* = Orbit process that claims a contained ticket; *containment broker* = `OrbitContainmentBroker` executor launcher; *executor* = `wxc-exec.exe`.

## Phase 1 — Setup: Release Manifest, Test Baseline, Real-Host Harness

**Purpose**: One reviewable source of pinned contract values, a regression baseline that can actually run, and the shared real-host harness both US3 and US4 extend.

- [ ] T001 [P] Create the closed release manifest `core/contracts/native-windows-containment-1.json` with `schema: orbit.native-windows-containment.v1`, `contract_epoch`, `orbit_version`, Claude `minimum_version: 2.1.295` plus required launch flags/shell tools, managed bootstrap records, MXC `1.0.1`/tag/commit/package digest `416D9607C9D4652395D95C3D9C5F5605F1F2F845DA1A63228BEE41B7392CEF49`, schema `1.0.0` digest `207254FA94966A800FA70F01A2DA73AE813D27FE8847200C92F4DD0E219649C2`, x64/ARM64 executor and host-prep paths/digests, Microsoft Corporation signer requirement, minimum builds `26100.9278`/`26200.9278`/`26300.9550`/`28000.2804`, contained-tool dependency paths/digests, and handler/parser/dispatcher file digests; URLs must not float to `latest`/branch/range. (FR-026, FR-027, FR-028, FR-029, FR-031)
- [ ] T002 [P] Create `core/contracts/windows-evidence-trust-v1.json` defining the Store-pinned bootstrap identity (Package/Identity/Name `BasemTarekkamal.OrbitSecurityBootstrap`, separately pinned Store Product ID, exact publisher/family/`1.0.0.0`), TPM RSA-2048-PSS-SHA256 runner roles, offline Ed25519 release-approver role, RFC 8785 domain strings, validity/revocation, exact release workflow identity, and dual-signed rotation envelope requirements. (FR-033, FR-034)
- [ ] T003 [P] Add the hash-locked `jsonschema==4.25.1` dependency in `requirements-native-windows.lock` with a complete transitive lock (wheel digests) for native Windows, referenced by setup and runtime rather than installed at run time. (FR-029)
- [ ] T004 Align existing platform expectations with the documented exec-form managed hook contract in `tests/test_platforms.py` (the committed `=======` marker was already removed in `b310ae7`); assert no `allowedTools`-only assumption, no stray marker, and unchanged non-Windows output. (FR-035)
- [ ] T005 [P] Create the shared real-host harness `tests/windows/mxc-real-host-proof.ps1`: protected evidence root, architecture/candidate binding, suite dispatch (`Gateways`, `Contract`, `PolicyTampering`, `All`), fixed executor argv, closed result/exit contract, nonzero/uncertain-failure handling, and no-secret redaction. (FR-030, SC-004)

---

## Phase 2 — Foundational: Trusted State, Tickets, Dispositions, Process Ownership

**Purpose**: Shared security primitives that every story consumes. No story phase may begin until these parse and their unit suites pass.

- [ ] T006 [P] Implement `core/windows_contract.py` as the single manifest loader/verifier: strict closed parse (unknown/duplicate/missing/null/wrong-type fields invalidate the whole document), `VERSION` equality, `contract_epoch` monotonicity, absolute verified-path resolution with no reparse component, package/payload/schema/digest/PE-architecture/Authenticode publisher checks, companion verification, and `ArtifactVerificationResult` emission; never fall back to a default or `PATH`. (FR-026, FR-027, FR-028, FR-029, FR-031)
- [ ] T007 [P] Extend `core/osinfo.py` to expose exact Windows client SKU, process/OS architecture, branch, build and UBR without range guessing or product-name substitution, and to identify `KIND == windows` separately from recorded mode `wsl2`. (FR-031, FR-035)
- [ ] T008 [P] Add the strict `security` subtree API in `core/grants.py`: `orbit.owner-security.v1` schema with `revision`, mode, global/per-employee `network_domains`, `abilities`, `connectors`, `explicit_denies`, `additional_directories`, `additional_tools`, `timeout_ms`; typed mutation that validates the complete subtree, canonicalizes all values, increments `revision` exactly once, writes a same-directory temp file and atomically replaces, and invalidates readiness before exposing the grant. Generic dictionary merging is forbidden. (FR-011, FR-013, FR-015)
- [ ] T009 Implement one `TrustedPolicyRead` in `core/mxc.py`: reject symlink/junction/reparse/non-regular targets, open once and capture identity plus bounded bytes, parse and validate the strict security subtree and reviewed migration epoch, derive `EffectiveCommandPolicy` only from those bytes plus verified release base/catalog, compute the canonical `PolicySourceFingerprint`, and recheck before response. Enforce disjoint denied/writable sets after canonical/reparse resolution, default-deny network, and an allowlist-only contained environment. (FR-011, FR-013, FR-014, FR-015, FR-016)
- [ ] T010 Add the `orbit.execution-ticket.v1` envelope and issue/claim lifecycle in `core/mxc.py` for both `contained` and `gateway` payload variants: at least 128 random bits, employee/session/tool-use binding, policy fingerprint, readiness key, contract epoch, release digest, bounded timestamps, payload digest, states `issued|claimed|completed|failed|expired`, and atomic no-follow single-use claim that rejects links, replacement, extra keys, replay, and mismatch. (FR-001, FR-014, FR-016)
- [ ] T011 Add the closed `CommandDisposition` enum and terminal serializer in `core/mxc.py`: `contained`, `gateway`, `denied` only, each with required fields; no `none`/`pass-through`/`unknown`/empty-success path, and invalid construction raises instead of emitting silence. (FR-001, FR-005)
- [ ] T012 [P] Implement `core/windows_process.py`: explicit empty-base environment builder (worker `SYSTEMROOT`/`LOCALAPPDATA`/`USERPROFILE`/`TEMP`/`TMP` plus manifest-reviewed needs, no owner secrets/nonces/`PYTHONPATH`), restricted-child process attributes, kill-on-close `ActiveProcessLimit`/no-breakaway Job created before resume, bounded wait, child-tree termination, and survivor evidence. (FR-007, FR-011)
- [ ] T013 [P] Add `tests/test_windows_contract.py` covering manifest closure, epoch/version drift, digest/signature/architecture/companion tampering, exact-schema and Draft 7 acceptance/rejection, and default-block behavior when the manifest is unreadable. (FR-026, FR-027, FR-028, FR-029, FR-031)
- [ ] T014 [P] Add `tests/test_windows_environment.py` proving evaluator/parser/gateway-target/broker-workload environments never inherit `ORBIT_POLICY_*`, relay auth, owner profile config, or provider credentials, and that Job assignment happens before child spawn. (FR-007, FR-011)
- [ ] T015 Reverse the legacy expectations in `tests/test_mxc.py`: exit-zero empty/`{}`/plain/partial/array/string/schema-invalid output is a denial, workspace cache/profile data never authorizes, tickets are single-use, and any uncertain state denies. (FR-004, FR-005, FR-012)
- [ ] T016 Vendor the exact stable `mxc-config.schema.1.0.0.json` bytes and wire `Draft7Validator` against those bytes in `core/windows_contract.py`; reject missing, retired, experimental, version-changed, or unknown fields before serialization. (FR-029)
- [ ] T017 Add ticket/fingerprint unit coverage in `tests/test_mxc.py` (`TrustedPolicy` group) for missing/extra fields, wrong employee/session, expired/future ticket, replay, duplicate claim, policy-source replacement, revision change, and owner tightening between response and claim. (FR-014, FR-015, FR-016)

**Checkpoint**: Manifest, trusted policy derivation, tickets, dispositions, and process/job ownership are unit-verified; no employee shell path has been modified yet.

---

## Phase 3 — User Story 2: Employees Cannot Widen Their Policy (P0)

**Goal**: Workspace, profile, project settings, skills, connectors, and generic registry fields cannot authorize, widen, or remove an owner deny. Runs before US1 because the hook boundary must never ship on top of a widening policy path.

**Independent test**: Pre-seed permissive workspace caches (`state/mxc-policy.json`), profile security fields, project settings, skills, and hook-bearing content. With explicit owner denials for a secret, outside write, private-network access, and unapproved destination, every attempt stays denied and trusted fingerprint evidence is unchanged; without a deny, a completed leak warns and continues.

### Tests

- [ ] T018 [US2] Add the policy-tampering matrix to `tests/test_containment_readiness.py` (`PolicyTampering`): permissive/raced legacy cache, profile grant fields, generic connector/MCP fields, arbitrary remote/local-stdio MCP, project/local/HKCU settings, skill/agent hooks, malformed owner state, wrong employee/session/workspace, symlink/junction/reparse/replacement races, stale/replayed tickets, and forged workspace diagnostics. (FR-011, FR-012, FR-013, FR-014, FR-016, SC-002)
- [ ] T019 [P] [US2] Add `tests/test_mxc.py::TrustedPolicy` cases proving `state/mxc-policy.json` and every employee-writable cache are never opened for authorization, existing copies keep no wider access after upgrade, and profile/workspace metadata cannot supply domains, tools, denies, or timeouts. (FR-012, FR-013)
- [ ] T020 [P] [US2] Add `ExplicitDenyMatching` tests in `tests/test_containment_readiness.py` for every permitted pair (`path exact|subtree`, `registry-path exact|subtree`, `domain exact|wildcard-subdomain` excluding apex, `cidr -> cidr-contains`, `endpoint exact`, `ui-capability exact`, `any -> all`), plus rejection of regex/glob, cross-kind comparison, malformed canonical targets, and wrong employee/boundary. (FR-030, SC-002)
- [ ] T021 [P] [US2] Add settings/skill/hook tamper tests in `tests/test_platforms.py`: employee project settings, workspace skills, plugins, and agent hooks cannot register, replace, disable, or influence a host-side handler; only release-verified Orbit handlers execute. (FR-008, FR-011)

### Implementation

- [ ] T022 [US2] Remove workspace-cache authorization and `PATH` runtime resolution from `core/mxc.py`; never open `state/mxc-policy.json`, and resolve runtimes/handlers only through manifest-verified absolute paths. (FR-012, FR-023)
- [ ] T023 [US2] Split employee metadata from owner security inputs in `core/engine.py`, `core/hire.py`, and `core/panel.py`; access-granting writes go only through the strict `core/grants.py` API, and non-security metadata is returned through a separate API never merged into policy/settings/tool/gateway construction. (FR-011, FR-013)
- [ ] T024 [US2] Move connector/MCP grants into strict owner security state in `core/connectors.py`/`core/connectors.json`: reviewed remote catalog only, no arbitrary URL/local stdio/filesystem/host-execution server, with grant digests participating in policy/readiness invalidation. (FR-013)
- [ ] T025 [US2] Move ability and gateway authorization into strict owner state in `core/abilities.py`/`core/abilities.json`; employee-editable fields cannot widen filesystem, network, timeout, gateway, or execution rights. (FR-013, FR-019)
- [ ] T026 [US2] Rework `core/skillbook.py` to build immutable instruction-only skill bundles for each run and reject hook-bearing/plugin-bearing employee or team content. (FR-008)
- [ ] T027 [US2] Harden `core/guard/staff-guard/hooks/register.js` to verify release identity and preserve PowerShell defenses without permitting untrusted hook registration. (FR-008)
- [ ] T028 [US2] Keep diagnostics/audit copies in employee workspaces explicitly non-authoritative in `core/mxc.py`; editing, deleting, or forging them must not change any future decision, and trusted decisions read only owner-side state. (FR-017)
- [ ] T029 [US2] Complete tightening/race enforcement in `core/mxc.py`: fingerprint comparison at hook time and again at ticket claim, denial on any source change, no reusable per-run policy snapshot, and no stale access after an owner narrows paths/domains. (FR-015, FR-016)
- [ ] T030 [US2] Record legacy grants as owner-review-required migration blockers in `core/grants.py` while leaving existing files intact; install the narrower base policy and keep native work blocked until the owner reconfirms grants through the typed API. (FR-012, FR-013)

**Checkpoint**: US2 independently testable — the tampering matrix changes no trusted decision, and explicit owner denies survive every workspace mutation.

---

## Phase 4 — User Story 1: Shell Commands Fail Closed (P0)

**Goal**: Every native-Windows shell action is contained, canonical-gateway-approved, or denied — never continued after a hook fault.

**Independent test**: A harmless host-marker command is proposed under each failure class (missing registration, unsupported client, disabled hooks, missing handler, non-zero exit, crash, timeout, empty/malformed output, missing input fields, ticket-helper or policy-helper failure). No marker is created, each attempt reports one recovery action, and no policy-helper/ticket-helper/proxy/executor/workload process survives.

### Tests

- [ ] T031 [US1] Add the hook failure/output matrix to `tests/test_mxc.py`: missing handler, spawn error, non-zero exit, crash, timeout immediately before valid output, empty/`{}`/plain/partial/malformed/array/string/schema-invalid output, valid decision plus failed exit, unknown/missing/non-string tool or command, changed input schema, and ticket-helper/broker/proxy/executor start failure; every case asserts explicit denial and zero host execution. (FR-004, FR-005, FR-006)
- [ ] T032 [P] [US1] Implement `tests/windows/hook-failure-matrix.ps1` to drive the real installed Claude client with synthetic marker commands for all classes above, 100 repetitions each, architecture-specific output, host-marker absence, zero surviving hook/supervisor/evaluator descendants, safe message text, and receipt/lifecycle capture. (FR-002, FR-009, SC-001)
- [ ] T033 [P] [US1] Implement `tests/windows/managed-policy-proof.ps1` proving the absolute signed `orbit-policy-helper.exe` receives zero arguments, valid `ORBIT_POLICY_SESSION_ID` plus 256-bit token and authenticated `\\.\pipe\OrbitPolicyV1` yields the exact managed receipt, tokens are unreplayable before prompt delivery, absent Orbit variables yield `{}` with no `managedSettings`, and bad/replayed/wrong-image clients exit non-zero. (FR-003, FR-008, FR-009)
- [ ] T034 [US1] Add session-gate and message-redaction tests in `tests/test_mxc.py`: prompt withheld until policy-helper, relay, `system/init`, `SessionStart`, plugin/MCP, tool-inventory, watcher, and readiness checks pass; `PowerShell` present, `Bash`/`Monitor`/unknown shell tools absent; timeout/mismatch terminates the process tree; denial and blocker messages contain only the FR-010 allowlist (boundary code, recovery action ID/instruction, non-secret reason, employee/run ID) and never commands, secrets, credentials, unrestricted paths, or policy bodies. (FR-001, FR-009, FR-010)
- [ ] T035 [US1] Add multiple-matching-hook and managed-tier tests in `tests/test_mxc.py`/`tests/test_platforms.py`: a second matching hook, workspace/plugin/skill setting, enterprise managed-only policy, globally disabled hooks, or rejected command hooks can neither override a containment denial nor execute employee-controlled code on the host; each configuration is either honored safely or blocks the run before work. (FR-008, FR-009)
- [ ] T036 [US1] Add the newer-client behavioral-drift case to `tests/windows/hook-failure-matrix.ps1` (created by T032): a client newer than `2.1.295` whose hook parsing or failure semantics differ must be refused or blocked until the full behavior proof passes, regardless of its version text. (FR-009, FR-026)

### Implementation

- [ ] T037 [US1] Emit managed exec-form handlers from the policy-helper path in `core/mxc.py` — absolute verified `.exe` plus `args`, explicit sub-20s timeout, no `async`, and `onFailure: "block"` on `SessionStart`, `PreToolUse`, and `ConfigChange` — and remove every handler shape that leaves `onFailure` unset or continuing. (FR-002, FR-004)
- [ ] T038 [US1] Implement strict `PreToolUse` normalization in `core/mxc.py`: accept the documented common/PowerShell fields, reject unknown semantics, treat observational fields as non-authoritative, and rebuild `tool_input` from an allowlist (fixed helper command, fixed description, policy-derived foreground timeout, `run_in_background: false`) so model-selected timeout/background values are discarded. (FR-005)
- [ ] T039 [US1] Implement the hook supervisor and session entrypoints in `core/mxc.py` (`--hook-supervisor`, `--session-start`, `--config-changed`): one closed result per event, denial on any parse/serialization/IO failure, non-zero or exit-2 last-resort failure, owner-side SessionStart receipt bound to nonce/session/managed-policy/handler/readiness, and no workspace-derived configuration. (FR-001, FR-005, FR-009)
- [ ] T040 [US1] Add `native/orbit-policy-helper/` (signed x64/ARM64 `orbit-policy-helper.exe`): fixed `policyHelper.path` no-argument HKLM behavior, authenticated `\\.\pipe\OrbitPolicyV1` nonce protocol with DACL/client PID/image/hash/parent-tree checks, complete `managedSettings` emission (`allowManagedHooksOnly`, permission/plugin/MCP locks), `{}` for unrelated sessions, and non-zero exit for invalid Orbit credentials; include pinned MSVC/Windows SDK build and manifest hashes. (FR-003, FR-008, FR-009)
- [ ] T041 [US1] Extend `setup-windows.ps1` to install the exact HKLM managed document plus the verified policy helper under owner-approved elevation, record its digest/nonce contract, and reject any link/reparse or lower-source shadowing. (FR-003, FR-008)
- [ ] T042 [US1] Implement `core/claude_api_relay.py`: loopback-only, session-auth-header, closed method/path/size/header protocol to exact `api.anthropic.com` with TLS validation, no redirects, no body persistence, no policy/cache endpoint, no direct fallback, and non-secret health receipt. (FR-003, FR-008)
- [ ] T043 [US1] Implement `core/windows_policy_watch.py` watchers for the HKLM policy key, managed files, policy helper, relay, and config root; any mutation terminates the employee process tree and invalidates readiness before another tool can run; `ConfigChange` remains supplemental only. (FR-009)
- [ ] T044 [US1] Update the `core/engine.py` launch contract: `--restricted`, `--setting-sources ""`, dedicated no-follow `CLAUDE_CONFIG_DIR`, explicit `--tools` inventory, bare denies for `Bash`/`Monitor`, `--strict-mcp-config`, verified plugin/skill bundle, non-default `ANTHROPIC_BASE_URL`, stdin-held prompt until gate completion, and refusal of native Desktop/folder sessions. (FR-001, FR-008, FR-009)
- [ ] T045 [US1] Enforce no-retry and no-host-fallback in `core/mxc.py` across request construction, trusted-policy load, ticket-helper launch, relay launch, broker/executor launch, and contained setup; every failure returns a terminal denial and never re-runs the original command on the host. (FR-006)
- [ ] T046 [US1] Layer deadlines in `core/mxc.py`/`core/windows_process.py` (evaluator inside hook timeout, MXC workload inside ticket-helper watchdog, Claude run outside both), terminate the full tree on expiry, and record zero-survivor evidence; cleanup failure is structural, never advisory. (FR-007)

**Checkpoint**: US1 independently testable — real-client fault injection blocks every failure class and creates no host marker.

---

## Phase 5 — User Story 3: Gateway Host Execution Is Narrow and Auditable (P0)

**Goal**: Exactly one canonical, currently authorized `staff-apify` or `staff-compute` invocation may run on the host; every other command is contained or denied.

**Independent test**: Run a corpus of canonical calls plus ≥50 bypass variants per host gateway (chaining, pipeline, redirect, substitution, environment prefix, alias/function, relative/absolute path, extension/PATHEXT, case/Unicode, quoted metacharacters, PATH shadowing, junction, disabled ability). Only canonical authorized calls reach the verified dispatcher.

### Tests

- [ ] T047 [US3] Build `tests/test_gateway_security.py`: canonical positives (literal metacharacters as argument data), the ≥50-variant bypass corpus per host gateway, final host set exactly `staff-apify`/`staff-compute`, other `staff-*` commands contained/denied, mid-flight ability disable wins, and parser/catalog/launcher/shared-module/dependency tamper denies. (FR-018, FR-020, FR-023, SC-003)
- [ ] T048 [P] [US3] Add the `-Suite Gateways` coverage to `tests/windows/mxc-real-host-proof.ps1` (created by T005): canonical dispatch to the intended childless target, bypass rejection, quoted literals, no descendant spawn, no credential exposure, and audit records for approved and rejected calls. (FR-020, SC-003)
- [ ] T049 [P] [US3] Add audit tests in `tests/test_gateway_security.py`: every approved and rejected gateway-like call writes employee, gateway identity, policy version, decision, and a non-secret reason; raw argv/bodies/tokens never appear; primary-sink failure falls back to Event Log or blocks readiness. (FR-025)

### Implementation

- [ ] T050 [US3] Implement `core/gateway-parse.ps1`: absolute verified Windows PowerShell, `-NoLogo -NoProfile -NonInteractive`, stdin-only data, `Parser::ParseInput` with no evaluation, one closed JSON result or non-zero exit, one statement/pipeline/`CommandAst`, no active construct, exact lowercase unquoted catalog command, bounded static arguments, and denial on uncertainty. (FR-020)
- [ ] T051 [US3] Implement `core/gateway.py`: explicit catalog identity, hook-time current-authorization checks, one-use gateway ticket issue/claim, verified dispatcher order, minimal environment, structured argv (`shell=False`), restricted-child/one-process Job, and terminal denial on any classification/dispatch fault. (FR-019, FR-021, FR-024)
- [ ] T052 [US3] Restrict `core/abilities.json` host eligibility to exactly `staff-apify` and `staff-compute` with explicit `host_eligible: true`, per-gateway control profiles, argument limits, and dependency locks; every other `staff-*` ability is contained. (FR-018, FR-019)
- [ ] T053 [US3] Rewrite `core/tools/apify.py` as a childless, hash-locked in-process HTTPS target using fresh owner-state authorization, existing budget/method/private-network/secret controls, and no subprocess or runtime install. (FR-021, FR-023)
- [ ] T054 [US3] Rewrite `core/tools/compute.py` to use in-process GitHub REST/Git-data/workflow/artifact HTTPS APIs instead of `gh`, `git`, PowerShell, cmd, or any descendant executable, preserving workspace file boundaries and no-workflow-secret behavior. (FR-021, FR-023)
- [ ] T055 [US3] Ensure `core/tools/fetch.py`, `browse.py`, `watch.py`, `video.py`, `connectors_cli.py`, and `docs.py` run only through contained MXC with setup-pinned absolute dependencies; incompatibility denies rather than promoting to host. (FR-022, FR-023)
- [ ] T056 [US3] Add the protected audit WAL plus Windows Event Log fallback in `core/gateway.py`: reserve a record before classification can approve, record audit unavailability, and block readiness/session start when neither sink is durable. (FR-025)
- [ ] T057 [US3] Implement the closed gateway failure table in `core/gateway.py`: parser/catalog/authorization/audit/launch/runtime-install/child-spawn faults are terminal denials with no normal host-shell fallback. (FR-024)

**Checkpoint**: US3 independently testable — the bypass corpus executes nothing outside the two verified dispatcher targets.

---

## Phase 6 — User Story 4: Setup and Release Prove the Exact Security Contract (P0)

**Goal**: Native MXC mode becomes usable only for the exact verified Claude/MXC/schema/architecture/Windows combination, with actionable blockers and non-waivable release evidence.

**Independent test**: Exercise supported and unsupported Claude/effective-settings, MXC package/executable/schema/architecture, and Windows build combinations; tamper with each artifact or contract value. Only a fully verified combination reaches `ready`/`ready-with-warnings`; every blocker names one recovery action within 30 seconds.

### Tests

- [ ] T058 [US4] Complete `tests/test_windows_contract.py` with `SchemaContract` and `ArtifactContract` groups: package/payload/schema/validator/PE/version/signature/publisher checks, wrong architecture, one-byte tamper, base and final-wire Draft 7 validation, request-aware argv exactness, and rejection of unknown/retired/experimental fields. (FR-026, FR-027, FR-028, FR-029, FR-031)
- [ ] T059 [P] [US4] Add the `-Suite Contract` coverage to `tests/windows/mxc-real-host-proof.ps1` (created by T005): exact artifact/request matrix, environment allowlist, restrictive UI request bits, and refusal of a no-request probe as readiness. (FR-028, FR-029, FR-030)
- [ ] T060 [US4] Add the `-Suite PolicyTampering` coverage to `tests/windows/mxc-real-host-proof.ps1` (created by T005), reusing the matrix from `tests/test_containment_readiness.py` against a real host and explicit owner denies. (FR-011, FR-030, SC-002)
- [ ] T061 [P] [US4] Implement `tests/windows/registry-dns-ui-proof.ps1` covering explicit owner-SID/hive read/write/load, authoritative DNS-query canaries, direct public/private/host-loopback sockets, and Session 0/private-desktop screen/raw-input/hook/foreground/UI capabilities, with dual-policy warning-versus-deny modes. (FR-030, FR-031, SC-002)
- [ ] T062 [P] [US4] Implement `tests/windows/broker-process-proof.ps1` proving restricted service SID, no network, exact privileges, batch-token Session 0 without `SetTokenInformation`, no-profile/private-desktop/suspended pre-Job launch, no fallback primitive, and delayed-marker absence. (FR-007, FR-030)
- [ ] T063 [P] [US4] Add `tests/test_windows_broker_contract.py`: closed IPC frame schema, pipe DACL/client verification, exact service account/privilege/session configuration, one-use ticket-only launch, malformed/frame-oversize/replay rejection, and proof that no owner-token, interactive-logon, or `SeTcbPrivilege` fallback path exists. (FR-007, FR-011, FR-031)
- [ ] T064 [P] [US4] Add `tests/test_upgrade_security.py` for contract epoch, legacy `_key()` comparator equality against `0.8.0-sec.N`, pre-mutation blocked marker, legacy authorization ignored, scheduler/run blocking, and team-data preservation. (FR-036, SC-007)
- [ ] T065 [P] [US4] Implement `tests/windows/SetupWindows.Tests.ps1` covering installer staging, manifest verification, tamper/rollback, architecture/publisher rejection, HKLM policy-helper/relay/worker/ACL/Event Log/trust-root installation, and readiness invalidation. (FR-028, FR-031, FR-032)
- [ ] T066 [US4] Add the structured blocker benchmark in `tests/test_windows_contract.py`: unsupported or tampered dependency cases emit a blocker with one exact recovery action within 30 seconds, measured end to end, with the FR-010 redaction allowlist asserted and no secret/policy/path leakage. (FR-010, FR-032, SC-006)

### Implementation

- [ ] T067 [US4] Add `native/orbit-containment-broker/` (signed x64/ARM64 `OrbitContainmentBroker` service) plus `core/windows_shell_identity.py`: restricted service SID, exact three privileges/no network, closed `\\.\pipe\OrbitContainmentBrokerV1` protocol, LSA-held `OrbitMxcWorker` credential, batch logon with already-Session-0 token, private desktop/window station, suspended `CreateProcessAsUser` assigned to the Job before resume, and no owner-token/`CreateProcessWithLogonW`/`SeTcbPrivilege` fallback. (FR-007, FR-011, FR-031)
- [ ] T068 [US4] Implement `core/containment_readiness.py` machine/policy proof layers: strict records for `blocked|proving|ready|ready-with-warnings`, readiness key binding contract/candidate/Claude/MXC/schema/build/host-prep/employee policy/explicit denies, invalidation on every bound change, and no reuse of another session's proof. (FR-030, FR-032, SC-005)
- [ ] T069 [US4] Build exact MXC requests in `core/mxc.py`: fixed `1.0.0` ProcessContainer subset, closed builder, base plus final proxy-bearing wire validation against vendored schema bytes immediately before use, and removal of unnecessary `internetClient` while applying the restrictive clipboard/injection/handle/atom/desktop/system-setting/IME policy. (FR-029)
- [ ] T070 [US4] Implement request-aware `wxc-exec.exe <request> --probe` plus positive/negative real-host proofs in `core/mxc.py`: require exit zero, valid JSON, absent `error`, `tier == base-container`, `needsDaclAugmentation == false`; run functional file operations, filesystem/registry/DNS/network/UI leak canaries, and structural timeout/process-tree cleanup with zero survivors. (FR-030, FR-007)
- [ ] T071 [US4] Implement deterministic `ExplicitDeny`/`LeakResult` join in `core/containment_readiness.py`: completed non-denied leaks produce bound warnings and `ready-with-warnings` with work continuing; a matching owner deny blocks the employee's complete native shell surface while control-plane work stays available; failed/inconclusive measurement and survivors block. (FR-030, SC-002)
- [ ] T072 [US4] Finish `setup-windows.ps1`: transactional manifest-driven MXC install (tarball, selected-architecture payload, vendored schema, host-prep companion), pinned contained-tool dependencies with no runtime install, worker identity/logon/ACL, Event Log source, machine trust root, readiness invalidation on repair, and exact build/architecture/capability admission. (FR-028, FR-030, FR-031, FR-036)
- [ ] T073 [US4] Unify the setup/doctor structured report in the repo-root `orbit` CLI and `core/containment_readiness.py`: effective Claude version plus hook proof, policy-helper/relay receipts, MXC/schema/artifact/build/probe/functional/leak/cleanup status, employee policy and readiness key, `ready|ready-with-warnings|blocked`, one recovery action per blocker, and exact continuation text per warning — no commands, secrets, credentials, unrestricted paths, or policy bodies. (FR-010, FR-032)
- [ ] T074 [US4] Keep `core/staffd.py` control plane available while suspending employee scheduling and native folder sessions whenever readiness is not `ready`/`ready-with-warnings`. (FR-036)
- [ ] T075 [US4] Add `bootstrap/OrbitSecurityBootstrap` (full-trust Store MSIX source/manifest with embedded trust-root digest and offline key) and rework `core/update.py` so the first secure release is refused by the legacy in-app updater, quiesces service/processes, writes the machine blocked marker before source mutation, activates atomically, and later updates require the external launcher plus evidence invalidation. (FR-036)

**Checkpoint**: US4 independently testable — tampering any reviewed value blocks native work with one exact recovery action; a verified combination reaches `ready` or `ready-with-warnings`.

---

## Phase 7 — Polish & Cross-Cutting: Non-Windows Regression, Evidence, Release Gate

**Purpose**: Prove released behavior, preserve other platforms, and make evidence non-waivable.

- [ ] T076 [P] Extend `tests/test_platforms.py` and run the full macOS/Linux/WSL2 suites unchanged: no native readiness/hook/dispatcher appears, `failIfUnavailable`/sandbox/gateway/service/team behavior is byte-equivalent, and WSL2 never inherits native exceptions. (FR-035, SC-007)
- [ ] T077 [P] Update `PRODUCT.md`, `README.md`, `SETUP.md`, and feature-001 notes to state the release-gating rule, supersede optional real-host claims, and point stale guidance to feature 003. (FR-033, FR-034)
- [ ] T078 [P] Update `.github/workflows/tests.yml` to keep hosted unit/fake coverage only, run guard tests, remove any optional-real-host claim, and validate the evidence schema without owning publication credentials. (FR-033)
- [ ] T079 [P] Add `.github/workflows/windows-native-security-build.yml`: pinned MSVC/Windows SDK, reproducible x64/ARM64 policy-helper/broker/Store-bootstrap builds, Authenticode/package signing, manifest hash emission, and signing gate. (FR-028)
- [ ] T080 Implement `tests/windows/upgrade-proof.ps1` with `Clean`/`Upgrade` scenarios, candidate binding, legacy inventory/digests, blocked-marker ordering, owner policy review, and team-data comparison. (FR-036, SC-004, SC-007)
- [ ] T081 Run and archive the x64 clean plus x64 upgrade bundles via `tests/windows/upgrade-proof.ps1` and `tests/windows/mxc-real-host-proof.ps1 -Suite All`, including explicit-deny blocking, advisory continuation, and zero-survivor cleanup. (SC-004)
- [ ] T082 Run and archive the native ARM64 clean plus ARM64 upgrade bundles via `tests/windows/upgrade-proof.ps1` and `tests/windows/mxc-real-host-proof.ps1`; if hardware evidence is unavailable, remove ARM64 from the release and reject ARM64 setup rather than emulating. (SC-004, FR-033)
- [ ] T083 Implement `tests/validate_windows_release_evidence.py`: closed evidence schema, candidate/architecture/scenario/counter/provenance checks, Store/prior-release-pinned TPM RSA-PSS runner signatures, offline Ed25519 aggregate signature, RFC 8785 canonical bytes/domain strings/base64url, revocation/validity, and exact publication-workflow identity. (FR-033, FR-034, SC-005)
- [ ] T084 Add `.github/workflows/windows-containment-release.yml` as the only publication-credential owner in protected environment `windows-containment-release`, pinned by workflow digest in the trust root, gated on the validator emitting the current candidate digest. (FR-034)
- [ ] T085 Run the owner-message study defined in `quickstart.md` §12: ≥9/10 non-technical owners identify that work did not run, the failing prerequisite, and the recovery action for blocked messages, and separately that a leak was observed, work continues without a matching owner deny, and mitigation is optional. (FR-010, SC-009)
- [ ] T086 Commission the independent adversarial security review recorded in `GATES.md` across workspace, managed policy, registry/DNS/UI, gateway descendants, upgrade bootstrap, and evidence trust root; any arbitrary-host-execution path blocks release. (SC-008)

**Final gate**: run `python -m compileall -q core tests`, all unit/installer suites, the hook/policy/gateway/schema matrices, the 30-second blocker benchmark, real-host x64/ARM64 bundles, and `tests/validate_windows_release_evidence.py`; archive candidate-bound evidence outside employee workspaces and require `WINDOWS CONTAINMENT RELEASE EVIDENCE PASSED` before publication. (SC-001, SC-003, SC-004, SC-005, SC-006, SC-007)

---

## Dependencies & Execution Order

### Phase dependencies

```text
Phase 1 (T001–T005)
    -> Phase 2 (T006–T017)
        -> Phase 3 US2 (T018–T030)
            -> Phase 4 US1 (T031–T046)
                -> Phase 5 US3 (T047–T057)
                    -> Phase 6 US4 (T058–T075)
                        -> Phase 7 (T076–T086)
```

Phase order matches `plan.md`'s delivery sequence: the strict-policy surfaces (US2) must land before the hook boundary (US1) can ship, and gateway, readiness, and release evidence follow. Task IDs reflect this order; where a test appears before its implementation, it is authored first and treated as complete only after that implementation lands.

- **Phase 1 → Phase 2**: T006 and T013 depend on the manifest (T001) and trust root (T002); T016 depends on T006 (same file) and T003. T005 is standalone but must exist before T048 and T059/T060.
- **Phase 2 internal**: T009 depends on T008; T010 depends on T009; T011 depends on T009; T015/T017 depend on T009–T011; T012 is independent of policy work.
- **US2**: T018–T021 depend on Phase 2. T020 follows T018 (same file). T022–T030 depend on T008/T009; T029 depends on T010. T022, T028, and T029 share `core/mxc.py` and serialize.
- **US1**: T031–T046 depend on Phase 2 and US2 (T022–T030). T036 depends on T032. T039 depends on T037/T038. T041 depends on T040. T044 depends on T040–T043. T045 depends on T044. T046 depends on T012.
- **US3**: T047–T057 depend on T008/T009/T010/T012. T048 depends on T005 (harness); T049 follows T047 (same file). T051 depends on T050; T048 is authored against the parser/dispatcher contract and must pass after T051.
- **US4**: T058–T075 depend on US1 (hook proof) and US2 (policy proof). T059/T060 depend on T005 and serialize on `tests/windows/mxc-real-host-proof.ps1`. T066 follows T058 (same file) and asserts the report contract implemented by T073; it may be authored first but must pass after T073. T070 depends on T069 (same file). T071 depends on T068/T070. T073 depends on T068/T070 and shares `core/containment_readiness.py` with T068/T071, so T068 → T071 → T073 serialize. T075 depends on T072/T073.
- **Phase 7**: T080–T084 depend on US1–US4; T085 depends on T073; the final gate depends on everything, including T066.

Tests are listed before implementation inside each story on purpose: they may be authored first, but no test is complete until the implementation tasks it names have landed and it passes.

### Parallel opportunities

- **Phase 1**: T001, T002, T003, T005 in parallel (distinct files); T004 independent.
- **Phase 2**: T006, T007, T008, T012, T013, T014 in parallel; T016 follows T006; T009–T011 form a serial chain in `core/mxc.py`; T015/T017 follow that chain.
- **US2 tests**: T019 and T021 in parallel; T020 follows T018 (same file). Implementations T023–T027 touch distinct files and can parallelize; T022/T028/T029 serialize on `core/mxc.py`.
- **US1 tests**: T032 and T033 in parallel (distinct harness files); T031/T034/T035 share `tests/test_mxc.py` and must serialize; T036 follows T032.
- **US3 tests**: T048 and T049 in parallel (different files, after T047); T053/T054 distinct files and can parallelize; T050 → T051 serial.
- **US4 tests**: T061, T062, T063, T064, T065 in parallel after T058; T059/T060 serialize on the shared real-host harness; T066 follows T058 and T073. Implementations T067, T069/T070, T072, T074, T075 are mostly parallel once readiness contracts are fixed; T068 → T071 → T073 serialize on `core/containment_readiness.py`.
- **Phase 7**: T076–T079 in parallel; T081/T082 can run concurrently on separate hosts once T080 exists.

## Parallel Execution Examples

### US1 real-client proof

```text
Task: "Implement tests/windows/hook-failure-matrix.ps1 (T032)"
Task: "Implement tests/windows/managed-policy-proof.ps1 (T033)"
```

Then, after T032 exists:

```text
Task: "Add multiple-matching-hook / managed-tier tests (T035)"
Task: "Add the newer-client behavioral-drift case (T036)"
```

### US2 strict-state surfaces

```text
Task: "Move connector/MCP grants into core/connectors.py (T024)"
Task: "Move ability/gateway authorization into core/abilities.py (T025)"
Task: "Build instruction-only skill bundles in core/skillbook.py (T026)"
Task: "Harden core/guard/staff-guard/hooks/register.js (T027)"
```

### US3 dispatcher targets

```text
Task: "Rewrite core/tools/apify.py as childless in-process HTTPS (T053)"
Task: "Rewrite core/tools/compute.py to in-process GitHub APIs (T054)"
```

### US4 contract/evidence harnesses

```text
Task: "Add -Suite Contract coverage (T059)"
Task: "Implement tests/windows/registry-dns-ui-proof.ps1 (T061)"
Task: "Implement tests/windows/broker-process-proof.ps1 (T062)"
Task: "Add tests/test_windows_broker_contract.py (T063)"
Task: "Add tests/test_upgrade_security.py (T064)"
Task: "Implement tests/windows/SetupWindows.Tests.ps1 (T065)"
```

## Implementation Strategy

### MVP scope (P0 baseline)

Setup (T001–T005) + Foundational (T006–T017) + **US2 (T018–T030)** + **US1 (T031–T046)**. US2 leads because no workspace value may authorize host execution before the hook boundary ships; together they close the original defect. US3–US4 remain required for release but can follow incrementally.

### Incremental delivery

1. **Baseline + trusted state**: T001–T017. No behavior change to employee launches yet; strict parse/ticket/policy tests must pass.
2. **US2 anti-widening surfaces**: T018–T030. Tamper matrix must show zero authority from workspace/profile/settings/skills/connectors.
3. **US1 hook boundary**: T031–T046. Real-client fault injection gates the increment; fake-executor success is not acceptable evidence.
4. **US3 gateway narrowing**: T047–T057. Bypass corpus must show zero non-canonical host execution.
5. **US4 exact contract + readiness**: T058–T075. Unsupported/tampered combinations stay blocked with one recovery action in ≤30 seconds.
6. **Polish + release evidence**: T076–T086. Publication is blocked until x64/ARM64 clean+upgrade bundles validate and the independent review passes.

### Team parallelization

- One owner for `core/mxc.py` (trusted read, tickets, hook, request/probe) — it is the highest-conflict file.
- One owner for native components (`native/orbit-policy-helper/`, `native/orbit-containment-broker/`, `bootstrap/`).
- One owner for `core/gateway.py` + `core/gateway-parse.ps1` + `core/tools/*`.
- One owner for policy/owner state (`core/grants.py`, `core/engine.py`, `connectors`, `abilities`, `skillbook`, `guard`).
- One owner for harnesses/evidence (`tests/windows/`, `tests/validate_windows_release_evidence.py`, workflows).

## Task Format Validation

Every task above uses `- [ ] TNNN [P?] [US?] Description with file path`. Setup, Foundational, and Polish tasks carry no story label; US1–US4 tasks are labeled. File paths name planned components from `plan.md` or concrete contract/data-model artifacts, so no task requires inventing a new surface at execution time.
