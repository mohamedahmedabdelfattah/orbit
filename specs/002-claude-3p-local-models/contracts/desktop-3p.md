# Contract: Claude Desktop 3P Verification and Open in Claude

**Producer**: `core/desktop3p.py` and `engine.claude_session()`.

**Consumer**: panel `Open in Claude`, setup/Settings guidance, doctor.

Claude Desktop controls interactive-provider routing. Orbit controls employee workspace/settings/guard. Both must match before Orbit calls the session local.

## Supported Configuration Facts

Orbit inspects, in platform precedence order, documented sources:

| Platform | Managed | Local |
| --- | --- | --- |
| macOS | managed preferences for `com.anthropic.claudefordesktop` | `~/Library/Application Support/Claude-3p/configLibrary/` |
| Windows | `HKLM\SOFTWARE\Policies\Claude`, otherwise HKCU | `%LOCALAPPDATA%\Claude-3p\configLibrary\` |
| Linux | `/etc/claude-desktop/managed-settings.json` | `~/.config/Claude-3p/configLibrary/` |

Relevant keys only:

- `inferenceProvider`
- `inferenceGatewayBaseUrl`
- `inferenceGatewayAuthScheme`
- `inferenceCredentialKind`
- credential presence (value never returned)
- `inferenceModels`
- deployment/source metadata needed to determine precedence

Unknown/bootstrap/admin-delivered values that Orbit cannot prove are `unverified`, not guessed from local stale files.

## Version/Capability Gate

1. Detect installed Claude Desktop/app version from platform-supported package metadata.
2. Require gateway 3P configuration and selected bearer/x-api-key support (minimum documented baseline v1.3036.0; capability detection wins over unusual version strings).
3. If too old: return `too_old` and one action: install current Claude Desktop from `https://claude.com/download`.

Headless Orbit local operation remains available when standalone Claude Code passes its own readiness; this gate controls P3 interactive support.

## Sanitized Status

```json
{
  "installed": true,
  "version": "...",
  "source": "local",
  "provider": "gateway",
  "base_url": "http://127.0.0.1:11434",
  "auth_scheme": "bearer",
  "credential_present": true,
  "credential_matches": true,
  "models": ["local-code-model"],
  "match": "matching",
  "actions": []
}
```

Never return/write credential, config file contents, registry dump, helper output, URL query/user info, or diagnostic lines containing secrets.

## Matching Rules

`matching` requires all:

1. app installed and version/capability gate passes;
2. effective `inferenceProvider == gateway`;
3. canonical endpoint equals Orbit active local endpoint;
4. auth scheme matches (`bearer` for Orbit none/bearer; `x-api-key` for API-key style) and credential is present;
5. when credential values are readable, constant-time comparison succeeds for authenticated gateway; no-auth may use any non-empty harmless placeholder;
6. effective model list/discovery contains Orbit primary and fallback exact IDs;
7. no higher-precedence managed source contradicts these values.

Other states:

| State | Meaning |
| --- | --- |
| `not_configured` | No effective 3P gateway config |
| `mismatch` | Effective facts known and differ |
| `unverified` | Active source/facts cannot be proven safely |
| `too_old` | App lacks required 3P behavior |

Only `matching` permits a response claiming/opening a local interactive employee session.

## Guided Setup

V1 never writes Claude Desktop configuration, registry, managed preferences, or config-library metadata.

For `not_configured`/`mismatch`, show:

1. Explain global effect: changes provider for Claude Desktop Chat/Cowork/Code sessions on this user/device.
2. Exact supported path: Help → Troubleshooting → Enable Developer Mode; Developer → Configure Third-Party Inference.
3. Values: Gateway provider, safe base URL, auth scheme, primary/fallback model IDs. Credential field says `enter the same local gateway credential in Claude` or `enter any harmless placeholder; gateway uses no auth`; no value copied from Orbit.
4. Owner clicks Apply Changes and Save & Restart in Claude Desktop.
5. Orbit rechecks after restart.

If managed/read-only, explain that the managing source must be changed and do not offer a write bypass.

This is explicit owner approval. Any future automated writer is a separate feature and must preview exact source/keys, ask confirmation, preserve backup, and re-verify; it is not part of v1.

## Session Preparation

After `matching`:

1. Run existing `engine.claude_session(emp_id)` workspace preparation.
2. Preserve employee `.claude/settings.local.json` safety settings: sandbox, permission allow/deny, MXC hooks where applicable, environment without provider secrets, MCP grants, Orbit guard plugin.
3. Do not add CLI gateway env to workspace settings; Desktop host supplies provider route/credential.
4. Return existing `claude://code/new?...` employee-folder deep link and hello prompt.
5. On macOS, existing auto-open behavior may open it; elsewhere return link as today.

Provider matching does not weaken Orbit safety policy. A Desktop-managed policy may tighten it.

## API Result

`POST /api/claude_session`:

Success:

```json
{
  "ok": true,
  "provider_verified": "local_gateway",
  "link": "claude://code/new?...",
  "folder": "<employee workspace>",
  "opened": false,
  "hello": "..."
}
```

Blocked (HTTP 409):

```json
{
  "error": "Claude Desktop is pointed at a different provider",
  "desktop": {"match": "mismatch", "base_url": "<safe URL>", "models": ["..."]},
  "actions": ["Open Claude Desktop third-party inference settings", "Set gateway to <safe URL>", "Restart Claude Desktop", "Try again"]
}
```

No result includes credential values.

## Verification Evidence

Automated tests compare all states using fixture config sources and precedence. Real-host validation additionally:

- checks gateway logs for interactive request at selected endpoint/model;
- performs one tool call and confirms Orbit guard/sandbox behavior;
- changes app provider/model and confirms Orbit reports mismatch rather than local;
- confirms account sign-in is absent/unneeded.

Orbit never claims provider identity from the deep link alone.
