# Atlas Creation OS Cortex Advisory Read-Model Refresh - 2026-07-16

## Outcome

Atlas now has a deterministic, root-owned Creation OS advisory catalog and retrieval model. The model consumes the six Playbook-accepted review candidates and keeps `creation-os-software-repo-voice-first-wedge` separately deferred as an Atlas product Decision.

This refresh does not update or claim freshness for the global Cortex current-state, context, operator-surface, ledger, or knowledge bundle outputs.

## Pinned evidence

| Evidence | Pinned identity |
| --- | --- |
| Atlas source set | `66f756768792de35ef00d1741cf8c6f6c965b733` |
| Atlas manifest | `sha256:eaab80257186a1f1d32e45106ed87858e0e254065df315ccb26b1e89b854efe2` |
| Playbook merged revision | `885ae2bb0104f5ffc1c99bc1febe1f4cf2fde1aa` |
| Playbook accepted head | `e692f574ed51cdb0f59ce423d0cbf6baa08fe51d` |
| Playbook intake receipt | `playbook-akc-intake-creation-os-66f756768792` |
| Playbook queue | `sha256:206e30ff026969dec954f04b2aa722fb047f6c8540e9258ddda8b9887dba0d75` |
| Playbook baseline | `8aa912b492e689fca4c296d59a438c2813cba4fc` |
| Playbook initial intake | `44ce21cdff47bc88817d164ac8578141eb939651` |

The Playbook evidence is read from exact Git blobs at the merged revision. The merge has the baseline and accepted head as its two parents, so open-only owner evidence cannot satisfy the refresh.

## Projected identities

| Identity | Class | Destination or status |
| --- | --- | --- |
| `creation-os-human-directed-authority` | Rule review candidate | proposal-only `Playbook/rules` |
| `creation-os-bootstrap-pointer-not-memory` | Rule review candidate | proposal-only `Playbook/rules` |
| `creation-os-builder-creative-loop-separation` | Pattern review candidate | proposal-only `Playbook/patterns` |
| `creation-os-platform-surface-vertical-contracts` | Pattern review candidate | proposal-only `Playbook/patterns` |
| `creation-os-infrastructure-shopping-before-wedge` | Failure Mode review candidate | proposal-only `Playbook/failure-modes` |
| `creation-os-xr-device-novelty-trap` | Failure Mode review candidate | proposal-only `Playbook/failure-modes` |
| `creation-os-software-repo-voice-first-wedge` | Atlas product Decision | contract-ineligible and deferred; success thresholds and kill criteria unresolved |

The Decision record hash remains `sha256:5f26456f7e2a5d18ca6ca513cdcd53d33af0df5a19a3b05c01a753d393a121d6`. It is absent from candidate and promoted-knowledge arrays.

## Determinism and failure semantics

The source-set digest covers, in an ordered length-prefixed stream, the Atlas revision, exact manifest bytes, exact six artifact bytes, Decision record hash, merged Playbook revision, exact owner-receipt bytes, and exact queue bytes. Output JSON is sorted-key UTF-8 with LF endings. A write followed by repeated checks must remain byte-identical.

- missing or unavailable evidence: `unknown`
- changed pinned revision: `stale`
- duplicate, hash, kind, destination, or disposition drift: `conflict`
- Decision admission or doctrine mutation: `conflict`
- conflict resolution: operator-required; never automatic selection

All non-ready evidence states stop before any read-model write.

## Authority boundary

Cortex may read and provide advisory synthesis, routing, and retrieval. It has no policy, doctrine, scheduling, execution, deployment, approval, board, repository-mutation, promotion, or automatic-selection authority.

`marker_deltas=[]` and `marker_movement_authorized=false` remain explicit in both read models and the receipt.

## Base-proof correction

The initial hold interpreted the left/right ancestry count backward. Verified ancestry proved that `origin/main` at `66f756768792de35ef00d1741cf8c6f6c965b733` is seven commits ahead of canonical local head `1d79d4ac3191dade11a2aa7c40352a5f210d35e2` and contains that head in its ancestry. The isolated worktree base was correct and was preserved; the canonical local checkout was not updated.

## Outputs

- `runtime/cortex/catalog/knowledge/creation-os/advisory-read-model.latest.json`
- `runtime/cortex/query/knowledge/creation-os/advisory-query.latest.json`
- `runtime/receipts/knowledge/cortex-creation-os-advisory-refresh.execution-receipt.v2.json`

The exact next lane after owner-receipt reconciliation is DiscordOS reliability continuation.
