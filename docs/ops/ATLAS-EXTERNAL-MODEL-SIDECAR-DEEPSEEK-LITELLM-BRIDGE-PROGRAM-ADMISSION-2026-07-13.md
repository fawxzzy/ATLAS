# External Model Sidecar Provider Integration - DeepSeek/LiteLLM Bridge

## Admission

- Status: admitted planning-only program
- Marker: `0%`; progress is `0 / 6`; admission completes no unit
- Lane: `External Model Sidecar Provider Integration - DeepSeek/LiteLLM Bridge`
- Owner: ATLAS root governance
- Admission date: 2026-07-13
- Provenance: operator-provided DeepSeek bridge execution order, admitted on 2026-07-13; local attachment path intentionally not persisted
- No workstation or external-system mutation occurred in this admission.

Native OpenAI remains fallback. There is no global redirect. Custom provider support must be proven before integration. The design preserves existing OpenAI/Codex behavior and permits only an explicit route after capability evidence is accepted.

## Six admitted units

Each unit is planned and not complete. The denominator is six, the numerator is zero, and no unit is credited by admission or documentation.

1. Read-only capability audit - outcome: admitted, not executed; inspect supported Codex, `_stack`, Atlas Control, LiteLLM, route, identity, and runtime capabilities without mutation.
2. Security/identity/runtime contract freeze - outcome: admitted, not executed; freeze secret handling, task identity, loopback boundary, logging redaction, backup, timeout, retry, and rollback contracts.
3. Dedicated runtime and one-time credential setup - outcome: admitted, not executed; request the future key exactly once at Phase 3, store it through the approved secret mechanism, and never print, commit, pass in process arguments, or write it to plaintext logs.
4. Loopback LiteLLM proxy and Scheduled Task - outcome: admitted, not executed; install/configure the dedicated runtime, bind only to loopback, and create persistent startup only after the prior gates pass.
5. Explicit-route Codex/_stack/Atlas Control integration only if proven supported - outcome: admitted, not executed; retain native OpenAI fallback and stop if custom provider support is not proven.
6. End-to-end/restart/persistence/failure/rollback proof - outcome: admitted, not executed; prove health, restart, persistence, failure handling, rollback, and explicit-route behavior before any completion claim.

## Boundaries and denied actions

This admission is planning-only. No software install, no secret request, no Program Files write, no Credential Manager write, no Scheduled Task write, no port binding, no Codex config write, and no paid API call occurs here. No workstation or external-system mutation occurred in this admission.

Future execution must use `Discover -> Back Up -> Modify -> Validate -> Document`, preserve native OpenAI as fallback, avoid a global redirect, and stop when custom provider support cannot be proven. The future key is requested exactly once at Phase 3 and is never printed, committed, passed in process arguments, or written to plaintext logs.

## Candidate doctrine

- External Model Sidecar
- Secret/Identity Alignment
- Discover -> Back Up -> Modify -> Validate -> Document
- Listening Is Not Healthy
- Dedicated Runtime

## Dependencies, risks, and resume gates

- Dependencies: Phase 1 capability evidence; Phase 2 security, identity, runtime, backup, and rollback contract; supported explicit provider route; approved secret-access identity; loopback health and persistence evidence.
- Risks: unsupported custom provider route, secret/task identity mismatch, a listening but unhealthy proxy, credential exposure, global redirect, or incomplete rollback.
- Resume gates: read-only capability evidence accepted; contract freeze accepted; one-time credential request authorized; dedicated runtime and task changes explicitly authorized; explicit route proven supported; end-to-end and rollback proof accepted.
- Cross-system links: Codex, `_stack`, Atlas Control, LiteLLM, Windows runtime, secret store, and Scheduled Task are future integration surfaces only; none were changed here.

## Exact next packet

`External Model Sidecar Provider Integration Phase 1 read-only capability audit`

No other marker moves. This admission creates no implementation, installation, secret, service, task, port, configuration, or paid-request state.
