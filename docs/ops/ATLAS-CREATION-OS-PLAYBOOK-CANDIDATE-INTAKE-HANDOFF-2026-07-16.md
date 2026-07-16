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
| `creation-os-human-directed-authority` | `data/knowledge-candidates/creation-os/creation-os-human-directed-authority.knowledge-candidate.v2.json` | `sha256:45daed22bd773604e1be0e068dd0582d69ae0304d7dfdc5f2dee4787b8b7ac76` | `Playbook/rules` |
| `creation-os-bootstrap-pointer-not-memory` | `data/knowledge-candidates/creation-os/creation-os-bootstrap-pointer-not-memory.knowledge-candidate.v2.json` | `sha256:da911a286e13cec9cf2458c347fc0029107154d062ab8d2ac1b58b6a2585b87a` | `Playbook/rules` |
| `creation-os-builder-creative-loop-separation` | `data/knowledge-candidates/creation-os/creation-os-builder-creative-loop-separation.knowledge-candidate.v2.json` | `sha256:c1757bab378fff7ab1cc17ed265ddb1bee2914437c27ebf95d8806f2d747ad67` | `Playbook/patterns` |
| `creation-os-platform-surface-vertical-contracts` | `data/knowledge-candidates/creation-os/creation-os-platform-surface-vertical-contracts.knowledge-candidate.v2.json` | `sha256:adc55f5262cf8a99c1ea0a47f2de05c9393698c8ac081c2c682176fb4dea19a1` | `Playbook/patterns` |
| `creation-os-infrastructure-shopping-before-wedge` | `data/knowledge-candidates/creation-os/creation-os-infrastructure-shopping-before-wedge.knowledge-candidate.v2.json` | `sha256:0497c6357d9049b30e913a8d72e4ebd9e30c61388a9d12479affd658bb5aa805` | `Playbook/failure-modes` |
| `creation-os-xr-device-novelty-trap` | `data/knowledge-candidates/creation-os/creation-os-xr-device-novelty-trap.knowledge-candidate.v2.json` | `sha256:20ce4b0a3277a9d025f382f23693475ba0e2ff4ad58f200261087cd77db573ef` | `Playbook/failure-modes` |

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
