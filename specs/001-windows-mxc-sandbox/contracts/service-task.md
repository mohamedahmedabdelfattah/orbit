# Contract: Windows background service task

**Producer**: `orbit start` (native Windows mode `mxc` or any native-Windows install)
**Consumer**: Windows Task Scheduler (owner-visible as a task named `Orbit`)

## Scheduled task contract

| Property | Value |
| --- | --- |
| Name | `Orbit` |
| Trigger | At log on (owner user only) |
| Action | `pythonw.exe` from the owner's Python install, args: `<kit>\orbit service-run` |
| Working dir | Kit folder |
| Environment | `STAFFROOM_HOME=<team root>` (defaults `%USERPROFILE%\Staff`) |
| Hidden | yes (no console window churn at login) |

## Liveness & control contract (shared with Linux non-systemd mode — unchanged)

- `team/staffd_alive` stamp refreshed by the worker; `orbit status`/doctor read it (fresh < 120 s = running).
- `orbit stop` stops the task and terminates the watchdog + worker (existing PID file honored).
- `orbit start` is idempotent; `orbit restart` = stop + start.
- Failure messaging: if the service doesn't come up, `orbit logs` names the native log (`team/staffd.out`) — no WSL mentions.

## Invariants

1. No dependency on WSL, WMI-from-WSL bridging, hidden `wsl.exe`, or Startup-folder `.lnk` into Linux.
2. `service_run()` watchdog behavior (restart on worker exit, ~20 s pacing) is reused unchanged.
3. On non-native platforms the existing task definitions (launchd/systemd/WSL bridge) are produced exactly as today.
