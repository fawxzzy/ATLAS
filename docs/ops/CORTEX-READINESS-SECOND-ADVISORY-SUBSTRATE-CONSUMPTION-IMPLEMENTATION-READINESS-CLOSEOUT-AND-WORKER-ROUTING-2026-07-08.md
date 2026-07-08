# Cortex Readiness Second Advisory Substrate Consumption Implementation-Readiness Closeout And Worker Routing - 2026-07-08

- CODEX-MSG-ID: `CODEX-2026-07-08-CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-IMPLEMENTATION-READINESS`
- Date: `2026-07-08`
- Mode: `docs-only implementation-readiness closeout and worker routing`
- Scope: `decide whether the second advisory substrate consumption worker is ready to implement`
- Selector basis: `docs/ops/CORTEX-READINESS-POST-SANDBOX-FINAL-BLOCKER-NEXT-SLICE-SELECTION-2026-07-08.md`
- Contract basis: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-CONTRACT-FREEZE-2026-07-08.md`
- Admission basis: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-08.md`
- Prompt-pack basis: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-08.md`
- Branch basis: `main@97d8f33e6169a33d314d3c859d3b6fa251534fae`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Decision

Readiness decision:

`implementation-ready`

The second advisory substrate consumption worker can now be routed as one bounded implementation packet.

This packet does not implement the worker or tests.

## 1. Durability Check

The required control-plane chain is durable:

- selector: `docs/ops/CORTEX-READINESS-POST-SANDBOX-FINAL-BLOCKER-NEXT-SLICE-SELECTION-2026-07-08.md`
- contract freeze: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-CONTRACT-FREEZE-2026-07-08.md`
- first-implementation admission: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-08.md`
- prompt-pack and worker handoff contract: `docs/ops/CORTEX-READINESS-SECOND-ADVISORY-SUBSTRATE-CONSUMPTION-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-08.md`

The chain consistently preserves an advisory-only Cortex consumer with no execution, approval, owner-truth, deploy, secret, workflow-dispatch, mutation, final-receipt, or marker authority.

## 2. Worker Objective

The worker objective is explicit:

Implement a read-only Cortex-side helper that consumes one explicit root-relative advisory substrate source, validates that the source belongs to an admitted second advisory substrate class, summarizes it as advisory-only context, preserves authority denials, and emits deterministic JSON.

## 3. CLI Contract

The CLI contract is explicit:

- `python ops/cortex/second_advisory_substrate_consumption.py`
- `python ops/cortex/second_advisory_substrate_consumption.py --json`
- `python ops/cortex/second_advisory_substrate_consumption.py --source <root-relative-path>`
- `python ops/cortex/second_advisory_substrate_consumption.py --output <root-relative-path>`
- `python ops/cortex/second_advisory_substrate_consumption.py --strict`

Default mode must write no files. Optional writes require explicit `--output`.

## 4. JSON Output Contract

The JSON output contract is explicit:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_ref`
- `source_digest`
- `substrate_class`
- `consumption_result`
- `preserved_authority_denials`
- `advisory_payload`
- `forbidden_surfaces`
- `warnings`
- `blockers`
- `safe_to_use`

Expected status classes:

- `ok`
- `advisory_gap`
- `blocker`
- `internal_error`

JSON ordering must be deterministic.

## 5. Input Substrate Contract

The input substrate contract is explicit.

The initial admitted substrate class is Cortex continuity and restart substrate:

- `docs/memory/initiatives/continuity-manifest-cortex-readiness.json`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

The worker may also consume the other root-owned classes already frozen by the contract only after its guards prove safe handling for those classes.

## 6. Read-Only And No-Mutation Guard

The read-only/no-mutation guard is explicit.

The worker must:

- read explicit root-relative source refs only
- default to stdout and no file writes
- write only with explicit `--output`
- write only under safe `tmp/**`
- reject protected, owner, secret, deploy, hidden transcript, absolute, and parent-traversal paths
- never mutate ATLAS Book, manifests, receipts, selector, runtime latest files, owner repos, platform surfaces, or protected surfaces by default

## 7. Authority Denials

Authority denials are explicit and remain mandatory:

- execution
- approval
- owner-truth
- final-receipt
- deploy
- secret-handling
- transcript-scraping
- automatic `_stack` dispatch
- repo mutation
- platform mutation
- owner-repo mutation
- protected-surface mutation
- workflow dispatch
- marker movement

The worker may report advisory findings only.

## 8. Allowed Source Surfaces

Allowed source surfaces are explicit:

- Cortex manifests and restart mirrors
- Cortex and Playbook/Cortex authority receipts
- existing Cortex advisory runtime artifacts
- validation and continuity proof outputs
- existing Cortex helpers and tests as read-only contract references

All source refs must be root-relative and remain inside the ATLAS root.

## 9. Forbidden Surfaces

Forbidden surfaces are explicit:

- `repos/**`
- Fitness owner-lane sources
- Mazer owner-lane sources
- owner-repo receipts as truth inputs
- hidden transcript, chat, or session state
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- deploy or platform output
- any source outside the ATLAS root
- any absolute path source
- any parent-traversal source
- runtime latest files by default
- final Lifeline receipts

## 10. Output-Path Guards

Output-path guards are explicit.

The worker must reject:

- absolute output paths
- parent-traversal output paths
- `repos/**`
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- `secrets/**`
- `.env*`
- runtime latest files by default
- final receipt paths
- any output path outside `tmp/**`

Safe `tmp/**.json` output is allowed only when explicitly requested.

## 11. Proof Obligations

Proof obligations are explicit:

1. valid second advisory substrate consumed safely
2. malformed source blocked
3. owner-repo source rejected
4. Fitness and Mazer source refs rejected
5. hidden transcript source rejected
6. deploy, platform, and secret paths rejected
7. absolute source and output paths rejected
8. protected source and output paths rejected
9. safe `tmp/**` output accepted only with explicit `--output`
10. deterministic JSON ordering
11. all authority denials preserved
12. default helper run writes no files
13. validation critical/error state prevents `safe_to_use=true`
14. no owner repo touched
15. no protected surface touched
16. no marker movement claimed until implementation-backed proof lands

## 12. Remaining Root-Side Ambiguity

No root-side ambiguity remains before worker implementation.

The worker file, test file, CLI, JSON shape, admitted input classes, forbidden surfaces, output-path guards, authority denials, proof matrix, and post-worker reconciliation target are all frozen.

## 13. Routed Worker Packet

The exact routed worker packet is:

`Cortex Readiness second advisory substrate consumption first-implementation worker packet 1`

## 14. Allowed Worker Files

The routed worker may touch only:

- `ops/cortex/second_advisory_substrate_consumption.py`
- `tests/test_cortex_second_advisory_substrate_consumption.py`

The later worker cluster may also add one implementation-backed reconciliation receipt and exact ATLAS Book/manifest mirrors only after the worker and proof pass.

## 15. Surfaces Still Forbidden

The routed worker remains forbidden from touching:

- `repos/**`
- Fitness
- Mazer
- Playbook owner repo
- any owner repo
- Supabase
- Vercel
- deploy surfaces
- secrets
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- final receipt surfaces
- hidden transcript, chat, or session state
- workflow dispatch or workflow edits
- `_stack` dispatch
- protected surfaces

## 16. Post-Worker Reconciliation Package

The exact post-worker package is:

`Cortex Readiness second advisory substrate consumption first-implementation worker cluster reconciliation`

That package is the first point where implementation-backed proof can be evaluated for any Cortex Readiness marker movement.

## 17. Marker Decision

No marker moves.

- `Cortex Readiness` remains `45%`.
- `Sandbox Simulation Readiness` remains `99%`.
- `AI Repetition-to-Automation Pipeline` remains `54%`.
- `AI Long-Run Batch Orchestration` remains `69%`.
- `AI Work Session Stability & Auto-Sync Loop` remains `85%`.
- `Playbook Everywhere + Cortex Interface` remains `40%`.

Reason: this is a docs-only readiness closeout. Marker movement requires implementation-backed proof from the routed worker cluster.

## Bundle B Decision

Bundle B is intentionally not executed in this packet.

The worker is routed, but this packet's scope explicitly forbids creating:

- `ops/cortex/second_advisory_substrate_consumption.py`
- `tests/test_cortex_second_advisory_substrate_consumption.py`

Implementation starts only in the routed worker packet.

## Exact Next Packet

`Cortex Readiness second advisory substrate consumption first-implementation worker packet 1`
