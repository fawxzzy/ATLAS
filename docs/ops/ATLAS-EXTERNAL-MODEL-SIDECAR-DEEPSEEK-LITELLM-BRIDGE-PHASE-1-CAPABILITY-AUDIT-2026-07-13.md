# External Model Sidecar Provider Integration - DeepSeek/LiteLLM Bridge

## Executive Decision

The Phase 1 read-only capability audit is accepted as **feasible with constraints**. The workstation, Codex provider shape, LiteLLM Responses bridge documentation, and DeepSeek compatibility are sufficient to proceed to a security, identity, and runtime contract freeze. This does not authorize implementation, credential handling, proxy startup, Codex configuration changes, or model execution.

Configuration capability is proven only to the level of documentation and parser admission: a redacted inline custom-provider probe entered Codex doctor execution. End-to-end provider execution is unproven because doctor did not finish inside the bounded 30-second audit window. Phase 2 is therefore the exact next packet.

## Evidence Method

Audit date: 2026-07-13. Evidence was collected read-only on the canonical Windows workstation and from current product documentation. The audit inspected host identity and elevation, PowerShell and Python runtimes, venv creation, LiteLLM and Codex availability, existing Codex configuration surfaces, TCP port availability, Scheduled Task state, credential-retrieval capabilities, and provider documentation. No live provider key or paid model request was used.

## Workstation and Runtime Findings

- Windows 11 Pro 10.0.26200, AMD64; identity `ZREDFIELD\\zjhre`; current process is not elevated.
- PowerShell 5.1.26100.8737 is available.
- Python 3.13.7 at the current-user installation and Python 3.12.6 at `C:\\Python312` both support venv creation.
- LiteLLM is absent from the inspected Python runtimes and no `litellm` command exists.
- TCP port 4000 was free during the audit. Task Scheduler is running with automatic startup, and no DeepSeek Scheduled Task was found.
- `C:\\Program Files\\DeepSeekBridge` does not exist. Standard Users have read/execute rather than create/write access to `C:\\Program Files`; the current process is not elevated. A machine-wide Program Files path therefore needs an elevated installation step or a separately approved user-scoped path decision.

## Codex Provider Findings

Codex CLI 0.144.1 is present. Its current manual supports custom model providers through `model_provider` and a `model_providers` table with `base_url`, `env_key` or command-backed authentication, and `wire_api = responses`.

Provider and authentication settings cannot be committed in project-local `.codex/config.toml`; Codex ignores provider/auth keys there. The future provider must use a named user-level Codex profile/config and remain opt-in. Native OpenAI stays the default and fallback, with no global redirect.

A redacted inline custom-provider probe was accepted by the Codex configuration parser far enough to enter doctor execution, but doctor did not finish within a bounded 30-second audit window. The provider configuration shape is supported by documentation and parser admission; end-to-end provider execution remains unproven.

## LiteLLM Responses Bridge Findings

LiteLLM 1.63.8+ documents a `/responses` endpoint and an explicit `/responses` to `/chat/completions` bridge. For an OpenAI-compatible custom `api_base` that only supports Chat Completions, the proxy configuration must use `use_chat_completions_api: true` or the `openai/chat_completions/<model>` route. Source: https://docs.litellm.ai/docs/response_api

Required route facts: `use_chat_completions_api: true`; durable models are `deepseek-v4-pro` and `deepseek-v4-flash`; the aliases `deepseek-chat` and `deepseek-reasoner` are scheduled for deprecation on 2026-07-24.

This is a documented route requirement, not proof that a local proxy was installed, started, healthy, or exercised.

## DeepSeek Provider Findings

DeepSeek documents the OpenAI-compatible base URL `https://api.deepseek.com` and current model IDs `deepseek-v4-flash` and `deepseek-v4-pro`. DeepSeek currently documents Chat Completions. The aliases `deepseek-chat` and `deepseek-reasoner` are scheduled for deprecation on 2026-07-24 15:59 UTC and must not be the durable Atlas default. Sources: https://api-docs.deepseek.com/ and https://api-docs.deepseek.com/quick_start/pricing/

## Security and Identity Findings

`cmdkey.exe` exists, but CredentialManager and Microsoft.PowerShell.SecretManagement modules are absent. `cmdkey` does not provide a reliable plaintext-secret retrieval contract for a worker. Phase 2 must freeze a non-logging retrieval helper and align the Scheduled Task identity with the credential owner before any key is requested. The future key must never be printed, committed, passed in process arguments, or written to plaintext logs.

The machine-wide `Program Files path` is blocked pending an elevated installation step or an approved user-scoped alternative. Port availability and Task Scheduler availability are observations only; no listener or task exists.

Phase 2 must freeze credential-owner and Scheduled Task identity alignment before any key is requested; the current process is not elevated.

## Feasibility Matrix

| Capability | Classification | Evidence or constraint |
|---|---|---|
| Windows host | supported | Windows 11 Pro 10.0.26200, AMD64 |
| Python/venv | supported | Python 3.13.7 and 3.12.6 both create venvs |
| LiteLLM installation | absent | LiteLLM and `litellm` command absent |
| Loopback port | supported with constraint | TCP 4000 was free; no port was bound |
| Scheduled Task | supported with constraint | Task Scheduler runs; no task exists and identity contract is pending |
| Program Files path | blocked pending contract | Current process is not elevated; write access is unavailable |
| Credential retrieval | blocked pending contract | No reliable non-logging worker retrieval helper is selected |
| Codex provider shape | supported with constraint | Documentation and parser admission; user-level opt-in required |
| Responses bridge | supported with constraint | LiteLLM documents `/responses`; Chat Completions requires `use_chat_completions_api: true` or route selection |
| Current DeepSeek model route | supported with constraint | Use `deepseek-v4-pro` or `deepseek-v4-flash`; Chat Completions compatibility must be explicitly mapped |
| Explicit opt-in fallback | supported | Native OpenAI remains default and fallback; no global redirect |
| End-to-end proof | unproven | Doctor timed out in the bounded 30-second audit window; no provider call was made |

## Constraints and Blockers

Phase 2 must freeze the user-level Codex profile/config, provider route, data classification, key retrieval behavior, proxy logging policy, runtime location, process identity, Scheduled Task identity, health checks, and rollback boundary. The machine-wide path is not available without elevated authorization or a separate user-scoped path decision. LiteLLM installation, task creation, port binding, key request, and provider execution remain later-phase actions.

## Privacy and Data Classification

Source code, prompts, repository context, and tool outputs routed through the sidecar leave the OpenAI path and may be processed by DeepSeek. Phase 2 must define explicit data classification, deny secrets and production credentials by default, and require deliberate routing. The contract must require prompt/body/key redaction from proxy logs and receipts. No sensitive content may be routed by ambient or global configuration, and native OpenAI must remain the safe default and fallback.

Privacy rule: deny secrets and production credentials by default; require deliberate routing and prompt/body/key redaction from proxy logs and receipts.

## Phase 2 Contract Inputs

- Freeze the exact user-level Codex profile/config and opt-in invocation boundary.
- Freeze explicit route and model policy using `deepseek-v4-pro` and/or `deepseek-v4-flash`; do not adopt deprecated aliases.
- Freeze data classes, with secrets and production credentials denied by default, and deliberate per-request routing.
- Freeze a non-logging credential retrieval helper and the credential owner.
- Freeze Scheduled Task identity to match the credential owner before any key is requested.
- Freeze proxy log and receipt redaction for prompts, request bodies, and keys.
- Freeze runtime path, health/rollback checks, and the unresolved Program Files versus user-scoped path decision.

## Mutations Explicitly Not Performed

- No software was installed.
- No secret was requested or written.
- No port was bound.
- No Scheduled Task was created.
- No Codex configuration was changed.
- No paid API call was made.
- No owner repository, runtime state, secret, production, remote, or external service was changed.

Audit boundary summary: No software was installed; No secret was requested or written; No port was bound; No Scheduled Task was created; No Codex configuration was changed; No paid API call was made.

## Marker Decision

Mark only this lane as moved: from `0 / 6` to `1 / 6`, `16.7%` rounded to one decimal. Phase 1 is complete; Phase 2 is ready; Phases 3 through 6 remain admitted but not executed. No other marker moved. Native OpenAI fallback, no global redirect, and all denied-mutation boundaries remain preserved.

## Exact Next Packet

`External Model Sidecar Provider Integration Phase 2 security identity and runtime contract freeze`
