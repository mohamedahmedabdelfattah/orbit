# Contract: Fail-Closed Claude Code Containment Hook

**Producer**: Orbit native-Windows launch/settings generation and verified hook supervisor
**Consumer**: Claude Code `2.1.295+` command-hook pipeline
**Scope**: Native Windows with recorded mode `mxc` only
**Contract version**: `orbit.containment-hook.v1`

## Security outcome

Every shell-capable tool event ends as exactly one of:

1. rewritten to Orbit's verified MXC helper using one opaque contained ticket;
2. rewritten to Orbit's verified gateway dispatcher using one opaque gateway ticket;
3. explicitly denied.

No matched event succeeds with silence, `{}`, plain text, partial text, an unknown result, or the original command.

## Client launch contract

Before starting an employee run, Orbit verifies the exact Claude executable and then supplies:

- `--restricted`;
- `--setting-sources ""`;
- an owner-controlled, no-follow `CLAUDE_CONFIG_DIR` dedicated to Orbit employee sessions, with a closed allowlist of required auth/session/transcript state and no user settings/plugins/remote-policy cache; unexplained config/cache creation invalidates readiness;
- no security-critical hook or permission grant through ordinary `--settings`; any release-owned non-security settings file is closed, hashed, and subordinate to managed locks;
- an explicit `--tools` inventory containing only current approved built-ins; on native Windows, `PowerShell` is the only shell tool;
- bare deny rules for `Bash` and `Monitor` as defense in depth;
- `--strict-mcp-config` and only owner-approved, security-reviewed MCP definitions; arbitrary local stdio commands, filesystem servers, or host-execution tools are unavailable;
- only release-verified Orbit plugin directories and a sanitized instruction-only skill bundle;
- `dontAsk` plus explicit allow rules, never `bypassPermissions`, for the restricted employee process.
- a non-default `ANTHROPIC_BASE_URL` naming the verified no-fallback Orbit loopback API relay.

`--allowedTools` is permission policy, not tool restriction, and cannot replace `--tools`.

Setup installs an exact HKLM managed document, requiring owner-approved elevation. `policyHelper.path` is an absolute signed/release-hashed x64/ARM64 native `orbit-policy-helper.exe`; Windows Claude invokes it with no arguments. For an Orbit launch, parent sets fixed inherited `ORBIT_POLICY_SESSION_ID` and 256-bit base64url `ORBIT_POLICY_TOKEN`. Helper connects to `\\.\pipe\OrbitPolicyV1`; pipe DACL plus server verification of client PID, absolute image path/hash/signature, expected process tree, one-use token, and short expiry authenticate request. It emits complete `managedSettings`: handlers below, `allowManagedHooksOnly: true`, `allowManagedPermissionRulesOnly: true`, plugin/MCP locks, and restrictive environment values. Parent receipt binds token/session, source/document/helper hashes, emitted-policy hash, timestamp, and process identities. Server consumes/zeroizes token before prompt delivery; every replay rejects.

Claude, the policy-helper process, managed Orbit hook process, and Claude-created fixed host PowerShell dispatcher necessarily inherit the launch environment. They are all release/system-verified and may observe the now-consumed policy token and live relay header. No claim relies on managed settings unsetting inherited values. Every Orbit-created child uses explicit environment reconstruction from an empty map: the hook supervisor creates evaluator/parser children with a fixed allowlist; gateway supervisor creates target with its minimal allowlist; broker creates MXC executor/workload environment from the request allowlist; there are no local MCP child processes. These environments omit both `ORBIT_POLICY_*` and relay auth variables. Fixed dispatcher removes them from its own `os.environ` before any library/child use, though OS process inspection tests still treat that dispatcher as secret-bearing trusted TCB.

For unrelated owner Claude sessions, Orbit variables are absent and helper emits exactly `{}`—it omits the `managedSettings` key so lower endpoint/HKCU/owner policy remains available. If either Orbit variable is present but IPC/token/path/process validation fails, helper exits nonzero; it never emits empty policy for an attempted Orbit launch.

The closed-layout, remote-cache-free config root plus non-default API relay causes Claude Code to skip server-managed settings by documented behavior and prevents prior direct-session policy cache reuse. The relay forwards only reviewed Claude API protocol to `api.anthropic.com`, never serves policy, never falls back direct, and records only non-secret health/receipt data. It requires a per-session owner-side authentication header supplied in Claude's parent-built environment; unauthenticated/local foreign callers reject. Readiness verifies config entries, remote-cache absence, fetch skip, relay auth, token replay rejection, and explicit environment maps for evaluator/parser/gateway target/broker/workload. With remote policy absent, exact HKLM document is first selected admin source; lower managed files and user-writable HKCU policy are ignored under `first-wins`. Any source merge, helper/cache/foreign handler, direct fallback, relay mismatch, or secret appearing in an untrusted/contained target environment blocks.

The relay is not a general HTTP/CONNECT proxy. It binds loopback only, accepts the session-bound auth header, enforces a closed method/path/size/header protocol needed by the proved Claude client, validates TLS and exact upstream `api.anthropic.com`, follows no redirect, strips hop-by-hop/proxy headers, streams without persisting request/response bodies, and exposes no policy/cache endpoint. Unsupported client traffic fails closed and blocks readiness. Real-client proof covers subscription/API-key authentication modes claimed by Orbit, streaming, retries, relay restart/failure, foreign caller rejection, body/log absence, and direct-network fallback denial.

Orbit holds independent registry/file/service watchers on the HKLM policy key, managed-file locations, policy helper, and relay. A mutation terminates the Claude process tree and invalidates readiness. The design does not rely on `system/init`, `resolveSettings()`, or `ConfigChange` to enumerate or continuously detect managed sources.

User, project, local, workspace plugin, workspace skill-hook, and workspace agent-hook sources do not load. A project `.claude` tree can be arbitrary without affecting host hooks.

## Hook configuration

The policy helper emits all Orbit command handlers in the managed tier. They use exec form: `command` is an absolute verified `.exe`; `args` is present; no shell resolves the handler.

Illustrative shape (actual absolute paths and digests come from the release manifest):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<absolute verified python.exe>",
            "args": ["<absolute verified core/mxc.py>", "--session-start"],
            "timeout": 20,
            "onFailure": "block"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell|Monitor",
        "hooks": [
          {
            "type": "command",
            "command": "<absolute verified python.exe>",
            "args": ["<absolute verified core/mxc.py>", "--hook-supervisor"],
            "timeout": 20,
            "onFailure": "block"
          }
        ]
      }
    ],
    "ConfigChange": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<absolute verified python.exe>",
            "args": ["<absolute verified core/mxc.py>", "--config-changed"],
            "timeout": 20,
            "onFailure": "block"
          }
        ]
      }
    ]
  }
}
```

Additional rules:

- `async` and `asyncRewake` are absent/false.
- Internal supervisor/evaluator deadlines are shorter than 20 seconds.
- Handler, interpreter, parser, manifest, and imported security-module identities are bound to readiness.
- No handler command, argument, environment value, or path comes from employee content.
- The HKLM document, policy helper, relay, and any subordinate settings file live outside every employee scope and are not link/reparse targets.
- Managed policy disables background tasks and fixes `BASH_MAX_TIMEOUT_MS`/tool timeout above the inner MXC workload budget (630000 ms for the 600000-ms baseline) so cleanup grace is owned rather than model-selected.

## Session gate

Orbit starts Claude with stdin open but sends no employee prompt until all checks pass:

1. Static verifier proves exact HKLM document/helper/relay bytes and absence of a higher/merged local source.
2. No-argument native policy helper authenticates fixed env + named pipe token, emits and durably receipts exact managed policy for this launch nonce; negative control proves `{}`/no `managedSettings` for unrelated session.
3. Relay receipt and real-client diagnostics prove non-default endpoint use and skipped server-managed fetch; no direct fallback exists.
4. Real `system/init` stream reports expected session ID, exact Claude version, exact tool inventory, MCP servers, and no plugin/settings error.
5. Tool inventory contains `PowerShell`; it does not contain `Bash`, `Monitor`, or an unknown shell/code-execution tool.
6. Plugin and MCP inventories contain only release-verified/reviewed entries; no unreviewed local process or security-state writer exists.
7. `SessionStart` handler writes an owner-side receipt bound to launch nonce, real session ID, managed-policy digest, handler digest, and readiness key.
8. Independent policy-source watchers are armed before prompt delivery and current machine/policy readiness is `ready` or `ready-with-warnings`; bound warnings are surfaced without requiring acknowledgement.

Timeout, malformed init, missing receipt, source/plugin/tool mismatch, or a changed dependency terminates the Claude process tree before prompt delivery.

`onFailure: "block"` on SessionStart is defense in depth but does not block session start; the parent-held prompt and missing-receipt timeout are the gate. `ConfigChange` is supplemental. Registry/file/service watchers own mutation termination because server-managed and registry-policy changes do not reliably emit that hook.

## PreToolUse input

Required semantic fields and documented accepted optional fields:

| Field | Rule |
| --- | --- |
| `hook_event_name` | Exact `PreToolUse` |
| `session_id` | Nonempty string matching the live attested session |
| `tool_use_id` | Nonempty string, unique within session |
| `cwd` | String; observed only, never trusted as workspace authorization |
| `tool_name` | Exact `PowerShell`, `Bash`, or `Monitor` |
| `tool_input` | Object |
| `tool_input.command` | Nonempty string; original bytes retained in protected ticket only |
| `prompt_id`, `transcript_path`, `scratchpad_dir`, `permission_mode`, `effort` | Accepted when documented for the proved exact client; observed/ignored, never authority |
| `agent_id`, `agent_type` and other documented common fields | Accepted when type-valid; observed/ignored unless the contract explicitly binds them |
| `tool_input.description` | Optional string; never copied to rewritten execution input |
| `tool_input.timeout` | Optional documented number; validated then ignored in favor of policy timeout |
| `tool_input.run_in_background` | Optional boolean; accepted as input but rewritten to `false` |

The parser uses the exact documented input schema for the proved Claude version. Additive fields already documented for that version are accepted as above. Missing required fields, wrong types, duplicate keys, unknown-semantic fields, incompatible schema changes, or oversized values produce explicit denial. `cwd`, transcript/scratch paths, permission mode, descriptions, timeouts, background flags, environment employee ID, and workspace paths in payload cannot change trusted identity or execution policy.

## Evaluation order

1. Parse and validate complete hook input.
2. Resolve live session from owner-side launch state.
3. Require current `ready` or `ready-with-warnings` state and matching readiness/explicit-deny key. A matching explicit-deny breach is `blocked` and denies.
4. Stable-read owner policy and derive `PolicySourceFingerprint`.
5. Check exact tool:
   - `Bash`: deny with PowerShell recovery instruction.
   - `Monitor`: deny; background shell execution is not supported.
   - `PowerShell`: continue.
6. Parse gateway candidacy using verified no-evaluation PowerShell AST helper.
7. If canonical/current/verified gateway, issue gateway ticket.
8. If ordinary command, issue contained ticket.
9. Recheck policy/readiness fingerprints.
10. Render and self-validate exactly one response.

Any exception or uncertainty from steps 1–10 becomes denial. If valid denial serialization is impossible, supervisor exits nonzero/2 and emits no stdout; verified `onFailure: "block"` then blocks.

## Terminal outputs

### Contained

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Contained by Orbit's verified Windows sandbox.",
    "updatedInput": {
      "command": "& '<absolute verified python.exe>' '<absolute verified Orbit dispatcher>' _mxc-dispatch '<safe-ticket-id>'",
      "description": "Orbit contained command",
      "timeout": 630000,
      "run_in_background": false
    }
  }
}
```

`updatedInput` is newly constructed, not copied wholesale:

```json
{
  "command": "<fixed dispatch command>",
  "description": "Orbit contained command",
  "timeout": "<policy workload budget plus 30-second bounded cleanup grace; 630000 for the 600000-ms baseline>",
  "run_in_background": false
}
```

Only fields required by the exact PowerShell input contract are emitted. Original command bytes, model description, model timeout, background choice, and unknown fields never appear in the rewritten input.

### Canonical gateway

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Authorized Orbit gateway dispatch.",
    "updatedInput": {
      "command": "& '<absolute verified python.exe>' '<absolute verified Orbit dispatcher>' _gateway-dispatch '<safe-ticket-id>'",
      "description": "Orbit authorized gateway",
      "timeout": 630000,
      "run_in_background": false
    }
  }
}
```

The original gateway shell text never executes. The ticket carries structured argv, not shell source.

### Denied

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Orbit stopped this action because <safe boundary>. <one recovery action>."
  }
}
```

No `updatedInput` appears on denial.

## Output-byte contract

- Supervisor captures evaluator stdout/stderr and process status.
- Evaluator must return one UTF-8 JSON object matching the closed disposition schema and no other stdout bytes.
- Supervisor serializes the final Claude response once, writes it to stdout, flushes, and exits zero.
- Evaluator empty output, `{}`, plain text, partial `{`, invalid JSON, JSON array/string, schema-invalid object, multiple objects, extra trailing text, nonzero status, crash, timeout, or valid JSON followed by failure causes supervisor denial or nonzero/2.
- Errors and evaluator stderr are never copied verbatim into Claude output or trusted audit.

This is necessary because Claude Code treats several exit-zero non-object outputs as successful no-decision text even when `onFailure` is `block`.

## Failure matrix

| Failure | Required result |
| --- | --- |
| HKLM helper/relay receipt absent, remote fetch not skipped, hook absent, or matcher/tool inventory changed | Pre-run/full proof fails; employee prompt never sent |
| Higher/merged/foreign managed source, helper output mismatch, or direct relay fallback | Readiness blocked; process terminated |
| Handler/interpreter missing or cannot spawn | Claude blocks through `onFailure` |
| Evaluator/supervisor nonzero, crash, or hard termination | Claude blocks; host marker absent |
| Handler/evaluator timeout | Claude blocks; Job Object cleanup proves no descendants |
| Empty/plain/partial/malformed/schema-invalid evaluator output | Supervisor blocks; never forwarded as successful output |
| Missing/invalid event field | Explicit denial; no request/ticket launch |
| Policy/readiness load or race failure | Explicit denial; no stale retry |
| Ticket/request/proxy/executor startup failure | Trusted helper exits failure; original command is unavailable and never retried |
| Contained workload timeout | MXC inner job and Orbit outer supervisor terminate all descendants |
| HKLM/managed-file/helper/relay mutation during run | Independent watcher invalidates and terminates session; ConfigChange is not the security oracle |

## Multiple hooks and plugins

The policy-helper-emitted managed configuration contains only release-verified Orbit host handlers needed by the session and sets managed-only locks. A foreign managed, project, local, user, plugin, skill, agent, SDK callback, or mod handler outside the verified inventory blocks readiness even if Orbit's denial would win final permission precedence. Matching hooks execute in parallel, so final decision precedence cannot prevent sibling host effects.

## Behavior proof

After install, upgrade, repair, Claude binary/version change, effective-source/settings change, Orbit handler/plugin change, owner security policy change, or containment contract change, run the real installed client with the exact production launch shape.

Proof captures:

- `system/init` version/tools/plugins;
- HKLM policy-helper/emitted-policy receipt and API-relay/remote-fetch-skip receipt;
- `hook_started` and `hook_response` stream events using `--include-hook-events`;
- owner-side receipts keyed by session/tool-use/nonce;
- host-marker absence;
- contained/gateway receipt presence;
- process-tree survivor check.

Required cases: Windows invokes absolute `.exe` policy helper with zero arguments; valid fixed-env/named-pipe nonce yields exact managed policy/receipt; unrelated session yields `{}` with no `managedSettings`; malformed/expired/replayed token or wrong client PID/image exits nonzero; normal rewrite with every documented common/PowerShell optional field; model `timeout` and `run_in_background` replaced; explicit denial; missing handler; spawn failure; nonzero; crash; timeout; empty; `{}`; plain; partial; malformed/schema-invalid JSON; valid JSON followed by failure; HKLM/helper mutation; relay failure/direct-fallback attempt; and foreign managed hook. Failure to produce/observe intended real `PowerShell` event is failed proof, not pass.

Every accepted employee process still performs the live session gate. Full matrix results may be reused only while every bound byte/source/version/policy identity remains exact.

## Native Desktop/folder sessions

Native Windows MXC mode does not create `claude://` or `claude --desktop` employee sessions. Those entry points cannot carry the restricted settings/tool contract and the current workspace settings file is employee-writable. Orbit returns a blocker with one action: use the control-panel/headless employee path, or deliberately select WSL2. Other platforms remain unchanged.

## Message and logging rules

- User-facing reason identifies boundary and one recovery action.
- Never include original command, gateway arguments, URL query/body, credentials, ticket, nonce, unrestricted paths, full policy, raw exception, or raw hook stderr.
- Workspace decision mirrors may contain timestamp, disposition class, and non-secret reason code only; they are never read for authorization/readiness.
