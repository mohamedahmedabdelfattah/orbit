# Implementation Plan: Fail-Closed Native Windows Containment

**Feature**: `003-close-containment-gaps` — [spec.md](./spec.md)
**Status**: Plan complete; adversarial security re-review passed
**Priority**: P0 security fix
**Branch**: detached `HEAD` at `044c99d`; no branch created
**Plan path**: `specs/003-close-containment-gaps/plan.md`

## Setup note

This checkout has `.specify/feature.json` but no `.specify/scripts/`, plan template, or `.specify/memory/constitution.md`. The prescribed setup script therefore could not run on this Windows host. The active feature was resolved from `.specify/feature.json`; this plan follows the latest checked-in feature-001 plan structure and records the missing constitution as N/A. No extension hooks are registered.

## Technical Context

| Dimension | Decision | Notes |
| --- | --- | --- |
| Product shape | Python script kit, CLI, local service, control panel | No server/database migration; security state remains local JSON |
| Runtime | Python 3.9-compatible core; Windows PowerShell setup/harness; hash-locked `jsonschema==4.25.1` on native Windows | Exact Draft 7 validation; complete transitive lock is part of release manifest |
| Native security helpers | Small C++20 x64/ARM64 policy-helper, containment-broker service, and full-trust Store bootstrap; pinned MSVC/Windows SDK build image | Shipped signed binaries; no owner build toolchain; reproducible build/manifests gate signing |
| Claude client | Claude Code `2.1.295+` capability floor, exact binary/version bound to behavior proof | Exec-form hook; restricted headless client; current tool inventory verified |
| Native shell | `PowerShell` only | `Bash` denied; `Monitor` unavailable; unknown shell-capable tools omitted from `--tools` |
| MXC | Official `@microsoft/mxc-sdk` `1.0.1`; stable schema `1.0.0` | Exact package, payload, publisher, architecture, schema, and companion verification |
| Host OS | Windows 11 client x64/ARM64 at exact servicing minima, then capability/workload proof | Unknown SKU, architecture, build family, or capability blocks |
| Privileged setup | One owner-approved elevated bootstrap/setup phase | Installs exact HKLM policy helper, local worker/logon policy, ACLs, Event Log source, and machine trust root; employee work never elevates |
| Trusted storage | Strict `staff.json` security subtree; HKLM helper policy; LSA/DPAPI worker credential; bootstrap/trust root under ACL-protected machine state; runtime evidence/tickets outside workspaces | Entire employee workspace, HKCU policy, generic connector state, and model content remain untrusted |
| Hook delivery | Conditional Orbit HKLM `policyHelper` emits managed-only hooks/locks; `--restricted`; cache-free dedicated `CLAUDE_CONFIG_DIR` | Verified no-fallback local API relay suppresses server fetch/cache; source/config watchers terminate on mutation |
| Command handoff | Short-lived opaque, single-use tickets | Raw command/args stay out of rewritten shell string and ordinary logs |
| Gateway model | Whitelisted PowerShell AST -> verified dispatcher; final host set is `staff-apify` and `staff-compute` only | Childless hash-locked Python targets; compute uses in-process GitHub HTTPS API; all other commands contained |
| Process/registry isolation | Job Object supervisor plus dedicated non-admin `OrbitMxcWorker` identity for executor/workload | Alternate-user launch gives shell a clean HKCU; no fallback to owner token |
| Request validation | Exact schema + `Draft7Validator`, closed builder, base/final-wire checks, request-aware semantic probe | Structural/inconclusive failure blocks; measured enforcement leaks are classified against explicit owner denies |
| Readiness | Machine proof + per-employee policy/explicit-deny binding + live attestation | `ready-with-warnings` continues work for advisory leaks; matching owner deny, missing/stale/unknown state blocks |
| Testing | Python `unittest`, PowerShell installer/real-host harness, real Claude client, real Windows 11 x64/ARM64 | Hosted Windows Server remains unit/fake coverage only |
| Release evidence | Store-bootstrap-pinned trust root; TPM RSA-PSS host signatures; offline Ed25519 aggregate | Mandatory leak evidence/classification; advisory leaks may ship, explicit-deny breaches may not |
| First upgrade | Full-trust Store bootstrap (Package Identity Name `BasemTarekkamal.OrbitSecurityBootstrap`, separately pinned Store-assigned ID) plus `0.8.0-sec.N` line | Store identity is independent root; old comparator never offers secure line; stop/block precedes mutation |
| Performance | Blocker classification/recovery action within 30 seconds; hook evaluator below its explicit client timeout | Security proof may take longer, but work stays blocked while proving |
| Compatibility | macOS, Linux, and WSL2 generation/execution unchanged | Native mode checks require both `KIND == windows` and mode `mxc` |

## Constitution Check

`.specify/memory/constitution.md` does not exist. No formal constitution gate applies.

Feature-level gates used instead:

| Gate | Pre-design result | Design response |
| --- | --- | --- |
| No original model command reaches host uncontained | Pass | Hook emits only deny, one-use MXC helper ticket, or one-use gateway dispatcher ticket |
| Employee workspace is never an authorization source | Pass | Security fields split from metadata; legacy cache/profile settings ignored |
| Missing/uncertain state denies | Pass | Strict parsers, bound readiness, exact artifact verification, no compatibility fallback |
| Gateway exception is smaller than shell syntax | Pass | Closed grammar, current owner authorization, absolute verified dispatcher, no shell reparse |
| Exact external contract is immutable | Pass | One release manifest carries all reviewed values; any change changes contract epoch/review |
| Real-client/real-host validation gates release | Pass | Candidate-bound x64/ARM64 evidence required before publish |
| Non-Windows behavior remains unchanged | Pass | Native-only branch and regression assertions; no shared gateway rewrite |

## Architecture

```text
Owner setup/panel
    |
    +--> verified release manifest + strict owner security state
    |                |
    |                +--> machine/policy readiness proof
    |                              |
engine.run() -- native MXC gate ------+
    |
    +--> exact HKLM policyHelper + no-fallback local API relay
            |
            +--> managed-only containment hooks/locks receipt
            |
    +--> Claude Code --restricted --tools <exact>
            |
            +--> system/init + SessionStart receipt (prompt withheld until valid)
            |
            +--> PreToolUse: Bash|PowerShell|Monitor
                    |
                    +--> Orbit hook supervisor (onFailure=block)
                            |
                            +--> invalid/unknown/stale ----------> DENY
                            |
                            +--> ordinary PowerShell
                            |       -> one-use contained ticket
                            |       -> owner helper + OrbitMxcWorker token + Job Object
                            |       -> exact final MXC request --probe
                            |       -> proxy + wxc-exec one-shot
                            |
                            +--> canonical current gateway
                                    -> one-use gateway ticket
                                    -> verified dispatcher
                                    -> apify/compute only, childless in-process HTTPS
```

### Core invariants

1. Hook and dispatcher APIs return closed enums, never booleans/no-decision.
2. Original commands and gateway arguments never appear in the rewritten host shell command.
3. Hook classification occurs only after current readiness and policy validation.
4. Helper and dispatcher atomically claim a ticket, recheck policy/readiness, then launch once.
5. Any audit, integrity, parser, schema, race, or unmeasured uncertainty denies. A completed MXC leak measurement warns unless an explicit owner deny matches it.
6. Workspace diagnostics can be deleted or forged without changing any future decision.
7. `ready-with-warnings` is usable: warnings are highlighted/audited but do not require acknowledgement. Adding a matching owner deny changes the policy fingerprint and blocks native shell before further work.

## Planned Components and File Boundaries

### New security modules/artifacts

| Path | Responsibility |
| --- | --- |
| `core/contracts/native-windows-containment-1.json` | Single closed external/release manifest consumed by Python and PowerShell |
| `core/contracts/windows-evidence-trust-v1.json` | Store/prior-release-pinned TPM RSA runner and offline Ed25519 key roles, revocations/rotation, canonical signature format, publication identity |
| `native/orbit-policy-helper/` -> signed x64/ARM64 `orbit-policy-helper.exe` | No-argument HKLM `policyHelper.path`; fixed env + authenticated named-pipe nonce protocol; managed policy JSON/receipt |
| `core/claude_api_relay.py` | No-fallback loopback relay to Anthropic API; suppresses server-managed fetch and emits health receipt |
| `core/windows_policy_watch.py` | Independent HKLM/managed-file/helper/relay mutation watchers and process-tree stop |
| `core/windows_contract.py` | Windows client SKU, architecture, build/UBR, artifact, signer, schema, companion, and host-prep identity verification |
| `native/orbit-containment-broker/` -> signed x64/ARM64 Windows service | Restricted LocalSystem SID; exact three privileges/no network; closed pipe; LSA credential; batch token must already be Session 0; private desktop, suspended CreateProcessAsUser + Job |
| `core/windows_shell_identity.py` | Owner-side broker client, exact service/account/privilege/ACL/session/no-profile verification and receipts |
| `core/containment_readiness.py` | Proof execution, persistence, invalidation, blocker/recovery taxonomy, per-session attestation |
| `core/windows_process.py` | Explicit empty-base environment builder, restricted-child attributes, Job creation/pre-start assignment, bounded wait/tree termination/evidence |
| `core/gateway.py` | AST-result validation, catalog identity, ticket issuance/claim, dispatcher, trusted audit |
| `core/gateway-parse.ps1` | Fixed no-profile PowerShell AST parser; stdin data only, no evaluation |
| `bootstrap/OrbitSecurityBootstrap` full-trust MSIX/Store package source + manifest | Exact Store product/family/publisher verification; embeds trust-root digest/offline key; stop-the-world blocked marker and atomic activation |
| `tests/test_windows_contract.py` | Build/artifact/schema/architecture matrix |
| `tests/test_windows_broker_contract.py` | Closed IPC frames, privilege/service config, ticket-only launch, malformed/replay/fallback rejection |
| `tests/test_windows_environment.py` | Policy-token/relay-header inheritance map, one-use invalidation, fixed-dispatcher TCB, evaluator/gateway/MXC omission proof |
| `tests/test_containment_readiness.py` | Proof binding, invalidation, messages, session gate |
| `tests/test_gateway_security.py` | Canonical positives and generated bypass corpus |
| `tests/test_upgrade_security.py` | Contract epoch, legacy state, blocked upgrade, data preservation |
| `tests/windows/SetupWindows.Tests.ps1` | Installer staging, tamper, architecture, publisher, and rollback tests |
| `tests/windows/hook-failure-matrix.ps1` | Real-client failure/output/process matrix |
| `tests/windows/mxc-real-host-proof.ps1` | Real final-wire positive/negative/cleanup proof |
| `tests/windows/managed-policy-proof.ps1` | HKLM helper, relay skip, lower-source/HKCU exclusion, mutation ordering proof |
| `tests/windows/registry-dns-ui-proof.ps1` | Explicit owner-SID/hive, authoritative DNS, Session0/private-desktop screen/raw-input/hook/UI canaries |
| `tests/windows/broker-process-proof.ps1` | Batch token, Session 0/private desktop, no-profile, suspended pre-Job launch, cleanup/fallback proof |
| `tests/windows/upgrade-proof.ps1` | Clean and upgraded host scenarios |
| `tests/validate_windows_release_evidence.py` | Closed evidence schema, candidate/architecture/scenario/counter/provenance gate |
| `.github/workflows/windows-containment-release.yml` | Protected x64/ARM64 evidence collection/validation and release gate |
| `.github/workflows/windows-native-security-build.yml` | Pinned toolchain/reproducible x64/ARM64 policy-helper, broker, and Store-bootstrap builds; Authenticode/package signing and manifest hashes |

### Existing files changed

| Path | Planned change |
| --- | --- |
| `core/mxc.py` | Remove workspace cache and PATH runtime; strict hook supervisor; one-use tickets; final request validation; exact probe; helper cleanup |
| `core/engine.py` | Split metadata/security inputs; issue protected policy-helper/relay launch nonce; restricted explicit-tool launch; receipt/live-init gate; native Desktop refusal |
| `core/abilities.py` / `core/abilities.json` | Explicit gateway identities/metadata and current owner authorization; no wildcard authority |
| `core/connectors.py` / `core/connectors.json` | Move MCP grants into strict security state; remote reviewed catalog only; fingerprint/invalidation support |
| `core/hire.py`, `core/panel.py`, `core/grants.py` | Write access-granting fields only through strict owner state; owner reconfirmation path |
| `core/skillbook.py` | Build instruction-only skill bundles; reject hook-bearing/plugin-bearing employee content |
| `core/guard/staff-guard/` | Verify release identity and preserve PowerShell defenses; no untrusted hook registration |
| `core/staffd.py` | Keep control plane available but suspend employee scheduling while native readiness is not ready |
| `core/update.py` | Post-bootstrap updates delegate to external quiescing launcher; reject legacy/in-process native source mutation |
| `core/tools/apify.py` | Fresh owner-state authorization; locked in-process HTTPS only; no subprocess/runtime install |
| `core/tools/compute.py` | Replace `gh`/`git`/shell descendants with in-process GitHub REST/Git-data/workflow/artifact APIs |
| `core/tools/fetch.py`, `browse.py`, `watch.py`, `video.py`, `connectors_cli.py`, `docs.py` | Exact native-MXC-only branch uses setup-pinned absolute dependencies/no runtime install; macOS/Linux/WSL paths remain unchanged and regression-tested |
| `core/osinfo.py` | Expose exact OS/process architecture and Windows client build data without broad numeric compatibility |
| `orbit` | Shared structured setup/doctor report, readiness gate, policy migration/review, exact recovery actions |
| `setup-windows.ps1` | Transactional manifest-driven runtime plus pinned contained-tool dependencies, HKLM helper, relay, worker identity/ACL, Event Log source, trust root, and readiness invalidation |
| `tests/test_mxc.py` | Reverse legacy-cache/no-decision/pass-through expectations; add strict failure/schema/helper tests |
| `tests/test_platforms.py` | Remove stray marker; assert restricted settings, tool inventory, mode boundary, unchanged non-Windows output |
| `.github/workflows/tests.yml` | Keep hosted unit coverage, run guard tests, remove optional-real-host claim, validate evidence schema |
| `PRODUCT.md`, `README.md`, `SETUP.md`, feature-001 notes | State release-gating rule and point stale optional claims to feature 003 |

## Delivery Sequence

1. **Restore trustworthy test baseline**
   - Remove the committed `=======` marker.
   - Make existing platform expectations match documented hook exec form.
   - Add the machine-readable security manifest and parser tests first.
2. **Build trusted state foundation**
   - Separate employee metadata from owner security policy.
   - Move connector/MCP grants into strict versioned security state and fingerprints.
   - Stop reading legacy policy/profile grants.
   - Add stable reads, fingerprints, explicit owner-deny records, tickets, strict audit, and migration blockers.
3. **Close the client/hook boundary**
   - Install exact HKLM conditional policy helper, managed-only hooks/locks, no-fallback local API relay, and independent source watchers.
   - Add restricted explicit-tool launch, `onFailure: "block"`, documented-input normalization, supervisor, terminal dispositions, policy-helper/live-init/SessionStart gate, and Monitor denial.
   - Block native Desktop/folder sessions.
4. **Replace gateway pass-through**
   - Add canonical parser, final two-entry host catalog, current authorization, verified dispatcher, preallocated audit WAL/Event Log fallback, and minimal env.
   - Rewrite Apify/compute as childless locked HTTPS targets; contain every other gateway.
5. **Make MXC/runtime exact**
   - Transactional artifact/schema/host-prep installation plus dedicated low-privilege shell identity/profile/ACL.
   - Exact Windows build/architecture checks.
   - Draft 7 base/final-wire validation, exact environment/UI policy, removal of unnecessary `internetClient`, structural zero-survivor cleanup gates, filesystem/registry/DNS/UI/network leak classification, advisory continuation/owner-deny blocking, and functional file workflows.
6. **Enforce readiness and upgrade block**
   - Gate run, scheduling, hook, gateway, mode switch, and update paths.
   - Ship first migration only through externally verified stop-the-world bootstrap; never expose it to legacy in-app updater.
   - Unify doctor/setup report and owner recovery actions.
7. **Make evidence release-blocking**
   - Complete fake/unit matrices.
   - Produce clean/upgrade x64 and ARM64 real-host bundles.
   - Validate Store-pinned TPM RSA-PSS runner signatures, offline Ed25519 aggregate signature, canonical bytes, and exact workflow/environment before publication.

Task generation must preserve this order: later stages depend on trusted manifest/state and cannot safely ship independently.

## Requirement Coverage

| Requirement | Design owner | Required proof |
| --- | --- | --- |
| FR-001 | Closed hook disposition enum; explicit tool list; Monitor absent | Tool-inventory test and every-event disposition matrix |
| FR-002 | Exec-form handlers with `onFailure: "block"` | Settings assertion plus real spawn/crash/timeout calls |
| FR-003 | Exact HKLM policy helper + no-fallback API relay + real-client receipts | Version, source selection, remote-fetch skip, helper output, and mutation tests |
| FR-004 | Hook supervisor and client failure matrix | Host marker absent for every failure/output class |
| FR-005 | Documented common/PowerShell input accepted; required semantics strict; rewritten input rebuilt | Exact stdout-byte, documented-field, unknown-field, timeout/background stripping corpus |
| FR-006 | Ticket helper never carries fallback/original shell path | Fault injection at policy, proxy, helper, executor stages |
| FR-007 | Alternate-user executor plus Windows Job Object supervisor and layered deadlines | Worker-token, nested-job, grandchild delayed-marker/PID survivor tests |
| FR-008 | Managed-only Orbit handlers, restricted client, verified plugins/skills/MCP | HKLM/remote/lower-source/project/plugin/skill/MCP tamper matrix |
| FR-009 | Policy-helper, relay, live-init, SessionStart receipts and independent source watchers | Install/change/repair/session-start/source-mutation ordering scenarios |
| FR-010 | Closed blocker codes plus leak-warning codes; redacted action/hint | Blocked and advisory non-technical message reviews |
| FR-011 | Workspace excluded; shell runs under dedicated clean-HKCU identity | Taint-source, file, owner-registry, policy-key, and workspace mutation matrix |
| FR-012 | Cache APIs removed from authorization path | Preexisting/raced/symlinked cache tests |
| FR-013 | Strict owner security subtree includes tools, gateways, connectors/MCP, explicit denies plus catalogs | Grant/deny removal injection and typed owner-write tests |
| FR-014 | No reusable snapshot; bound one-use ticket schema | Missing/extra/stale/mismatched ticket corpus |
| FR-015 | Policy fingerprint checked at hook and claim | Owner-tightening and queued-command races |
| FR-016 | One stable read plus before-emit/before-launch recheck | Registry replacement/race tests |
| FR-017 | Workspace logs documented and tested non-authoritative | Edit/delete/forge diagnostics then compare decisions |
| FR-018 | Host deny default and explicit catalog gateway flag | Unknown/prefix/substr command corpus |
| FR-019 | Final two-entry host catalog + current owner grant + verified childless dispatcher target | Disable/replacement/reparse/descendant-install tests |
| FR-020 | Closed PowerShell AST whitelist | At least 50 bypass variants per host gateway |
| FR-021 | Childless locked HTTPS Apify/compute targets and structured argv dispatcher | API/method/budget/private-network/secret/no-descendant tests |
| FR-022 | Noncanonical calls contained only with valid readiness | Unknown/malformed/disabled decision table |
| FR-023 | Absolute verified interpreter/env/dependencies; no `.cmd`, PATH, profile, alias, link, `gh`, or `git` identity | Shadow/relative/suffix/case/junction/global-package/child-spawn tests |
| FR-024 | Classifier/dispatch/target-descendant faults are terminal denial | Parser/catalog/audit/launch/runtime-install/child-spawn fault injection |
| FR-025 | Reserved audit WAL with Windows Event Log fallback | Approved/rejected records, primary/fallback failure, readiness-block, redaction tests |
| FR-026 | Manifest minimum `2.1.295` plus exact-version proof | Older, exact, newer, changed binary cases |
| FR-027 | Exact MXC `1.0.1` and schema `1.0.0` only | Version/schema mutation matrix |
| FR-028 | Transactional package/payload/publisher/companion verifier | Tarball, PE, signer, arch, host-prep tamper cases |
| FR-029 | Exact schema artifact, pinned Draft 7 validator, strict base/final-wire validation | Unknown/retired/experimental field corpus |
| FR-030 | Real request-aware probe + filesystem/registry/DNS/UI/network canaries + owner-deny join | Advisory case warns/continues; matching explicit deny blocks; missing measurement blocks |
| FR-031 | Exact host/worker/capabilities plus measured limitation classification | Build/SID/UI/network/prep tests and warning-vs-deny outcomes |
| FR-032 | Shared blocker/warning readiness report | Doctor/setup ready-with-warnings, continuation text, hint, and blocker tests |
| FR-033 | Externally pinned evidence root/workflow plus leakage classification matrices | Every leak classified; advisory continuation passes; explicit-deny breach fails |
| FR-034 | Only exact signed validator job owns publication credential | Docs/workflow/root-digest/environment assertion plus publication denial tests |
| FR-035 | Exact native branch; non-Windows output unchanged | macOS/Linux/WSL2 regression suites |
| FR-036 | Externally signed first-upgrade bootstrap quiesces before mutation; later external updater | Legacy updater exclusion, pre-mutation stop marker, clean/upgrade data-preservation proof |

## Success-Criteria Coverage

| Criterion | Evidence owner |
| --- | --- |
| SC-001 | Real-client/runtime failure matrix: 100 repetitions per hook class, zero host markers, and zero hook/helper/proxy/executor/workload survivors |
| SC-002 | Policy-tampering matrix proves explicit owner-deny enforcement; non-denied canary leaks warn/continue |
| SC-003 | Canonical positives and >=50 bypass variants for final Apify/compute host gateways, with no-descendant/audit oracles |
| SC-004 | Clean/bootstrap-upgrade bundles prove owner-deny blocks, advisory-leak continuation, and mandatory timeout/process-tree cleanup on every architecture |
| SC-005 | Readiness key binds explicit denies and supports ready/ready-with-warnings; stale-key tests block |
| SC-006 | Structured blocker benchmark requires diagnosis plus one recovery action within 30 seconds and redaction tests |
| SC-007 | Existing macOS/Linux/WSL2 suites plus upgrade/fallback team-data inventory comparison |
| SC-008 | Independent adversarial review of workspace, managed-policy, registry/DNS/UI, gateway descendants, upgrade bootstrap, and evidence trust root before publication |
| SC-009 | Ten-owner blocked-message study plus warning-message continuation study, each with >=9 successful comprehension results |

## Phase 0: Research

[research.md](./research.md) records decisions and rejected alternatives for:

- effective Claude settings and shell-tool coverage;
- authoritative managed-policy delivery/remote-fetch suppression and source mutation ordering;
- strict hook output/failure semantics;
- trusted policy ownership and migration;
- policy race/ticket protocol;
- canonical gateway grammar and dispatch;
- exact MXC/schema/artifact/host-prep contract;
- alternate-user registry isolation, DNS/UI side-channel and functional file proof;
- Windows Job Object cleanup;
- stop-the-world legacy bootstrap and externally rooted release evidence.

All unknowns are resolved. No compatibility assumption remains implicit.

## Phase 1: Design and Contracts

- [data-model.md](./data-model.md) — trusted policy, tickets, dispositions, proofs, readiness, audit, and release evidence.
- [contracts/containment-hook.md](./contracts/containment-hook.md) — real-client launch, handlers, inputs, outputs, failures, and per-session proof.
- [contracts/trusted-policy.md](./contracts/trusted-policy.md) — source ownership, stable-read/race protocol, tickets, and migration.
- [contracts/gateway-invocation.md](./contracts/gateway-invocation.md) — canonical grammar, catalog/launcher verification, dispatch, controls, and audit.
- [contracts/mxc-runtime.md](./contracts/mxc-runtime.md) — exact external baseline, installation, final request, probe, and cleanup.
- [contracts/readiness-evidence.md](./contracts/readiness-evidence.md) — readiness/invalidation, doctor output, upgrade gate, and release bundle.
- [quickstart.md](./quickstart.md) — executable unit, real-client, real-host, clean-install, upgrade, and release validation guide.

## Post-Design Constitution Re-check

N/A: no project constitution exists. Feature-level gates remain satisfied after design:

- no workspace authorization input;
- no raw gateway or ordinary command host pass-through;
- no unproven native Desktop path;
- exact release/schema/build contract retained;
- stale/missing evidence blocks;
- native-only implementation boundary retained;
- x64/ARM64 real-host evidence remains non-waivable for shipped support.

## Risks and Mitigations

| Risk | Mitigation / release consequence |
| --- | --- |
| Remote/MDM/HKCU policy can outrank or add parallel host hooks | Non-default no-fallback API relay skips remote fetch; exact HKLM policy helper supplies sole managed policy/locks; lower sources ignored; independent watchers kill on mutation |
| Claude version has Windows hook regression despite meeting minimum | Exact-version behavioral proof fails; version is not admitted until tested |
| Restricted mode changes full-autonomy prompt behavior | Explicit tool/permission rules preserve approved capabilities; bypass mode is not used as a security dependency |
| Native Desktop cannot carry the contract | Disable that surface in native MXC mode; control-panel/headless and WSL2 remain available |
| Owner had legitimate domains only in profile data | Do not trust-import; owner reconfirms through panel/doctor; narrower policy applies meanwhile |
| Identity-less proxy leaks direct/private/loopback traffic | Bind warning to evidence; continue without matching owner deny; block that employee's native shell when owner explicitly denies channel |
| MXC 1.0.1 leaks owner registry, DNS, or UI | Alternate-user/session controls reduce risk; measured remainder warns/continues unless matching explicit owner deny |
| MXC 1.0.1 cannot rename/delete in readwrite roots | Highlight compatibility limitation; continue unrelated workflows and let affected operation report its natural failure |
| Job assignment conflicts with MXC internals | Real-host cleanup/positive proof fails; do not ship that architecture/build until supervisor design is compatible |
| ARM64 hardware evidence unavailable | Remove ARM64 support from that release and reject ARM64 setup; never substitute emulation |
| Tier-3 host prep is confused with Orbit's BaseContainer requirement | Install/verify host-prep as a companion, but require `base-container` and no DACL augmentation; never run prep as a substitute for missing proxy capability |
| Legacy updater merges before new quiescing code can run | Secure-line versions compare equal under old `_key()` and are external-bootstrap only; exact legacy comparator is a release test |
| Candidate signs its own evidence or another workflow publishes | Trust root is pinned by Microsoft Store bootstrap/prior release; TPM RSA runner keys plus offline Ed25519 aggregate key; exact protected workflow alone owns publication credential |
| Existing shared test module is syntactically invalid | Baseline repair is first delivery step and release evidence is invalid until all suites parse |
