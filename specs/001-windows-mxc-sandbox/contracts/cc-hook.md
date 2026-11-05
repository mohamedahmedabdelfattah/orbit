# Contract: Orbit containment hook (Claude Code PreToolUse)

**Producer**: Orbit's run-settings generation (native Windows, mode `mxc`).
**Consumer**: Claude Code's hook pipeline — documented `PreToolUse` event controls.

## Hook configuration Orbit emits (per employee run)

- Event: `PreToolUse`, matcher group: `Bash|PowerShell` (exact-string alternation per the hooks reference).
- Handler: Orbit's containment helper (exec form, absolute executable path, no shell), with a short `timeout`.
- Placement: inside the settings blob `engine.settings_json()` produces for the run (hooks are a documented settings key). If `--settings` cannot carry hooks in the installed Claude Code version, fall back to writing the hook into the employee workspace's `.claude/settings.json` — the installer-time verification task covers which surface applies.

## Hook behavior (the contract)

| Input | Output |
| --- | --- |
| `tool_input.command` for a Bash/PowerShell call; hook input also carries the session cwd | JSON with `hookSpecificOutput.permissionDecision` + optional `updatedInput` |

1. **Excluded command** (matches Orbit's gateway/limit-owning patterns) → no decision (exit 0): the command flows through the normal permission pipeline unwrapped, exactly as `excludedCommands` behaves under Claude's own sandbox.
2. **Contained command** → return `permissionDecision: "allow"` **and** `updatedInput` where `command` invokes Orbit's containment helper with the request and approved-domain sidecar. The original command lives in the request's `process.commandLine`, under the same Bash/PowerShell interpreter. The helper starts the short-lived domain proxy and invokes `wxc-exec.exe`; it never runs the original command on the host. Include unchanged input fields. `allow` + rewrite is the documented auto-approve pairing; deny/ask rules still evaluate the rewritten command.
3. **Containment impossible** (executor missing, request schema mismatch, policy build error) → `permissionDecision: "deny"` with a plain-language `permissionDecisionReason` (owner-readable; feeds run-log diagnostics). Never a silent unsandboxed pass.
4. **Never** returns a decision that widens permissions: deny/ask rules always remain in force on the rewritten command.
5. On native Windows, Orbit enables Claude Code's PowerShell tool as the primary shell. MXC 1.0 cannot initialize
   MSYS2/Git Bash (`microsoft/mxc#1061`), so a non-gateway `Bash` call is denied with a request to retry as
   PowerShell; it is never retried on the host or allowed outside containment.

## Invariants

1. The hook never runs executor `--audit` mode or telemetry-affecting flags on real commands.
2. Reason strings are single-line, sanitized (no secrets, no control characters) per the run-log diagnostics convention.
3. Latency: the hook adds minimal overhead — policy context is cached per run; request generation targets well under a second (SC6).
4. The tool names the matcher targets (`Bash|PowerShell`) are an implementation-time verification against the installed Claude Code's Windows tool surface (see research D9); the wiring task (T033) re-checks them when it lands.
