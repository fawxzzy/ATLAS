# Playbook and Atlas Book committed-text corpus inventory pilot receipt

Status: implementation complete; hosted publication evidence is intentionally external to this commit

Date: 2026-07-17, America/New_York

## Scope and authority

This receipt closes only the metadata-only two-authority pilot. It does not admit a third source, copy corpus bodies, normalize doctrine, move a marker, start Packet 2, or open the held closing audit.

- Atlas source commit: `59fb0bbad0054a725004746c29492c3abf4f08e3`
- Atlas source tree: `7ac23ac04e60115eeaa5adc659e1e54c12dcedb4`
- Playbook source commit: `952b63aa6457d871024a224a089c4088490d69c5`
- Playbook source tree: `9256609de8ae3463f568cc53614b630e53c6989c`
- Successor packet SHA-256: `792056a6cfd4af8eed73f0c786a70209271658d5ee166673c1abc19196b79e37`
- Generator: `atlas.text-corpus.inventory.generator.v1`
- Inventory contract: `atlas.text-corpus.inventory.v1`

The implementation began from the exact merged Atlas base on a clean, detached, fresh isolated worktree. The clean-restart branch is uniquely owned by that worktree. Task readback found no other active bounded writer and no existing commit or pull request for this packet. An inactive local branch pointer from an archived attempt remained at the untouched base and was preserved; it had no packet commit, worktree, pull request, or active task.

## Frozen contract

- Git commit/tree/blob objects are the only corpus source. Ignored, untracked, and mutable working-tree bytes are never enumerated.
- Playbook is read only through a temporary bare Git object store at the accepted commit. Its mutable owner checkout is not a source.
- Included UTF-8 text rows record stable identity, owner/component, repository-relative path, commit, blob, SHA-256, byte size, media/content type, source class, authority tier, privacy/indexing profile, lifecycle/supersession, disposition/reason, provenance, and generator version.
- Secret, private/transcript, runtime, temporary, dependency/vendor, build/generated, symlink, gitlink, binary, and unsupported-media surfaces fail closed. Excluded bodies are not stored and their content SHA-256 remains `UNKNOWN`.
- Repository and output paths are resolved before containment or hashing. Absolute paths, traversal, ambiguous real roots, duplicate identities, object/digest mismatches, malformed records, and resolved-path escapes are rejected.
- An unavailable admitted source remains `UNKNOWN`; its denominator and aggregate digest are not rewritten as zero, absent, or healthy.
- Playbook remains doctrine owner. Atlas remains inventory/adoption owner. Authority widening and marker movement are both false.

## Inventory result

| Component | Total | Included | Excluded | Unknown | Component digest |
| --- | ---: | ---: | ---: | ---: | --- |
| `atlas-root` | 3,491 | 3,431 | 60 | 0 | `sha256:a43f6b75fd7338cca54fb0b2f1121b187a05f2031148631d0bee1e21e7056fed` |
| `playbook` | 1,800 | 1,444 | 356 | 0 | `sha256:2cb25cb419aa7da6957f3eb58e9673fd69a5cc5f090878e9b7b3062750c6852b` |
| **Aggregate** | **5,291** | **4,875** | **416** | **0** | `sha256:1d0449be1f3328fa8c2573e35247703218ff864fddcb845d5ca6ced1653950dc` |

Exclusion denominator:

| Reason | Atlas | Playbook | Total |
| --- | ---: | ---: | ---: |
| `GENERATED_OR_BUILD_TREE` | 11 | 0 | 11 |
| `MUTABLE_RUNTIME_SURFACE` | 24 | 335 | 359 |
| `PRIVATE_OR_TRANSCRIPT_SURFACE` | 0 | 11 | 11 |
| `SECRET_SURFACE` | 0 | 1 | 1 |
| `UNSUPPORTED_MEDIA_TYPE` | 25 | 9 | 34 |

Serialized output byte digests:

- Aggregate index: `sha256:9671ba83cc28f36962305c05e5e3aa01677fe216a101246ab4ada91ca8ae4aa5`
- Atlas shard: `sha256:dac94200e1222676979f5e9fe31130c5a98340cafc6e1ae96bfb712b7d98bf40`
- Playbook shard: `sha256:c619d410b0cb245493c5d4f782dc8b4b10d0ad9b6e2a40c8bdcd5dcedf7f1ff4`

## Verification evidence

- Focused suite: 19 tests passed. The deterministic cross-platform resolved-path escape regression is non-skipped. The optional Python symlink test skipped because this Windows runtime lacks symlink privilege; an independent real Windows junction proof passed and cleaned up both endpoints.
- Large-corpus transport regression: 256 blobs larger than the OS pipe buffers completed within the test timeout. The reader interleaves each Git object request and response.
- Source-only check mode regenerated both pinned inventories and matched every committed output byte.
- Two independent staging runs produced byte-identical output files and the same aggregate digest; both staging trees were removed.
- Every included row was rebuilt from its pinned blob and rechecked against Git object identity, byte size, UTF-8 classification, and SHA-256 before output comparison.
- Atlas and Playbook source tree IDs were unchanged after all generation, replay, and escape tests.
- Stack validation completed with `critical=0`, `error=1`, `warning=10`, `info=0`. The error is pre-existing isolated-worktree state: the archive registry declares `repos/repo-backups` present while that ignored owner surface is absent. The warnings are the expected missing `_stack` and Lifeline owner worktrees. This packet did not repair or suppress those unrelated findings.

## Invariance and unknowns

- The canonical Atlas coordination checkout remained on its preflight branch and exact head, with 0 tracked changes and 71 scratch entries.
- The mutable Playbook owner checkout remained on `codex/atlas-knowledge-candidate-v2-consumer` at `14fce44268084bcaaab6d189b6ef18eb7a992faf` with a clean status. No owner-repository mutation occurred.
- Pilot source availability unknowns: 0.
- Excluded content SHA-256 values: `UNKNOWN` by policy; excluded bodies were not copied into the inventory.
- Pull request, hosted CI, and exact-head Codex review: `UNKNOWN` at commit construction time. Those self-referential publication facts must be proven in the terminal external receipt against the final immutable head.
- Production, deployment, Discord, board, Supabase, authentication, billing, schema/data service, secret, daemon, scheduler, and marker state were not touched.

## Reusable failure mode

Failure Mode: sending an entire large `git cat-file --batch` request set before consuming responses can fill both OS pipe buffers and deadlock even though small fixtures pass. Interleave each object request with its response and retain a corpus larger than the pipe buffers as a timed regression.

## Exact next packet

Held and not started: `Playbook universal adoption 13-component denominator reconciliation` (Packet 2). Its component basis must be regenerated from then-current governed topology after this pilot is accepted or explicitly reordered by Atlas Main.
