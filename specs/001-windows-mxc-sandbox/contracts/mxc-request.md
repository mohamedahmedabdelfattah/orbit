# Contract: MXC container-creation request emitted by Orbit (per shell command)

**Producer**: Orbit's containment helper (native Windows, mode `mxc`) — one request **per contained shell/PowerShell command**, generated when the PreToolUse hook rewrites the command.
**Consumer**: MXC runtime executor (`wxc-exec.exe`), per the MXC stable schema (v1.0.0+).

This is the stable interface between Orbit and MXC. The full JSON schema is Microsoft's (`schemas/stable` in the MXC repo); this document fixes **Orbit's mapping and invariants**.

## Request shape (Orbit's mapping)

```json
{
  "version": "1.0.0",
  "containment": "processcontainer",
  "lifecycle": { "destroyOnExit": true, "preservePolicy": false },
  "process": {
    "commandLine": "<the proposed command under its Bash/PowerShell interpreter>",
    "cwd": "<the employee's workspace (Windows path)>",
    "inheritDefaultEnv": true,
    "timeout": "<per-command budget in milliseconds>"
  },
  "filesystem": {
    "deniedPaths": ["<Windows secret-store paths, Orbit's SECRET_PATHS set>"],
    "readonlyPaths": ["<host volume roots; deniedPaths override these>"],
    "readwritePaths": ["<employee workspace>", "<team tree>", "<per-command temp>"]
  },
  "network": {
    "egress": { "default": "deny" },
    "ingress": { "default": "deny", "hostLoopback": "deny" }
  },
  "telemetry": { "enabled": false },
  "fallback": { "allowDaclMutation": false }
}
```

MXC's stable schema accepts CIDRs, not durable DNS names, in direct egress rules. Orbit therefore never
places owner domains into `network.egress.allow`. The rewritten command invokes Orbit's helper, which starts
a short-lived allowlist HTTP/S proxy, changes the wire copy to MXC's proxy-only model (`egress.default: deny`,
loopback proxy endpoint only), and then launches the executor. Tools that ignore proxy settings remain blocked.
The audit copy is deterministic apart from its per-command temp path; the ephemeral proxy port exists only
in the wire copy.

## Invariants (must hold for every generated request)

1. **Fail-closed defaults**: `network.egress.default` is `"deny"`; `readwritePaths` never covers the denied set or configuration paths (`.claude` settings, `.git` hooks/config protected as today — negative probe).
2. **No silent loosening**: tightened owner config narrows the request; Orbit never widens beyond owner-approved domains/paths.
3. **Agent-flow neutrality**: the workload inside the container is the agent's proposed shell command — nothing Orbit-added wraps or alters the agent itself.
4. **Impossible wrapper ⇒ denied command**: if the executor can't be launched or the request can't be built, the hook denies the command with a reason — the command never runs unsandboxed.
5. **Gateway exclusions**: commands matching Orbit's exclusion patterns run unwrapped (their own limits apply), mirroring `excludedCommands` semantics.

## Executor invocation (informative)

`python core/mxc.py --run <request.json> <domains.json>` starts the per-command proxy and invokes
`wxc-exec.exe <wire-request.json>`. The executor streams stdout/stderr/stdin through to Claude's tool output.
`--audit` is used only by the explicit doctor triage command (never on real runs).

## Versioning

Orbit emits exact stable schema `1.0.0`; the installer pins official signed runtime package `1.0.1` and records
both versions. A major-version mismatch fails setup with the fix command.
