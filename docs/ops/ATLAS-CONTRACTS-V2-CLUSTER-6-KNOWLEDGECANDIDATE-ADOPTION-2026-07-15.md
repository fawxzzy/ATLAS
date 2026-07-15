# ATLAS Contracts v2 Cluster 6 KnowledgeCandidate Terminal Adoption

## Accepted Result

KnowledgeCandidate is independently accepted as the eleventh and final Atlas Contracts v2 family. The complete chain is Atlas root producer and schema authority, exact `atlas.knowledge-candidate.v2` package validation, Playbook's independently merged candidate-only consumer, deterministic correlated consumer receipts, byte-identical replay, two-candidate deterministic append proof, fail-closed negative conformance, current MarkerEvidence reconciliation, and matching machine/human root projections.

Contracts Mesh moves exactly from `10 / 11` (`91%`) to `11 / 11` (`100%`) on its fixed denominator. Atlas Full-System Re-evaluation remains exactly `1 / 2` and `50%`. Marker Integrity remains exactly `51 / 51`, `100%`, complete. No Playbook Everywhere, Cortex Readiness, DiscordOS, Vercel, DeepSeek, parent audit-gate, or unrelated marker completion is inferred.

## Authority Boundary

Atlas remains the sole owner of KnowledgeCandidate contract semantics and validation behavior through `@atlas/contracts`. Playbook consumes the public Atlas validator and artifact; it does not copy the schema or redefine Atlas semantics. Playbook owns its candidate-only intake semantics, dedicated review queue, and consumer receipt.

Candidate admission grants no authority to create or mutate a Rule, Pattern, Failure Mode, story, promoted pattern, notes surface, memory doctrine, or other canonical doctrine. `suggested_destination` remains proposal-only.

No owner-repository file, live Discord state, board, Supabase data, Vercel project, deployment, production alias, external account, secret, or user-owned data was mutated. All candidate queue and Playbook runtime artifacts were written only under disposable Atlas `tmp/` project roots and removed after proof.

## Merged Playbook Consumer Evidence

Playbook PR [#25](https://github.com/fawxzzy/playbook/pull/25), `feat: admit Atlas knowledge candidates without promotion`, is merged and ready-state truth was read directly from GitHub:

- trusted feature head: `14fce44268084bcaaab6d189b6ef18eb7a992faf`;
- merge commit: `f39dbac27d9a1c706ad11dbefe7f37feeebd5c3d`;
- merged at: `2026-07-15T17:15:39Z`;
- observed current `origin/main`: `f39dbac27d9a1c706ad11dbefe7f37feeebd5c3d`;
- the feature head is an ancestor of current `origin/main`;
- the merge commit is retained as an ancestor of current `origin/main`;
- the observed local checkout is the trusted feature tree or a descendant whose consumer paths are unchanged from that tree;
- the checkout remained tracked-clean before and after proof.

All seven distinct GitHub workflows were successful before merge: `Playbook CI`, `Playbook Diagrams Check`, `Playbook Remediation Example`, `analyze-pr-comment`, `changelog`, `ci`, and `security`. Conditional `apply`, `generate`, and `plan` jobs were skipped rather than failed.

The monotonic trust rule does not pin a moving `origin/main` equality. Later Playbook descendants remain trusted only while the feature and merge commits remain ancestors and the exact exercised consumer paths remain unchanged from the trusted feature tree. Synthetic tests accept an unchanged descendant and reject both non-ancestor history and consumer-path drift.

## Executable Consumer Seam

`ops/atlas/knowledge_candidate_adoption.mjs` executes the real shipped Playbook public command:

```text
playbook knowledge atlas-admit --artifact <candidate> --atlas-contracts-root <package> --json
```

The command runs with a disposable Atlas `tmp/` project as its current repository, so `.playbook/memory/atlas-knowledge-candidates.json` and incidental runtime observation state never enter the Playbook owner repository or committed Atlas doctrine.

The actual executable is not read from the owner's ignored or pre-existing `dist`. Atlas materializes the exact trusted feature tree `5be6274e97c06af0211db24b073d43fa7686f815` with `git archive`, resolves only its frozen lockfile through `pnpm install --frozen-lockfile --offline`, and immediately runs Playbook's canonical `pnpm -r build` inside disposable Atlas state. The generated CLI and engine outputs must exist and retain their recorded digests before every admission command. Playbook tracked status is empty both before and after the build; the owner checkout remains untouched.

The deterministic root adoption receipt is `akcar_ca2afc9543d0b909c375586610c7eb62`. The exercised public artifacts are:

| Playbook surface | SHA-256 |
| --- | --- |
| public CLI entrypoint | `sha256:02ee67029c94d1edf3a5d72c17efa195ca0bde22dadbcdd0764bff77d2efdd86` |
| engine candidate admission | `sha256:7fcee0844b6e9a59fc91cb9ad5ec0d23ebcbdf03f3700897449a01620ccf0269` |

## Exact Candidate And Receipt Proof

The Atlas valid fixture is preserved field-for-field, including `candidate_id`, `kind`, `name`, `statement`, `scope`, every provenance `source_type`, `ref`, and `classification`, the complete `review` object, `suggested_destination`, and `created_at`.

| Candidate | Input digest | Provenance digest | Record | Consumer receipt |
| --- | --- | --- | --- | --- |
| `knowledge-001` | `sha256:5b76c0d842006f35dd05b6235a443d58017a278c6a48cb20e1743238d717edcf` | `sha256:36b0ab61ddf453c50550b2c757ab89aae700a0a8e997352f97fe91eeb81990c0` | `playbook-akc-e41776343d6c8a9da8c9ddd5` | `playbook-akc-receipt-64cc425a70932663ec0f993d` |
| `knowledge-002` | `sha256:269055e3849157256a6dea512675edecf66a4c41bf2964667e2c99d6a3c43b97` | `sha256:689df8d8dc9e1aea36daf5c785919e9790394cf587f411c89f37cbd30e6c0e2f` | `playbook-akc-8060545e7f96f9d1ecf5f6e3` | `playbook-akc-receipt-98f21dca7811d89e9de6a523` |

The final two-candidate queue digest is `sha256:47bc02782c4d19001e7d0759b201292085e6784498a72855498d2304dff8f2f0`. Both candidate replays preserve queue bytes and consumer receipts exactly. The two candidate identities, record identities, and receipt identities remain unique; append order is deterministic; replay adds no duplicate.

The canonical doctrine snapshot digest remains `sha256:a20fc99f01216b83e67e06fe0ccc23b3ad554ade9551db424e1a2399bb6ff496` before and after admission. Candidate-only proof flags are all true, while `auto_promotion=false`, `promotion_authority=none`, `owner_repository_mutation=false`, and `doctrine_mutation=false`.

## Stable Fail-Closed Matrix

| Rejected drift | Stable root reason |
| --- | --- |
| Atlas bad-kind fixture or other canonical schema rejection | `KNOWLEDGE_ATLAS_SCHEMA_REJECTED` |
| candidate id or any non-provenance candidate field loss | `KNOWLEDGE_IDENTITY_LOSS` |
| provenance reference or classification drift | `KNOWLEDGE_PROVENANCE_MISMATCH` |
| unsupported kind/destination pairing | `KNOWLEDGE_DESTINATION_UNSUPPORTED` |
| absent correlated Playbook consumer receipt | `KNOWLEDGE_CONSUMER_RECEIPT_MISSING` |
| changed receipt identity, digest, decision, destination, or record correlation | `KNOWLEDGE_CONSUMER_RECEIPT_MISMATCH` |
| explicit promotion or candidate-to-doctrine authority | `KNOWLEDGE_AUTO_PROMOTION_DETECTED` |
| feature/merge ancestry loss, non-descendant checkout, consumer-path drift, or tracked dirt | `KNOWLEDGE_CONSUMER_REVISION_UNTRUSTED` |
| Rule, Pattern, Failure Mode, story, notes, memory, or other doctrine mutation | `KNOWLEDGE_DOCTRINE_MUTATION` |

Focused tests deliberately exercise the Atlas bad-kind fixture and identity, provenance, destination, receipt, promotion, revision, and doctrine tampering. A separate trust negative presents the owner checkout's pre-existing `dist` as the executable and proves it is rejected rather than reused. Every case fails closed at its stable root reason.

## Ratchet And Projection

The complete fixed family set is ComponentManifest, JobEnvelope, ContextPacket, ApprovalRecord, WorkerLease, EvidenceBundle, ExecutionReceipt, CardRecord, BoardEvent, MarkerEvidence, and KnowledgeCandidate.

`10 + 1 = 11`. `11 / 11 = 1.0 = 100%`. The Contracts Mesh lane is therefore `complete` at `11` accepted units and `11` implementation foundations. Current MarkerEvidence records the exact `91 -> 100` transition with `parent_marker_movement=false` and no external or marker mutation authority.

The current deterministic MarkerEvidence consumer receipt is `amer_129e808e4485f4ee75bd7d2abbd729b8`, with result identity `ameres_5d7d13d9a87ab458bde178f7f560ae26`. Its exact inputs are:

| Current marker input | SHA-256 |
| --- | --- |
| MarkerEvidence | `sha256:d01dd4641d084f43cc5fa80f960ae12ad1a6e315c802bed8e1629ec8f66f7942` |
| JobEnvelope | `sha256:f1281c4349b6483247c8acbfa5afa390b4392ea1cb69f1ba5d329de72a94f351` |
| ExecutionReceipt | `sha256:b4045aa8c23308bffd68812fc444660df1035d283747894cefd403165ebc4c2c` |
| source registry | `sha256:e1edccd1e7860f5aae31590e4b9a49a23f2fa3d3888aac7c9abe90e82e7fefa1` |

The receipt binds `adopted_family=KnowledgeCandidate`, numerator `11`, denominator `11`, percentage `100`, previous percentage `91`, and execution receipt `atr_knowledge_candidate_adoption_20260715`. Its scope, percentage math, freshness, transition, rollup, execution lineage, and evidence identity conformance flags are all true.

The authoritative lane registry, Atlas Book, contracts package README, and generated Atlas/Cortex owner exports agree. The canonical stack lock and repo inventory were regenerated because Playbook's governed local source-tree pin changed from the prior branch to the trusted KnowledgeCandidate feature tree; stack membership and release eligibility did not change. The resulting lock digest is `sha256:5d0cbfc752985784629daa62c5010f29a0896ce1599b6a58b165f8b5e02bc3ca`, and the inventory content digest is `sha256:aeb211bdc1f200e4499b61735655fb10be9b2ddd9af2749eaa53efd15e825c81`.

The owner-export generator refreshed 31 Atlas cards and two Cortex cards with `discord_mutation_authorized=false` and source revision `sha256:8e42b3408f377dda60c6da152f81fbd7fea536bd803301b0a3044702ce40f0ac`.

## Verification

- `npm --prefix packages/atlas-contracts run validate` - passed;
- `node ops/atlas/test_validate_contracts_v2_adoption.mjs` - passed with exactly `11 / 11 = 100%`;
- `node --test tests/test_atlas_knowledge_candidate_adoption.mjs` - 11 tests passed, including exact-revision build and stale-owner-`dist` rejection;
- `node --test tests/test_atlas_marker_evidence_admission.mjs` - 10 tests passed;
- actual public Playbook admission and replay proof in disposable Atlas state - passed twice with byte-identical deterministic receipts;
- `python ops/atlas/project_board_owner_export.py --check` and owner-export schema/semantic validation - passed;
- `python -m unittest tests.test_stack_repo_inventory tests.validation.test_validate_stack_lock_refresh -v` - 13 tests passed;
- root stack validation - `critical=0`, `error=0`; two inherited warnings remained outside this packet;
- `git diff --check`, bounded changed-path review, private-data scan, machine-specific committed-path scan, exact pre-existing untracked inventory comparison, and nested owner-repository before/after comparison - passed at closeout.

## Governance Closeout

**RULE - Atlas owns knowledge contract semantics; Playbook consumes without copying.**

**RULE - Candidate admission never grants doctrine-promotion authority.**

**PATTERN - Exact identity/provenance candidate-only intake with deterministic correlated receipt.**

**FAILURE MODE - Candidate-to-Doctrine Collapse.** Candidate intake becomes unsafe when a review candidate silently mutates or authorizes canonical Rule, Pattern, Failure Mode, story, notes, memory, or promoted doctrine.

No prohibited mutation or inferred marker movement occurred.
