# External Model Sidecar Provider Integration - DeepSeek/LiteLLM Bridge

## Contract Status

Phase 2 is accepted and frozen for the six-unit program. This contract is documentation and machine-readable policy only; it authorizes no implementation or external action. Phase 2 completes unit `2 / 6`, `33.3%` rounded to one decimal. Native OpenAI remains the base/default path and explicit fallback.

## Architecture and Ownership

ATLAS root governance owns this contract. The external provider is an opt-in sidecar selected only through a task/job declaration naming `deepseek-sidecar`; ambient or global routing is denied. `_stack` and Atlas Control must record requested and effective provider, profile, model, reasoning, speed, and fallback. Native OpenAI fallback requires an explicit fallback policy or operator choice; silent provider substitution is denied.

## Runtime Location and Identity

v1 is current-user scoped at `${LOCALAPPDATA}/ATLAS/DeepSeekBridge`. `C:/Program Files/DeepSeekBridge` is deferred and is not used. The dedicated virtual environment is `${LOCALAPPDATA}/ATLAS/DeepSeekBridge/venv`; Phase 3 must pin and receipt the exact Python and LiteLLM versions before installation. No global Python or package mutation is allowed.

The interactive operator, Credential Manager owner, LiteLLM process, Scheduled Task principal, and Codex profile owner are the same Windows user. The future Scheduled Task uses a user-logon trigger and least-privilege current-user execution, stores no account password, and does not claim to run while the user is logged out. Availability requires the host to be awake and the user signed in.

## Secret Storage and Retrieval

The only credential targets are current-user Windows Credential Manager generic credentials `ATLAS/DeepSeekBridge/ProviderApiKey` and `ATLAS/DeepSeekBridge/ProxyToken`. A dedicated local helper uses native Windows Credential Manager APIs. The provider key is retrieved directly into the proxy child environment and is never printed. The generated proxy token may be emitted only to a direct Codex command-backed authentication stdout pipe, with no inherited console, transcript, log, receipt, or process-argument exposure. Empty or failed retrieval is fail-closed.

## Codex Profile and Provider Route

The user-level opt-in profile is `${CODEX_HOME}/deepseek-sidecar.config.toml`, invoked only with `--profile deepseek-sidecar`. Its provider ID is `atlas_deepseek_sidecar`, base URL is `http://127.0.0.1:4000/v1`, and configuration uses `wire_api = "responses"`. Command-backed authentication retrieves only the proxy token; it must not be combined with `env_key`, `experimental_bearer_token`, or `requires_openai_auth`. No base user config global redirect is allowed.

## LiteLLM Proxy Contract

The proxy binds only `127.0.0.1:4000`; it never binds `0.0.0.0`, LAN, public, or remote addresses, and no firewall exposure is added. A generated local client token is required even on loopback. LiteLLM exposes an OpenAI Responses-compatible endpoint to Codex and explicitly bridges to DeepSeek Chat Completions with `use_chat_completions_api: true` or an equivalent `openai/chat_completions/<model>` route.

Stable aliases are `atlas-deepseek-pro` to `deepseek-v4-pro` and `atlas-deepseek-flash` to `deepseek-v4-flash`. Pro is the default external sidecar route; flash is a lower-cost explicit alternative. Deprecated `deepseek-chat` and `deepseek-reasoner` aliases are never durable routes. Exact upstream compatibility remains subject to Phase 4 proof.

## Data Classification and Privacy

- D0 public, synthetic, or benchmark data is allowed only by an explicit sidecar route.
- D1 internal source code, architecture, prompts, and non-secret repository context is allowed only when the job explicitly selects the sidecar and a preflight confirms that no secrets, credentials, production data, private account data, or regulated data are included.
- D2 secrets, credentials, tokens, production database content, private user/account data, payment data, auth/session material, and unredacted operational logs are denied.

The task receipt records classification and route but never content.

## Logging and Receipt Redaction

Allowed telemetry is timestamps, route alias, status, latency, token counts, retry counts, redacted error classes, and correlation IDs. Prompts, request/response bodies, Authorization headers, keys, proxy tokens, source excerpts, and tool output content are denied. LiteLLM request/response body logging is disabled, and secret-helper output has no inherited console.

## Health, Retry, and Persistence

Listening is not healthy. Readiness requires authenticated loopback health, expected model aliases, bridge configuration checksum, credential retrieval success without disclosure, and a non-paid local route/config probe. Paid/provider proof waits for explicit authorization in Phase 4 or later.

The startup readiness deadline is 60 seconds and health request timeout is 2 seconds. Provider request max retries are 2, stream max retries are 2, and stream idle timeout is 120 seconds. The future Scheduled Task restart interval is 60 seconds with at most 3 restart attempts per failure window. No unbounded loop is allowed.

The future task starts at current-user logon and may restart after failure. Phase 4 must prove start, stop, restart, duplicate-instance prevention, and lock/port ownership. One process owns the loopback port.

## Backup and Rollback

Before every future config, helper, or task mutation, copy the prior non-secret artifact to `${LOCALAPPDATA}/ATLAS/DeepSeekBridge/backups/<UTC timestamp>/` with a SHA-256 manifest. Secret values are never backed up in plaintext.

Rollback stops the task/process, verifies port release, restores the last checksummed non-secret backup, removes or disables only the named Codex profile and task created by this program, preserves native OpenAI configuration, and verifies native OpenAI health. Credential deletion is separately explicit and is not implied by software rollback.

## Phase 3 Admission Checklist

- Confirm root and `_stack` state are clean and published.
- Confirm Python version and select/pin a LiteLLM version compatible with `/responses` bridging.
- Create only the user-scoped runtime directories and venv.
- Implement and locally test the native Credential Manager helper without a real provider key first.
- Generate the local proxy token without displaying it and store it in the named current-user credential target.
- Request the DeepSeek key exactly once through a secure local prompt; never through chat, command arguments, committed files, clipboard logs, or plaintext output.
- Store it only in the named current-user Credential Manager target, then prove redacted retrieval.
- Do not yet create the Scheduled Task or start a listening proxy; those are Phase 4.
- If secure key entry is unavailable, stop Phase 3 at a durable blocker receipt and switch lanes.

## Mutations Explicitly Not Performed

No software was installed or updated. No secret was requested, written, stored, or handled. Windows Credential Manager was not read, written, or deleted. No Scheduled Task, service, startup entry, listener, firewall rule, or process was created or modified. No port was bound. No user-level or project Codex configuration was edited. No DeepSeek or other paid API call was made. No owner repositories, Discord, Vercel, Supabase, production, or other marker lanes were mutated.

## Marker Decision

Only the External Model Sidecar Provider Integration - DeepSeek/LiteLLM Bridge lane moves from `16.7%` (`1 / 6`) to `33.3%` (`2 / 6`). Phase 1 remains completed, Phase 2 is completed with this frozen contract, Phase 3 is ready, and Phases 4 through 6 remain admitted but not executed. No other marker moved.

## Exact Next Packet

`External Model Sidecar Provider Integration Phase 3 dedicated runtime and one-time credential setup`
