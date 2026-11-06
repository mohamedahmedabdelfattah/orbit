# Implementation Plan: Claude 3P Local Model Support

**Feature**: `002-claude-3p-local-models` — [spec.md](./spec.md)

**Status**: Plan complete

**Branch**: `main` (current worktree is detached at `main`; no branch hook is configured)

## Technical Context

| Dimension | Decision | Notes |
| --- | --- | --- |
| Runtime | Python 3.9-compatible; plain browser JavaScript; no new runtime dependency | Matches Orbit's current kit. HTTP validation and relay use Python stdlib (`http.client`, `http.server`, `urllib.parse`, `ipaddress`). |
| Claude integration | Official Claude Code LLM-gateway controls for headless work; Claude Desktop 3P configuration for interactive sessions | CLI and Desktop use different configuration surfaces and must be verified separately. |
| Gateway protocol | Anthropic Messages-compatible loopback gateway: `POST /v1/messages`; streaming and tool use required; `GET /v1/models` and token counting optional | Orbit tests actual required behavior instead of trusting a product name or capability claim. |
| Provider architecture | New harness-owned `core/inference.py` is sole source for provider selection, migration, routing env, model resolution, readiness, health, redaction, and local relay | Replaces duplicated auth/env logic in `engine.py`, `onboard.py`, `panel.py`, and setup/doctor. |
| Secret boundary | Real local-gateway credentials stay in `~/Staff/.secrets` and in Orbit parent-process memory; Claude talks to an ephemeral Orbit loopback relay with a harmless fixed placeholder | Credential never appears in Claude's argv, environment, settings, workspace, logs, or tool subprocesses. Relay injects the selected upstream header. |
| Endpoint safety | Only canonical loopback HTTP/HTTPS base URLs; no user info, query, or fragment; loopback resolution pinned; redirects rejected | Relay opens only the validated upstream address and only supported API paths. |
| Model routing | Exact gateway models assigned to `primary` and `fallback` workload roles; employee local role stored separately from existing Claude-family choice | `fallback` is an explicit workload assignment, never automatic error fallback. Existing `opus`/`sonnet`/`haiku` choices remain intact for cloud modes. |
| Context handling | Require and probe at least 32,000 input tokens; launch Claude with an Orbit synthetic model ID and `CLAUDE_CODE_MAX_CONTEXT_TOKENS` set to the verified window | Relay rewrites only the synthetic model ID to the exact gateway ID. This avoids Claude's built-in assumptions for model-like aliases. |
| Run binding | Snapshot profile ID, revision, model role, exact model, and deadline when work is accepted | Queued and running work cannot be silently rerouted by a provider switch. Session IDs are namespaced by provider revision. |
| Capacity | One local inference run at a time by default, with a profile-scoped gate and visible FIFO wait state; parse Claude `system/api_retry` events for gateway saturation | No duplicate process launch. Existing task deadline remains the outer bound. Advanced concurrency can be raised only by owner config. |
| Storage | Extend `~/Staff/staff.json`; secrets remain separate files; readiness stores only sanitized evidence | Legacy `auth` is read as migration input. Existing installs are not rewritten until owner changes provider settings. |
| UI/CLI | Provider card in setup/Settings; provider-aware checklist, status, doctor, usage, cloud-shift controls; `orbit provider ...` commands | All responses omit secret values and credential-bearing URLs. |
| Interactive app | Read and compare effective Claude Desktop 3P configuration; guide owner through app's supported configuration UI; never write another app's global config in v1 | `Open in Claude` is gated on a verified matching endpoint, auth scheme, and model list. |
| Tests | `unittest`, fake Claude executable, two in-process fake gateways, socket egress trap, all existing suites unchanged | Real-model qualification remains an on-demand matrix across two independent gateways and each supported OS. |
| Performance | Relay startup plus forwarding target <100 ms median and <2 s median Orbit-added delay | Stream bytes immediately; never buffer an upstream response. |

**Constitution check**: `.specify/memory/constitution.md` does not exist. No project constitution constraints apply; no gate violations.

## Architecture Decisions

Full evidence and alternatives: [research.md](./research.md).

1. **One provider boundary for every model-backed flow.** `core/inference.py` supplies immutable run bindings and launch material. `engine.run()` and `onboard._ask()` consume it; role sharing already reaches `onboard._ask()`. Cloud-only calls are explicitly unavailable in local mode rather than accidentally inheriting local settings.
2. **Credential-injecting loopback relay, not a provider credential in Claude's environment.** Orbit starts one short-lived relay for each local Claude process. Claude receives a fixed non-secret placeholder and an isolated `CLAUDE_CONFIG_DIR`; the relay strips `Authorization`, `x-api-key`, cookies, and caller routing headers, then adds only the active local profile's selected credential upstream.
3. **Synthetic client model IDs.** Claude sees an unrecognized `orbit-local-*` model ID and a verified context-window override. The relay maps that ID to exactly one selected gateway model and rejects all other model IDs. Internal/background model aliases are pinned to that same synthetic ID for the process.
4. **Staged activation.** A candidate profile is saved separately, fully checked, then activated only after owner confirmation and an optimistic readiness-result/revision match. Failed checks retain the draft and leave the old provider active.
5. **Immutable acceptance-time routing.** Work captures a provider binding before employee and provider-capacity queues. Provider switches affect only work accepted afterward. Existing queued/running work finishes or reaches its original deadline on its original binding.
6. **Readiness proves the exact Orbit path.** Static URL checks and raw protocol probes are followed by real `claude -p` streaming, tool-use, and hiring-schema probes through the relay for each distinct assigned model. A 32K-input challenge verifies context capacity.
7. **No automatic model/provider failover.** Runtime unavailability blocks the profile. Capacity responses wait/retry on the same bound profile. Partial or malformed streams fail without an Orbit-level replay.
8. **Local mode suspends cloud shift; it does not erase preference.** Activation must disable existing cloud triggers before the provider commit. Desired cloud-shift settings remain stored and can be restored after a validated switch back.
9. **Claude Desktop stays owner-controlled.** Orbit inspects and compares supported 3P config sources, shows exact guided changes, and opens an employee only after a match. It does not edit Claude Desktop's local/managed configuration.

## Planned Code Surfaces

| Surface | Planned change |
| --- | --- |
| `core/inference.py` *(new)* | Profile migration, candidate/activation transaction, safe URL validation, model discovery, readiness probes/results, immutable run binding, launch settings, redaction, relay, health/error taxonomy. |
| `core/desktop3p.py` *(new)* | Claude Desktop install/version discovery, effective 3P config inspection, sanitized comparison, guided setup state. |
| `core/engine.py` | Consume run binding; provider-aware model/env/online/error/usage logic; relay lifecycle; provider-namespaced sessions; run-log fields. |
| `core/onboard.py` | Use shared inference launch path and provider-selected primary model for both structured hiring calls. |
| `core/team.py`, `core/staffd.py` | Bind provider at acceptance; local capacity queue and waiting states; preserve same-provider retries; provider-aware scheduling. |
| `core/cloud.py`, `core/orders.py` | Suspend/restore cloud triggers across mode switches; prevent local-mode enable/default-on behavior. |
| `core/panel.py`, `core/panel/app.js` | Sanitized provider API and setup/Settings/doctor status; local usage/model/cloud copy; guided Desktop 3P flow. |
| `orbit` | `provider` commands; setup and doctor provider checks; provider-aware connectivity and exact upgrade action. |
| `install.sh`, `setup-windows.ps1`, `SETUP.md`, `README.md` | Require Claude installation, not account sign-in; document three modes, locality limits, recovery, switch, and removal. |
| `tests/` and `.github/workflows/tests.yml` | Fake gateway/Claude seams, routing and leak tests on macOS/Linux/Windows jobs, unchanged legacy-mode regression suites. |

## Phase 0: Research

See [research.md](./research.md). Resolved decisions:

- D1: official headless and Desktop 3P integration surfaces and minimum client behavior.
- D2: one provider boundary and backward-compatible registry migration.
- D3: credential containment through an ephemeral relay and isolated Claude config.
- D4: loopback URL validation, redirect refusal, and destination pinning.
- D5: readiness matrix and stable owner-facing failure taxonomy.
- D6: model discovery, primary/fallback roles, synthetic IDs, and 32K context handling.
- D7: acceptance-time binding, capacity waiting, retry, and partial-stream semantics.
- D8: local usage/cost presentation and cloud-shift suspension.
- D9: Claude Desktop 3P verification and owner-controlled configuration.
- D10: test seams, qualification matrix, and performance evidence.

No `NEEDS CLARIFICATION` items remain.

## Phase 1: Design

- [data-model.md](./data-model.md) — registry additions, readiness evidence, run bindings, cloud preferences, and state transitions.
- [contracts/provider-control.md](./contracts/provider-control.md) — owner CLI/panel API, staged check/activation/switch/removal contract.
- [contracts/gateway-relay.md](./contracts/gateway-relay.md) — gateway protocol, endpoint safety, credential injection, model rewriting, and streaming invariants.
- [contracts/readiness.md](./contracts/readiness.md) — capability probes, verdict rules, cache/recheck behavior, and error taxonomy.
- [contracts/run-routing.md](./contracts/run-routing.md) — immutable provider binding, queues, retries, sessions, usage records, and fail-closed behavior.
- [contracts/desktop-3p.md](./contracts/desktop-3p.md) — Claude Desktop inspection, matching, guided setup, and Open-in-Claude gate.
- [quickstart.md](./quickstart.md) — automated and real-host end-to-end validation scenarios.

## Post-design Constitution Re-check

N/A: no constitution file. Design preserves current safety controls and adds stricter local-provider isolation; no gate violation introduced.

## Requirement Coverage

| Requirements | Design evidence |
| --- | --- |
| FR-001–008 | [provider-control.md](./contracts/provider-control.md), [readiness.md](./contracts/readiness.md), provider/profile/readiness entities |
| FR-009–015 | [gateway-relay.md](./contracts/gateway-relay.md), [run-routing.md](./contracts/run-routing.md), isolated config + credential-injecting relay |
| FR-016–021 | Provider surfaces, failure taxonomy, capacity states, usage record, cloud preference model |
| FR-022–025 | [desktop-3p.md](./contracts/desktop-3p.md), staged switch/removal contracts, immutable run binding |
| FR-026–030 | Lazy legacy migration, unchanged mode contracts, client version gate, shared safety generation, planned docs/test surfaces |
| SC-001–010 | [quickstart.md](./quickstart.md) scenarios A–M plus automated fake-gateway/security seams |

## Risks

| Risk | Mitigation |
| --- | --- |
| A gateway advertises Anthropic compatibility but drops current Claude fields or produces malformed streams | Exact raw + Claude CLI readiness suite; activation fails by capability; no product allowlist. |
| Provider credentials inherited by model-generated shell/MCP processes | Never place real local credential in Claude env/settings/argv; relay injects it from parent memory; protected secret path remains denied. |
| Saved Claude login or API key silently wins | Scrub provider variables, isolated `CLAUDE_CONFIG_DIR`, fixed placeholder to relay, relay strips caller auth, readiness egress trap. |
| Endpoint changes after validation or redirects off host | Canonical loopback-only address, pinned numeric destination, no redirects, validation repeated when relay opens. |
| Local model uses less context than Claude assumes | Synthetic ID plus verified context override; 32K challenge; exact context failure message. |
| Busy single-model gateway causes duplicate work | Profile FIFO gate; one Claude process per accepted run; parse internal retry events; no outer replay after partial output. |
| Switch races with queued/running work | Acceptance-time immutable binding and profile revision; removal blocked while bindings remain. |
| Local activation leaves old cloud triggers running | Trigger suspension is a pre-commit activation gate; failure leaves old provider active. |
| Desktop app routes differently from headless Orbit | Separate effective-config inspection; mismatch/unverified state blocks `Open in Claude`; no false “local” claim. |
| Relay adds latency or buffers output | In-process stdlib relay, response streaming, timing telemetry without payloads; SC-007 benchmark in quickstart. |
| Non-Claude local model quality is too weak for reliable tool use | Full readiness canary and qualification suite; docs state compatibility does not guarantee answer quality. |
