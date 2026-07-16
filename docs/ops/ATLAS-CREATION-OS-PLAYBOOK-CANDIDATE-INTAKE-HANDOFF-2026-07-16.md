# Playbook Creation OS Candidate Intake Handoff - 2026-07-16

## Authority

This is an exact six-artifact, candidate-only owner intake. Atlas supplies
review candidates and immutable evidence; Atlas does not mutate Playbook,
promote doctrine, bulk-copy prose, or grant automatic promotion authority.

Playbook consumer truth was inspected read-only at
`fawxzzy/playbook@8aa912b492e689fca4c296d59a438c2813cba4fc`, path
`packages/engine/src/memory/atlasCandidateAdmission.ts`. Its accepted mapping is exactly:

- `rule -> Playbook/rules`
- `pattern -> Playbook/patterns`
- `failure-mode -> Playbook/failure-modes`

## Exact intake

| Candidate ID | Atlas artifact | Exact artifact SHA-256 | Supported destination |
| --- | --- | --- | --- |
| `creation-os-human-directed-authority` | `data/knowledge-candidates/creation-os/creation-os-human-directed-authority.knowledge-candidate.v2.json` | `sha256:0aee7841a054b2460d0260699151d0e878602af4fd63961ca9697e5cf71e2b4a` | `Playbook/rules` |
| `creation-os-bootstrap-pointer-not-memory` | `data/knowledge-candidates/creation-os/creation-os-bootstrap-pointer-not-memory.knowledge-candidate.v2.json` | `sha256:71170a9442e24862e0f79876e3f8e7028c9146efe5a91bc20daacf1b3a679c05` | `Playbook/rules` |
| `creation-os-builder-creative-loop-separation` | `data/knowledge-candidates/creation-os/creation-os-builder-creative-loop-separation.knowledge-candidate.v2.json` | `sha256:8c50f2611698756850c88c15ff4ba3d3f09a8807378e4aeb339572842bf4d986` | `Playbook/patterns` |
| `creation-os-platform-surface-vertical-contracts` | `data/knowledge-candidates/creation-os/creation-os-platform-surface-vertical-contracts.knowledge-candidate.v2.json` | `sha256:b8ce18b2720dbcc5900721e43de96dc660e91f4625223b683550c52de8bb8da2` | `Playbook/patterns` |
| `creation-os-infrastructure-shopping-before-wedge` | `data/knowledge-candidates/creation-os/creation-os-infrastructure-shopping-before-wedge.knowledge-candidate.v2.json` | `sha256:44f882ae82ee35b4691457a6ac5039ff481c37d9aecb37fed75bbf659673405a` | `Playbook/failure-modes` |
| `creation-os-xr-device-novelty-trap` | `data/knowledge-candidates/creation-os/creation-os-xr-device-novelty-trap.knowledge-candidate.v2.json` | `sha256:d44055c02c0acb69a58e15a9f28fd8a69421b083d927cecbe6828e0aebad390d` | `Playbook/failure-modes` |

The source of truth for this set is
`data/knowledge-candidates/creation-os/manifest.v1.json`. Intake must reject any identity, byte hash, provenance,
review status, kind, or destination mismatch.

## Owner disposition contract

Playbook must return one correlated candidate-only owner receipt per input:

- **accept** - admit the exact artifact into governed candidate review only;
  this is not doctrine promotion;
- **revise** - preserve the Atlas source identity and hash while returning the
  proposed owner revision as a new review record;
- **split** - preserve the Atlas source identity and hash and correlate every
  derived review candidate;
- **reject** - preserve the Atlas source identity and hash and state the
  evidence-backed rejection reason.

No bulk-copy or auto-promotion is allowed. Any later doctrine mutation belongs
to a separately authorized Playbook owner decision and validation path, never
to Atlas projection.

## Excluded Decision

`creation-os-software-repo-voice-first-wedge` is intentionally absent from this intake. It remains an
Atlas product Decision in the manifest because `decision` is not a current
`atlas.knowledge-candidate.v2` kind and Playbook has no Decision destination.
Do not relabel it.

## Required owner receipt

The receipt must report the observed Playbook head, all six candidate IDs,
Atlas paths and hashes, exact destinations, one accept/revise/split/reject
disposition per candidate, candidate-only truth, validation results, and zero
Atlas-authored Playbook doctrine mutation.

## Next sequence

1. Playbook Creation OS candidate-only owner adoption.
2. Cortex Creation OS advisory read-model refresh after the Playbook receipt is reconciled.
3. DiscordOS reliability continuation only after both owner receipts are reconciled.
