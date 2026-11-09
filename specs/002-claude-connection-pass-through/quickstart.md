# Quickstart: Validate Claude Connection Pass-Through

## Purpose

Prove Orbit no longer requires Claude-account sign-in, ordinary work uses Claude's existing configuration, safety arguments remain, and account-only Cloud Shift stays separate.

No real provider or model is required. Use a temporary Orbit home and fake Claude executable that records argv/environment and emits valid JSON or stream-JSON responses.

## Automated Baseline

```bash
python -m unittest tests.test_core tests.test_platforms
python -m unittest discover -s tests
```

Platform-specific suites may require their existing host prerequisites. New tests must not require network, GPU, provider credentials, or a Claude account.

The existing CI matrix runs only selected platform tests on native Windows; full `tests.test_core` validation belongs to the macOS, Linux, and WSL2 jobs.

Recorded during the User Story 1 implementation pass (2026-11-07): a local native-Windows host (no WSL, no bundled audio devices, no Claude install) runs the full `tests.test_core tests.test_platforms` pair with a pre-existing set of ~39 platform-related failures unrelated to this feature. The MVP verification compared failure lists before and after the change: exactly one id differs (the intentionally removed obsolete `test_clean_env_never_leaks_api_settings` case, superseded by the `LaunchPolicy` tests). No feature-caused regression. The CI jobs remain the authoritative feature gates.

Recorded during the User Story 2 implementation pass: the `EmployeeLaunch` matrix, persistence-boundary, and `SignedOutSetup` (Scenario signed-out, SC-001) tests require the POSIX fake-Claude shim — the `--settings` JSON token does not survive `cmd.exe`'s quote reparse when a `.bat` shim carries the real employee argv (the same reason the pre-existing `LiveSteps` fake is among the native-Windows baseline failures). On native Windows, these tests skip with that reason; they are in the CI coverage of the macOS, Ubuntu 24.04, and WSL2 jobs. The native-Windows validation this host can perform: structured-onboarding, guard-plugin administration, legacy key isolation, and the availability checks all pass live through the `.bat` shim.

## Scenario A — Signed-Out End-to-End Flow

Use one temporary Orbit home and one fake Claude executable for the whole scenario:

1. Make `claude --version` succeed.
2. Make account status return `{"loggedIn":false,"authMethod":"none"}` if any account-only check is requested.
3. Complete the mandatory setup check.
4. Complete structured hiring with valid fake structured output.
5. Run one employee task with valid fake stream output.

Expected:

- setup, hiring, and employee work all complete;
- general setup never invokes account status;
- no command invokes `claude auth login` and no owner message prescribes it;
- installation/status says available rather than signed in.

## Scenario B — Production Launch Inventory Is Complete

Compare production direct uses of the resolved Claude executable in `orbit` and `core/` with IDs L01–L11 in [the launch contract](./contracts/claude-launch.md).

Expected:

- every direct process/exec launch is classified exactly once;
- employee business flows that route through `engine.run()` map to L02 rather than duplicate entries;
- adding an unclassified direct launch makes automated validation fail.

## Scenario C — Ordinary Pass-Through Matrix

1. Add known and arbitrary future-provider sentinels to the inherited environment and user settings.
2. Exercise an employee run, structured onboarding, and guard-plugin administration with fake Claude.

Expected:

- employee argv selects `--setting-sources user,project`;
- onboarding argv selects `--setting-sources user` and retains no-tools, schema, strict-MCP, model, effort, and no-session-persistence controls;
- ordinary paths preserve both known and arbitrary inherited sentinels;
- `CLAUDECODE` is absent and Orbit employee/workspace/safety values win;
- sandbox, guard, strict MCP, model, effort, allowed/denied tools, workspace, and session controls remain;
- plugin administration keeps its fixed operation and workspace.

## Scenario D — Anthropic Host Is Not an Ordinary Gate

1. Fail any attempted socket connection to `api.anthropic.com:443`.
2. Make fake Claude return successful employee output.
3. Run chat, routine, catch-up, and agent-follow-up dispatch paths.

Expected:

- no Anthropic socket attempt occurs before ordinary launch;
- fake Claude starts immediately and work succeeds;
- scheduled work is not deferred solely because Anthropic is unreachable;
- actual transient failure still invokes the existing delayed retry callback.

## Scenario E — Provider-Neutral Failure and Diagnostic Provenance

Make fake Claude return authentication, connection, rate-limit, and unknown failures without echoing inherited sentinels. Separately make it emit a harmless output marker.

Expected:

- owner text refers to Claude's configured connection where classified and never prescribes a generic account login;
- process result, failure class, and transient retry metadata remain;
- no second provider/fallback process starts;
- inherited sentinels do not enter Orbit-generated registry data, employee files, UI responses, activity records, diagnostic metadata, or logs;
- the harmless Claude-emitted marker follows existing output/error handling.

## Scenario F — Cloud Shift Eligibility and Freshness

Return each account method: `none`, `third_party`, `api_key`, `api_key_helper`, `oauth_token`, and qualifying `claude.ai`.

Expected:

- only `loggedIn:true` plus `authMethod:"claude.ai"` is eligible;
- read-only status may reuse a result for no more than 60 seconds;
- manual enablement, new-hire auto-enablement, and every L07–L11 command force a new account check;
- ineligible methods cannot enable, auto-enable, or launch Cloud Shift;
- qualifying account behavior remains unchanged.

## Scenario G — Cloud Account Environment Fails Closed

Seed the process with base URL, auth token, API key, proxy, `CLAUDE_CONFIG_DIR`, recognized provider flags, and an arbitrary `FUTURE_PROVIDER_TOKEN` sentinel. Exercise account status and L07–L11.

Expected:

- only the platform bootstrap keys documented in the launch contract reach fake Claude;
- every seeded connection/routing sentinel is absent, including the unknown future name;
- cloud inference commands receive empty setting sources;
- installation resolution, owner native account state, locale, temporary paths, and required platform process bootstrap still work.

## Scenario H — Enabled Shift Loses Eligibility

1. Enable Cloud Shift with a fresh qualifying account result.
2. Change fake account status to ineligible while a read-only positive result is still cached.
3. Attempt manual enablement, new-hire auto-enablement, and each local cloud launch family.

Expected:

- every state-changing/launch operation ignores the stale display cache and is rejected;
- an already-enabled employee keeps the configured switch but exposes an account-only error;
- ordinary local employee work continues through pass-through;
- no claim is made that Orbit can retroactively revoke a remote schedule created while it was offline.

## Scenario I — Legacy Orbit API Key Is Unchanged

1. Set `staff.json.auth` to `api_key` and store a test key through existing secret storage.
2. Add conflicting inherited base URL, auth token, API key, provider, proxy, and user-setting sentinels.
3. Build employee, onboarding, and guard-plugin administration launches.

Expected:

- conflicting inherited values are absent;
- only employee/onboarding inference receives the stored Orbit key;
- employee and onboarding retain their existing isolated setting sources;
- plugin administration remains isolated and does not receive the stored inference key;
- no user setting can reroute the key.

## Scenario J — Trusted User Customization Is Explicit

Use fake user settings containing hook/plugin markers.

Expected:

- ordinary employee and onboarding launches include their required user source;
- Orbit docs state owner hooks/plugins are trusted and may execute;
- Orbit does not describe those customizations as provider-only, reviewed, or additionally isolated;
- Cloud Shift and legacy API-key paths remain isolated from those settings.

## Scenario K — Tracked-File Static Gates

Run the automated tracked-file checks, then review these searches from the repository root:

```bash
git grep -n -E "Claude Code isn't signed in|Signed in to Claude|claude auth login|paid Claude plan" -- . ":(exclude)specs/**" ":(exclude)tests/**" ":(exclude)docs/superpowers/**"
git grep -n "api\.anthropic\.com" -- orbit core install.sh setup-windows.ps1 SETUP.md README.md docs templates .github ":(exclude)docs/superpowers/**"
git grep -n -E "ANTHROPIC_|CLAUDE_CODE_|CLAUDE_CONFIG_DIR" -- orbit core
git grep -n "resolve_claude" -- orbit core
```

Expected:

- account-login wording appears only in exact account-only Cloud Shift guidance;
- ordinary runtime paths contain no Anthropic-host preflight;
- inherited provider filtering remains only in legacy compatibility code; Cloud Shift uses an allowlist;
- every direct resolved-Claude process call maps to L01–L11;
- no provider profile/schema/module, endpoint field, credential store, relay, inference dependency, or migration was added.

Historical specifications under `specs/**` and `docs/superpowers/**`, and test fixtures under `tests/**`, are excluded by SC-007; they may quote the old wording or the rejected preflight design.

The automated equivalents are `tests.test_core.StaticContracts` (generic sign-in wording, the sole
`api.anthropic.com` probe, provider prefix filtering only in legacy mode, no provider integration
surface or migration) and `tests.test_core.LaunchInventory` (every production launch maps to L01–L11).

## Phase 7 Validation Record (2026-11-09)

Local host: native Windows 11, Python 3.12, no WSL, no `bash`, no Claude installation. No real
provider, account or network was used.

### T036 — full suite and scenarios

`python -m unittest tests.test_core tests.test_platforms` (run twice, with `cmd.exe` redirection so
native unittest lines are not console-wrapped):

- 149 tests: 17 failures, 18 errors, 9 skipped.
- 35 unique failure IDs. 34 are the exact pre-existing native-Windows baseline set. The extra ID is
  `tests.test_platforms.CloudShift.test_here_says_skip_gone_it_fires_back_it_pulls`, which is in the
  original 40-failure baseline and is absent from the later 34-failure run only because it self-skips
  outside 01:00–22:00. It also passes alone and with `tests.test_platforms` run by itself; in the
  combined run it fails only on the pre-existing cross-module `STAFFROOM_HOME` binding. It is not
  feature-caused.
- No feature-caused regression: the four `StaticContracts` tests and all targeted feature classes pass.

Targeted feature classes run separately so the shared home cannot mask them:

```text
tests.test_core.ProviderNeutralRun Diagnostics DiagnosticProvenance LaunchPolicy EmployeeLaunch
                 HireAndPluginLaunch LaunchInventory StaticContracts CloudShiftPanel
=> 28 tests, OK (8 skipped: POSIX fake-Claude shim cases)

tests.test_platforms.CloudAccount ClaudeAvailability SignedOutSetup
=> 12 tests, OK (1 skipped: POSIX fake-Claude shim case)
```

Scenario coverage on this host:

| Scenario | Evidence |
| --- | --- |
| A — signed-out end-to-end | `SignedOutSetup` skips on native Windows (real employee argv cannot cross `cmd.exe`'s `.bat` shim); covered by CI macOS/Ubuntu/WSL2. |
| B — launch inventory | `LaunchInventory` passes (all sites mapped, contract IDs L01–L11 unique). |
| C — pass-through matrix | `LaunchPolicy`, `EmployeeLaunch`, `HireAndPluginLaunch` pass; POSIX-shim cases skip locally. |
| D — no Anthropic ordinary gate | `ProviderNeutralRun` passes; `StaticContracts` proves the sole host probe is Cloud Shift's `_online`. |
| E — neutral failures and provenance | `ProviderNeutralRun`, `Diagnostics`, `DiagnosticProvenance` pass. |
| F — Cloud Shift eligibility/freshness | `CloudAccount` and `CloudShiftPanel` pass. |
| G — account environment fails closed | `CloudAccount` passes. |
| H — enabled shift loses eligibility | `CloudShiftPanel` and `CloudAccount` pass. |
| I — legacy API key unchanged | `LaunchPolicy`, `HireAndPluginLaunch` pass. |
| J — trusted user customization is explicit | `SETUP.md`/`README.md` disclose trusted hooks/plugins and full environment pass-through; ordinary launch assertions pass. |
| K — tracked-file static gates | `StaticContracts` passes; the four `git grep` searches return only the allowlisted Cloud Shift `_online`, legacy-mode prefix declarations/injection, Orbit-owned overrides, or the historical `docs/superpowers` design note. |

Scenario checks that need the POSIX fake shim (`bash`, WSL, macOS, Linux) are recorded as unavailable
on this host, not as passing.

## CI Evidence

The full fake-only suite must pass in the existing GitHub Actions jobs for macOS, Ubuntu 24.04, native
Windows unit coverage, and Ubuntu 24.04 under WSL2. Record a platform-specific pre-existing failure
separately rather than weakening a feature assertion.

Status recorded 2026-11-09 from the available host:

| Job | Status |
| --- | --- |
| `mac` (`macos-latest`, full suite) | Not run on this host: no macOS runner available. |
| `linux` (`ubuntu-24.04`, full suite) | Not run on this host: no Linux host or WSL available. |
| `windows` (Ubuntu 24.04 under WSL2, full suite) | Not run on this host: WSL is not installed. |
| `windows-unit` (`tests.test_mxc`) | Ran locally: 31 tests, OK. |
| `windows-unit` (`tests.test_platforms -k Windows`) | Ran locally: 9 tests, 1 pre-existing failure — `NativeWindows.test_windows_runs_carry_the_containment_hook_not_fail_unavailable` reads only the hook's `command` (`sys.executable`), while `mxc.hook_settings()` now carries the helper in `args`; this is in the original baseline and unrelated to Claude connection pass-through. |
| `windows-unit` (`tests.test_platforms -k .Mode.`) | Ran locally: 4 tests, OK. |

The macOS, Ubuntu 24.04 and WSL2 jobs remain the authoritative gates for the POSIX fake-shim
scenarios and for the legacy API-key, sandbox, guard, MCP, session, no-migration, and
credential-sentinel checks that this host can only partially exercise.
