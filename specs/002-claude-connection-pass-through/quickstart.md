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

## Scenario A — Signed-Out Setup Passes

1. Put fake `claude` first on `PATH`.
2. Make `claude --version` succeed.
3. Make `claude auth status` return `{"loggedIn":false,"authMethod":"none"}`.
4. Run the setup/check function under test.

Expected:

- mandatory Claude row passes;
- status says installed/available, not signed in;
- no command invokes `claude auth login`;
- setup does not exit because account status is false.

## Scenario B — User Settings and Environment Reach Employee Work

1. Add sentinel provider values to inherited environment.
2. Point fake Claude's config home at a temporary user settings file with another sentinel.
3. Build and run one employee command.

Expected:

- argv contains `--setting-sources user,project`;
- provider sentinels remain in environment;
- `CLAUDECODE` is absent;
- Orbit employee/workspace values override inherited values;
- sandbox, guard, strict MCP, model, effort, allowed tools, and denied tools remain present.

## Scenario C — Hiring Uses Same Connection

Run `onboard._ask()` against fake Claude.

Expected:

- argv selects `--setting-sources user`;
- inherited connection sentinels remain;
- `--tools ""`, strict MCP, schema, no-session-persistence, system prompt, model, and effort remain;
- valid structured output is returned.

## Scenario D — Anthropic Host Is Not a Gate

1. Make any socket attempt to `api.anthropic.com:443` fail the test.
2. Make fake Claude return a valid employee result.
3. Run chat and scheduled-work paths.

Expected:

- no Anthropic socket attempt occurs before launch;
- fake Claude starts immediately;
- work succeeds;
- scheduler does not defer solely because Anthropic is unreachable.

## Scenario E — Provider-Neutral Failure

Make fake Claude return each of:

- authentication failure;
- connection refused/network timeout;
- rate limit;
- unknown provider failure.

Expected:

- owner text refers to Claude's configured connection where classified;
- generic local-work text never prescribes `claude auth login`;
- transient network/rate failures retain retry metadata;
- no second provider or fallback process starts.

## Scenario F — Cloud Shift Eligibility Matrix

Test account status methods `none`, `third_party`, `api_key`, and the supported Claude-account method.

Expected:

- first three make `cloud.available()` return an account-only reason;
- manual enable fails for ineligible methods;
- new hire does not set `cloud_shift` for ineligible methods;
- supported account method retains existing enable/setup behavior;
- cloud commands still receive sanitized environment and empty setting sources.

## Scenario G — Legacy Orbit API Key Is Unchanged

1. Set `staff.json.auth` to `api_key` and store a test key through existing secret storage.
2. Add conflicting inherited base URL, auth token, API key, and provider flags.
3. Build employee and onboarding launches.

Expected:

- conflicting inherited provider values are absent;
- only stored Orbit API key is injected;
- existing isolated setting-source behavior remains;
- no user setting can reroute the key.

## Scenario H — Trusted User Customization Is Explicit

Use a fake user settings file containing a hook/plugin marker.

Expected:

- ordinary launch includes user setting source;
- Orbit docs state owner hooks/plugins are trusted and may execute;
- Orbit does not claim those customizations are provider-only or sandboxed;
- inherited credential values do not appear in registry, employee files, logs, or panel JSON fixtures.

## Static Checks

Search production/setup surfaces for stale global requirements:

```bash
rg -n "Claude Code isn't signed in|Signed in to Claude|claude auth login|paid Claude plan" orbit core install.sh setup-windows.ps1 SETUP.md README.md
rg -n "api\.anthropic\.com" core orbit
rg -n "ANTHROPIC_|CLAUDE_CODE_" core/engine.py core/onboard.py core/panel.py orbit
```

Expected:

- login instructions remain only in clearly account-only Cloud Shift guidance, if present;
- no ordinary runtime connectivity probe targets Anthropic;
- provider-variable filtering exists only in documented legacy API-key or Cloud Shift isolation paths;
- no provider profile/schema/module was added.
