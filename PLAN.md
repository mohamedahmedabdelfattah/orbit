# Plan: make `orbit sandbox off` also disable MXC on native Windows

## Problem
`orbit sandbox off` toggles only the optional team sandbox (macOS/Linux/WSL). On native
Windows, MXC (Microsoft Execution Containers) is mandatory: `core/engine.py:467`
(`settings_json`) always returns the sandbox blob with `mxc.hook_settings()` attached
when `osinfo.KIND == "windows"` and mode is `mxc`. There is no supported way to turn
MXC off. Goal: an explicit owner opt-out, while keeping MXC **on by default**.

## Design decision
Distinguish three states instead of two:
- **Default (registry key absent):** MXC on on native Windows (fail-safe, unchanged for
  existing installs — upgrading never silently unsandboxes anyone).
- **`orbit sandbox on`:** team sandbox on; MXC hook on Windows (unchanged).
- **`orbit sandbox off`:** writes `"sandbox": false` **explicitly** (instead of popping
  the key). On native Windows this means MXC off too. On macOS/Linux/WSL behavior is
  byte-identical to today (`sandboxed()` still tests `is True`).

No new registry key; no migration needed. Old registries that had the key popped
simply stay in default state (MXC on) until the owner re-runs `orbit sandbox off`.

## Steps (each with its proof)

1. **`orbit` → `sandbox_cmd` (lines 1085–1102):** on `off`, set `reg["sandbox"] = False`
   instead of `reg.pop("sandbox", None)`. Add a confirmation prompt when
   `osinfo.KIND == "windows"` and mode is `mxc`: warn that shell commands will run
   unsandboxed with full user rights (guard plugin and `denyRead`/tool denials remain).
   Require typed confirmation or a `--yes` flag on the parser.
   *Proof: run `orbit sandbox off` on Windows → registry has `sandbox: false`; docstring
   and help text (line 24) no longer claim MXC stays on.*

2. **`core/engine.py` → `settings_json` (lines 461–469):** off-branch condition becomes
   "not sandboxed() and not (windows and mode==mxc and registry sandbox key is not
   explicitly False)" — i.e. MXC attaches only unless the owner opted out.
   `sandbox_blob` unchanged.
   *Proof: unit test — Windows + default registry → blob has `hooks`; Windows +
   `sandbox: false` → `{"sandbox": {"enabled": false}}` with no `hooks` key.*

3. **`orbit` → `say_sandbox_status` / `sandbox_change_summary`:** show and say the
   native-Windows MXC state ("MXC containment off at owner's request").
   *Proof: `orbit sandbox` output on Windows reflects the new state.*

4. **`orbit` → `windows_checks` (lines 306–335) / doctor:** when the owner opted out,
   MXC checks (build gate, `wxc-exec.exe` presence, probe) become informational lines
   ("disabled by owner's choice"), not failures — doctor must not tell users to fix
   something they deliberately turned off.
   *Proof: `orbit doctor` on a Windows box with sandbox off exits clean, shows the note.*

5. **Docs:** `orbit` docstring line 24, `docs/toolbelt.md:25–26`, `docs/SETUP.md:79`,
   `README.md:258–270, 343–344`: document that native Windows keeps MXC by default and
   `orbit sandbox off` (with confirmation) disables it, and what is lost (per-command
   containment, egress deny, filesystem allow-write) vs what stays (guard plugin,
   secret deny-lists, PowerShell-tool requirement).
   *Proof: grep for "MXC stays on" / "remains mandatory" returns no stale claims.*

6. **Tests:** extend `tests/test_core.py` (~line 2198 settings_json tests) and
   `tests/test_platforms.py` (~line 2073 sandbox_blob tests):
   - Windows default registry → `hooks` present.
   - Windows + `"sandbox": false` → no `hooks`, `sandbox.enabled == false`.
   - Windows + `"sandbox": true` → `hooks` present (unchanged).
   - macOS/WSL with `"sandbox": false` → identical JSON to today's off state.
   - `sandbox_cmd("off")` writes `False` and prompts on Windows (monkeypatched input).
   *Proof: `python -m pytest tests/test_core.py tests/test_platforms.py tests/test_mxc.py` green.*

## Setup-time sandbox choice (added later, US4)

`orbit setup` must ask the owner about the sandbox before anything else is gated on it,
with **no sandbox as the default answer**:

1. **Question placement**: at the start of `setup()` (orbit:798), before the
   `platform_checks()` must-fix gate (orbit:804) — the choice decides whether MXC
   checks are must-fix or informational.
2. **macOS/Linux/WSL**: one yes/no question ("Run the crew in the sandbox?"). Default
   answer is **No**. Yes → `reg["sandbox"] = True`; No → explicit `reg["sandbox"] = False`.
   There is no mode question — the built-in Claude Code sandbox is the only mode.
3. **Native Windows**: yes/no question (text shows the current state; MXC on is noted).
   Default answer **No** → explicit `reg["sandbox"] = False` (the MXC opt-out from
   steps 1–3; the crew keeps running on the Windows side, unsandboxed).
   Yes → offer the **available modes only**: MXC if build ≥ 24H2 and `mxc.discover()`
   ok and `sandbox_probe()` usable; WSL2 if `wsl.exe` exists. Default mode MXC when
   available (the machine's own; WSL2 requires reinstalling the kit inside WSL).
   Record via the existing helpers (`mxc.set_mode(..., decided_by="owner")` or the
   guided text), never silent bootstrapping.
4. **Sandbox wanted but no mode available**: explain the fixes (MXC_FIX text, WSL
   install), offer "continue without a sandbox? (y/N)" — default exits setup, matching
   today's fail-closed spirit; an explicit yes writes the opt-out.
5. **Check gating falls out naturally**: `windows_checks()` sees the registry state
   (step-8 downgrade task), so after the question the MXC items are informational when
   the owner declined, and must-fix only when they opted in. The existing WSL2
   fallback block (orbit:806–817) stays as defense in depth.
6. **Re-runs**: the question re-asks with the current state as the prompt text; the
   bare-Enter default is still No (per owner's decision) — the text must make the
   current containment state visible so a re-run downgrade is deliberate.

## Intentionally skipped
- Re-enabling the Bash tool on Windows when MXC is off: `CLAUDE_CODE_USE_POWERSHELL_TOOL`
  stays set; switching shells back is a separate, riskier change.
- Desktop/app launch gating (engine.py:415–417) — unrelated to MXC (feature 003).
- Any change to `orbit sandbox mxc|wsl2` switching or `core/mxc.py` itself.

## Done condition
On native Windows: fresh/default install → MXC on (unchanged); `orbit sandbox off`
(confirmed) → next run's settings JSON is `{"enabledPlugins": {}, "sandbox": {"enabled": false}}`
with no `hooks`, and doctor reports it as owner's choice without failing. macOS/Linux/WSL
`settings_json` output unchanged for all three states. Full test suite passes.
