# Contract: MXC container-creation request emitted by Orbit (per shell command)

**Producer**: Orbit's containment helper (native Windows, mode `mxc`) — one request **per contained shell/PowerShell command**, generated when the PreToolUse hook rewrites the command.
**Consumer**: MXC runtime executor (`wxc-exec.exe`), per the MXC stable schema (v1.0.0+).

This is the stable interface between Orbit and MXC. The full JSON schema is Microsoft's (`schemas/stable` in the MXC repo); this document fixes **Orbit's mapping and invariants**.

## Request shape (Orbit's mapping)

```json
{
  "command": "<the shell command being contained, as proposed by the agent>",
  "working_directory": "<the employee's workspace (Windows path)>",
  "filesystem": {
    "deny_read":  ["<Windows secret-store paths, Orbit's SECRET_PATHS set>"],
    "allow_write": ["<employee workspace>", "<team tree>", "<per-command temp>"]
  },
  "network": {
    "egress": { "default": "deny", "allow": ["<pypi/pythonhosted + owner-approved domains>"] }
  },
  "timeout_ms": "<per-command budget; no orphaned workload after the hook gives up>"
}
```

## Invariants (must hold for every generated request)

1. **Fail-closed defaults**: `network.egress.default` is `"deny"`; `allow_write` never covers the deny_read set or configuration paths (`.claude` settings, `.git` hooks/config protected as today — negative probe).
2. **No silent loosening**: tightened owner config narrows the request; Orbit never widens beyond owner-approved domains/paths.
3. **Agent-flow neutrality**: the workload inside the container is the agent's proposed shell command — nothing Orbit-added wraps or alters the agent itself.
4. **Impossible wrapper ⇒ denied command**: if the executor can't be launched or the request can't be built, the hook denies the command with a reason — the command never runs unsandboxed.
5. **Gateway exclusions**: commands matching Orbit's exclusion patterns run unwrapped (their own limits apply), mirroring `excludedCommands` semantics.

## Executor invocation (informative)

`wxc-exec.exe <request.json>` — the wrapped command streams stdout/stderr/stdin through to Claude's Bash/PowerShell tool output exactly as the un-contained command would (verified at implementation; see D1's verification item). `--debug` for diagnostics capture; `--audit` only as an explicit doctor triage command (never on real runs).

## Versioning

Orbit pins the MXC request schema major version it emits; installer records the MXC runtime version; doctor reports both. A major-version mismatch fails setup with the fix command.
