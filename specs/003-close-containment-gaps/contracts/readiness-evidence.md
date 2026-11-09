# Contract: Containment Readiness and Release Evidence

**Producer**: Orbit setup, doctor, update, real-client harness, real-host harness, protected release workflow
**Consumers**: Service scheduler, engine, Claude session gate, hook, MXC helper, gateway dispatcher, release publisher
**Contract versions**: `orbit.native-readiness.v1`, `orbit.windows-containment-evidence.v1`

## Principle

Native Windows containment is unavailable until current evidence measures the exact client, settings, policy, release, runtime, request, host, and architecture combination. Presence/version text alone never grants readiness. Only completed enumerated filesystem/registry/DNS/network/UI MXC leak measurements are advisory by default; process cleanup/survivors and every other structural boundary always block on failure.

Missing, failed, inconclusive, or integrity-related proof means:

- employee scheduling and headless work remain blocked;
- shell tools and gateway dispatch remain unavailable;
- native Desktop/folder employee sessions remain unavailable;
- panel, doctor, setup/repair, data export, and explicit WSL2 selection remain available;
- original commands never run on host.

`ready-with-warnings` is an accepted native state, not failure. It preserves workflows while highlighting enumerated measured MXC leaks that do not intersect explicit owner denies. Hook, host-execution, trusted-policy-source, gateway, artifact, process-cleanup/survivor, and unknown-state failures never use this state.

## Readiness layers

### MachineProof

Bound to one machine and exact security contract:

- Orbit candidate version, commit/tree, manifest, contract epoch, handler/parser/dispatcher/catalog digests;
- Claude executable canonical path/hash/version;
- exact HKLM managed document, policy-helper/emitted-policy receipt, closed-layout remote-cache-free Claude config root, local API relay, remote-fetch/cache-skip proof, watcher state, settings/hook/plugin/tool digests;
- complete real-client behavior proof;
- exact MXC package/executor/host-prep/schema/validator/conditional-companion and dedicated shell identity/no-profile/ephemeral-root/ACL identities;
- Windows client SKU, branch, full build/UBR, OS/process architecture;
- request-aware final-wire probe, filesystem/registry/DNS/UI/network leak proof, and separate structural cleanup proof.

### EmployeePolicyProof

Bound to:

- employee ID and active status;
- exact trusted owner-policy fingerprint/revision;
- exact explicit owner-deny digest;
- workspace/team canonical paths;
- enabled tool/gateway/connector catalog and grant identities;
- machine proof key.

It binds actual employee request/policy shape. A policy change invalidates it. A measured leak plus no matching owner deny permits warnings; adding/tightening a matching deny causes immediate fingerprint mismatch and blocks native shell until enforcement/WSL2 is available.

### SessionAttestation

Fresh for every real Claude employee process:

- parent launch nonce and expected session ID;
- policy-helper emitted-policy receipt and API-relay/remote-fetch-skip receipt;
- `system/init` Claude version, tools, and plugin/error state;
- settings/handler/readiness digests;
- owner-side SessionStart receipt;
- no prompt sent until attestation passes.

It is not reusable by another session and does not replace full behavior proof.

## Readiness state machine

```text
missing / old epoch / mismatch / failed proof
                     |
                     v
                  BLOCKED
                     |
          owner setup/repair/prove
                     v
                  PROVING
              /       |        \
 missing/fail   enforced     measured leak
      |             |       no owner deny
      v             v            v
   BLOCKED         READY   READY-WITH-WARNINGS
                                   |
                          matching owner deny added
                                   v
                                BLOCKED
```

State is a closed enum. A malformed/unknown/stale state is `blocked`. `ready-with-warnings` requires completed bound measurements and zero explicit-owner-deny intersections.

## Protected storage

Readiness records and evidence digests live under owner runtime state outside every employee working/additional directory, for example:

```text
%USERPROFILE%\Staff\.runtime\security\readiness\
  machine.json
  employees\<employee-id>.json
  sessions\<session-id>.json
  receipts\...
  audit\gateway.jsonl
```

The first-upgrade blocked marker and evidence-trust root live in bootstrap-owned machine state outside both kit and team trees. Gateway audit also has the independently registered `Orbit-Containment` Windows Event Log fallback.

Rules:

- no link/junction/reparse component;
- bounded regular files, closed schemas, atomic writes;
- release/contract/readiness digest in every record;
- no employee workspace copy is authoritative;
- required record write failure leaves/returns `blocked`;
- successful proof logs contain hashes/counters/status only, not secrets/raw commands/policy bodies;
- diagnostics mirrors in workspaces are optional and ignored.

## Readiness key

`readiness_key` is the SHA-256 of canonical identities/results required to accept the run:

```text
contract epoch + Orbit candidate/manifest/files
+ Claude executable/version/HKLM helper/emitted policy/relay/settings/handlers/tools/plugins/MCP/proof
+ MXC package/payload/schema/validator/worker identity/host/build/request/side-channel proof
+ employee trusted-policy and explicit-owner-deny fingerprint
```

Hook, ticket, helper, and gateway dispatcher compare the current key. They never trust a key supplied by the employee command/environment.

## Full proof triggers

Run the complete real-client and real-host proof after:

- first install;
- Orbit upgrade or contract epoch change;
- Claude executable path, bytes, or version change;
- HKLM managed document, policy helper, emitted-policy schema, relay, remote-fetch behavior, source watcher, settings/hook/plugin/tool change;
- Orbit handler, supervisor, parser, dispatcher, catalog, gateway security module, or base policy change;
- owner security policy, explicit deny, or connector/MCP grant change for the affected employee;
- MXC package, executor, companion, schema, validator, active path, or repair change;
- Windows SKU, branch, build/UBR, architecture, worker identity/profile/ACL, or relevant host-preparation/capability change;
- containment repair or a previous proof failure;
- any unreadable/unexplained current evidence mismatch.

Newer Claude/MXC/Windows versions are not admitted by numeric ordering. MXC/schema changes require a new reviewed manifest. A newer Claude version may be admitted only after its exact real-client proof passes.

## Machine proof sequence

1. Validate release security manifest and all Orbit-owned security file digests.
2. Verify Windows client SKU, branch, full build/UBR, OS/process architecture.
3. Verify Claude canonical path/hash/version and capability floor.
4. Verify exact HKLM document/helper, dedicated config-root allowlist and remote-cache absence, and local relay; prove non-default endpoint skips server-managed fetch/cache, exact helper output is selected, lower file/HKCU sources are ignored, no merge/direct fallback exists, and independent source/config watchers are armed.
5. Verify restricted production managed settings, managed-only locks, exec-form hook fields, `onFailure: "block"`, timeouts, explicit tools/MCP, and Monitor absence.
6. Run real-client normal rewrite, documented-input-field normalization, deny, source-mutation, failure/output, timeout, and hook-tree cleanup matrix.
7. Verify MXC package/payload/schema/validator/companion paths, hashes, PE machine, versions, Authenticode, publisher.
8. Verify signed broker/service privileges/IPC, dedicated worker batch SID/no-profile Session0/private-desktop launch/ephemeral roots/ACLs; plant explicit owner-SID/hive canaries.
9. Build actual final proxy request and validate exact schema/environment/UI fields.
10. Run request-aware probe; require complete parse/error/tier result and capture all network/UI capabilities/warnings.
11. Run structural cleanup/process-survivor gates; any failure or uncertainty blocks before leak classification.
12. Run enumerated filesystem, owner-registry, DNS, UI, and network canaries plus compatibility operations; classify complete leak results separately from compatibility warnings.
13. Join only eligible leak results with explicit owner-deny digest: any intersection -> blocked; otherwise leaks -> ready-with-warnings; no leaks -> ready.
14. Persist evidence digests/counters/warnings only after classification completes.

Any missing, failed, inconclusive, or integrity proof stops the sequence and produces blockers. A completed leak produces warnings unless explicitly denied. Setup/doctor identifies blockers plus one recovery action, and warnings plus an optional hint, within 30 seconds even if full proof takes longer.

## Real-client hook proof

Uses the actual installed Claude binary and production-equivalent restricted launch/settings/plugins/tool inventory. It captures stream hook lifecycle events and owner-side receipts.

Required classes:

- normal PowerShell command rewritten and contained;
- explicit policy denial;
- missing registration/handler;
- unsupported/older version;
- managed hooks disabled/filtered/extra;
- HKLM document/helper nonce/output mismatch, foreign/merged source, lower file/HKCU policy attempt, helper mutation, relay failure, remote-fetch attempt, and direct-API fallback;
- handler spawn error;
- nonzero exit;
- crash/hard termination;
- timeout immediately before valid output;
- empty output;
- `{}`;
- plain text;
- partial `{` and other partial JSON;
- malformed object;
- JSON string/array;
- schema-invalid decision;
- valid decision followed by nonzero exit;
- complete documented common and PowerShell input fields, missing/non-string/unknown-semantic fields, and proof that model timeout/background values are replaced;
- evaluator/supervisor child/grandchild cleanup.

For release evidence, each failure class runs 100 times. Every attempt requires absent host marker and no surviving process. Failure to observe the intended real PowerShell tool event is a failed/inconclusive proof, never success.

## Real-host MXC proof

Uses actual verified final request/helper/proxy/executor path under the dedicated low-privilege Windows identity:

- request-aware probe with strict predicates;
- in-scope create/read/update/atomic-rename/delete positives;
- approved HTTP and HTTPS proxy positives;
- secret-read and out-of-scope-write canaries classified by observed bytes/markers;
- public/private/link-local/direct/non-proxy-loopback canaries classified by observed connection;
- explicit `HKEY_USERS\<owner-SID>`/owner-hive and worker-persistence canaries classified by access/change;
- authoritative DNS canary classified by query receipt;
- clipboard/input/external-handle/atom/desktop/session/system/display/IME/screen/raw-input/hook/foreground canaries classified by data/change;
- proxy stopped/replaced/raced failure with no direct fallback;
- workload timeout and child/grandchild cleanup;
- normal-root-exit background child cleanup;
- hard helper and executor kill cleanup.
- worker SID/no-profile/ephemeral-root/ACL substitution and alternate-user launch failures deny without owner-token fallback.

Each enumerated filesystem/registry/DNS/network/UI leak canary runs under both policies where applicable: no matching owner deny MUST warn and continue if leaked; matching explicit owner deny MUST block native shell if leaked. Cleanup/survivor cases must always pass structurally and never enter this dual-policy join. Discovery/no-request probe and fake executor results cannot satisfy this layer.

## Employee/session gate locations

All paths call one readiness API and fail closed:

| Location | Required behavior |
| --- | --- |
| Microsoft Store bootstrap / `setup-windows.ps1` | Verify exact Store package identity, stop legacy service before first source mutation, install HKLM helper/relay/worker, invalidate, then prove |
| `orbit doctor` | Read/recheck current evidence; never create readiness from prose |
| `orbit sandbox mxc` | Refuse switch until complete current proof yields ready or ready-with-warnings |
| Native `orbit start` / service startup | Start panel/repair control plane; suspend employee scheduler only while blocked/proving |
| `core/staffd.py` scheduler/inbox | Do not dequeue/start employee work while blocked |
| `core/engine.py::run` | Accept current ready/ready-with-warnings proof; surface bound warnings before/with work |
| `core/engine.py::claude_session` | Refuse native Desktop/folder session under MXC contract |
| Claude process before prompt | Require live SessionAttestation |
| HKLM/file/relay watchers | Arm before prompt; terminate process tree and invalidate on mutation |
| `core/mxc.py` hook | Recheck readiness key and current policy before disposition |
| MXC helper ticket claim | Recheck readiness/policy/artifacts/request before launch |
| Gateway dispatcher ticket claim | Recheck readiness/policy/catalog/launcher/audit before launch |
| Post-bootstrap update | External launcher quiesces and invalidates before atomic replacement; legacy in-app updater is never offered feature 003 |

Defense-in-depth gates prevent one missed caller from reopening host execution.

## Invalidation behavior during work

- Owner policy or explicit-deny change changes fingerprint immediately. Next hook/claim rejects stale tickets; proof recomputes warning intersections. A newly matching owner deny converts ready-with-warnings to blocked before new native shell work.
- HKLM managed document, policy helper, managed-file location, or relay mutation is detected by independent owner-side watchers; parent invalidates and terminates. `ConfigChange` is supplemental and not the security oracle.
- Claude auto-update/path replacement causes hash/version mismatch; next run/hook blocks.
- Orbit/MXC/schema/runtime file replacement causes current digest mismatch; helper/dispatcher blocks.
- Missing audit/readiness state never falls back to workspace logs or generated defaults.
- A proof process that crashes or times out leaves `blocked`, cleans descendants, and records safe blocker code.

## Structured blocker and recovery output

Every blocker contains:

- boundary (`client-hook`, `trusted-policy`, `gateway`, `mxc-artifact`, `mxc-schema`, `windows-host`, `proof`, `upgrade`, `release-evidence`);
- stable non-secret code;
- statement that employee work did not run;
- exact observed non-secret prerequisite state needed for support;
- exactly one fixed recovery action.

Examples of action classes:

- upgrade Claude Code to supported release;
- run verified Windows containment repair;
- install named Windows servicing update;
- review migrated employee access in control panel;
- remove/approve conflicting enterprise policy through administrator;
- deliberately switch to WSL2.

Never include raw command, secret/credential, URL query/body, ticket/nonce, policy body, unrestricted path list, raw exception, or raw hook/runtime output.

Every advisory leak warning contains employee/canary/boundary/target identity, evidence digest, empty recomputed matching-deny IDs, observed limitation, statement that workflow continues because no explicit owner deny matches, and optional mitigation/WSL2 hint. It is not styled as a blocker and requires no acknowledgement. The same leak with nonempty matching-deny IDs is never serialized as warning and becomes a blocker.

`orbit doctor` displays, for every native check:

- effective Claude path/version/hash and hook proof status;
- HKLM policy-helper/emitted-policy, API-relay/remote-fetch-skip, watcher, handler/tool/plugin/MCP proof state;
- MXC release/schema/validator and artifact/publisher/architecture state;
- Windows client branch/full build/UBR/architecture and dedicated worker SID/no-profile/ephemeral-root/ACL state;
- request-aware probe tier/error/capability summary;
- last functional and each filesystem/registry/DNS/UI/network leak canary classification, plus separate cleanup structural status;
- employee policy/explicit-deny fingerprint and readiness state;
- every advisory warning, continuation statement, and optional hint;
- one recovery action per blocker.

## First-upgrade and later-update contract

The release increments containment contract epoch but deliberately uses a secure-line version whose first three numeric components remain `0.8.0` (for example `0.8.0-sec.1`). Old `update._key()` therefore sees no newer version and cannot offer `update.apply()`. A release test feeds every secure-line version through the exact legacy comparator and requires `newer == false`. Old `update.apply()` merges source before new code can quiesce, so any greater legacy-visible version is forbidden while those clients remain supported.

Initial migration requires a full-trust Microsoft Store package. `BasemTarekkamal.OrbitSecurityBootstrap` is its exact Package/Identity/Name, not the WinGet Store ID. The Store-assigned alphanumeric Product ID, exact Publisher, Package Family Name, and version are separate non-placeholder fields in the externally pinned trust root and setup instructions. Installation uses that exact Store-assigned ID/version with `winget --source msstore`. Windows Store/package APIs must report all identities and packaged full-trust status; unpackaged/copied executables refuse. Store signing/distribution is independent initial root. Signed payload embeds offline release public key and evidence-trust digest. Before any kit/source mutation it:

The initial accepted Store version is exactly `1.0.0.0`; the install command pins it. Another bootstrap version needs prior secure-release authorization or trust-root rotation/review.

1. stops and disables the legacy Scheduled Task/service;
2. terminates all active Orbit employee Claude/hook/helper/gateway processes and verifies zero survivors;
3. writes and flushes a machine-level `blocked-before-update` marker outside the kit/team trees;
4. snapshots team-data inventory without copying security authority;
5. stages and verifies complete candidate, HKLM policy helper, API relay, worker identity/ACLs, and manifests;
6. atomically activates the staged kit only after all preceding gates pass;
7. starts control-plane/repair mode only; employee work remains blocked pending owner migration and proofs.

The bootstrap package is manual/external. A secure-line GitHub release may be visible, but its legacy comparison key must remain equal to `0.8.0`; later secure-line updates always use the external launcher and full version, which quiesces and invalidates before replacement.

After restart:

- panel/doctor/repair remain available;
- old/absent readiness cannot match new epoch/release digest;
- legacy workspace cache/profile grants remain present but non-authoritative;
- owner reviews untrusted legacy access-like profile data;
- setup/repair/client/runtime/policy proofs run;
- employee work resumes only after all current records are `ready` or `ready-with-warnings`; matching explicit-deny breaches remain blocked.

Manual Git pull is unsupported for the first native P0 transition because it cannot provide pre-mutation quiescence. If source is changed anyway, the external marker/epoch mismatch keeps new code blocked, but owner must run bootstrap repair. Team/workspace/history/skill/log bytes are not deleted or silently moved. Explicit WSL2 remains separate and contained.

## Release evidence bundle

Each architecture/scenario bundle is closed JSON plus digested bounded artifacts:

```json
{
  "schema": "orbit.windows-containment-evidence.v1",
  "candidate": {
    "version": "0.8.0-sec.<N>",
    "git_commit": "<sha>",
    "git_tree": "<sha>",
    "manifest_sha256": "<sha256>",
    "harness_sha256": "<sha256>"
  },
  "host": {
    "sku": "Windows 11 client",
    "branch": "24H2|25H2|26H2|26H1",
    "build": "<full build.UBR>",
    "architecture": "x64|arm64"
  },
  "install_scenario": "clean|upgrade",
  "dependencies": {
    "claude": "<version/hash/proof digest>",
    "mxc": "1.0.1",
    "schema": "1.0.0",
    "artifact_digests": "<digest map>"
  },
  "matrices": {
    "hook_failure": "<result digest/counters>",
    "policy_tampering": "<result digest/counters>",
    "gateway_bypass": "<result digest/counters>",
    "schema_artifact": "<result digest/counters>",
    "structural_boundaries": "<all-pass result digest/counters>",
    "registry_dns_ui": "<result digest/counters>",
    "advisory_leak_continuation": "<result digest/counters>",
    "explicit_owner_deny_blocking": "<result digest/counters>",
    "mxc_workloads": "<result digest/counters>",
    "cleanup": "<result digest/counters>"
  },
  "data_preservation": "passed",
  "provenance": {
    "key_id": "<architecture-role TPM key from Store/prior-release-pinned trust root>",
    "algorithm": "RSA-PSS-SHA256-MGF1-SHA256-salt32",
    "signature": "<signature over canonical manifest and artifact digest map>"
  },
  "verdict": "passed"
}
```

Required candidate set:

| Architecture | Clean install | Upgrade install |
| --- | --- | --- |
| x64 | Required | Required |
| ARM64 | Required if shipped | Required if shipped |

ARM64 emulation is not evidence. Hosts must be native Windows 11 client and report matching PE payloads.

## Matrix gates

Release publisher requires all:

- hook failure/output/process matrix; 100 repetitions each failure class, zero host markers/survivors;
- policy-tampering/race/cache/profile/settings/skill/link matrix; 100% denied/no widening;
- owner-registry, DNS, UI, filesystem, and network canaries all measured and correctly classified;
- every cleanup/process-survivor gate passes with zero survivors and no uncertainty;
- each observed leak without matching owner deny produces warning and successful unrelated workflow continuation;
- each same leak with matching explicit owner deny blocks native shell before affected work;
- gateway valid forms and at least 50 bypass variants per enabled host gateway; only intended dispatcher/target reach host;
- exact package/payload/publisher/architecture/schema/validator/companion tamper matrix;
- exact-schema unknown/retired/experimental-field rejections;
- closed structural-boundary matrix passes before leak classification: hook/host/policy/gateway/audit/artifact/request/broker/launch/measurement/cleanup all pass;
- real request-aware probe and proxy/filesystem/registry/DNS/UI/network leak classification plus structural timeout/cleanup pass;
- functional create/update/rename/delete results under exact worker identity, with limitations warned rather than globally blocking;
- clean and upgrade data-preservation scenarios;
- macOS, Linux, and WSL2 existing regression suites;
- independent security review with no workspace/hook-failure arbitrary-host path.

## Attestation/signature

Evidence trust is defined by `core/contracts/windows-evidence-trust-v1.json`. Its SHA-256 is pinned outside the candidate by the Microsoft Store bootstrap package and prior secure release. The closed document contains:

- RSA public key IDs/bytes for exactly one protected native x64 runner role and one protected native ARM64 runner role, plus a distinct offline Ed25519 release-approver role;
- each key's permitted architecture/role, validity interval, and revocation state;
- exact repository `BasemTarekkamal/orbit`, workflow path `.github/workflows/windows-containment-release.yml`, workflow digest, protected GitHub Environment `windows-containment-release`, and publication job identity;
- exact signature contract: UTF-8 RFC 8785/JCS canonical JSON, canonical field/number/artifact-map ordering, signature field omitted, base64url without padding, and exact NUL-terminated ASCII domain strings for host, aggregate, and rotation envelopes;
- dual-signature key-rotation rules. A rotation requires old-root and new-root signatures over the domain-separated canonical rotation envelope plus a new contract epoch; a candidate cannot trust a key it introduces by itself.

Native runner private keys are non-exportable RSA-2048-or-stronger keys in Microsoft Platform Crypto Provider (TPM). Host envelopes are prefixed by `Orbit Windows Containment Host Evidence v1\0`, canonicalized, SHA-256 hashed, then signed with RSA-PSS using MGF1-SHA256 and 32-byte salt. Each clean/upgrade host bundle is signed by role matching native architecture. Aggregate index uses domain `Orbit Windows Containment Aggregate v1\0` and is signed directly by offline Ed25519 release-approver key. Rotation uses `Orbit Windows Containment Trust Root Rotation v1\0`. GitHub OIDC/artifact attestations may accompany these signatures but cannot replace them.

The publication workflow has the only release-publication credential. It runs `tests/validate_windows_release_evidence.py`, verifies the externally pinned trust-root digest, key validity/revocation/role, all host signatures, aggregate offline signature, candidate/workflow digests, and complete matrices. The protected environment receives the exact validator output/candidate digest; no other workflow/job can publish a native-containment release. Branch/environment protection and the offline signature are both required.

Unsigned prose, screenshots, hand-edited checklists, feature-001 gate statements, fake-executor-only output, and on-demand optional quickstarts are not release evidence.

Validator checks:

- closed bundle schema;
- candidate/manifest/harness exact match;
- architecture/build/payload coherence;
- complete clean/upgrade set;
- matrix names/counters/thresholds/verdicts;
- artifact digest existence and consistency;
- valid nonrevoked role-correct x64/ARM64 TPM RSA-PSS signatures and distinct offline Ed25519 aggregate signature from the Store/prior-release-pinned trust root;
- externally pinned trust-root digest, key role/validity/revocation, exact workflow/environment identity, and aggregate offline signature;
- no stale evidence from prior candidate/dependency/policy.

Publication job cannot be manually waived. Changing trust root, workflow identity, environment, keys, or validator policy requires dual-signed root rotation, contract-epoch change, and security review.

## Supersession

This contract supersedes all feature-001 and product/workflow text that says real-host MXC validation is optional, on-demand, informational, or non-gating. Historical documents remain readable but receive a clear feature-003 supersession notice; release automation enforces this contract.

## Owner comprehension evidence

Before release, blocked-run message study shows at least 9 of 10 non-technical owners can state:

1. employee work did not run;
2. which prerequisite failed;
3. the one displayed recovery action.

Warning-message study separately shows at least 9 of 10 can state that an MXC leak was observed, work continues because no explicit owner deny matches it, and the displayed mitigation is optional. Study material uses only safe synthetic cases and no sensitive command/policy data.
