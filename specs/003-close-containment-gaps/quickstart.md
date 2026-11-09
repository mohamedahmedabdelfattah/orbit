# Validation Quickstart: Fail-Closed Native Windows Containment

**Feature**: `003-close-containment-gaps`
**Purpose**: Repeatable post-implementation validation guide; not implementation code
**Release status**: Every release section is gating

## Safety and prerequisites

- Use disposable/restorable Windows 11 client hosts, never Windows Server, for real MXC proof.
- Use synthetic employee homes, credentials, commands, domains, and markers. Never point the harness at an owner's real `%USERPROFILE%\Staff`.
- Real Claude proof needs controlled test authentication. Credentials stay in the protected host store and never enter evidence.
- Write output to a fresh protected evidence directory outside synthetic employee workspaces.
- A missing tool call, failed/inconclusive proof, harness timeout, cleanup uncertainty, or missing evidence is failure. The intentional workload-timeout canary must complete and prove zero survivors.

All development hosts need Python 3.9+ and the exact clean release-candidate checkout. Native release hosts additionally need:

- native Windows 11 client;
- native `x64` or `ARM64` architecture matching the evidence target;
- recognized servicing build at/above `26100.9278`, `26200.9278`, `26300.9550`, or `28000.2804`;
- Claude Code `2.1.295+`, signed in to a controlled test account;
- owner-approved elevation for HKLM policy helper, local worker/logon policy, ACL, Event Log, and machine trust-root installation;
- MXC installed only through the candidate's `setup-windows.ps1`;
- a known-clean snapshot for clean evidence and a pre-feature-003 snapshot for upgrade evidence.

## 1. Static and unit baseline

From repository root:

```powershell
python -m compileall -q core tests
python -m unittest tests.test_mxc -v
python -m unittest tests.test_windows_contract -v
python -m unittest tests.test_containment_readiness -v
python -m unittest tests.test_gateway_security -v
python -m unittest tests.test_upgrade_security -v
python -m unittest tests.test_platforms -v
```

Installer contract tests:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\SetupWindows.Tests.ps1
```

Expected:

- all modules parse; no `=======` marker remains;
- every critical handler uses exec form, explicit timeout, and `onFailure: "block"`;
- HKLM policy helper emits managed-only hooks for a valid Orbit nonce; API relay suppresses remote managed fetch with no direct fallback;
- `PowerShell` is the only shell; `Bash` is denied; `Monitor` is absent;
- every hook event returns one contained/gateway/denied disposition;
- workspace cache/profile/settings/skills/generic connector fields/HKCU policy never widen policy;
- no runtime or gateway lookup uses `PATH`;
- package/payload/schema/build/architecture mutations block;
- unknown/retired/experimental request fields fail;
- native Desktop employee surface is blocked;
- non-Windows settings/commands remain unchanged.

Fake-executor success is unit evidence only, never real-client or real-host evidence.

## 2. Native setup and doctor

On each disposable Windows host:

```powershell
$env:STAFFROOM_HOME = Join-Path $env:TEMP "orbit-containment-proof"
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\setup-windows.ps1 -Yes
python .\orbit doctor
```

Expected doctor report:

- exact Claude version/path hash and hook proof;
- exact HKLM document/policy-helper/emitted-policy receipt, relay/remote-fetch-skip receipt, source watchers, handler/tool/plugin/MCP proof;
- MXC `1.0.1`, schema `1.0.0`, validator, package/payload/host-prep identities;
- Microsoft Corporation signature/publisher and matching PE architecture;
- full Windows branch/build/UBR and dedicated worker SID/profile/credential/ACL state;
- final request-aware probe with `tier=base-container`, no error, no DACL augmentation;
- functional create/update/rename/delete results, filesystem/registry/DNS/UI/network leak classifications, and separate zero-survivor cleanup structural status;
- current employee policy/explicit-deny fingerprint and readiness key;
- `ready`, `ready-with-warnings`, or blockers; every warning says work continues absent matching owner deny and may include an optional hint; every blocker has one recovery action.

Employee work may start in `ready` or `ready-with-warnings`; it cannot start while blocked/proving.

Managed-policy/relay proof:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\managed-policy-proof.ps1 `
  -Output (Join-Path $env:TEMP "orbit-evidence-managed-policy")
```

Expected: HKLM path is absolute signed `orbit-policy-helper.exe`; Claude invokes it with zero args; valid `ORBIT_POLICY_SESSION_ID`/256-bit token plus authenticated `\\.\pipe\OrbitPolicyV1` yields exact managed receipt and token becomes unreplayable before prompt; absent Orbit vars yields `{}` with no `managedSettings`; bad/replayed token or wrong client image exits nonzero. Claude/helper/managed hook/fixed host PowerShell are enumerated trusted secret-bearing TCB; evaluator/parser/gateway target/broker workload/contained process receive explicit empty-base environments without policy/relay secrets. Dedicated Claude config root contains only enumerated auth/session/transcript entries and no settings/plugin/remote-policy cache; server fetch/cache skipped; lower file/HKCU settings ignored; foreign/merged source denied; helper/HKLM/config-root/relay mutation terminates session before another tool; relay failure never reconnects directly.

## 3. Hook failure matrix

Run through the real installed Claude client, not by calling the hook function directly:

```powershell
$evidence = Join-Path $env:TEMP "orbit-evidence-hook-x64"
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\hook-failure-matrix.ps1 `
  -Repetitions 100 `
  -Output $evidence
```

Use an architecture-specific output name on ARM64.

Required cases:

- normal rewrite and explicit denial;
- absent/disabled/mismatched hook and unsupported client;
- missing handler, spawn error, nonzero exit, crash;
- timeout, including immediately before valid output;
- empty, `{}`, plain, partial, malformed, array/string, and schema-invalid output;
- valid decision followed by failed exit;
- all documented common/PowerShell fields accepted; model timeout/background values replaced; missing/non-string/unknown-semantic fields denied;
- HKLM/helper/relay receipt mismatch, foreign managed source, source mutation, and direct-fallback attempt;
- containment-helper failure;
- hook/evaluator child and grandchild timeout cleanup.

Expected for every repetition:

- real `PowerShell` tool event and hook lifecycle receipt observed;
- zero host-marker commands execute;
- zero hook/supervisor/evaluator descendants survive;
- blocked result names a safe boundary and one recovery action;
- no raw command, credential, policy body, or unrestricted path enters output/evidence.

Failure to induce a real tool event is failure, not skipped success.

## 4. Policy-tampering matrix

```powershell
python -m unittest tests.test_containment_readiness.PolicyTampering -v
python -m unittest tests.test_containment_readiness.ExplicitDenyMatching -v
python -m unittest tests.test_mxc.TrustedPolicy -v
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\mxc-real-host-proof.ps1 `
  -Suite PolicyTampering `
  -Output (Join-Path $env:TEMP "orbit-evidence-policy")
```

Tamper cases include permissive/raced legacy cache; profile grants; generic-registry connector/MCP grants; arbitrary remote URL/local stdio/filesystem MCP; project/local/HKCU settings; skill/agent hooks; malformed owner state; wrong employee/session/workspace; symlink/junction/reparse/replacement races; owner tightening before response/claim; stale/replayed tickets; and forged workspace diagnostics.

For every case, first configure explicit owner denials and attempt secret read, out-of-scope write, private connection, and unapproved public connection. Then remove those explicit denies and rerun leakage canaries.

Expected: workspace tampering never changes trusted fingerprint or removes owner denies. A leaked boundary with matching owner deny blocks native shell; the same measured leak without matching deny yields visible/audited warning and unrelated contained work continues. No stale access survives tightening.

Matching fixtures cover every allowed pair: path exact/subtree, registry exact/subtree, domain exact/wildcard-subdomain (apex excluded), CIDR containment, endpoint exact, UI-capability exact, and boundary-wide `any/all`; cross-kind, regex/glob, malformed canonical targets, and wrong employee/boundary must reject or not match identically in setup, runtime, and evidence validator.

## 5. Gateway bypass corpus

```powershell
python -m unittest tests.test_gateway_security -v
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\mxc-real-host-proof.ps1 `
  -Suite Gateways `
  -Output (Join-Path $env:TEMP "orbit-evidence-gateways")
```

Expected:

- canonical current-authorized forms reach only verified dispatcher and intended target;
- final host set is exactly `staff-apify` and `staff-compute`; every other current `staff-*` command is contained or denied;
- every reclassified fetch/browser/watch/video/connectors/docs/skill valid form still works through real MXC using setup-pinned absolute dependencies; no runtime install or host fallback occurs;
- at least 50 bypass variants per host gateway are rejected/contained as contracted;
- chaining, pipeline, redirect, substitution, assignment, nested shell, alias, function, profile, path, extension, PATHEXT, case, Unicode, and link variants never reach host target;
- quoted literal metacharacters remain argument data and pass only intended validator;
- mid-flight ability disable wins;
- launcher/catalog/shared-module tamper or audit failure denies;
- Apify/compute target runs suspended with restricted-child process policy in `ActiveProcessLimit=1` Job; child-creation canary fails, target installs nothing, and uses no global/user-site package;
- compute uses in-process GitHub HTTPS APIs and never resolves/executes `gh`, `git`, PowerShell, cmd, or another executable;
- gateway credentials are absent from PowerShell, process arguments, output, and audit;
- approved and rejected gateway-like calls produce required non-secret audit records.

## 6. Exact-schema validation and artifact matrix

```powershell
python -m unittest tests.test_windows_contract.SchemaContract -v
python -m unittest tests.test_windows_contract.ArtifactContract -v
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\mxc-real-host-proof.ps1 `
  -Suite Contract `
  -Output (Join-Path $env:TEMP "orbit-evidence-contract")
```

Expected:

- package, selected x64/ARM64 payload, schema, validator, PE machine, versions, signature, and publisher match manifest;
- wrong architecture and every one-byte tamper block;
- base and final requests pass exact Draft 7 schema;
- missing/extra/retired/experimental/version-changed fields fail before use;
- request-aware argv is exact vendored executor + request + `--probe`;
- exit zero with non-null `error`, wrong/absent tier, or DACL augmentation fails; capability gaps and runtime warnings are captured for canary classification, not silently discarded;
- environment contains explicit worker `SYSTEMROOT`, `LOCALAPPDATA`, `USERPROFILE`, `TEMP`, and `TMP`; no inherited owner/provider secret; PowerShell path and readonly dependencies are absolute/manifest-listed;
- exact restrictive clipboard/injection/handle/atom/desktop/system-setting/IME request validates; capability bits are captured and real canaries decide enforced/advisory/owner-deny-breach classification;
- no-request probe never becomes readiness.

## 7. Real-host MXC positive, negative, and timeout cleanup

Run separately on native x64 and ARM64:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\mxc-real-host-proof.ps1 `
  -Suite All `
  -Output (Join-Path $env:TEMP "orbit-evidence-mxc")
```

Expected positives:

- in-scope file created, read, updated, atomically renamed, and deleted;
- approved HTTP and HTTPS use real Orbit proxy.

Expected measured canaries:

- planted-secret output/absence recorded;
- signed broker service has restricted SID, no network, exact privileges `{SeAssignPrimaryTokenPrivilege, SeIncreaseQuotaPrivilege, SeChangeNotifyPrivilege}` and no `SeTcbPrivilege`; worker batch token must already report Session 0, with no session-ID mutation; private desktop/no profile/suspended pre-Job launch passes; every alternate/fallback primitive is absent;
- owner-SID registry/hive, outside/junction writes, public/private/direct/loopback/relay/proxy-race connections, DNS rebinding/authoritative query, and UI/screen/raw-input/hook/foreground effects are recorded as enforced or leaked;

Expected structural cleanup results:

- timeout, normal-root background child, hard-killed helper/executor, proxy, workload, and delayed-marker checks all show zero survivors. Any survivor or uncertainty blocks; cleanup is never advisory.

Run side-channel harness explicitly:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\registry-dns-ui-proof.ps1 `
  -Output (Join-Path $env:TEMP "orbit-evidence-side-channels")
```

Run every filesystem/registry/DNS/network/UI leak in two policy modes. Without matching explicit owner deny, doctor displays warning and a harmless contained workflow succeeds. With matching owner deny, the employee's complete native shell-capable surface is blocked before work and WSL2/recovery action is shown. Rename/delete incompatibility is warned and unrelated workflows continue. Cleanup/survivor results are excluded from this dual-policy mode and must always pass.

## 8. Clean installation

On restored x64 host, then restored native ARM64 host:

1. Confirm no prior active Orbit/MXC install or synthetic Staff home.
2. Check out exact candidate commit.
3. Run setup and doctor.
4. Run sections 3–7.
5. Produce candidate-bound evidence with `install_scenario: clean`.

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\upgrade-proof.ps1 `
  -Scenario Clean `
  -Candidate (git rev-parse HEAD) `
  -Output (Join-Path $env:TEMP "orbit-release-clean")
```

Expected: work stays blocked until measurement/classification completes; then `ready` or `ready-with-warnings` permits one contained action. Explicit-owner-deny breach scenarios remain blocked.

## 9. Upgraded installation

On restored pre-feature-003 x64 host, then equivalent native ARM64 host:

1. Seed real legacy layout, employee/team data, and permissive legacy policy/profile/settings files.
2. Record team-data inventory/content digests.
3. Run the exact legacy `_key()` comparator against candidate `0.8.0-sec.<N>` and prove old in-app updater reports `newer == false`, even if the release is visible/latest.
4. From the separately verified bootstrap package, run the stop-the-world installer below.
5. Verify legacy service/task and every Claude/helper process stopped and machine blocked marker flushed before the first kit/source byte changed.
6. Verify scheduler/runs/native folder sessions block while panel/doctor work.
7. Verify legacy authorization is ignored.
8. Complete owner policy review and all proofs.
9. Run sections 3–7 and compare team-data digests.
10. Produce candidate-bound evidence with `install_scenario: upgrade`.

```powershell
$storeId = '<exact Store-assigned alphanumeric Product ID pinned before release; not the Package Identity Name>'
if ($storeId.StartsWith('<')) { throw 'Release Store ID was not populated; publication must be blocked.' }
winget install --id $storeId --version 1.0.0.0 --source msstore -e `
  --accept-package-agreements --accept-source-agreements

orbit-security-bootstrap.exe `
  --candidate <feature-003 candidate commit from Store-pinned manifest> `
  --output (Join-Path $env:TEMP "orbit-release-upgrade")

powershell -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File .\tests\windows\upgrade-proof.ps1 `
  -Scenario Upgrade `
  -Candidate (git rev-parse HEAD) `
  -Input (Join-Path $env:TEMP "orbit-release-upgrade")
```

Expected: exact Microsoft Store product/family/publisher/full-trust identity and embedded trust-root digest pass; unpackaged copy refuses; zero employee shell/gateway execution from before source mutation through readiness; legacy authority ignored; team data unchanged; explicit WSL2 fallback remains available. Running old `update.apply()` or a manual Git pull is a failed scenario.

## 10. Non-Windows regression

Run existing complete suites in native CI environments:

```bash
for t in test_core test_channels test_tools test_calls test_platforms test_mxc; do
  python3 -m unittest "tests.$t" || exit 1
done
```

Required environments: macOS, Linux, and Windows through WSL2.

Expected: existing `failIfUnavailable`, sandbox, gateway, service, and team-data behavior remain unchanged; no native readiness/hook/dispatcher appears; WSL2 never uses native exceptions.

## 11. Release evidence

Collect four bundles when both architectures ship:

- x64 clean;
- x64 upgrade;
- ARM64 clean;
- ARM64 upgrade.

```powershell
python .\tests\validate_windows_release_evidence.py `
  --candidate (git rev-parse HEAD) `
  --trust-root C:\ProgramData\Orbit\security\windows-evidence-trust-v1.json `
  --expected-trust-root-sha256 <digest embedded in signed bootstrap/prior release> `
  --require-architecture x64 `
  --require-architecture arm64 `
  --input <protected-evidence-root>
```

Expected final line:

```text
WINDOWS CONTAINMENT RELEASE EVIDENCE PASSED
```

Validator requires the Microsoft Store/prior-release-pinned `windows-evidence-trust-v1.json` digest; valid nonrevoked architecture-role TPM RSA-PSS-SHA256/MGF1-SHA256/salt32 signatures from native x64/ARM64 runners; distinct offline Ed25519 release-approver signature over aggregate index; exact RFC 8785 canonical bytes/domain strings/base64url encoding; exact repository/workflow digest/protected environment/publication job; exact candidate/manifest/harness; native SKU/build/architecture; clean and upgrade scenarios; exact dependencies; complete leak classifications and warning/continuation/owner-deny outcomes; zero hook/uncontained-host escapes; and team-data preservation. Candidate-provided keys or a generic “signature exists” result fail.

Missing native ARM64 evidence means ARM64 support is removed from that release and setup rejects ARM64. Emulation is not accepted.

## 12. Owner-message validation

Show safe synthetic blocked-run messages to ten non-technical owners. At least nine must identify:

- work did not run;
- failing prerequisite;
- displayed recovery action.

Messages exposing commands, credentials, policy contents, or sensitive paths fail regardless of score.

Show advisory-leak messages separately. At least nine of ten owners must identify that a leak was observed, work continues because no explicit owner deny matches it, and the displayed mitigation is optional.

## Release checklist

- [ ] Static/unit/installer tests pass.
- [ ] Hook failure matrix passes 100 repetitions per class.
- [ ] Policy-tampering matrix passes.
- [ ] HKLM policy-helper/relay source-selection and mutation-ordering matrix passes.
- [ ] Gateway bypass corpus passes >=50 variants per host gateway.
- [ ] Exact-schema validation and artifact tamper matrix pass.
- [ ] Real-host MXC filesystem/registry/DNS/network/UI leak canaries complete and every result is classified.
- [ ] Registry, authoritative DNS, and UI side-channel canaries complete on every architecture.
- [ ] Every advisory leak warns and allows an unrelated workflow; every matching explicit owner deny blocks native shell.
- [ ] Every hook/helper/proxy/executor/workload cleanup case has zero survivors; no cleanup failure is advisory.
- [ ] Clean installation passes on every shipped architecture.
- [ ] Upgraded installation passes on every shipped architecture with zero data loss.
- [ ] macOS/Linux/WSL2 regressions pass.
- [ ] Independent security review finds no workspace/hook-failure arbitrary-host path.
- [ ] Owner-message threshold passes.
- [ ] Release evidence validator passes Store/prior-release-pinned TPM RSA runner signatures, offline Ed25519 aggregate signature, canonical-byte contract, and exact publication workflow gate.

No evidence item is optional. Measured MXC leaks may be advisory, but their classification, warning, continuation test, and owner-deny test are mandatory.
