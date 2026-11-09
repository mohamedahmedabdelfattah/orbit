# Contract: Exact MXC Runtime, Schema, Windows Host, and Request

**Producer**: Orbit release manifest, Windows installer, request builder, proxy/helper, and readiness service
**Consumer**: Microsoft `wxc-exec.exe` one-shot and request-aware probe interfaces
**Scope**: Native Windows mode `mxc`
**Contract version**: `orbit.mxc-runtime.v1`

## Immutable reviewed baseline

These are security inputs, not examples or compatible ranges.

| Contract | Exact value |
| --- | --- |
| Claude Code capability floor | `2.1.295`; exact installed version still needs behavior proof |
| MXC repository release | `microsoft/mxc` tag `v1.0.1` |
| MXC commit | `fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2` |
| npm package | `@microsoft/mxc-sdk` `1.0.1` |
| Package URL | `https://registry.npmjs.org/@microsoft/mxc-sdk/-/mxc-sdk-1.0.1.tgz` |
| Package SHA-256 | `416D9607C9D4652395D95C3D9C5F5605F1F2F845DA1A63228BEE41B7392CEF49` |
| Package npm integrity | `sha512-2cP925G5+lQyKzjBVha8uNtVd7XESgDBtgi1yCYYSo9M3xiFyZWtCO4SWPGTk509rdI6nqjyGcZxvEP3t6l8Hg==` |
| Stable schema | `schemas/stable/mxc-config.schema.1.0.0.json` |
| Schema source | Pinned raw bytes at commit `fda29ac63bc306b7f97f3b86b4b63d44f7f40cf2` |
| Schema SHA-256 | `207254FA94966A800FA70F01A2DA73AE813D27FE8847200C92F4DD0E219649C2` |
| Runtime JSON contract | Exact stable `1.0.0` |
| Schema validator | Python `jsonschema` `4.25.1`, `Draft7Validator`, locked wheel SHA-256 `3FBA0169E345C7175110351D456342C364814CFCF3B964BA4587F22915230A63`, complete transitive hash lock |
| Authenticode publisher | Valid Windows trust; signer organization `Microsoft Corporation` |
| File/product version | `1.0.1` / `1.0.1+fda29ac6` for reviewed MXC binaries |

### Architecture payloads

| Architecture | PE machine | Artifact | SHA-256 |
| --- | --- | --- | --- |
| x64 | `IMAGE_FILE_MACHINE_AMD64` (`0x8664`) | `package/bin/x64/wxc-exec.exe` | `090F5D1F7BB93104AB08DCD4E8034EF954AEEFCDAF6658DDE5F7DFF4CFC12F3A` |
| ARM64 | `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) | `package/bin/arm64/wxc-exec.exe` | `91AA4171E8809F33F19622C381116188EAB7D8C8CFFAD231230A31B58146EE77` |
| x64 | `IMAGE_FILE_MACHINE_AMD64` (`0x8664`) | `package/bin/x64/wxc-host-prep.exe` | `C18783AD3DD62C0A54530B25192B7C4015706B3F518CD9619259AE9750D4AB6E` |
| ARM64 | `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) | `package/bin/arm64/wxc-host-prep.exe` | `74CCAE215A9C5E81215BC7124AA31CDD7A0B2215A79B5CF8865865BBDAAF93E2` |

### Conditional package companions

| Feature | Companion | x64 SHA-256 | ARM64 SHA-256 | Decision |
| --- | --- | --- | --- | --- |
| Guarded-WPR/certain audit paths | `plm.exe` | `BEFFC9C9AB974CA9E7455089FD8ECB36EB8C92811DDD1705DB91370A689692C3` | `8818982C6B91C78D9198DC03D5EFC8A9A34A1075AFB4A6A3E9F1A750C5462532` | Employee work never uses audit; `orbit doctor --audit` stays disabled unless companion and protected install are separately verified |
| Legacy AppContainer proxy path | `winhttp-proxy-shim.exe` | `E855E609496EF9A3DCB678656A80090C157EF1244FB62E0F63A2CDF260F938B4` | `AF8AFB03ED4CB9AF57C9B4E702A29580315E68C93549C62DFB34F90AC6D3F388` | Accepted request must select BaseContainer, so this path is unreachable |
| Node/.NET in-process SDK | `mxc_ffi.dll` | Not used | Not used | Not installed for standalone executor contract |

A conditional feature is unavailable unless its complete companion contract passes. Absence never causes a less-contained fallback.

## Windows client support

Windows product name alone and broad numeric `>=` comparisons are invalid.

| Windows 11 branch | Minimum Process Isolation build |
| --- | ---: |
| 24H2 | `26100.9278` |
| 25H2 | `26200.9278` |
| 26H2 | `26300.9550` |
| 26H1 | `28000.2804` |

Readiness requires:

- Windows client/workstation SKU, not Windows Server;
- recognized branch from the table;
- full build and UBR at/above that branch's floor;
- native OS architecture exactly x64 or ARM64;
- selected payload PE machine matching OS architecture (not Python process/emulation architecture);
- exact request-aware runtime proof after build checks.

Unknown architecture, branch, SKU, unreadable UBR, or future build family is blocked until contract review. A numerically larger unknown build is not assumed compatible.

## Release manifest and active install

One closed release manifest contains every value above plus managed helper/relay/worker identities, Orbit handler/gateway identities, and every preinstalled absolute browser/media/OCR/tool dependency admitted to contained commands. Python and PowerShell read the same manifest; no contained tool installs or resolves a new runtime dependency on demand.

The active MXC directory is versioned and architecture-specific outside employee workspaces. Runtime never:

- searches `PATH`;
- trusts `version.txt`/`schema-version.txt` alone;
- accepts another `1.x` runtime/schema;
- maps unknown architecture to x64;
- follows a link/junction/reparse path;
- uses a previous active directory after repair begins.

Observed bytes, PE machine, signatures/publisher, versions, schema, and manifest decide identity.

## Transactional install/repair

`setup-windows.ps1` performs:

1. Mark native containment readiness blocked for install/repair.
2. Read/validate release manifest from verified Orbit source.
3. Read exact Windows client branch/build/UBR and OS architecture.
4. Reject unsupported SKU/build/architecture before download.
5. Download exact npm URL to a new stage.
6. Verify package SHA-256 and npm integrity where available.
7. Extract only selected architecture payloads needed by enabled contract.
8. Verify executor and host-prep exact SHA-256, PE machine, File/ProductVersion, Authenticode status, and Microsoft Corporation signer organization.
9. Obtain stable schema separately from release-vendored bytes or pinned commit URL; verify exact SHA-256. The npm tarball does not contain this schema file.
10. Install the hash-locked Draft 7 validator dependency set or verify the bundled lock.
11. Verify conditional companions or disable the dependent diagnostic feature.
12. Install/verify signed restricted `OrbitContainmentBroker` service and closed IPC; create non-admin `OrbitMxcWorker`, batch-only/deny-interactive-network policy, LSA credential, no-profile Session 0/private-desktop contract, and exact ACL template.
13. Run static artifact/schema self-tests in the stage.
14. Atomically activate the complete versioned stage.
15. Run the shared alternate-user readiness proof; only a full pass may create `ready` state.

Any failure removes/quarantines the incomplete stage, leaves readiness blocked, and never reports the old install as repaired. Existing team data is outside this transaction and remains unchanged.

An already-installed runtime takes the same observed verification path; a marker plus generic valid signature is insufficient.

## Host-prep contract

`wxc-host-prep.exe` is a verified companion with administrator-required manifest. Its `prepare-system-drive` and per-boot `prepare-null-device` operations are for AppContainer+DACL Tier 3.

Orbit's reviewed identity-less proxy request requires BaseContainer/PSEC, keeps `fallback.allowDaclMutation: false`, and is accepted only when probe reports:

```text
tier == "base-container"
needsDaclAugmentation == false
```

Therefore:

- setup installs/verifies host-prep identity;
- normal employee readiness does not run it unconditionally or request elevation;
- a probe selecting/requiring Tier 3 is blocked, not repaired into a weaker employee request;
- any future Tier-3 support needs a new contract review, elevated preparation, per-boot null-device verification, and a compatible network design.

## Exact request contract

Every emitted document declares exact `version: "1.0.0"`. One-shot employee requests omit lifecycle `phase` and `sandboxId`. Unknown/retired/experimental fields fail Draft 7 validation.

### Base request

Orbit constructs a closed one-shot request from the current trusted policy. It includes only reviewed fields:

```json
{
  "version": "1.0.0",
  "containment": "processcontainer",
  "lifecycle": {
    "destroyOnExit": true,
    "preservePolicy": false
  },
  "process": {
    "commandLine": "\"<absolute verified WindowsPowerShell\\v1.0\\powershell.exe>\" -NoLogo -NoProfile -NonInteractive -Command <exact workload>",
    "cwd": "<trusted canonical workspace>",
    "env": [
      "SYSTEMROOT=<verified Windows root>",
      "LOCALAPPDATA=<per-command disposable worker local app data>",
      "USERPROFILE=<per-command disposable worker profile root>",
      "TEMP=<per-command temp>",
      "TMP=<per-command temp>",
      "<other individually reviewed non-secret entries>"
    ],
    "inheritDefaultEnv": false,
    "timeout": 600000
  },
  "filesystem": {
    "readwritePaths": ["<workspace>", "<approved team subtree>", "<command temp>"],
    "readonlyPaths": ["<exact manifest-listed executable/runtime/dependency paths>"],
    "deniedPaths": ["<verified existing protected paths>"]
  },
  "network": {
    "egress": { "default": "deny" },
    "ingress": { "default": "deny", "hostLoopback": "deny" }
  },
  "ui": {
    "disable": false,
    "clipboard": "none",
    "injection": false
  },
  "processContainer": {
    "ui": {
      "isolation": "container",
      "desktopSystemControl": false,
      "systemSettings": "none",
      "ime": false
    }
  },
  "telemetry": { "enabled": false },
  "fallback": { "allowDaclMutation": false }
}
```

The original command lives only in protected ticket/request content and MXC `process.commandLine`. It is never a trailing executor override or host fallback.

### Final proxy wire request

Immediately before probe/one-shot launch, the trusted helper starts Orbit's per-command proxy and creates a fresh final request copy:

```json
{
  "version": "1.0.0",
  "containment": "processcontainer",
  "lifecycle": {
    "destroyOnExit": true,
    "preservePolicy": false
  },
  "process": {
    "commandLine": "\"<absolute verified WindowsPowerShell\\v1.0\\powershell.exe>\" -NoLogo -NoProfile -NonInteractive -Command <exact workload>",
    "cwd": "<trusted canonical workspace>",
    "env": [
      "SYSTEMROOT=<verified Windows root>",
      "LOCALAPPDATA=<per-command disposable worker local app data>",
      "USERPROFILE=<per-command disposable worker profile root>",
      "TEMP=<per-command temp>",
      "TMP=<per-command temp>",
      "HTTP_PROXY=http://127.0.0.1:<port>",
      "HTTPS_PROXY=http://127.0.0.1:<port>",
      "NO_PROXY=",
      "no_proxy="
    ],
    "inheritDefaultEnv": false,
    "timeout": 600000
  },
  "filesystem": {
    "readwritePaths": ["<workspace>", "<approved team subtree>", "<command temp>"],
    "readonlyPaths": ["<exact manifest-listed executable/runtime/dependency paths>"],
    "deniedPaths": ["<verified protected paths>"]
  },
  "network": {
    "egress": { "default": "deny" },
    "ingress": { "default": "allow", "hostLoopback": "allow" }
  },
  "runtimeConfig": {
    "networkProxy": "http://127.0.0.1:<port>"
  },
  "ui": {
    "disable": false,
    "clipboard": "none",
    "injection": false
  },
  "processContainer": {
    "ui": {
      "isolation": "container",
      "desktopSystemControl": false,
      "systemSettings": "none",
      "ime": false
    }
  },
  "telemetry": { "enabled": false },
  "fallback": { "allowDaclMutation": false }
}
```

The current unneeded `processContainer.capabilities: ["internetClient"]` is removed. It belongs to a broader direct-internet posture and is not part of Microsoft's documented proxy-client model. The explicit UI fields are the strongest stable-1.0.0 noninteractive-PowerShell posture: no clipboard, input injection, cross-job handles/global atoms, desktop/session control, system/display setting changes, or IME loading. Failure to parse/start the exact request blocks because no contained workflow exists. A measured UI enforcement leak after successful launch becomes advisory unless it intersects an explicit owner deny.

`processContainer.leastPrivilege` is deliberately omitted/false. MXC `1.0.1` does not support LPAC on the required BaseContainer tier; setting it would force an incompatible AppContainer/DACL fallback while `allowDaclMutation` is false. Registry/owner isolation comes from the dedicated no-profile worker identity and Session 0 broker launch, not an unsatisfiable LPAC flag. Tests assert the field is absent and probe still selects `base-container`.

Volume-root readonly entries are forbidden as dependency shorthand. The release manifest enumerates the exact PowerShell, Python/helper, system runtime, certificate, and command dependency paths needed by the validated workload class; request-aware and functional proof must establish them. An unlisted dependency causes denial and contract review rather than a drive-wide readonly grant.

The final wire document is written to a unique protected file, validated again, and never accepted from an employee/legacy sidecar. Proxy destination policy comes from the ticket's bound trusted policy.

## Schema validation

For both base and final documents:

1. Verify schema file hash before loading.
2. Using only release-owned/standard-library code, verify installed `jsonschema` and transitive files against the lock before importing validator code.
3. Load only the verified in-memory schema with remote reference/network resolution disabled.
4. Run `Draft7Validator.check_schema()` on the vendored schema during setup/readiness.
5. Run `Draft7Validator.validate()` on request object before serialization.
6. Serialize canonically to the protected request file.
7. Parse those exact serialized bytes and validate again immediately before external use.
8. Run the request-aware executor probe for semantic/backend compatibility.

Validation errors are mapped to closed non-secret blocker codes. Raw command, policy values, and unrestricted paths are not printed.

## Request-aware probe

Canonical readiness form:

```text
<absolute verified wxc-exec.exe> <final-request.json> --probe
```

No-request `wxc-exec.exe --probe` is discovery/recovery information only. It cannot set ready state.

A request-aware probe passes only when:

- process started and exited zero;
- stdout is one valid bounded probe JSON document;
- `error` is absent/null;
- `tier` is exactly `base-container`;
- `needsDaclAugmentation` is exactly false;
- BaseContainer API is present so the exact request can launch;
- denied-path, identity-less proxy, ingress/host-loopback, and every UI capability flag are captured and bound to canary results;
- every runtime warning is captured, classified, and shown.

Probe exit zero alone is not success: tier-selection failures may serialize an `error` and still exit zero. A false enforcement-capability bit is a measured warning candidate, not automatically a readiness blocker; explicit owner-deny intersection decides blocking after real canaries run.

The CLI runs orphaned-DACL recovery before its probe arm. This bounded repair side effect is recorded; it does not launch the workload and is not treated as proof.

## One-shot execution

Canonical employee form, launched only by signed `OrbitContainmentBroker` under exact batch-logon `OrbitMxcWorker` token in Session 0/private per-command window station/desktop:

```text
<absolute verified wxc-exec.exe> <final-request.json>
```

Orbit never uses:

- trailing `-- <COMMAND>` override;
- `--audit` for employee/model work;
- telemetry/debug flags for ordinary work;
- another executor from `PATH`;
- retry of original command on the host.

The helper rechecks ticket, policy/readiness, artifacts/schema, proxy ownership, and final request before this launch.

Owner helper sends only ticket ID/session authenticator over `\\.\pipe\OrbitContainmentBrokerV1`. Broker verifies exact service privilege set `{SeAssignPrimaryTokenPrivilege, SeIncreaseQuotaPrivilege, SeChangeNotifyPrivilege}` with `SeTcbPrivilege` absent, pipe/client/ticket/readiness, retrieves LSA credential, calls `LogonUserW(LOGON32_LOGON_BATCH)`, and requires worker SID/non-elevation/`TokenSessionId == 0` as returned. It never sets token session ID. It creates private window station/desktop and disposable dirs, exact environment, then `CreateProcessAsUserW` with `CREATE_SUSPENDED|CREATE_UNICODE_ENVIRONMENT|CREATE_NO_WINDOW`, assigning outer Job before resume. Any mismatch/failure denies. It never uses `SetTokenInformation(TokenSessionId)`, `CreateProcessWithLogonW`, worker hive, interactive logon, conditional privilege set, or owner-token fallback.

## Proxy acceptance

The reviewed baseline uses MXC's identity-less loopback proxy form. Microsoft describes it as the weakest, development/testing-oriented proxy deployment because Windows cannot bind the endpoint to one named proxy peer and host loopback is bidirectional.

Orbit accepts it for a release only if real-host proof on each architecture demonstrates:

- approved HTTP and HTTPS reach only the intended public host through Orbit's proxy;
- direct public sockets fail;
- unapproved public destinations fail;
- private/link-local/loopback destinations through proxy fail;
- direct private destinations fail;
- every other host-loopback listener is unreachable;
- stopped/replaced/raced proxy fails without direct fallback;
- DNS rebinding/private resolution is rejected by proxy.
- a unique unapproved hostname aimed at an authoritative DNS canary produces no DNS query outside the Orbit proxy path.

Every probe must complete. A measured DNS, direct-socket, private-network, loopback, or proxy leak is recorded and produces `ready-with-warnings` when no explicit owner deny intersects it. A matching owner deny blocks that employee's native shell. Missing/inconclusive probes, request rejection, or inability to launch remain blocking. An identity-scoped proxy or newer MXC may replace this design only under a new reviewed contract.

## Runtime workload proof

After request-aware probe, readiness uses the same ticket/helper/proxy/executor path as employee work:

### Functional compatibility

- Create, read, update, atomically rename, and delete markers inside approved workspace/temp.
- Approved HTTP and HTTPS through real proxy.

### Leak and enforcement canaries

- Attempt planted-secret read and record whether secret bytes appear.
- Attempt explicit `HKEY_USERS\<owner-SID>\Environment` / Claude policy and owner `NTUSER.DAT` access; record access/change and worker-hive persistence.
- Attempt outside and symlink/junction writes; record target changes.
- Attempt unapproved public, private/link-local/direct, second-loopback, and stopped/replaced proxy connections; record listener/connection effects.
- Resolve unique authoritative DNS canary outside proxy; record query receipt.
- Attempt clipboard/input, external handles/atoms, desktop/session/system/display/IME, screen capture, raw input, low-level hooks, and foreground control; record data/change.

### Structural cleanup gates

- Exceed process budget, normal-root exit with background descendant, and hard helper/executor kill; enumerate every descendant/marker.
- Any hook/helper/proxy/executor/workload survivor, missing PID evidence, or cleanup uncertainty is a structural blocker and never enters owner-deny matching.

Results are measured from side effects, external canaries, registry values, and process state, not denial-looking output. After every structural gate passes, only completed filesystem/registry/DNS/network/UI `LeakResult` records join with explicit owner denies: no intersection -> warning/continuation; intersection -> blocked native shell. Normal create/update/rename/delete incompatibility is a separate compatibility warning. Cleanup never becomes advisory.

## Process-tree contract

The signed broker service launches `wxc-exec` suspended under the dedicated low-privilege batch token and assigns the outer Job before resume. MXC then creates its workload suspended, assigns it to an inner kill-on-close Job Object before resume, terminates that job on timeout/normal teardown, and uses kill-on-close after hard launcher loss. Orbit's outer supervisor/broker owns helper, proxy, executor, token, private desktop/window station, and ephemeral directories and verifies alternate-user/session and nested-job compatibility.

Required release tests:

- normal root exit with background descendant;
- request timeout with child/grandchild;
- hard kill of helper;
- hard kill of executor;
- proxy shutdown/race;
- broker-service/privilege/IPC, worker batch-token/Session0/private-desktop/no-profile/ephemeral-root/ACL loss or substitution;
- no uniquely named hook/helper/proxy/executor/workload process or delayed marker after bounded deadline.

MXC's ordinary drain warning is not accepted as Orbit success when a survivor is observed or cleanup certainty is missing.

## Failure and recovery

| Blocker | Required state | One recovery action category |
| --- | --- | --- |
| Package/payload/schema/validator digest mismatch | Blocked | Run verified Windows repair |
| Signature invalid or publisher not Microsoft | Blocked | Restore official runtime through repair |
| Wrong/unknown architecture | Blocked | Install supported native package or use WSL2 |
| Unsupported client SKU/branch/build/UBR | Blocked | Install named Windows update or use WSL2 |
| Probe missing, nonzero, malformed, inconclusive, `error`, or no usable tier | Blocked | Update/repair prerequisite or use WSL2 |
| Schema validation failure | Blocked | Restore reviewed Orbit/runtime contract |
| Measured filesystem/registry/DNS/network/UI leak, no matching owner deny | Ready with warnings | Highlight limitation and optional WSL2/mitigation hint; continue workflows |
| Same measured leak intersects explicit owner deny | Blocked for affected employee native shell | Use WSL2 or change owner policy deliberately |
| In-scope create/update/rename/delete compatibility failure | Ready with warning | Highlight unsupported operation; continue unrelated workflows |
| Hook/helper/proxy/executor/workload survivor or cleanup uncertainty | Blocked | Stop native work and repair/update or use WSL2 |
| Worker/broker identity, IPC, token, launch, or measurement failure | Blocked | Repair dedicated shell boundary or use WSL2 |
| Conditional audit companion absent | Employee readiness unaffected; audit disabled | Restore companion before using audit |

Messages never expose request command, policy body, credentials, unrestricted paths, raw probe diagnostics, or raw exception. Doctor may include exact non-secret version/hash state and bounded reason code.

## Change policy

Any MXC runtime, package, schema, executable, host-prep, signer rule, validator, request field, proxy model, accepted tier, Windows branch table, or invocation change is a new security-contract review and contract epoch. No patch/minor compatibility is inferred.
