# ATLAS text corpus inventory pilot R2 receipt

Status: source refresh verified; draft publication evidence is intentionally external to this commit

Date: 2026-07-21, America/New_York

## Correlation

- Packet ID: `ATLAS-TEXT-CORPUS-INVENTORY-PILOT-R2-SOURCE-20260721-001`
- Delivery event ID: `onv1_78163bb0bbff72d843379220f22e9de4ea660ac384a2c188152ad1fde693d094`
- Payload digest: `sha256:78163bb0bbff72d843379220f22e9de4ea660ac384a2c188152ad1fde693d094`
- Idempotency key: `ATLAS-TEXT-CORPUS-INVENTORY-PILOT-R2-SOURCE-20260721-001-FORWARDED`
- Reservation ID: `rsrv_aa775944b285fc09a2a8fde8f00c0ee3d15b60d297ff5000958aa118b6deed71`
- Logical role: `playbook.atlas-book`
- Writer scope: `source.atlas.text-corpus-inventory.pilot.r2`
- Runtime task: `019f6dac-f36e-7b61-8d4d-feec0f4c39b6`

## Immutable basis

- Atlas parent/source commit: `78a906240cf6c8a5fc1967cbf9d797df62cfa1f5`
- Atlas source tree: `7c97730a86a32a127f77339ac18f3221d5ddf64f`
- Playbook source commit: `952b63aa6457d871024a224a089c4088490d69c5`
- Playbook source tree: `9256609de8ae3463f568cc53614b630e53c6989c`
- Branch: `codex/text-corpus-inventory-pilot-r2`
- Repository: `fawxzzy/ATLAS`

The absolute runtime worktree path is intentionally omitted from committed evidence. The admitted worktree was fresh, clean, and uniquely reserved at the exact parent before mutation. The requested branch, remote branch, matching task, and matching pull request were absent. PR #146's 22-path scheduler scope had zero overlap with this packet.

## Provenance decision

The immutable parent already contains the accepted clean-restart corpus contract from merged PR #141. That history is separate from the earlier mixed-author collision lane and includes the subsequent review-hardening commits. R2 therefore preserves the accepted schema, generator architecture, and 24-test contract instead of replacing them.

The smallest coherent R2 source change is:

1. update the Atlas source pin from `59fb0bbad0054a725004746c29492c3abf4f08e3` to the admitted parent `78a906240cf6c8a5fc1967cbf9d797df62cfa1f5`;
2. regenerate the Atlas component shard and aggregate index from committed Git objects;
3. retain the byte-identical Playbook component shard at its immutable accepted pin; and
4. add this correlated R2 receipt.

No bytes were read or reused from the contaminated collision worktree.

## Changed paths

Exactly four paths changed, all inside the seven-path ceiling:

1. `docs/ops/ATLAS-TEXT-CORPUS-INVENTORY-PILOT-R2-RECEIPT.md`
2. `docs/registry/text-corpus/ATLAS-TEXT-CORPUS-INDEX.v1.json`
3. `docs/registry/text-corpus/components/atlas-root.v1.json`
4. `ops/atlas/text_corpus_inventory.py`

The fifth regenerated ceiling path, `docs/registry/text-corpus/components/playbook.v1.json`, is byte-identical to the parent and therefore does not appear in the Git diff.

The schema and focused test file were verified but intentionally left byte-identical to the accepted parent:

- `schemas/atlas.text-corpus.inventory.v1.json` — SHA-256 `340f43c4f91ff360151aed5cdacf556e71ad24e589f11bf81e9e7676ad976fb4`
- `tests/test_atlas_text_corpus_inventory.py` — SHA-256 `68b2a83d883a1e06fba2df29a49d7d31fb0a1c58cd02acdfecff737a81d87c2`

## Inventory result

| Component | Total | Included | Excluded | Unknown | Component digest |
| --- | ---: | ---: | ---: | ---: | --- |
| `atlas-root` | 3,548 | 3,488 | 60 | 0 | `sha256:050e3f134b31762c05907f3fb8081f15d3b26380976f681506880b1ac45cc47d` |
| `playbook` | 1,800 | 1,444 | 356 | 0 | `sha256:2cb25cb419aa7da6957f3eb58e9673fd69a5cc5f090878e9b7b3062750c6852b` |
| **Aggregate** | **5,348** | **4,932** | **416** | **0** | `sha256:de52cdad0b0a58ea0c82cd05248021f587d6e501a6d810d19edc247281e51855` |

`unknown: 0` is limited to availability/disposition inside these two pinned sources. It is not a whole-stack coverage or health claim.

Exclusion denominator:

| Reason | Atlas | Playbook | Total |
| --- | ---: | ---: | ---: |
| `GENERATED_OR_BUILD_TREE` | 11 | 0 | 11 |
| `MUTABLE_RUNTIME_SURFACE` | 24 | 335 | 359 |
| `PRIVATE_OR_TRANSCRIPT_SURFACE` | 0 | 11 | 11 |
| `SECRET_SURFACE` | 0 | 1 | 1 |
| `UNSUPPORTED_MEDIA_TYPE` | 25 | 9 | 34 |

Serialized output SHA-256 values:

- Aggregate index: `83ae148e5b15cdf5f5603d30419860b49ea62d87a4cc042792b54023c7b17f54`
- Atlas component shard: `1d4607cbdbd97549ca10e9df696232f063e062ffa0bab5a043cd2e261fb2536a`
- Playbook component shard: `c619d410b0cb245493c5d4f782dc8b4b10d0ad9b6e2a40c8bdcd5dcedf7f1ff4`

The Playbook shard hash matches the accepted parent exactly. Its immutable source did not change.

## Verification

- Focused suite run 1: 24 passed, 1 optional privileged-symlink integration skipped.
- Focused suite run 2: 24 passed, 1 optional privileged-symlink integration skipped.
- Required cross-platform, non-skipped resolved-path escape regression: passed in both runs.
- Source-only inventory check run 1: passed with aggregate digest `sha256:de52cdad0b0a58ea0c82cd05248021f587d6e501a6d810d19edc247281e51855`.
- Source-only inventory check run 2: passed with the same digest and byte readback.
- Python source compilation: passed without writing bytecode.
- All four inventory/schema JSON artifacts parsed successfully. Generated registry JSON and this receipt use LF with a terminal newline; the one-line Python pin edit retains the parent's CRLF convention to avoid unrelated whole-file normalization.
- Current stack validation: `critical=0`, `error=1`, `warning=10`, `info=0`; this matches the pre-existing isolated-worktree baseline and was not repaired or suppressed by this packet.
- Validation-generated ignored runtime receipts were removed after readback; no validation residue is retained.
- Final Git diff, exact-path, JSON/LF, credential, machine-path, source-tree invariance, commit, push, draft PR, and exact-final-head review evidence are recorded in the external terminal receipt because commit/PR identities cannot self-reference inside this commit.

## Mutation truth and held scope

- No canonical Atlas checkout files were edited.
- No Playbook or other owner-repository bytes were edited.
- No provider, Supabase, data, deployment, production, workflow dispatch, source pause/delete, Discord, board, secret, or marker mutation occurred.
- No ready transition or merge is authorized.
- Packet 2 and denominator reconciliation remain held and were not started.
