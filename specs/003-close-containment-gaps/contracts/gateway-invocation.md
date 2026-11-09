# Contract: Canonical Native-Windows Gateway Invocation

**Producer**: Orbit containment hook, release gateway catalog, and owner ability state
**Consumer**: Verified Orbit gateway dispatcher
**Scope**: Native Windows, mode `mxc`
**Contract version**: `orbit.gateway-request.v1`

## Security outcome

Host execution is denied by default. A gateway exception exists only for one simple, statically parsed, currently authorized invocation that Orbit rewrites to its verified dispatcher. The employee's original PowerShell text never executes on the host.

Gateway identity never depends on `PATH`, `PATHEXT`, current directory, shell profile, alias, function, case folding, extension resolution, `.cmd`, symlink, junction, or employee-supplied path.

## Explicit native host catalog

Native host eligibility is separate from the general abilities catalog. Missing `host_eligible: true` means the command remains contained. Contract v1 has a final, closed host set:

| Gateway ID | Ability | Host eligibility | Required controls before release |
| --- | --- | --- | --- |
| `staff-apify` | `apify` | **Host eligible when owner enabled** | Fixed API/catalog, fresh ability/autonomy state, budget, token loaded internally, sanitized input, no child process |
| `staff-compute` | `compute` | **Host eligible when owner configured** | In-process GitHub HTTPS API only, owner-selected private repo, workspace file boundary, no workflow secrets, no child process |
| `staff-fetch`, `staff-browse`, `staff-watch`, `staff-video`, `staff-connectors`, `staff-docs`, `staff-skill` | Existing abilities | **Contained** | Setup preinstalls/verifies browser/media/OCR/tool dependencies; request grants exact readonly paths; every valid form must pass real contained compatibility or release blocks |

There are no provisional host candidates. Adding another host gateway changes the contract epoch and requires a new security review. A listed host entry whose controls, dependencies, launcher, or tests do not pass is disabled for the release.

Each release-owned `GatewayCatalogEntry` contains exact gateway/ability IDs, entrypoint and shared-module digests, a complete hash-locked third-party dependency/environment digest, policy version, argument limits, control profile, and explicit eligibility.

## Parser boundary

Orbit does not use `fnmatch`, wildcard permission strings, substring/regex prefixes, `shlex`, or a hand-written approximation of PowerShell syntax for authorization.

The release-owned `core/gateway-parse.ps1` helper:

- runs through an absolute verified Windows PowerShell executable;
- uses `-NoLogo -NoProfile -NonInteractive`;
- receives the proposed command only through stdin as data;
- calls `System.Management.Automation.Language.Parser::ParseInput`;
- never invokes, expands, evaluates, dot-sources, or passes the AST to a runspace;
- runs within the hook supervisor's Job Object and shorter internal deadline;
- emits one closed JSON parser result or exits nonzero.

Parser/helper absence, timeout, crash, malformed result, integrity mismatch, or unexpected AST causes explicit denial. It never causes original host execution.

## Accepted AST

A canonical gateway call must satisfy every condition:

1. No lexer/parser error or control/NUL character.
2. Input length, argument count, and individual argument length are within catalog bounds.
3. Exactly one top-level statement.
4. Exactly one pipeline and one pipeline element.
5. Element is one `CommandAst`.
6. No redirection, pipeline chain, background operator, trap, block, assignment, or additional statement.
7. No call operator (`&`) or dot sourcing.
8. First command element is one unquoted bareword, exact lowercase, and exactly equals one catalog gateway ID.
9. Remaining elements are static literal strings or static option/bare tokens that the parser can convert to one deterministic string each.
10. No variable, environment reference, splatting, subexpression, expandable string with nested expression, script block, here-string, backtick escape/execution, comment, alias/function path, nested shell, or dynamic command element.

Literal metacharacters are valid argument data only when the AST proves they belong to a static literal string. Examples accepted after exact catalog/argument validation:

```powershell
staff-apify run actor-id '{"searchTerms":["a;b"]}'
staff-compute run 'python job.py | tee out/result.txt' --files job.py
```

The same characters used as active operators, interpolation, or nested commands are rejected.

PowerShell AST acceptance proves syntax only. It does not grant authorization or select an executable.

## Candidate classification

| Parsed input | Classification |
| --- | --- |
| Exact accepted AST whose command is an explicit host gateway | Gateway candidate; continue authorization/integrity checks |
| One valid ordinary command not gateway-like | Ordinary; rewrite through MXC |
| Exact known/`staff-*` command with active/noncanonical/dynamic syntax | Rejected gateway-like; deny and audit |
| Known gateway disabled, paused/retired employee, or missing context | Rejected gateway-like; deny and audit |
| Unknown `staff-*` command | Rejected gateway-like; deny and audit |
| Gateway name only appears as static argument to another ordinary command | Ordinary contained command; audit nonqualification if corpus marks it gateway-like |
| Valid compound/nested command containing a gateway command position | Rejected gateway-like; deny the whole event and audit |
| Parser/classifier/integrity uncertainty | Deny the whole event and audit when identity is available |

There is no partial execution. A command is never split so one part reaches host while another is contained.

## Authorization at hook time

Before issuing a gateway ticket, hook requires:

- current `ready` or `ready-with-warnings` containment state with no explicit-owner-deny breach;
- valid live employee/session binding from protected launch state;
- active employee status;
- exact gateway catalog entry with `host_eligible: true`;
- current owner ability grant from one stable owner-state read;
- passing per-gateway argument validator;
- current catalog, parser, dispatcher, dedicated Python environment/dependency lock, entrypoint, and shared-module integrity;
- writable trusted audit store.

Failure denies. Gateway classification never runs before readiness/policy checks.

## One-use gateway request

Accepted static argv is stored in a protected ticket outside the workspace:

```json
{
  "schema": "orbit.execution-ticket.v1",
  "ticket_id": "<opaque safe id>",
  "kind": "gateway",
  "employee_id": "sara",
  "session_id": "<real client session>",
  "tool_use_id": "<tool call>",
  "policy_fingerprint": "<sha256>",
  "readiness_key": "<sha256>",
  "contract_epoch": 1,
  "orbit_release_digest": "<sha256>",
  "created_at": "<utc>",
  "expires_at": "<utc>",
  "state": "issued",
  "payload_digest": "<sha256>",
  "payload": {
    "gateway_id": "staff-apify",
    "argv": ["run", "actor-id", "{\"searchTerms\":[\"a;b\"]}"],
    "catalog_digest": "<sha256>",
    "launcher_digest": "<sha256>",
    "shared_file_digests": {"<path>": "<sha256>"},
    "dependency_lock_digest": "<sha256>"
  }
}
```

This is the authoritative ticket shape from [data-model.md](../data-model.md). Extra, flattened, or legacy shapes are invalid.

Hook returns explicit allow with an updated command containing only fixed absolute verified paths, private `_gateway-dispatch`, and the safe ticket ID. Raw gateway ID/argv need not appear in the host shell string and raw model command never appears.

## Dispatcher contract

The dispatcher performs this exact order:

1. Verify its own running release/manifest and protected runtime root.
2. Open and atomically claim the ticket without following links/reparse points.
3. Validate closed schema, expiry, single-use state, payload digest, contract/release/session/tool binding.
4. Stable-read current owner state.
5. Revalidate active employee, exact current ability, policy fingerprint, readiness key, catalog entry/policy version, and argument limits.
6. Reverify dedicated Python interpreter/environment, complete dependency lock, parser, dispatcher, entrypoint, and shared security-module final paths/digests; reject any symlink/junction/reparse component or replacement race.
7. Transition the already reserved audit WAL record to `approved`. If the primary store fails, write minimal failure to the independent Windows Event Log sink, block readiness, and do not launch.
8. Build minimal environment and trusted cwd.
9. Create the one verified Python target suspended with `PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY=PROCESS_CREATION_CHILD_PROCESS_RESTRICTED`, assign it to a dedicated kill-on-close Job Object with `ActiveProcessLimit=1`, then resume. `shell=False` remains required. Any child-creation attempt fails at the OS boundary.
10. Preserve bounded stdout/stderr and target exit code without a shell fallback.
11. Append coarse completion/failure audit result without raw args/output.
12. Remove/tombstone ticket and clean children/temp state.

Target form:

```text
[<absolute verified python.exe>, <absolute verified gateway entrypoint>, <argv...>]
```

Forbidden:

- `.cmd` or `.bat` as security launcher;
- bare `python`, global/user-site Python packages, or gateway names;
- shell command string or `shell=True`;
- employee-selected executable/interpreter/cwd/environment;
- retrying the original command;
- falling back to PowerShell/cmd on failure.

Existing `bin/staff-*.cmd` files may remain for owner/manual UX and non-Windows compatibility, but native employee host dispatch never calls them.

## Minimal gateway environment

Dispatcher begins from an allowlist, not inherited process environment. It supplies only values required by the verified target, including trusted employee/workspace/home identity and safe system/runtime variables.

It removes at least:

- Claude/Anthropic/API credentials;
- gateway tokens and GitHub/Apify credentials from inherited environment;
- `PYTHONPATH`, `PYTHONSTARTUP`, shell/profile startup variables;
- employee-provided environment overrides;
- policy/readiness/ticket nonces not required by target.

Gateway code loads its own owner-held secret internally after authorization. Secrets never appear in PowerShell input, ticket-visible rewritten command, process arguments, employee environment, stdout/stderr, or audit.

## Gateway controls

Canonical dispatch does not replace target controls. Each of the two targets independently rechecks current ability and enforces its catalog profile:

- exact URL scheme/host/public-address policy across redirects and secondary requests;
- allowed HTTP method/operation;
- local/private/link-local/loopback denial unless that gateway's reviewed contract explicitly needs one;
- owner budget and consent;
- workspace-bound inputs/outputs;
- timeout/output/download limits;
- secret isolation;
- no subprocess, external executable, runtime installation, shell, user-site package, or dynamic plugin surface; childlessness is enforced by process attribute plus one-process Job, not code review alone.

Required implementation before host eligibility:

- Apify autonomy/store authorization is reread from current owner state, not `STAFF_ABILITIES` run-start snapshot.
- `staff-compute` replaces `gh`, `git`, clone, and host subprocess calls with in-process GitHub REST/Git-data/workflow/artifact/ref APIs through the hash-locked HTTPS stack. Uploads remain workspace-bounded; downloaded artifact ZIP entries are size/count bounded and reject absolute/traversal/link/reparse targets before extraction.
- Both entrypoints use a protected non-employee-writable cwd/temp root and canonical workspace file reads; they cannot install dependencies at runtime.
- Every other current tool is marked contained, loses runtime-install/PATH assumptions, uses setup-pinned absolute dependencies inside the exact MXC readonly/environment policy, and is tested end-to-end to receive no host ticket while preserving valid behavior.

## Audit contract

Authoritative append target is a preallocated append-WAL outside all employee scopes, for example `%USERPROFILE%\Staff\.runtime\security\audit\gateway.jsonl`. Setup also registers a distinct Windows Event Log source as independent fallback. Readiness fault-tests both before admitting a session.

Each approved and rejected gateway-like attempt records:

| Field | Rule |
| --- | --- |
| `schema` | Exact `orbit.gateway-audit.v1` |
| `timestamp` / `request_id` | Correlation without raw command |
| `employee_id` | Trusted identity |
| `gateway_id` | Exact ID or `unknown` |
| `policy_fingerprint` / `catalog_digest` | Decision context |
| `decision` | approved, rejected, dispatch-failed, completed |
| `reason_code` | Closed non-secret vocabulary |
| `argument_digest` | SHA-256 only |
| `exit_class` | Optional coarse result |

Reason codes include `canonical-authorized`, `disabled`, `unknown-gateway`, `noncanonical-syntax`, `active-operator`, `ambiguous-parse`, `employee-missing`, `employee-inactive`, `authorization-revoked`, `launcher-missing`, `launcher-modified`, `reparse-point`, `stale-request`, `audit-unavailable`, and `dispatch-failed`.

Continuous health watchers cover both sinks. Every gateway-like classification first reserves a `pending` record with request ID and non-secret identity. The final decision completes that record. If primary reservation/completion fails, Windows Event Log receives `audit-unavailable`, readiness is blocked, and event is denied. If neither sink is writable, no employee session is admitted.

If both independently watched sinks fail in the race between the last health check and append, Orbit guarantees denial/session termination but cannot physically guarantee that event's durable FR-025 record. It emits an `audit-total-failure` readiness blocker at the first writable opportunity and marks the affected interval audit-incomplete; release/support output must not claim complete audit for that interval. Native host approval never occurs in this state. Never record raw command, argv, URL query, request body, JSON payload, token, secret, unrestricted path, or raw exception. Workspace mirrors are optional and never authoritative.

## Failure table

| Failure | Terminal behavior |
| --- | --- |
| Parser unavailable/crash/timeout/malformed result | Explicit deny; no host fallback |
| Active/ambiguous/noncanonical gateway syntax | Explicit deny + rejected audit |
| Unknown/disabled/inactive employee or gateway | Explicit deny + rejected audit |
| Catalog/launcher/shared file missing, changed, linked, shadowed, wrong release | Explicit deny + rejected audit |
| Owner disables between hook and dispatcher | Ticket fingerprint mismatch; dispatcher refuses |
| Ticket stale/replayed/replaced/extra-keyed | Dispatcher refuses; no target launch |
| Primary audit append fails | Event Log fallback records failure; approval withheld; readiness blocked |
| Gateway argument/control validation fails | Refuse target; no shell/fallback; safe result |
| Target spawn/crash/timeout or attempts a descendant process | Job cleanup, safe failure, completion audit, readiness blocked on policy violation |

## Bypass corpus

Machine-readable fixtures apply common variants to every host-eligible gateway, at least 50 rejected variants per gateway:

- `;`, newline, `&&`, `||`, `|`, `|&`, `&`, background execution;
- `>`, `>>`, `<`, `2>`, stream merges;
- `$()`, `${}`, `$env:`, `@()`, splatting, expandable strings, backticks, and stop-parsing token `--%`;
- `Invoke-Expression`, `Start-Process`, nested PowerShell/cmd;
- assignment/prefix, call operator, dot source;
- relative/absolute/UNC/device path, extension/PATHEXT, alternate wrapper;
- mixed case, trailing dot/space, Unicode homoglyph/dash;
- quoted command identity, gateway as another command's argument, multiple gateways;
- alias/function/profile/current-directory/PATH shadow;
- parse errors, here-strings, comments, controls, oversize input;
- missing/unknown/paused/retired employee, disable race;
- missing/corrupt registry, stale fingerprint;
- missing/modified/swapped/link/junction launcher/catalog/shared module;
- any descendant executable, runtime install, global/user-site package, employee-writable cwd/temp, or child-spawn attempt;
- audit failure, dispatcher spawn failure, timeout;
- credential-like argument/environment values proving redaction.

Accepted paired fixtures prove metacharacters inside static literal arguments remain data.

Real-client x64/ARM64 evidence additionally proves no rejected variant creates a host marker, only verified dispatcher/target processes appear, profiles/aliases/PATH are irrelevant, revocation wins, and credentials remain absent from process arguments/output/audit.

## Platform compatibility

This canonical dispatcher replaces native-Windows MXC exclusions only. macOS, Linux, and WSL2 keep existing gateway invocation/containment behavior under FR-035. Native Windows recorded as WSL2 exposes no native gateway dispatcher.
