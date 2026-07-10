# Cortex Dual-Mode Replacement Readiness Codex Closeout Ingestion Read-Model First-Implementation Admission

- Date: `2026-07-10`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Control-plane checkpoint: `main@8e602313`
- Scheduler packet: `Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation admission`
- Marker movement: none

## Decision

Admit one future root-owned helper/test pair for bounded Codex closeout ingestion into a Cortex read model.

The admitted future files are:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `tests/test_cortex_codex_closeout_ingestion_read_model.py`

The next exact packet is:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model prompt-pack and worker handoff contract
```

This admission does not implement the helper, read hidden transcripts, inspect external product sessions, mutate owner repos, move markers, or claim the `40%` implementation milestone.

## Objective

Freeze the smallest honest implementation slice that can later turn ATLAS-root Codex closeout evidence into deterministic Cortex-readable state.

The future helper must remain advisory and read-only. It should transform durable closeout evidence into a machine-readable read model that Cortex can consume before it is allowed to plan or execute from that state.

## Why This Is The Next Dual-Mode Slice

`Cortex Dual-Mode Replacement Readiness` is currently at `30%`.

The satisfied thresholds are:

- `10%`: dual-mode operating model contract frozen
- `20%`: ChatGPT/Codex role inventory completed
- `30%`: synthesis-to-execution bridge schema frozen

The next published milestone is:

- `40%`: Codex closeout ingestion into Cortex read model implemented

Implementation should not start until the first implementation slice is admitted. This packet admits only the future helper/test surface and the minimum contract boundaries for the next prompt-pack packet.

## Admitted Future Surfaces

Only these future files are admitted:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `tests/test_cortex_codex_closeout_ingestion_read_model.py`

No other implementation, fixture, schema, Book, selector, manifest, owner-repo, platform, deploy, workflow, or secret surface is admitted by this packet.

## Admitted Source Truth

The future helper may consume only root-owned durable truth:

- ATLAS receipts under `docs/ops/**`
- ATLAS Book projection surfaces under `docs/atlas-book/**`
- dual-mode continuity manifests under `docs/memory/initiatives/**`
- workflow profile doctrine under `docs/memory/profiles/**`
- explicit scheduler outputs under `tmp/atlas/**` only when a later prompt-pack admits them as local proof references
- committed root-owned helper outputs under `tmp/**` only when a later prompt-pack admits exact paths

The future helper may not consume:

- hidden chat transcripts
- private model summaries
- browser session state
- Codex app private state
- external product session state
- owner-repo source files as closeout truth
- uncommitted diffs as canonical evidence
- `.env*`, secrets, tokens, `.vercel`, `.playwright-mcp`, or `archive`
- live Vercel or Supabase data

## Admitted Closeout Evidence Classes

The future helper may classify closeout evidence only when it is explicitly present in root-owned durable surfaces.

Admitted evidence classes:

- `selected_packet`
- `routing_mode`
- `commit_hash`
- `commit_message`
- `pushed_branch`
- `parity_result`
- `validation_result`
- `tests_run`
- `receipts_created`
- `manifest_updates`
- `marker_decision`
- `authority_denials_preserved`
- `blockers`
- `risks`
- `next_packet`

It must not infer missing evidence from conversational memory.

## Required Read-Model Output Shape

The future helper must emit deterministic advisory JSON.

Required top-level fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `closeout_count`
- `ingested_closeouts`
- `packet_transitions`
- `proof_summary`
- `marker_impacts`
- `authority_denials`
- `blocked_items`
- `next_packets`
- `warnings`
- `blockers`
- `safe_to_use`

Required schema version:

```text
atlas.cortex.codex_closeout_ingestion_read_model.v1
```

## Required Closeout Record Shape

Each ingested closeout record must be able to carry:

- `closeout_id`
- `source_ref`
- `selected_marker`
- `selected_packet`
- `packet_phase`
- `routing_mode`
- `commit_hashes`
- `receipts_created`
- `tests_run`
- `validation_result`
- `parity_result`
- `marker_movement`
- `authority_denials_preserved`
- `blockers`
- `risks`
- `next_packet`

Records must preserve unknown fields as absent or explicit warnings, not guessed values.

## Required Status Classes

Allowed future helper status classes:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

The helper must return `advisory_gap` when admitted source refs are valid but do not contain enough durable closeout evidence to build a useful read model.

## Required Safety Behavior

The future helper must:

- stay read-only
- reject hidden transcript sources
- reject private model-summary sources
- reject owner-repo source paths
- reject deploy, platform, secret, workflow, `.env*`, `.vercel`, `.playwright-mcp`, and `archive` paths
- reject absolute and traversal output paths
- write only to explicit root-relative `tmp/**.json` output paths
- preserve deterministic JSON field order
- preserve marker-write denial
- keep advisory gaps explicit
- keep final receipt authority outside the helper

## Required Future CLI Posture

The intended first CLI shape is:

```text
python ops/cortex/codex_closeout_ingestion_read_model.py
  [--json]
  [--source <root-relative admitted source ref>]...
  [--output <root-relative tmp report path>]
  [--strict]
```

The next prompt-pack packet may tighten flags, source refs, fixture paths, status behavior, and proof commands.

## Proof Matrix For The Future Worker

The future implementation must prove at least:

1. deterministic ingestion of one receipt-backed Codex closeout source
2. deterministic packet transition output
3. deterministic proof summary output
4. deterministic marker-impact output
5. explicit preservation of authority denials
6. `advisory_gap` behavior when a source lacks closeout evidence
7. failure-closed behavior when required durable source refs are missing
8. rejection of hidden transcript or private summary source attempts
9. rejection of owner-repo, platform, deploy, workflow, secret, `.env*`, `.vercel`, `.playwright-mcp`, and `archive` paths
10. safe `tmp/**.json` output acceptance
11. absolute and traversal output-path rejection
12. deterministic JSON ordering
13. `--strict` exits nonzero on blockers

## Not Yet Admitted

This packet does not yet admit:

- exact fixture filenames
- exact worker command strings beyond the provisional CLI posture
- implementation-readiness verdict
- worker execution
- marker movement to `40%`
- Cortex-generated packet planning
- bridge validator or generator implementation
- execution routing from Cortex state

Those belong to later prompt-pack, implementation-readiness, worker, reconciliation, and marker-surface ratchet packets.

## Marker Decision

No marker moves.

`Cortex Dual-Mode Replacement Readiness` remains `30%`.

Reason:

- this packet admits only the future helper/test slice
- no closeout-ingestion read model is implemented yet
- no ingestion proof exists yet
- no `40%` milestone completion is justified from admission alone

## Next

Open only this next packet:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model prompt-pack and worker handoff contract
```

That packet should freeze worker instructions, exact source fixtures, proof commands, output contracts, and stop conditions while preserving hidden transcript, owner-repo, deploy/platform, secret, workflow, marker, and final-receipt authority denials.

## Completion

Completion: `100%` for the Codex closeout ingestion read-model first-implementation admission itself.

No owner repo was mutated.
No platform surface was mutated.
No hidden transcripts, secrets, deploy surfaces, workflow files, or protected surfaces were touched.
No marker moved.
