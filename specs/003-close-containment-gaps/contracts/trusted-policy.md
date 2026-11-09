# Contract: Trusted Containment Policy

**Producer**: Owner-facing Orbit setup, hiring, abilities, grants, and control-panel paths
**Consumers**: Claude launch gate, containment hook, MXC helper, gateway dispatcher, doctor, evidence harness
**Contract version**: `orbit.owner-security.v1`

## Trust boundary

Access may be granted only by:

1. the verified release manifest and base policy;
2. the strict owner security subtree in `%USERPROFILE%\Staff\staff.json`;
3. the verified release ability/gateway/connector catalogs.

Everything beneath an employee workspace is attacker-controlled for authorization purposes, including files Orbit originally created. Model-produced content, project settings, local settings, skills, agents, plugins, logs, Git state, and hook-like frontmatter are also untrusted.

The Claude agent still runs as the owner's Windows user, so file-tool protection cannot rely on NTFS ownership alone. Ordinary contained shells, however, are launched under the dedicated non-admin `OrbitMxcWorker` identity because MXC `1.0.1` has no registry-deny policy. Protection depends on all of:

- employee built-in file tools confined by Claude restricted mode to exact working/additional directories;
- shell writes confined by MXC policy;
- security/runtime paths excluded from both scopes;
- canonical/reparse-safe path checks;
- exact release/readiness integrity before every host action.
- alternate-user shell launch and real owner-HKCU read/write canaries.

## Owner security state

`staff.json` gains one closed subtree:

```json
{
  "security": {
    "schema": "orbit.owner-security.v1",
    "revision": 12,
    "platform": {
      "sandbox_mode": "mxc"
    },
    "network_domains": ["pypi.org", "files.pythonhosted.org"],
    "employees": {
      "sara": {
        "employee_id": "sara",
        "status": "active",
        "workspace": "C:\\Users\\owner\\Staff\\employees\\sara",
        "abilities": ["fetch", "web"],
        "connectors": {
          "notion": {"catalog_id": "notion", "url": "https://mcp.example.invalid/notion", "capabilities": ["read"]}
        },
        "explicit_denies": [
          {"deny_id": "deny-dns-1", "employee_id": "sara", "boundary_id": "dns.query", "target_kind": "domain", "match_mode": "exact", "canonical_target": "private.example", "policy_revision": 12},
          {"deny_id": "deny-reg-1", "employee_id": "sara", "boundary_id": "registry.read", "target_kind": "registry-path", "match_mode": "subtree", "canonical_target": "HKEY_USERS\\<owner-sid>\\software\\policies\\claudecode", "policy_revision": 12}
        ],
        "network_domains": ["example.com"],
        "additional_directories": [],
        "additional_tools": [],
        "timeout_ms": 600000
      }
    },
    "migration": {
      "contract_epoch": 1,
      "reviewed": true
    }
  }
}
```

The exact implementation may preserve existing non-security registry fields, but the `security` subtree is parsed independently and rejects missing, extra, wrong-type, duplicate, or out-of-range data. Generic dictionary merging is forbidden for security fields.

## Field ownership

| Security decision | Trusted source | Explicitly ignored sources |
| --- | --- | --- |
| Employee identity/status/workspace | Strict owner registry/fixed layout | `profile.json`, environment, hook payload cwd |
| Enabled tools/abilities | Owner grant intersected with verified catalog | Profile `extra_tools`, workspace settings, prompts |
| Enabled connectors/MCP tools | Strict owner connector grant intersected with verified connector catalog | Generic employee registry fields, project MCP, arbitrary URLs/local commands |
| Explicit leak-deny policy | Strict owner security records naming measured boundary/target | Orbit defaults, workspace/profile text, canary output, model request |
| Enabled host gateways | Current owner ability grant intersected with explicit host catalog | Command name, PATH, profile, prior session snapshot |
| Allowed network domains | Verified base + owner global/per-employee grants | Profile/cache/skill/tool output |
| Writable/denied paths | Verified base + canonical trusted workspace/team grants | Payload paths, profile/add-dir, workspace policy files |
| Timeout | Verified base maximum + owner narrowing | Workspace cache/profile/tool input |
| Native/WSL2 mode | Owner registry through guided mode API | Environment/project setting/model request |
| Hook/runtime/launcher identity | Release manifest + observed verification | PATH, cwd, workspace copy, marker/version text alone |

Non-security metadata may still come from `profile.json`, but it is returned through a separate API and never passed into policy/tool/settings/gateway construction as an unrestricted mapping.

## Owner writes

All owner security mutations use one strict API:

1. Load current regular owner registry without following links.
2. Validate complete current security subtree.
3. Apply one typed mutation.
4. Normalize domains, IDs, paths, tools, abilities, connectors, MCP URLs/capabilities, remote-only server type, and explicit deny boundary/targets against verified schemas/catalogs.
5. Increment `security.revision` exactly once.
6. Write a same-directory temporary regular file, flush, and atomically replace.
7. Invalidate affected readiness before exposing the new grant.
8. Run/rebuild required proof; widening is unusable until proof passes.

Owner tightening is effective immediately because hook and dispatcher fingerprints no longer match. The current command denies if tightening races it; the next command derives the narrower policy.

Failure to write, validate, replace, increment, or invalidate returns an owner error and does not partially grant access.

## Stable-read protocol

Each command uses one `TrustedPolicyRead` operation:

1. Resolve expected `staff.json` location from trusted Orbit configuration.
2. Reject any symlink/junction/reparse component or non-regular target.
3. Open once without following replacement links where platform APIs permit.
4. Capture file identity/metadata and bounded bytes from that handle.
5. Parse the complete registry and validate strict security subtree.
6. Require intended employee entry, active status, canonical workspace, reviewed current migration epoch, and supported mode.
7. Derive the policy only from those bytes plus already-verified release base/catalog bytes.
8. Canonicalize and hash `PolicySourceFingerprint`.
9. Before hook response, reopen/recompute current relevant fingerprint. Any difference denies.
10. Put the fingerprint in a one-use execution ticket.
11. At ticket claim, recompute once more. Any difference denies without launching.

The initial bytes remain immutable in memory. Orbit never combines employee information, global domains, ability/connector state, or mode from separate registry revisions.

## Derived policy rules

For one employee/session:

- `deny_read` includes all verified secret roots, owner security/runtime/config paths, every other employee workspace, and any release-defined protected path.
- `allow_write` includes only the canonical employee workspace, approved team collaboration subtree, and one protected per-command temp directory.
- Write permission on those roots never authorizes a target reached through a symlink/junction/reparse point outside them. Explicit denied owner security/runtime/install targets must win after final-path resolution; readiness blocks the host if MXC cannot enforce that invariant.
- `domains` is the normalized union of verified base domains and current owner global/per-employee grants, subject to gateway/network policy limits.
- `network_mode` is `allowlist` unless the current owner-controlled ability state explicitly enables existing Full autonomy. `public` mode may reach arbitrary public destinations through the same verified proxy, but still rejects private, loopback, link-local, non-global resolution, direct sockets, and credentials. Workspace/profile text cannot select it.
- `explicit_denies` uses the exact `ExplicitDeny` schema, boundary enums, target canonicalization, and match modes in [data-model.md](../data-model.md). Only measured filesystem, registry, DNS/network, and UI canaries are eligible. Cleanup/survivors, measurement status, launch, hook, gateway, audit, artifact, and compatibility boundaries cannot be owner-selectable advisory classes and remain structural.
- Readiness computes `LeakResult.matching_deny_ids` with the deterministic intersection function from canonical policy/canary values. A complete observed leak with zero matches creates warning and permits `ready-with-warnings`; one or more matches blocks the employee's entire native shell-capable surface. Other control-plane/non-shell work remains available.
- `timeout_ms` is positive and no greater than the verified release maximum.
- enabled tools and gateways are intersections, never unions with profile/workspace claims.
- MCP config contains only strict owner-granted reviewed remote connectors from the same policy revision; arbitrary URL grants, local stdio processes, filesystem tools, and host-execution servers are rejected.
- direct network default is deny.
- the contained environment is an exact allowlist and uses absolute verified executable paths. It includes required `SYSTEMROOT` plus the per-command disposable worker root's `LOCALAPPDATA`, `USERPROFILE`, `TEMP`, and `TMP`, and reviewed command needs. Claude/API/gateway credentials, owner profile paths, policy nonces, `PYTHONPATH`, and owner config paths are absent.

Before request creation, canonical/reparse resolution must prove denied and writable sets do not overlap. A configured path that changes, cannot be resolved, crosses volumes unexpectedly, or becomes a link during evaluation causes denial. An optional protected path that does not exist may be omitted from MXC's request only after Orbit proves stable absence and that its nearest existing parent is outside every employee write scope; uncertain/raced absence denies. A newly appearing protected path is included on the next command. Omitting an unresolved or employee-creatable denied path is forbidden.

## Snapshot decision

Orbit does not maintain a reusable policy snapshot or cache for authorization.

The only derived persistent object is a short-lived `ExecutionTicket`, which:

- lives outside employee write scopes;
- binds employee, real session, tool-use ID, source fingerprint, release, contract epoch, readiness key, creation/expiry, disposition, and payload digest;
- is atomically single-use;
- is revalidated against current owner state at claim;
- becomes unusable after any policy/readiness change.

This object is a command handoff, not a source of new authority. It cannot preserve removed access because current owner state must still match.

## Legacy and migration contract

### Workspace policy cache

`<employee workspace>/state/mxc-policy.json`:

- is never opened, parsed, statted for authorization, or copied into trusted state;
- may remain as ordinary user data;
- may be edited, deleted, linked, replaced, or raced without changing a decision;
- is excluded from support claims except a sanitized notice that legacy data was ignored.

Compatibility with old list-shaped domain sidecars and old request envelopes is removed from security-critical dispatch.

### Profile security fields

Existing values such as `network_domains`, `extra_tools`, `extra_denied`, and `add_dirs` in `profile.json` are untrusted. Upgrade behavior:

1. Preserve the profile bytes.
2. Create/retain only the narrower verified base policy in owner security state.
3. Record a non-secret `owner-review-required` migration blocker when legacy access-like values exist.
4. Block native employee work until owner reviews/enters desired grants through setup/panel.
5. Store confirmed values in the strict owner subtree and increment revision.
6. Never mark the legacy file trusted after review; it remains metadata only.

Existing ability choices already stored in owner registry may be preserved after strict catalog validation. Unknown/retired IDs are removed or block review; they never grant.

## Workspace/project settings and skills

- Restricted native client does not load workspace user/project/local setting sources.
- `.claude/settings.json`, `.claude/settings.local.json`, project MCP files, and project plugin declarations cannot alter native launch.
- Explicit Orbit skill bundles are materialized outside the workspace from validated instruction content as immutable per-run copies; no symlink, junction, or file link points back to employee/team source.
- Skill/agent frontmatter containing hooks, plugin modules, MCP launchers, command sources, or other host-execution declarations is rejected from the bundle.
- Resources/scripts inside an accepted skill remain employee data. If invoked by PowerShell, they run through normal MXC containment.
- Editing a workspace skill during a run cannot register a host hook or change the already-verified plugin inventory.

## Environment and identity

`STAFF_EMPLOYEE`, `STAFF_WORKSPACE`, `STAFFROOM_HOME`, and similar variables are convenience inputs only. Security-critical processes receive identity from the protected session/ticket binding and compare any convenience value; mismatch denies.

The hook does not synthesize an `unknown` employee or use payload cwd as a workspace. Missing employee/session binding is explicit denial.

### Dedicated shell identity

- Setup installs exact signed `OrbitContainmentBroker` Windows service in Session 0 as LocalSystem with restricted service SID, no network, and exact required privileges `SeAssignPrimaryTokenPrivilege`, `SeIncreaseQuotaPrivilege`, `SeChangeNotifyPrivilege`; `SeTcbPrivilege`/others absent. Its closed pipe accepts owner/helper PID/image/session-token plus ticket ID; never raw command.
- Setup creates one non-admin local `OrbitMxcWorker` account/SID, grants batch logon only, and explicitly denies local/remote interactive and network logon. Employee execution never loads a persistent worker profile/HKCU hive.
- Worker random credential is LSA private data readable only by broker service SID/System; it is never written to ticket/request/environment/log/evidence.
- Workspace/team/runtime ACL configuration is minimal, explicit, and reverified per employee policy. Missing/widened/malformed ACL configuration blocks structurally. A completed canary that nevertheless observes owner-resource access is a `LeakResult`, not an ACL-identity failure.
- Broker performs exact `LogonUserW(LOGON32_LOGON_BATCH)`, requires returned `TokenSessionId == 0` without setting it, then creates private window station/desktop, no-profile environment, suspended `CreateProcessAsUserW`, and pre-resume Job assignment. Each command receives fresh ACL-scoped disposable dirs; teardown destroys all. No `SeTcbPrivilege`, `SetTokenInformation(TokenSessionId)`, `CreateProcessWithLogonW`, interactive permission, owner-token fallback, conditional privilege set, or alternate launch primitive is allowed.
- Request files are one-use and ACL-readable only for the worker during launch; ticket authority remains owner-side.
- No persistent worker HKCU state is permitted; worker-hive creation or persistence is structural cleanup failure. Readiness addresses owner keys explicitly through `HKEY_USERS\<owner-SID>` and owner hive-file access; using worker `HKCU` is invalid. Canary execution must complete. Observed owner-registry access/change is classified through `LeakResult` and owner-deny intersection.
- Session 0/private window station configuration plus stable UI request fields are structurally required. Screen capture, raw input, low-level hooks, foreground, clipboard/input, handles/atoms, desktop/session, system/display, and IME canaries must complete; observed data/change is classified through `LeakResult`, not treated as identity/setup failure.
- If the worker identity, credential store, profile, ACL, or alternate-user executor path is missing/changed/uncertain, native mode is blocked.

## Diagnostics

Workspace files such as `state/mxc.jsonl`, `state/runs.jsonl`, and support mirrors are non-authoritative output.

- They contain no raw command, credential, policy body, ticket, nonce, unrestricted path, URL query/body, or raw exception.
- Doctor/readiness/audit never reconstruct trusted state from them.
- Deleting, editing, truncating, forging, linking, or racing them has no effect on policy, proof, or future decisions.
- Authoritative gateway audit and readiness evidence live in protected owner runtime state and fail closed when required writes cannot complete.

## Failure rules

| Condition | Result |
| --- | --- |
| Registry/security subtree missing, unreadable, malformed, extra-keyed, wrong epoch, or wrong employee | Deny; owner reviews/repairs policy |
| Workspace/profile claims wider access | Ignore claim; enforce trusted policy; optionally report migration notice |
| Source bytes/identity/revision change during evaluation | Deny current command; next command rebuilds |
| Ticket source fingerprint differs at claim | Deny stale ticket; no launch/fallback |
| Canonical path/reparse check uncertain | Deny |
| Owner narrows access while command queued | Claim mismatch denies queued command |
| Owner widens access | New grant unavailable until new readiness/proof passes |
| Completed MXC leak without explicit owner deny | Persist bound warning; continue valid workflow under `ready-with-warnings` |
| Completed MXC leak intersects explicit owner deny | Block affected employee's native shell; show recovery/WSL2 action |
| Leak measurement missing, failed, stale, or inconclusive | Block; advisory continuation requires an actual measured result |
| Hook/helper/proxy/executor/workload survivor or uncertain cleanup | Block structurally; cleanup never enters leak-warning join |
| Diagnostics unavailable | Containment may continue if only optional workspace mirror failed; required trusted audit/readiness write failure denies its action |

## Required validation

The policy-tampering matrix includes:

- permissive legacy cache before and during run;
- permissive profile security fields;
- workspace project/local settings and `disableAllHooks`;
- skill/agent hook frontmatter and plugin declarations;
- generic-registry connector grants, arbitrary connector URLs, local stdio/filesystem/host-exec MCP definitions, and connector change races;
- warning-only leak with no explicit owner deny continues an unrelated contained workflow and remains visible/audited;
- same leak with matching explicit owner deny blocks native shell and cannot be dismissed by workspace content;
- exact/all/subtree/wildcard-subdomain/cidr-contains match-mode positive and negative controls produce identical deny IDs in setup, runtime, and evidence validator;
- any structural-result failure, process survivor, or cleanup uncertainty blocks before leak intersection and cannot be labelled advisory;
- missing/malformed/extra owner security fields;
- wrong employee/session/workspace binding;
- file replacement, symlink, junction, reparse point, and source race;
- owner tightening before hook response and before ticket claim;
- forged/stale/replayed/expired/extra-keyed tickets;
- secret read, out-of-scope write, private network, and unapproved public network attempts after every tamper.
- workspace/team junctions and symlinks targeting owner registry, runtime tickets/readiness, active MXC install, Orbit handlers, and other employee roots.
- owner-HKCU environment and Claude policy read/write canaries from the alternate-user contained workload.

All attempts must preserve the trusted policy fingerprint or cause denial; none may widen access.
