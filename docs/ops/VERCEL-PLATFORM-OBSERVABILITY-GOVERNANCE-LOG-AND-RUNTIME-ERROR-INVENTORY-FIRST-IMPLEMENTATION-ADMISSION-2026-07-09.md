# Vercel Platform Observability Governance log and runtime-error inventory first-implementation admission

- Date: `2026-07-09`
- Lane: `Vercel Platform Observability Governance`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Control-plane checkpoint: `ca6b66637870b64dc18c89863115be6594c7e157`
- Marker movement: none

## Decision

Admit one future read-only helper/test pair for Vercel log and runtime-error wrapper validation, redaction enforcement, and deterministic observability summary emission.

The next exact packet is:

```text
Vercel Platform Observability Governance log and runtime-error inventory prompt-pack and worker handoff contract
```

This admission does not pull live logs, call Vercel, store tokens, inspect env values, or move any marker.

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/atlas/vercel_log_runtime_error_inventory.py`
- `tests/test_atlas_vercel_log_runtime_error_inventory.py`

No other file is admitted by this packet.

## Implementation Slice Admitted

The admitted first slice is the smallest honest helper that can:

1. read sanitized Vercel log or runtime-error wrappers under admitted `tmp/**`
2. validate schema, project identity, source class, and path safety
3. enforce fail-closed redaction and sensitive-field rejection
4. aggregate safe observability evidence deterministically
5. classify bounded runtime-error clusters without opening owner-repo work

The first implementation is advisory only.

## Why This Is Vercel Platform Observability Governance Work

This lane is root-owned platform-governance work because it operates only on:

- ATLAS-root governance receipts
- governed Vercel project identity already reconciled at root
- root-safe local wrapper artifacts under `tmp/**`
- read-only observability doctrine, summary, and proof surfaces

It does not change product code, deploy behavior, or owner-repo runtime.

## Why This Is Not Owner Work

This is not DiscordOS, Fitness, Mazer, Trove, or Foundation implementation work because the future helper may only classify observability evidence already exported into safe local wrappers.

It may not:

- patch product routes
- debug application logic in place
- fix webhook code
- change deployment configuration
- mutate any owner repo

The Fitness `/api/billing/webhook/stripe` cluster remains observability evidence only.

## Why This Is Not Vercel Hobby Cost Governance

This packet does not evaluate cost posture, request-volume pressure, middleware pressure, or upgrade-vs-stay-hobby economics.

It is a different family because its purpose is:

- safe log/runtime-error intake
- redaction enforcement
- cluster classification
- read-only observability evidence

not spend governance or plan-threshold management.

## Why Project Inventory Coverage Is Sufficient Prerequisite

Full governed project-inventory coverage is now enough to admit this helper because:

- governed project inventory coverage is already `5/5`
- helper-backed project identity exists for all five governed projects
- the log/runtime-error contract freeze already defined admitted sources, exclusions, and redaction boundaries
- the capability audit already proved grouped runtime-log and grouped runtime-error visibility exists

This means the remaining work is no longer project discovery. It is safe wrapper validation and observability summary logic.

## In-Scope Projects

The future helper applies only to:

- `fawxzzy-discordos`
- `fawxzzy-fitness`
- `fawxzzy-mazer`
- `fawxzzy-trove`
- `fawxzzy-foundation`

Unknown projects must be rejected.

## Admitted Later Source Classes

The future helper may later consume only these sanitized source classes:

- request-log wrapper input
- runtime-log wrapper input
- grouped runtime-error wrapper input
- non-secret build-log summary wrapper input when separately admitted by wrapper content

These are intake classes only. They do not grant live platform authority.

## Source Classes Still Excluded

The future helper must continue to exclude:

- live Vercel API responses by default
- live `vercel logs` execution by default
- env-value exports
- token-bearing artifacts
- secret-bearing terminal transcripts
- raw request-body exports
- auth-cookie or authorization-header exports
- raw payment or customer payload exports
- mutation payloads
- unredacted sensitive stack traces

## Required Inputs

The future helper may consume only:

- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-CAPABILITY-AUDIT-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-PROJECT-INVENTORY-COVERAGE-RECONCILIATION-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/VERCEL-PLATFORM-OBSERVABILITY-GOVERNANCE-LOG-AND-RUNTIME-ERROR-INVENTORY-CONTRACT-FREEZE-2026-07-09.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/registry/STACK-REPO-INVENTORY.json`
- sanitized wrapper files under `tmp/atlas/vercel-observability/*.json`

## Fields The Future Helper May Retain

The future helper may retain only safe summary fields such as:

- governed project slug
- deployment id
- environment
- runtime or request log class
- runtime-error cluster label or normalized error family
- route or path pattern
- status-code family
- level
- first seen
- last seen
- occurrence count
- sample count
- source class
- redaction status
- blocker state
- warning state
- capture window metadata

These fields are admitted because they are sufficient for observability inventory without storing raw sensitive payloads.

## Fields The Future Helper Must Reject Or Redact

The future helper must reject or drop:

- env values
- token values
- secrets
- auth cookies
- authorization headers
- raw request bodies
- raw payment or customer data
- mutation payloads
- raw query values when they may contain secrets or customer identifiers
- unredacted sensitive stack traces
- raw personalized URLs when the path can be preserved as a pattern instead

When uncertain whether a field is safe, the helper must exclude it.

## Admitted Future Interface Posture

The future helper is admitted with this expected CLI surface:

- `python ops/atlas/vercel_log_runtime_error_inventory.py`
- `--json`
- `--input <root-relative tmp wrapper path>` repeatable
- `--output <root-relative tmp report path>`
- `--strict`

These flags are admitted as the intended first interface and may be tightened in the next prompt-pack if implementation constraints require a smaller surface.

## Required Future JSON Fields

Expected top-level JSON fields:

- `schema_version`
- `status`
- `safe_to_use`
- `captured_project_count`
- `project_count`
- `runtime_error_cluster_count`
- `log_record_count`
- `redaction_status`
- `projects`
- `clusters`
- `warnings`
- `blockers`
- `forbidden_fields_detected`
- `next_recommended_packet`

## Required Future Status Classes

Expected status classes:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

## What The Future Helper Must Not Do

The future helper must not:

- call Vercel APIs directly by default
- run `vercel logs` directly by default
- mutate Vercel
- mutate owner repos
- read `.env*`
- read `secrets/**`
- write runtime latest files by default
- stage, commit, or push
- emit final receipts
- claim marker movement

## Required Safety Behavior

The future helper must:

- accept only root-relative `tmp/**` wrapper paths
- reject absolute paths and parent traversal
- fail closed on malformed wrapper JSON or JSON Lines
- reject unknown governed project ids or names
- reject unsupported source classes
- reject raw sensitive payloads before summary emission
- accept safe `tmp/**` output paths only
- reject protected output paths
- preserve deterministic JSON ordering for stable proof

## Proof Matrix For The Future Worker

The future implementation must prove at least:

1. valid sanitized JSONL or wrapper input is accepted
2. multiple governed projects can be aggregated together
3. one runtime-error cluster can be counted without retaining raw sensitive payload
4. the Fitness webhook route cluster can be classified as observability evidence without opening Fitness work
5. env-value patterns are rejected
6. token-value patterns are rejected
7. auth cookie or authorization-header patterns are rejected
8. raw request bodies are rejected unless explicitly redacted away
9. unknown projects are rejected
10. wrapper paths outside `tmp/**` are rejected
11. absolute output paths are rejected
12. protected output paths are rejected
13. safe `tmp/**` output is accepted
14. JSON output is deterministic
15. `--strict` exits nonzero on blockers

## Not Yet Admitted

This packet does not yet admit:

- implementation code
- fixture file names
- exact sample wrapper schemas beyond the contract freeze
- worker execution commands
- live log capture
- runtime proof receipts

Those belong to the next prompt-pack packet.

## Marker Decision

No marker moves.

`Vercel Platform Observability Governance` remains `0%`.

Reason:

- this packet admits only the future helper/test slice
- no helper is implemented yet
- no helper reconciliation proof exists yet
- no broader observability adoption surface has widened

## Next

Open only this next packet:

```text
Vercel Platform Observability Governance log and runtime-error inventory prompt-pack and worker handoff contract
```

That packet may freeze the worker instructions, fixture posture, and implementation proof commands, but it must still keep live log capture, env values, token values, secret handling, Vercel mutation, and owner-repo mutation denied.

## Completion

Completion: `100%` for the log and runtime-error inventory first-implementation admission itself.

No Vercel mutation was performed.
No owner repo was mutated.
No env values or token values were read or committed.
