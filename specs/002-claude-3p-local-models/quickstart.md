# Quickstart: Validation Guide — Claude 3P Local Model Support

Feature: `002-claude-3p-local-models`. This is a validation/run guide, not model-runtime installation documentation. Read [gateway-relay contract](./contracts/gateway-relay.md), [readiness contract](./contracts/readiness.md), and [run-routing contract](./contracts/run-routing.md) first.

## Automated Baseline

From repository root:

```text
python -m unittest discover -s tests
```

Expected: all existing subscription/API-key tests pass unchanged; new provider tests pass without a real model, account, or internet connection. CI runs equivalent suites on macOS, Linux, native Windows, and WSL2.

## Scenario A — Clean Local Setup, No Claude Account (US1, SC-001)

**Prerequisites**:

- current supported Claude Code installed but never signed in;
- one same-computer Anthropic Messages-compatible gateway already running;
- a loaded model with at least 32K input context, streaming, tool use, and reliable structured output;
- no internet connection required after binaries/runtime/model are present.

**Steps**:

1. Run `orbit setup`.
2. Choose **Local gateway**.
3. Enter the loopback base URL, credential style, primary model, and fallback model. For a no-auth gateway, choose **None**; Orbit supplies only a harmless internal placeholder to Claude.
4. Run readiness. Expect separate passes for endpoint, credential, each model, streaming, tools, hiring output, and 32K context.
5. Confirm activation.
6. Complete business setup, run the hiring interview, hire one person, and give them a real file-producing task.

**Expected**:

- no `claude auth login`, account page, or Anthropic API key request;
- setup + hire + completed task within 10 minutes on already-running compatible hardware;
- Settings and `orbit doctor` show Local gateway, safe address, exact model, result time, and recovery action;
- gateway records all model calls; an Anthropic sink records zero inference calls.

## Scenario B — Offline Local Work (US1.5, FR-012/017)

1. With Local gateway active and healthy, disconnect internet access while leaving loopback working.
2. Ask an employee to create/summarize a local text file; use no connector, website, chat delivery, or owner-enabled external tool.

**Expected**: provider remains ready and task completes. Status may explain that update checks/chat/connectors need network, but internet loss alone does not block inference.

## Scenario C — Readiness Failure Matrix (SC-003)

For each row, stage settings and run readiness. Keep a previously working profile active.

| Fault | Expected code/message | Expected recovery |
| --- | --- | --- |
| Gateway stopped/wrong port | `gateway_unreachable` | Start gateway or correct address |
| 401/403 | `credential_rejected` | Replace/check credential style |
| Model absent/unloaded | `model_unavailable` | Load/select exact model |
| Buffered/incomplete/malformed SSE | `stream_incompatible` | Enable complete Anthropic streaming |
| Model never calls canary tool | `tool_use_missing` | Choose tool-capable model/gateway |
| Hiring schema absent/invalid | `structured_output_missing` | Choose compatible model/gateway |
| Context below 32K | `context_too_small` | Raise configured context/load another model |
| 429/529 during check | `gateway_saturated` | Wait for capacity/stop other work |
| Redirect to any target | `redirect_refused` | Enter final loopback URL directly |

**Expected for every row**: specific blocker and action within 30 seconds, candidate values preserved, no crew work starts, active provider/generation unchanged, zero fallback requests.

## Scenario D — Routing and Secret Isolation (SC-002/008)

Use a test gateway that records destination, path, model, and header names but redacts values; also run listeners on representative Anthropic inference hosts through the test seam.

Run:

1. hiring questions/card;
2. employee panel chat;
3. one scheduled routine;
4. role-share summary;
5. employee tool call.

Inspect panel responses, `staffd.log`, orders/activity/run logs, child argv/env capture, employee-readable files, and process details.

**Expected**:

- every model request goes `Claude → Orbit relay → selected loopback gateway`;
- upstream request model is exact bound model;
- relay strips placeholder/caller auth and inserts only selected upstream auth;
- saved Claude OAuth/API credentials and local gateway secret appear nowhere in inspected surfaces;
- no request reaches Anthropic inference;
- tool subprocess cannot read provider profile or credential.

## Scenario E — Capacity, Stop/Restart, No Duplicate Work (US2.2, FR-019)

1. Set local profile capacity to one.
2. Submit work simultaneously to three employees; each writes a uniquely named canary file once.
3. Observe two runs in **Waiting for local model** state.
4. Make gateway return `429`/`529` for active run, then restore capacity before its normal deadline.
5. Separately stop gateway during a streamed response and restore it.

**Expected**:

- FIFO visible wait; one active local process by default;
- capacity retry remains same `run_id` and process/session; work resumes when accepted;
- each canary exists once, with no duplicate tool execution;
- a partial/malformed stream fails without Orbit launching a replay;
- deadline expiry produces provider-specific failure and preserves task/history records.

## Scenario F — Provider Switching and Removal (US2.3, SC-005)

1. Start a long local run and queue another local run.
2. Stage and validate Claude-account or API-key mode.
3. Confirm switch; submit new work.
4. Verify old accepted runs retain local binding; new work uses destination provider.
5. Switch back after local readiness passes.
6. After all old bindings finish, switch away and remove local profile/credential.
7. Hash/compare employee directories and team settings before/after, excluding expected run/activity additions.

**Expected**:

- each switch under three minutes once destination is ready;
- no in-flight rerouting, fallback, or cancellation;
- provider removal blocked while a binding references it, then removes only profile/secret;
- employees, history, skills, routines, model files, and owner settings remain.

## Scenario G — Cloud Shift Suspension

1. In Claude-account mode, enable cloud shift for an employee and confirm triggers exist.
2. Activate validated Local gateway.
3. Inspect employee Manage view and cloud status.
4. Switch back to validated Claude-account mode.

**Expected**:

- local activation does not commit until old triggers are disabled;
- desired preference remains stored but local UI says suspended/unavailable;
- no future cloud trigger runs while local active;
- switching back rearms preference or reports a visible rearm error; no preference loss.

## Scenario H — Usage and Cost Presentation (FR-020)

Run several local tasks with a gateway that returns token usage but no cost, then with a test gateway that returns explicit trusted local cost metadata.

**Expected**:

- tokens/work shown when measured;
- no Claude 5-hour/weekly plan meters, plan-limit warning, or Anthropic billing claim;
- first gateway shows cost `unknown`, never a Claude-equivalent estimate;
- explicit gateway cost is labeled gateway-reported.

## Scenario I — Open in Claude Desktop 3P (US3)

1. Keep Claude account signed out.
2. With Orbit local mode active, select **Open in Claude** before configuring Desktop.
3. Follow Orbit's guide in Claude Desktop: Help → Troubleshooting → Enable Developer Mode; Developer → Configure Third-Party Inference; choose Gateway; enter matching endpoint/auth/model; Apply Changes; Save & Restart.
4. Retry **Open in Claude**.
5. Complete a tool-using task and verify gateway traffic.
6. Change Desktop endpoint/model to a mismatch and retry.

**Expected**:

- first attempt does not redirect to account sign-in and makes no global config edit;
- Orbit reports `matching` only after effective Desktop config matches;
- employee workspace, role, memory, tools, guard, sandbox, and approvals remain active;
- mismatch/unverified config blocks the local claim and gives exact correction steps;
- credential never appears in Orbit UI/logs/diagnostics.

## Scenario J — Cross-Gateway / Cross-OS Qualification (SC-006)

Use two independent gateway implementations that pass readiness on the validation date. Initial candidates are Ollama 0.14+ and LM Studio 0.4.1+; replace either if its current build cannot pass every mandatory check. Orbit does not install or endorse either.

For each supported OS and gateway:

1. Load the same capable model/config where possible, at 32K+ context.
2. Run the standard Orbit task suite: hire, chat, routine, plan/summary, tools, files, cancellation/deadline, capacity wait, provider switch, interactive session where that OS/app supports it.
3. Record Orbit-specific routing/parsing/tool-control failures separately from model-quality failures.

**Expected**: at least 95% standard tasks complete without Orbit-specific failure. Headless operation is the required all-OS baseline; interactive result records installed Desktop support separately.

## Scenario K — Relay Overhead (SC-007)

For 20 representative prompts, record gateway first-byte handling time:

1. direct request to same gateway/model;
2. equivalent request through Orbit relay.

Use warmed model, alternating order, same machine, response streaming on. Exclude model generation time after upstream first handling.

**Expected**: Orbit adds no more than two seconds median; target is below 100 ms. No relay response buffering.

## Scenario L — Legacy Regression (FR-026, SC-009)

1. Upgrade one subscription install and one API-key install without opening provider settings.
2. Run setup/status/doctor, hiring, chat, routine, usage display, cloud shift, and Open in Claude.
3. Run all pre-feature automated tests unchanged.

**Expected**: provider selection and stored team data remain unchanged; behavior/error text/model routing/cloud shift match baseline; neither mode ever routes through a local profile unless owner confirms a switch.

## Scenario M — First-Attempt Usability and Comprehension (SC-004/010)

Recruit at least 10 non-technical owners. Give each a clean Orbit home, installed supported Claude client with no account session, and an already-running compatible local gateway/model. Give only the task: “Connect this local model, hire one crew member, and finish one task.” Do not provide external docs or coaching; Orbit's own UI guidance is allowed.

Record:

- whether connection/readiness succeeds on first attempt;
- elapsed setup/hire/task time;
- screen/error where an attempt stops;
- after completion, answers to four questions: active provider; whether inference leaves computer; why cloud shift is unavailable; how to switch or recover.

**Expected**:

- at least 9/10 connect on first attempt;
- at least 90% answer all four comprehension topics correctly;
- no participant is directed to Claude account sign-in or exposes a credential in chat;
- observed confusion becomes copy/flow fixes before release, then affected checks are rerun.
