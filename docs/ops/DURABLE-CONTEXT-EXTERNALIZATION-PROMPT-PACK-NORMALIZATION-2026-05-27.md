# Durable Context Externalization Prompt-Pack Normalization - 2026-05-27

- Date: `2026-05-27`
- Lane: `Durable Context Externalization prompt-pack normalization`
- Mode: `docs-only continuation and prompt-pack normalization`
- Source surfaces:
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-CONTINUITY-MANIFEST-PASS-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-RETRIEVAL-SURFACE-INVENTORY-2026-05-27.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/atlas-book/13-vision-and-endgames.md`
  - `docs/PLAYBOOK_NOTES.md`
  - `docs/memory/README.md`
  - `docs/ops/ATLAS-CONTINUITY-LANE.md`
- Control-plane checkpoint: `main@210110b`

## Objective

Normalize the canonical continuation and clean-and-re-sync prompt pack so retrieval-first and external-context-first doctrine are expressed consistently across the active ATLAS restart surfaces.

This pass does not:

- change owner-repo truth
- create retrieval automation
- treat transcript memory as durable state
- rewrite the ATLAS book broadly
- touch runtime, schema, env, or application code

## Canonical Prompt / Continuation Surfaces Chosen

These are the live surfaces that actually govern restart behavior and prompt-pack posture:

1. `docs/atlas-book/12-restart-and-handoff-guide.md`
   - primary restart surface for new chats
2. `docs/memory/README.md`
   - canonical durable memory and retrieval taxonomy surface
3. `docs/PLAYBOOK_NOTES.md`
   - promoted doctrine surface for reusable rules, patterns, and failure modes
4. `docs/ops/ATLAS-CONTINUITY-LANE.md`
   - active continuity runbook for structured handoffs and promotion routing
5. `docs/atlas-book/13-vision-and-endgames.md`
   - active endgame surface that names what continuity is still missing

These were preferred over other files because:

- `docs/atlas-book/README.md` and `docs/atlas-book/INDEX.md` route operators into the restart guide rather than acting as the detailed restart contract themselves
- `docs/codex/**` prompt-pack files are lane-specific prompt artifacts, not the canonical stack restart doctrine
- older pause or checkpoint receipts may reference restart posture, but they are historical receipts rather than the maintained prompt-pack surfaces

## Normalization Applied

The normalized continuation pack now consistently says:

- prior chat continuity is non-authoritative
- workers should retrieve durable ATLAS context first
- continuity manifests, receipts, truth maps, promoted notes, and verification/adoption surfaces outrank transcript carryover
- ATLAS remains coordination-only
- owner repos remain truth owners
- `Durable Context Externalization` should be used in future continuity evaluations

## Doctrine Reinforced

### Rule

`External Context First`

Workers should retrieve durable context before trusting chat continuity.

### Pattern

`Ephemeral Worker, Durable Substrate`

GPT/Codex are temporary reasoning workers; durable continuity lives in ATLAS and owner repos.

### Failure Mode

`Recursive Context Rot Loop`

Continuation prompts that still privilege remembered transcript state over receipts, manifests, and owner truth will reproduce stale lane posture and duplicate summary drift.

## What Changed In The Live Prompt Pack

### Restart surface

`docs/atlas-book/12-restart-and-handoff-guide.md` now:

- makes continuity manifest retrieval explicit before book/receipt reconstruction
- spells out the durable-context hierarchy more clearly
- treats prior transcript continuity as non-authoritative by default
- refreshes the stale current-next-package guidance so restart posture reflects current live lanes rather than old Local Data Gateway milestones

### Memory doctrine surface

`docs/memory/README.md` now:

- sharpens the retrieval-first rule wording
- makes the retrieval order more explicit
- reinforces that manifests point to truth rather than replacing it

### Promoted doctrine surface

`docs/PLAYBOOK_NOTES.md` now carries a new normalized doctrine summary for prompt-pack behavior so later receipts can reuse the same language.

### Continuity runbook

`docs/ops/ATLAS-CONTINUITY-LANE.md` now:

- explicitly routes serious sessions through external durable context before transcript interpretation
- tightens the split between raw traceability, structured handoff, and promoted durable state

### Endgame surface

`docs/atlas-book/13-vision-and-endgames.md` now:

- updates the continuity lane read so it reflects the manifest, retrieval inventory, and prompt-pack normalization work already landed

## Current Assessment

This pass does not move the marker by itself.

Why:

- prompt-pack normalization reduces restart ambiguity
- but it does not by itself prove broader operational adoption
- continuity manifests are still not universal across all major lanes
- retrieval remains partly manual even though the doctrine is now much more consistent

## Exact Next Package

`Durable Context Externalization marker ratchet checkpoint 2`

Why:

- marker admission is durable
- continuity-manifest doctrine is durable
- retrieval-surface inventory is durable
- prompt-pack normalization is now durable
- the next honest move is to recompute whether those four durable pieces justify a bounded marker ratchet

## Rule

Prompt-pack normalization must prefer retrieval-first resume without pretending chat continuity is trustworthy.

## Pattern

continuity manifest -> receipt index -> truth map -> promoted notes -> owner verification/adoption surface -> transcript nuance last

## Failure Mode

A continuation prompt still treats transcript memory as authoritative even after durable externalization doctrine exists.
