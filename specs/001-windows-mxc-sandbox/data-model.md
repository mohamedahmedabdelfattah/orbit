# Data Model: Native Windows with MXC

Feature: `001-windows-mxc-sandbox`. Additions to Orbit's existing entities only; nothing on macOS/Linux/WSL2 changes.

## Entities

### 1. PlatformMode *(new)*

Owner-settable, machine-level choice of containment path on Windows.

| Field | Type | Values |
| --- | --- | --- |
| sandbox_mode | enum | `"mxc"` (default on native Windows where available) , `"wsl2"` |
| decided_by | enum | `"owner"`, `"unavailable"` (auto-set only when MXC was detected unavailable/disable — the spec's trigger (b)) |
| decided_at | ISO date | for doctor display |
| mxc_unavailable_reason | string\|null | machine-readable reason when `decided_by = "unavailable"` |

**Validation**: mode changes require explicit owner action or a recorded unavailability reason (spec R4.1); doctor displays the effective mode (R4.5).

**Relationships**: referenced by the employee-run launch (entity 2) and doctor checks.

### 2. ContainmentPolicy *(new, derived — not stored)*

Per-**contained-command** mapping of the existing Orbit policy onto MXC request surfaces. Derived at hook time from the registry + employee profile (source of truth unchanged: `~/Staff/staff.json` + `profile.json`), cached per run to keep per-command rewrite latency low.

| Field (Orbit concept) | Source (unchanged) | MXC surface |
| --- | --- | --- |
| deny_read | `SECRET_PATHS` + secrets folder + Windows-native additions | `filesystem.deny_read` |
| allow_write | employee workspace, team tree, temp | `filesystem.allow_write` |
| allowed_domains | `BASE_DOMAINS` + registry `network_domains` + gateway host needs | `network` egress deny-default + allow list |
| strict allowlist | autonomy flag (existing) | same semantics — no ask-callback widening for autonomous runs |
| `excluded commands / gateways` | abilities.json/command config | hook passes these through unwrapped (Orbit-layer limits unchanged) |
| refused-unavailable | `failIfUnavailable` semantics | hook denies the command when containment can't be established; Orbit omits the built-in sandbox `failIfUnavailable` key in run settings on native Windows |

**Validation rules**: deterministic for a given registry/profile state (R2.5); negative probe must fail for deny_read/allow_write/egress surfaces (SC2).

### 3. ProbeResult *(new, ephemeral + logged)*

Outcome of the setup/doctor containment check.

| Field | Type |
| --- | --- |
| mode attempted | `mxc` / `wsl2` |
| positive tests (workload) | pass/fail each |
| negative tests (write, read, network) | pass/fail each (pass = correctly denied) |
| capability notes | e.g., network-host filtering unavailable on this build |
| verdict | usable / unusable-with-reason |

**State transitions**: `unknown → probing → usable` (setup proceeds); `unknown → probing → unusable` (native Windows: refuse unsandboxed; offer WSL2 recommendation — the one auto path, recorded in PlatformMode.decided_by = `unavailable`).

### 4. Staff run log *(existing, extended)*

`state/runs.jsonl` entries gain the platform mode and probe/diagnostic reference id for support triage. No schema break for other platforms.

## Windows-native path additions to existing entities

| Entity | Native-Windows value |
| --- | --- |
| `SECRET_PATHS` | `%USERPROFILE%\.ssh`, `%USERPROFILE%\.aws`, `%APPDATA%\gnupg`, `%APPDATA%\rclone`, `~/.netrc`, Chrome (`%APPDATA%\Google\Chrome`), Edge (`%LOCALAPPDATA%\Microsoft\Edge`), browser caches (`%LOCALAPPDATA%\Microsoft\Windows\INetCookies`), Desktop/Documents/Downloads, Orbit secrets folder |
| denied command families | keep `powershell`, `cmd`, `wsl`, `schtasks` families on native Windows (they are local tools there) |
| team data root | `%USERPROFILE%\Staff` (or `STAFFROOM_HOME`) |
| service identity | Scheduled Task `Orbit` (logon trigger) + `staffd_alive` stamp |
| hook registration | a `PreToolUse` hook (matcher `Bash\|PowerShell`) in the employee-facing settings Orbit generates per run, invoking Orbit's containment helper |
