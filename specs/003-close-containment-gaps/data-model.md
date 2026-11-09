# Data Model: Fail-Closed Native Windows Containment

**Feature**: `003-close-containment-gaps`
**Status**: Phase 1 design

## Trust classes

| Class | Examples | May authorize host execution? |
| --- | --- | --- |
| Release-owned | Security manifest, base policy, gateway catalog, handler/parser/dispatcher modules | Yes, only after release-integrity verification |
| Owner/admin-controlled | `staff.json` security subtree, HKLM policy helper, LSA/DPAPI worker credential, mode/grants, readiness store | Yes, only through strict schemas, OS protection, and stable reads |
| Derived protected runtime | One-use tickets, receipts, proof results, trusted audit | Yes, only while all bindings remain current |
| Employee-controlled | Complete employee workspace, profile, `.claude`, skills, logs, model output, shell text | Never |
| External observed | Claude binary/settings behavior, MXC binaries/schema/signatures, Windows build/capabilities | Never by assertion alone; accepted only through exact verification/proof |

Employee-controlled data may describe work or gateway arguments. It cannot select a handler, policy source, launcher, runtime, proof, or authorization identity.

## 1. NativeWindowsSecurityContract

Release-owned, closed JSON document shared by Python, PowerShell, tests, doctor, and evidence validation.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact internal manifest schema, for example `orbit.native-windows-containment.v1` |
| `contract_epoch` | positive integer | Incremented for any security-contract change; old readiness never matches |
| `orbit_version` | string | Must equal `VERSION` for a release candidate |
| `claude.minimum_version` | string | Exact `2.1.295` capability floor |
| `claude.required_launch_flags` | string array | Includes restricted mode, explicit settings/tool/MCP controls |
| `claude.shell_tools` | object | `PowerShell` allowed; `Bash` denied; `Monitor` unavailable |
| `claude.managed_bootstrap` | object | Exact HKLM document, policy-helper/relay paths and hashes, first-wins policy, remote-fetch skip contract |
| `windows.shell_identity` | object | Dedicated non-admin account name/SID, logon policy, ACL template, credential-store identifier |
| `mxc.release` | string | Exact `1.0.1` |
| `mxc.tag` / `mxc.commit` | strings | Exact reviewed tag and commit |
| `mxc.package` | object | Pinned URL, package SHA-256, optional npm integrity |
| `mxc.schema` | object | Version `1.0.0`, pinned source URL/path, exact SHA-256 |
| `mxc.architectures` | object | Exact `x64` and `arm64` PE machine values and payload records |
| `mxc.companions` | object | Required or feature-conditional executable records |
| `mxc.signer` | object | Valid Windows trust plus Microsoft Corporation organization/publisher |
| `mxc.probe_predicates` | object | Required tier, no error/DACL augmentation, capabilities, warning allowlist |
| `windows.minimum_builds` | object | Exact branch -> build/UBR floor map |
| `windows.contained_tool_dependencies` | object | Exact absolute paths/digests/publishers for preinstalled browser/media/OCR/tool binaries used inside MXC; runtime install forbidden |
| `python.schema_validator` | object | `jsonschema` `4.25.1` and complete hash-locked dependency set |
| `orbit_files` | object | Relative path, SHA-256, role for handler/parser/dispatcher/catalog/shared gateway code |
| `release_evidence_trust` | object | Externally pinned trust-document digest and required runner/release key roles |

### Validation

- Unknown, duplicate, missing, null, wrong-type, or noncanonical fields invalidate the whole contract.
- URLs cannot float to `latest`, a branch, or an unpinned package range.
- An architecture record cannot inherit another architecture's hash.
- Runtime code never uses a fallback contract when this document is unreadable.

## 1A. ClaudeManagedBootstrap

Externally inspectable source that places Orbit's critical hook in the effective managed tier.

| Field | Type | Rules |
| --- | --- | --- |
| `hklm_document_digest` | SHA-256 | Exact `HKLM\SOFTWARE\Policies\ClaudeCode\Settings` JSON installed with elevation |
| `policy_helper_path` / `policy_helper_digest` | identity | Absolute signed native `.exe`; Windows policy helper receives no arguments |
| `session_id_env` / `token_env` | fixed names/value contract | `ORBIT_POLICY_SESSION_ID` plus 256-bit base64url `ORBIT_POLICY_TOKEN`; stripped from all descendants |
| `pipe_identity` | fixed IPC contract | `\\.\pipe\OrbitPolicyV1`, owner/helper-only DACL, verified client PID/image/hash, exact framed schema |
| `launch_nonce_id` | opaque ID | One-use, short expiry, bound to expected Claude/helper process tree; never model input |
| `emitted_policy_digest` | SHA-256 | Managed-only hooks/permissions/plugins/MCP/env locks emitted for this session |
| `config_root_identity` / `remote_cache_state` | identity/result | Dedicated no-follow Orbit config root is cache-free; unexplained cache/file creation blocks |
| `relay_endpoint` / `relay_digest` | identity | Fixed loopback non-default API endpoint and verified no-fallback relay |
| `remote_fetch_skipped` | proof | Real client diagnostics prove server-managed fetch skipped because endpoint is non-default |
| `source_mode` | enum | Exact `first-wins`; merge is forbidden |
| `watchers` | records | HKLM key, managed-file locations, helper, relay; all armed before prompt |
| `receipt` | record | Nonce, process/session, source/emitted/relay digests, timestamp, verdict |

Any receipt/source/relay/watcher mismatch is `blocked`. For unrelated sessions with no Orbit environment, helper emits `{}` with no `managedSettings` key, so it neither adds Orbit hooks nor suppresses lower owner/admin policy. Presence of Orbit variables with invalid IPC/token fails nonzero.

## 1B. DedicatedShellIdentity

| Field | Type | Rules |
| --- | --- | --- |
| `broker_service` | identity | Exact signed `OrbitContainmentBroker` service binary/config, LocalSystem restricted service SID, no network |
| `broker_privileges` | exact set | Exactly `SeAssignPrimaryTokenPrivilege`, `SeIncreaseQuotaPrivilege`, `SeChangeNotifyPrivilege`; `SeTcbPrivilege` and undeclared privileges absent |
| `broker_pipe` | IPC contract | `\\.\pipe\OrbitContainmentBrokerV1`, owner/helper + service SID DACL, closed frames, client PID/image/session token, ticket ID only |
| `account_name` / `sid` | identity | Exact local non-admin `OrbitMxcWorker` |
| `logon_policy` | object | Batch logon granted; local/remote interactive and network logon explicitly denied |
| `credential_ref` | opaque Windows reference | LSA private data readable only by broker service SID/System; secret bytes never in Orbit JSON/evidence |
| `profile_mode` | enum | Exact `no-persistent-profile`; no worker HKCU hive is loaded |
| `ephemeral_profile_root` | path binding | Fresh per-command `USERPROFILE`/`LOCALAPPDATA`/temp tree, ACL-scoped and destroyed |
| `session_id` / `window_station` / `desktop` | binding | Session 0 plus private per-command noninteractive window station/desktop, never owner's interactive objects |
| `acl_digest` | SHA-256 | Exact runtime/workspace/team/temp grants and owner-state denials |
| `token_proof` | record | Batch `LogonUser`, exact SID/integrity/non-elevation/session, suspended `CreateProcessAsUser`, pre-resume Job assignment, no fallback |
| `registry_canary_result` | `LeakResult` records | Explicit owner-SID/hive read/write/load outcomes; completed access becomes advisory or deny breach, while canary execution failure is structural |
| `interactive_canary_result` | `LeakResult` records | Screen/raw-input/hooks/foreground/stable-UI outcomes with same warning-versus-deny join |

The owner helper launches only verified executor under this token. Broker/service/token/session/profile/ACL or canary-execution mismatch blocks structurally. A successfully completed registry/UI canary that observes access is handled only through `LeakResult`; it is not an identity mismatch.

## 2. OwnerSecurityState

Strict subtree of owner-controlled `staff.json`. Ordinary employee metadata remains outside this entity.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact `orbit.owner-security.v1` |
| `revision` | positive integer | Incremented atomically on every security-affecting owner write |
| `platform.sandbox_mode` | enum | `mxc` or `wsl2`; only owner/recorded unavailable flow writes it |
| `network_domains` | string array | Global owner-approved exact/wildcard domains; normalized and bounded |
| `employees` | map | Key is canonical employee ID; values are `EmployeeSecurityGrant` |
| `migration` | object | Contract epoch, review status, non-secret blockers; no legacy grant bytes become authority |

### EmployeeSecurityGrant

| Field | Type | Rules |
| --- | --- | --- |
| `employee_id` | string | Must equal map key and trusted employee registry identity |
| `status` | enum | Only active employees can receive execution or gateway tickets |
| `workspace` | canonical path | Owner registry/fixed layout only; must not be a link/reparse path or overlap another employee/security state |
| `abilities` | unique string array | IDs must exist in verified release catalog |
| `connectors` | closed map | Owner-granted reviewed remote MCP IDs/URLs/capabilities; no arbitrary local command server |
| `network_domains` | string array | Per-employee owner grants; profile values ignored |
| `explicit_denies` | closed records | Owner-selected resource/channel categories and canonical targets; only these turn a measured MXC leak into blocking state |
| `additional_directories` | canonical path array | Optional; owner-confirmed, non-security-state paths only |
| `additional_tools` | string array | Optional vetted non-shell tools; never arbitrary/new shell tools |
| `timeout_ms` | integer | Optional narrowing within release maximum; no zero/unbounded value |

### Forbidden sources

`profile.json`, `.claude/**`, `state/mxc-policy.json`, workspace logs, skill/agent frontmatter, environment-provided identity, and payload `cwd` never populate this entity.

### ExplicitDeny

Closed owner-authored record used only after structural readiness passes:

| Field | Type | Rules |
| --- | --- | --- |
| `deny_id` | string | Stable unique owner-state identifier |
| `employee_id` | string | Exact policy subject |
| `boundary_id` | enum | One advisory-eligible canary boundary listed below |
| `target_kind` | enum | `path`, `registry-path`, `domain`, `cidr`, `endpoint`, `ui-capability`, or `any` |
| `match_mode` | enum | `exact`, `subtree`, `wildcard-subdomain`, `cidr-contains`, or `all`; allowed combinations are fixed by target kind |
| `canonical_target` | string/null | Required except `all`; canonicalized when owner writes policy |
| `policy_revision` | integer | Revision that created/changed deny |

Advisory-eligible `boundary_id` values are exactly: `filesystem.read`, `filesystem.write`, `registry.read`, `registry.write`, `dns.query`, `network.egress`, `network.host-loopback`, `ui.clipboard`, `ui.input-injection`, `ui.external-handles`, `ui.global-atoms`, `ui.desktop-control`, `ui.system-settings`, `ui.ime`, `ui.screen-capture`, `ui.raw-input`, `ui.low-level-hooks`, and `ui.foreground-control`. Cleanup/process survival, hook/host execution, policy provenance, artifacts, audit, parsing, launch, and measurement status cannot appear in `ExplicitDeny` because they are always structural blockers.

Canonicalization is deterministic: filesystem paths use final volume/path identity plus Windows case folding and segment boundaries; registry paths use explicit hive/SID plus case-folded segments; domains use lowercase IDNA with trailing dot removed; wildcard mode accepts only `*.example` and excludes apex; CIDRs use canonical network/prefix; endpoints use protocol + canonical address + port; UI capabilities use exact enum and `all` has null target. Regex and free-form glob are forbidden.

Permitted `(target_kind, match_mode)` pairs are exactly: `path -> exact|subtree`; `registry-path -> exact|subtree`; `domain -> exact|wildcard-subdomain`; `cidr -> cidr-contains`; `endpoint -> exact`; `ui-capability -> exact`; `any -> all`. No other pair parses.

### LeakResult

| Field | Type | Rules |
| --- | --- | --- |
| `canary_id` | enum/string | Release-manifest canary identity, unique per boundary/target |
| `employee_id` | string | Exact employee-bound policy subject; never inferred from environment |
| `boundary_id` / `target_kind` / `canonical_target` | values | Same canonical vocabulary as `ExplicitDeny` |
| `observed` | boolean | True only when completed canary proves data/access leak |
| `measurement_status` | enum | `complete`; failed/missing/inconclusive is a `StructuralResult`, never a leak |
| `evidence_digest` | SHA-256 | Candidate/host/request/canary-bound evidence |
| `matching_deny_ids` | sorted string array | Independently recomputable exact intersection result |
| `disposition` | enum | `enforced`, `advisory-leak`, or `explicit-deny-breach` |

Intersection first requires equal `employee_id` and `boundary_id`. `any/all` matches every target in that boundary. Otherwise target kinds must be equal. `exact` requires canonical equality; `subtree` requires equal path or descendant on a segment boundary; `wildcard-subdomain` requires strict subdomain and not apex; `cidr-contains` requires observed address inside canonical network. Invalid pair or cross-kind comparison blocks policy parsing. `observed=false` yields `enforced`; `observed=true` plus zero matches yields `advisory-leak`; one or more matches yields `explicit-deny-breach`.

### StructuralResult

Closed result for boundaries that never become advisory: hook/client/managed source, original-command host execution, policy provenance, gateway/dispatcher/audit, artifact/schema/request validation, broker/token/launch, process cleanup/survivors, and measurement completion. Any non-pass `StructuralResult` takes precedence over all `LeakResult` values and makes readiness `blocked`.

## 3. PolicySourceFingerprint

Canonical digest that binds one command to current trusted authorization.

| Field | Type | Meaning |
| --- | --- | --- |
| `contract_epoch` | integer | Release security contract |
| `orbit_release_digest` | SHA-256 | Candidate/source manifest identity |
| `registry_revision` | integer | Owner security revision read from stable bytes |
| `registry_file_identity` | platform identity | Canonical path and stable file identity observed through no-follow read |
| `employee_id` | string | Intended subject |
| `employee_grant_digest` | SHA-256 | Canonical `EmployeeSecurityGrant` |
| `base_policy_digest` | SHA-256 | Release base rules |
| `ability_catalog_digest` | SHA-256 | Release catalog used for tools/gateways |
| `gateway_catalog_digest` | SHA-256 | Native host-exception catalog |
| `connector_catalog_digest` / `connector_grant_digest` | SHA-256 | Exact reviewed MCP definitions and current owner grants |
| `fingerprint` | SHA-256 | Canonical digest of every field above |

The hook recomputes/compares this fingerprint before emitting. The helper or gateway dispatcher compares it again when claiming a ticket. A mismatch never preserves earlier access.

## 4. EffectiveCommandPolicy

Immutable in-memory policy derived once from one stable owner-state read.

| Field | Type | Rules |
| --- | --- | --- |
| `employee_id` / `session_id` | strings | Exact subject and live real-client session |
| `workspace` | canonical path | From trusted grant only |
| `deny_read` | path array | Verified base secrets, other workspaces, security/runtime/config state |
| `allow_write` | path array | Employee workspace, approved team subtree, protected per-command temp only |
| `domains` | domain array | Verified base + current owner grants; normalized and deduplicated |
| `network_mode` | enum | `allowlist` or owner-enabled `public`; both deny private/link-local/loopback destinations and require proxy |
| `explicit_denies` | `ExplicitDeny` records | Current owner-denied advisory-eligible filesystem, registry, DNS/network, or UI targets only; cleanup/structural boundaries forbidden |
| `leak_disposition` | enum | `warn-unless-owner-denied`; fixed by feature contract, not employee input |
| `timeout_ms` | positive integer | At or below release maximum |
| `enabled_gateways` | gateway IDs | Intersection of owner ability choices and verified native catalog |
| `tool_inventory` | tool names | Explicit release-approved built-ins and connector tools; `Monitor` absent |
| `mcp_servers` | closed records | Exact owner-granted remote reviewed servers; status/tool digest participates in readiness |
| `source` | `PolicySourceFingerprint` | Required binding |

### Invariants

- Denied paths and writable paths are disjoint after canonical/reparse resolution.
- Security state, trusted settings, ticket store, runtime/schema, handler, and gateway code are never writable.
- Default network posture is deny.
- Environment exported into MXC is an allowlist and excludes Claude/API/gateway credentials and readiness nonces.

## 5. CommandDisposition

Closed internal result from one matched shell event.

| Variant | Required fields | Hook result |
| --- | --- | --- |
| `contained` | ticket ID, policy fingerprint, non-secret reason code | Explicit allow + rewritten trusted MXC helper command |
| `gateway` | ticket ID, gateway ID, policy fingerprint, non-secret reason code | Explicit allow + rewritten trusted dispatcher command |
| `denied` | boundary code, owner-safe reason, one recovery action | Explicit deny, no updated command |

Exactly one variant exists. There is no `none`, `pass-through`, `unknown`, implicit default, or successful empty response.

## 6. ExecutionTicket

Protected, short-lived, single-use handoff. Two payload variants share one envelope.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact `orbit.execution-ticket.v1` |
| `ticket_id` | random identifier | At least 128 bits; safe alphabet for fixed rewritten command |
| `kind` | enum | `contained` or `gateway` |
| `employee_id` / `session_id` / `tool_use_id` | strings | All required and matched at claim |
| `policy_fingerprint` | SHA-256 | Must equal current trusted state at claim |
| `readiness_key` | SHA-256 | Must equal current ready result |
| `contract_epoch` / `orbit_release_digest` | values | Must match running verified release |
| `created_at` / `expires_at` | timestamps | Short bounded lifetime; future/expired invalid |
| `state` | enum | `issued`, `claimed`, `completed`, `failed`, `expired` |
| `payload_digest` | SHA-256 | Canonical payload digest |
| `payload` | variant | Contained request inputs or gateway identity + structured argv |

### Contained payload

- Original command bytes and exact tool name.
- Canonical cwd from trusted policy, not hook payload.
- Effective policy needed to build final request.
- No employee-selected executor/helper path.

### Gateway payload

- Exact catalog gateway ID.
- Static argument vector emitted by the PowerShell AST parser.
- Catalog/launcher/shared-module digests.
- No credential value.

### Lifecycle

```text
issued --atomic no-follow claim--> claimed --launch--> completed
   |                                  |  \--failure--> failed
   +--expiry/mismatch/replay--------> expired/denied
```

Only `issued -> claimed` can authorize launch. Claim uses atomic rename/open semantics and rejects links, replacement, extra keys, duplicate use, and mismatched binding. Support copies are separate hashes and cannot be claimed.

## 7. GatewayCatalogEntry

Release-owned explicit host-exception identity.

| Field | Type | Rules |
| --- | --- | --- |
| `gateway_id` | string | Exact lowercase canonical command |
| `ability_id` | string | Current owner grant required |
| `host_eligible` | boolean | Must be explicitly true; absence means contained |
| `entrypoint` | release-relative path | Python module/script, never `.cmd`/`.bat` |
| `entrypoint_digest` | SHA-256 | Verified at readiness and dispatch |
| `shared_file_digests` | map | Security-relevant imports covered by release manifest |
| `dependency_lock_digest` | SHA-256 | Dedicated Python environment and every third-party distribution are hash-locked |
| `process_policy` | exact object | Restricted-child process attribute, one-process kill-on-close Job, no runtime install |
| `policy_version` | string | Gateway-specific restrictions contract |
| `argument_limits` | object | Count/size plus optional gateway validator |
| `control_profile` | object | URL/method/budget/private-network/secret/consent requirements |

The final v1 native host catalog contains exactly `staff-apify` and `staff-compute`. Both run in the dedicated hash-locked Python environment and are forbidden from spawning descendant executables. `staff-compute` uses in-process GitHub HTTPS APIs rather than `gh`, `git`, or a host shell. Every other `staff-*` command is contained or denied.

## 8. ParsedGatewayInvocation

Output of the no-evaluation PowerShell AST helper.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact internal parser result version |
| `candidate` | boolean | Whether first syntactic command is gateway-like |
| `gateway_id` | string/null | Exact lowercase unquoted catalog identity |
| `argv` | string array | Static literals only; canonical decoded values |
| `reason_code` | enum | `canonical`, or one closed rejection reason |
| `input_digest` | SHA-256 | Raw proposed command hash; raw text is not logged |

Acceptance requires no parse errors, one statement/pipeline/command, no active construct, exact command identity, and bounded static arguments. Parser failure/timeout is denial for a gateway-like candidate, never ordinary host execution.

## 9. GatewayAuditRecord

Authoritative owner-side append record.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact `orbit.gateway-audit.v1` |
| `timestamp` | UTC timestamp | Owner clock plus monotonic ordering where available |
| `request_id` | string | Correlates classifier, ticket, dispatcher |
| `employee_id` | string | Trusted identity |
| `gateway_id` | string | Exact ID or `unknown` for rejected candidate |
| `policy_fingerprint` / `catalog_digest` | SHA-256 | Decision context |
| `decision` | enum | `approved`, `rejected`, `dispatch-failed`, `completed` |
| `reason_code` | enum | Closed non-secret vocabulary |
| `argument_digest` | SHA-256 | Never raw args, query strings, JSON bodies, or tokens |
| `exit_class` | optional enum | Coarse completion result; no secret output |

Before classification can approve, Orbit reserves a primary append-WAL record. If the primary store fails, a separately installed Windows Event Log source records `audit-unavailable` and readiness becomes blocked. Continuous watchers cover both; no session starts unless both pass. If both fail after the last check, action denies/session stops and later blocker marks interval audit-incomplete because that event cannot be guaranteed durable. Workspace mirrors are optional and non-authoritative.

## 10. ArtifactVerificationResult

Observed identity, never self-asserted marker data.

| Field | Type | Rules |
| --- | --- | --- |
| `path` / `final_path` | paths | Must remain inside active versioned install and contain no reparse component |
| `role` | enum | package, executor, host-prep, schema, conditional companion, Orbit handler/dispatcher/catalog |
| `expected_sha256` / `observed_sha256` | hashes | Exact match |
| `architecture` / `pe_machine` | values | Exact OS architecture match for native payloads |
| `signature_status` | enum | `valid` required for Microsoft binaries |
| `publisher` / `file_version` / `product_version` | strings | Microsoft and `1.0.1+fda29ac6` contract as applicable |
| `verified_at` | timestamp | Evidence only; current bytes still checked against readiness key |
| `verdict` | enum | `verified` or `blocked` |
| `blocker` | `SecurityBlocker` | Required when blocked |

## 11. HookBehaviorProof

Result of the actual installed Claude client and exact launch/settings contract.

| Field | Type | Rules |
| --- | --- | --- |
| `claude_path` / `claude_sha256` / `claude_version` | identity | Minimum `2.1.295`; exact observed version bound |
| `managed_document_digest` / `policy_helper_receipt_digest` | hashes | Exact HKLM source and emitted managed policy for protected launch nonce |
| `api_relay_digest` / `remote_fetch_skip_proof` | hashes/result | No-fallback local relay identity and real-client proof that server-managed fetch is skipped |
| `handler_digest` / `handler_config_digest` | hashes | Exec form, args, timeout, synchronous, `onFailure: block` |
| `tool_inventory` | unique strings | Expected exact built-in surface; `PowerShell` present, `Monitor` absent |
| `plugin_inventory` | records | Only release-verified Orbit plugins; no untrusted hook source |
| `normal_rewrite` | proof case | Hook event seen; original host marker absent; contained receipt present |
| `explicit_deny` | proof case | Tool blocked with sanitized reason |
| `failure_cases` | map | Missing/spawn/nonzero/crash/timeout/empty/plain/partial/malformed/schema-invalid outcomes |
| `tree_cleanup` | result | No hook/evaluator descendants survive |
| `verdict` | enum | `passed` or `blocked` only |

Failure to induce/observe the intended PowerShell tool call is inconclusive and therefore `blocked`, not passed.

## 12. MxcRuntimeProof

| Field | Type | Rules |
| --- | --- | --- |
| `artifacts` | verification array | All required `ArtifactVerificationResult` entries passed |
| `windows` | object | Client SKU, recognized branch, exact build/UBR, OS/process architecture |
| `schema_validation` | object | Exact schema hash, `Draft7Validator` identity, base/final request passed |
| `probe_argv` | array | Exact vendored executor + final request + `--probe` |
| `probe_output` | bounded object/digest | Exit zero, parse success, `error` absent, `tier=base-container`, no DACL augmentation; all capabilities/warnings captured |
| `functional_results` | map | In-scope file operations, approved proxy, and contained-tool compatibility recorded as supported or warned limitation |
| `structural_results` | map | Every non-advisory boundary, including all process cleanup/survivor and measurement-completion checks; any failure blocks before leak join |
| `leak_results` | `LeakResult` map | Only enumerated filesystem/registry/DNS/network/UI canaries; deterministic owner-deny intersection |
| `shell_identity` | result | Exact dedicated SID/profile plus measured owner-registry access classification and owner-deny intersection |
| `cleanup_results` | structural map | Timeout/background/hard-kill survivors; any survivor/uncertainty is blocking |
| `compatibility_warnings` | map | Non-security operation limitations such as rename/delete; warnings do not enter owner-deny join |
| `verdict` | enum | `passed`, `passed-with-warnings`, or `blocked`; leak warnings require no explicit owner-deny intersection |

## 13. SessionAttestation

Fresh result for one real employee client process before prompt delivery.

| Field | Type | Rules |
| --- | --- | --- |
| `session_id` / `run_nonce` | strings | Match parent launch and SessionStart receipt |
| `claude_version` | string | Matches current `HookBehaviorProof` |
| `tools` / `plugins` | arrays | Match approved inventories |
| `policy_helper_receipt` / `managed_document_digest` | records | Exact conditional managed policy selected for this nonce |
| `api_relay_receipt` | record | Session used fixed no-fallback relay and skipped remote managed fetch |
| `settings_digest` / `handler_digest` | hashes | Match readiness key |
| `session_start_received` | boolean | Must be true before prompt is written |
| `attested_at` | timestamp | This process only; never reusable as another session's receipt |

No attestation, mismatched init, timeout, or plugin error causes process-tree termination without sending employee work.

## 14. ContainmentReadinessResult

Authoritative gate used by setup, doctor, service, engine, hook, helper, and gateway dispatcher.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact `orbit.native-readiness.v1` |
| `state` | enum | `blocked`, `proving`, `ready`, `ready-with-warnings` |
| `readiness_key` | SHA-256 | Digest of every bound identity/proof below |
| `contract` / `orbit` | identities | Contract epoch, manifest and candidate digests |
| `claude` | `HookBehaviorProof` reference/digest | Passed and current |
| `mxc` | `MxcRuntimeProof` reference/digest | Passed or passed-with-warnings and current |
| `employee_id` / `policy_fingerprint` | values | Exact accepted employee policy |
| `last_full_proof_at` | timestamp | Informational; matching inputs, not age alone, decide validity |
| `blockers` | `SecurityBlocker` array | Empty in `ready` and `ready-with-warnings`; nonempty in `blocked` |
| `warnings` | `LeakWarning` / compatibility-warning array | Nonempty in `ready-with-warnings`; warning never overrides structural failure or explicit owner deny |
| `evidence_digests` | map | Bounded review artifacts; no secret/raw command content |

### State transitions

```text
absent/old/mismatch/failure --> blocked
blocked --owner repair/proof starts--> proving
proving --enforced/no leak----------> ready
proving --measured advisory leak----> ready-with-warnings
proving --explicit-deny breach------> blocked
proving --any gate fails------------> blocked
ready|ready-with-warnings --bound input changes--> blocked
```

`ready-with-warnings` is usable and preserves workflow execution. It differs from `blocked`: all measurements completed, no explicit owner deny intersects the leak, and warnings are bound/displayed. Explicit owner-selected `wsl2` remains a separate path.

## 15. SecurityBlocker and RecoveryAction

| Field | Type | Rules |
| --- | --- | --- |
| `boundary` | enum | client-hook, trusted-policy, gateway, MXC artifact/schema, Windows host, proof/evidence, upgrade |
| `code` | enum | Stable support-safe identifier |
| `message` | string | States work did not run and names one prerequisite; no raw command/secret/policy/path dump |
| `recovery` | `RecoveryAction` | Exactly one action |

`RecoveryAction` has `action_id`, owner-facing instruction, expected result, and optional safe command chosen from a fixed release-owned catalog. Exception text never becomes recovery text.

### LeakWarning

| Field | Type | Rules |
| --- | --- | --- |
| `boundary_id` / `canary_id` / `canonical_target` | values | Exact `LeakResult` identity; cleanup and structural boundaries forbidden |
| `evidence_digest` | SHA-256 | Candidate/host/policy-bound result |
| `owner_deny_intersection` | boolean | Must be false for a warning; true converts readiness to blocker |
| `matching_deny_ids` | array | Must be empty for warning and recompute exactly from bound policy; nonempty result is never a warning |
| `message` | string | Clearly states observed limitation and that workflow continues because owner did not deny it |
| `hint` | string | Optional safe mitigation/WSL2 hint; no forced action or secret details |

`CompatibilityWarning` separately carries operation ID, evidence digest, message, and optional hint for non-security limitations such as rename/delete failure. It never participates in `ExplicitDeny` matching and never converts a structural failure into a warning.

## 16. ReleaseEvidenceTrustRoot

Externally pinned authority independent of the candidate under test.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact `orbit.windows-evidence-trust.v1` |
| `root_version` / `contract_epoch` | integers | Monotonic; hash pinned by bootstrap/prior release |
| `bootstrap_store_identity` | identity | Separately pinned Store-assigned alphanumeric Product ID; Package/Identity/Name `BasemTarekkamal.OrbitSecurityBootstrap`; exact Publisher, Package Family Name, initial `1.0.0.0`, full-trust requirement |
| `keys` | closed records | TPM RSA-PSS runner or offline Ed25519 key ID/public key, role (`x64-runner`, `arm64-runner`, `release-approver`), validity, revocation |
| `signature_contract` | object | RFC 8785 canonical JSON, domain strings, hash, RSA-PSS MGF1/salt/key size, Ed25519/base64url encoding |
| `workflow` | object | Exact repository, workflow path/digest, protected environment, publication job identity |
| `rotation` | object | Old/new dual-signature requirement and effective candidate |

Runner keys are non-exportable RSA keys in Microsoft Platform Crypto Provider (TPM), minimum 2048 bits, using RSA-PSS-SHA256/MGF1-SHA256/32-byte salt. Aggregate approver key is offline Ed25519. A candidate cannot add its own trusted key. Revoked/expired/wrong-role keys fail validation.

## 17. ReleaseEvidenceBundle

One bundle per architecture plus one aggregate candidate index.

| Field | Type | Rules |
| --- | --- | --- |
| `schema` | string | Exact `orbit.windows-containment-evidence.v1` |
| `candidate` | object | Version, git commit/tree, source/manifest/harness digests |
| `host` | object | Windows client SKU, branch, full build/UBR, native x64/ARM64 architecture |
| `dependencies` | object | Exact Claude, MXC, schema, payload, signer, validator identities |
| `install_scenario` | enum | `clean` or `upgrade` |
| `matrices` | object | Hook, policy, gateway, schema/artifact, runtime leak classification, advisory continuation, explicit-deny blocking, cleanup results |
| `counts` | object | 100 repetitions per hook failure class; >=50 bypass variants per enabled host gateway |
| `data_preservation` | result | Existing team data unchanged in upgrade scenario |
| `artifacts` | digest map | Bounded logs/results; no credentials or raw sensitive commands |
| `provenance` | object | Architecture-role TPM RSA-PSS signature over domain-separated RFC 8785 host envelope plus key ID from `ReleaseEvidenceTrustRoot` |
| `verdict` | enum | `passed` or `blocked` |

Aggregate release evidence is `passed` only when both clean and upgrade bundles pass for every architecture, each host signature verifies, and a distinct offline release-approver key signs the aggregate candidate index. Missing native ARM64 evidence means ARM64 is not shipped.

## Relationships

```text
NativeWindowsSecurityContract
  +-- verifies --> ArtifactVerificationResult[*]
  +-- defines --> GatewayCatalogEntry[*]
  +-- binds --> HKLM policy helper + API relay + dedicated shell identity
  +-- binds --> HookBehaviorProof
  +-- binds --> MxcRuntimeProof

OwnerSecurityState + release base/catalog
  -> PolicySourceFingerprint
  -> EffectiveCommandPolicy
  -> ExecutionTicket

HookBehaviorProof + MxcRuntimeProof + PolicySourceFingerprint
  -> ContainmentReadinessResult
  -> SessionAttestation
  -> CommandDisposition

Gateway CommandDisposition
  -> ParsedGatewayInvocation
  -> gateway ExecutionTicket
  -> GatewayAuditRecord[*]

Candidate + readiness/proof matrices
  + ReleaseEvidenceTrustRoot
  -> ReleaseEvidenceBundle[x64, arm64]
```
