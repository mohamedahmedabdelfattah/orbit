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
2. **Contained command** → return `permissionDecision: "allow"` **and** `updatedInput` where `command` is the contained form: `<wxc-exec.exe> <request.json> <original command>` (request built per `contracts/mxc-request.md`). Include unchanged input fields. `allow` + rewrite is the documented auto-approve pairing; deny/ask rules still evaluate the rewritten command.
3. **Containment impossible** (executor missing, request schema mismatch, policy build error) → `permissionDecision: "deny"` with a plain-language `permissionDecisionReason` (owner-readable; feeds run-log diagnostics). Never a silent unsandboxed pass.
4. **Never** returns a decision that widens permissions: deny/ask rules always remain in force on the rewritten command.

## Invariants

1. The hook never runs executor `--audit` mode or telemetry-affecting flags on real commands.
2. Reason strings are single-line, sanitized (no secrets, no control characters) per the run-log diagnostics convention.
3. Latency: the hook adds minimal overhead — policy context is cached per run; request generation targets well under a second (SC6).
