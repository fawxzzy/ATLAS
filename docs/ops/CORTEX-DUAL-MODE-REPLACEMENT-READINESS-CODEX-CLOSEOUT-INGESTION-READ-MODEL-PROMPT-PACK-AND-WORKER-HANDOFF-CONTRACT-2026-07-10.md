# Cortex Dual-Mode Replacement Readiness Codex Closeout Ingestion Read-Model Prompt-Pack And Worker Handoff Contract

- Date: `2026-07-10`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only prompt-pack and worker handoff contract`
- Control-plane checkpoint: `main@8859a580`
- Admission receipt: `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CODEX-CLOSEOUT-INGESTION-READ-MODEL-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md`
- Scheduler packet: `Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model prompt-pack and worker handoff contract`
- Marker movement: none

## Decision

Freeze the exact implementation contract for a future read-only Cortex helper that converts explicit Codex closeout artifacts into a deterministic, provenance-aware read model.

The future helper is part of the Cortex Bridge:

```text
Codex execution closeout
-> structured ingestion
-> verified/advisory Cortex read model
-> ATLAS restart state and future synthesis inputs
```

This packet does not implement the helper, create tests, ingest hidden transcripts, mutate owner repos, touch platform state, move markers, or claim the `40%` implementation milestone.

## Exact Future Files

The already-admitted future worker may touch only:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `tests/test_cortex_codex_closeout_ingestion_read_model.py`

Do not create either file in this prompt-pack packet.

## Worker Objective

The future helper must:

- ingest explicit, operator-supplied Codex closeout artifacts
- normalize closeout fields into a deterministic Cortex read model
- distinguish claims from verified evidence
- compare closeout claims against approved ATLAS-root evidence
- identify stale commits, stale packets, conflicting marker claims, and missing proof
- preserve source provenance and source digests
- emit advisory output only
- remain read-only
- never execute packets
- never commit, stage, push, deploy, or mutate repositories
- never ratchet markers
- never scrape hidden transcript state
- never infer private reasoning
- never treat user-pasted text as automatically authoritative

## Admitted Source Classes

The future helper may consume only explicit root-relative inputs from these source classes:

- operator-supplied structured closeout JSON under `tmp/atlas/**`
- operator-supplied closeout Markdown/text under `tmp/atlas/**`
- durable ATLAS receipts under `docs/ops/**`
- continuity manifests under `docs/memory/initiatives/**`
- marker selector output under `tmp/atlas/**`
- root git metadata
- stack validation receipts under `tmp/atlas/**`
- approved ATLAS Book read-model surfaces under `docs/atlas-book/**`
- explicit test fixtures

The helper must not admit by default:

- hidden conversation history
- private chain of thought
- browser profiles
- owner-repo source trees
- `.env*`
- tokens or secrets
- Vercel/Supabase live data
- customer, payment, or health data
- arbitrary network/API input
- raw deployment logs
- unbounded chat exports

## Input Trust Model

Every ingested assertion must be classified as exactly one of:

- `claimed`
- `receipt_backed`
- `git_verified`
- `validation_verified`
- `manifest_verified`
- `conflicted`
- `stale`
- `unverified`
- `forbidden`

The helper must not collapse these into a single truth class. A pasted closeout can supply claims, but only local evidence can promote a claim into a verified class.

## Core Closeout Fields

The future helper should normalize:

- `message_id`
- `captured_at`
- `source_ref`
- `source_digest`
- `branch`
- `head`
- `remote_head`
- `parity`
- `commits`
- `bundles_attempted`
- `bundles_completed`
- `files_changed`
- `tests_run`
- `validation`
- `marker_changes`
- `current_marker_board`
- `blockers`
- `risks`
- `residue`
- `boundaries_preserved`
- `owner_repos_mutated`
- `platforms_mutated`
- `secrets_touched`
- `next_exact_packet`
- `completion_percent`

Unknown or absent fields must remain absent or become explicit warnings. They must not be guessed.

## Verification Model

Where evidence is available, the helper must compare closeout claims against:

- current branch/head
- `origin/main...HEAD`
- commit existence
- receipt existence
- manifest current/next packet
- marker selector output
- stack validation summary
- committed file presence

The helper must report:

- verified matches
- unverifiable claims
- conflicts
- stale claims
- missing receipts
- marker-board disagreement
- next-packet disagreement

## Conflict And Staleness Model

A claim must be marked `conflicted` when local evidence contradicts it.

A claim must be marked `stale` when it refers to an older head, older packet, older marker board, or superseded manifest checkpoint while newer root evidence exists.

A claim must remain `unverified` when it is plausible but lacks local evidence.

A claim must be marked `forbidden` when verification would require protected sources such as hidden transcripts, secrets, owner repos, Vercel/Supabase live data, deploy logs, workflow dispatch state, or arbitrary network/API access.

## CLI Contract

Expected command:

```text
python ops/cortex/codex_closeout_ingestion_read_model.py
```

Required options:

- `--json`
- `--source <root-relative-path>` repeatable
- `--output <root-relative-path>`
- `--strict`

Optional options if the local convention supports them:

- `--verify-git`
- `--verify-receipts`
- `--verify-marker-board`
- `--schema-only`

No network access should be required.

## JSON Output Contract

The helper must emit deterministic JSON with this schema version:

```text
atlas.cortex.codex_closeout_ingestion_read_model.v1
```

Top-level deterministic fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `source_digests`
- `closeouts`
- `normalized_state`
- `verification_summary`
- `verified_claims`
- `unverified_claims`
- `conflicts`
- `stale_claims`
- `missing_receipts`
- `marker_deltas`
- `next_packet`
- `authority_denials`
- `warnings`
- `blockers`
- `safe_to_use`
- `next_recommended_packet`

Each claim record should support:

- `claim_id`
- `category`
- `field`
- `claimed_value`
- `evidence_class`
- `evidence_refs`
- `verified_value`
- `status`
- `conflict_reason`

## Status Classes

Allowed status classes:

- `ok`
- `advisory_gap`
- `conflict`
- `blocker`
- `internal_error`

## Exit Policy

- Exit `0` for `ok`.
- Exit `0` for `advisory_gap` unless `--strict`.
- Exit nonzero for `conflict` in strict mode.
- Exit nonzero for `blocker`.
- Exit nonzero for `internal_error`.

## Path Policy

The helper must:

- reject absolute input/output paths
- reject paths outside ATLAS root
- reject owner-repo paths
- reject `.env*`, `.vercel`, `.playwright-mcp`, and `archive`
- allow explicit input/output under `tmp/atlas/**`
- write only when `--output` is supplied
- avoid creating runtime-latest files by default

## Authority Denials

The helper must always state that it cannot:

- execute a packet
- mutate a repository
- stage, commit, or push
- change a marker
- approve a PR
- deploy
- access secrets
- scrape hidden transcripts
- treat closeout prose as final truth
- override ATLAS receipts, manifests, or selectors

## Proof Matrix

The future implementation must prove at least:

1. Valid structured Codex closeout accepted.
2. Markdown/text closeout accepted if explicit and root-relative.
3. Branch/head normalized.
4. Commit existence verified when requested.
5. Parity claim verified when requested.
6. Validation summary normalized.
7. Marker deltas normalized.
8. Current marker board normalized.
9. Next exact packet normalized.
10. Receipt-backed claim classified correctly.
11. Unverified prose claim remains advisory.
12. Stale head detected.
13. Missing commit detected.
14. Missing receipt detected.
15. Marker-board conflict detected.
16. Manifest next-packet conflict detected.
17. Duplicate closeout deduplicated by digest/message id.
18. Hidden transcript source rejected.
19. Owner-repo source path rejected.
20. `.env*` source rejected.
21. Vercel/Supabase live-data source rejected.
22. Absolute input path rejected.
23. Absolute output path rejected.
24. Protected output path rejected.
25. Safe `tmp/atlas/**.json` output accepted.
26. Deterministic JSON ordering.
27. Strict mode exits nonzero on conflicts/blockers.
28. No output file written without `--output`.
29. Authority denials always emitted.
30. Inherited validation warning count is not increased.

## Exact Proof Commands For The Worker

The implementation worker must run:

1. `python -m unittest tests.test_cortex_codex_closeout_ingestion_read_model -v`
2. `python ops/cortex/codex_closeout_ingestion_read_model.py --json --source tmp/atlas/codex-closeout-fixture.json --output tmp/atlas/codex-closeout-ingestion-smoke.json --strict --verify-git --verify-receipts --verify-marker-board`
3. `python ops/cortex/codex_closeout_ingestion_read_model.py --json --schema-only`
4. `python ops/validation/validate_stack.py`
5. `git status --short`
6. `git diff --name-only`

Fixture names may be tightened by the implementation-readiness packet, but the worker must not widen beyond the exact admitted helper/test files without a new admission.

## Exact Forbidden Authority

The worker must not:

- create implementation files before the implementation packet
- touch owner repos
- read or print secrets
- read `.env*`
- touch deploy or workflow surfaces
- query Vercel or Supabase
- scrape hidden transcript/private reasoning state
- consume unbounded chat exports
- train or fine-tune a model
- move markers
- emit final receipts
- add files outside the admitted helper/test pair
- widen into Book or restart-guide edits during helper implementation

## Stop Conditions

Stop and return without implementation if the worker would require:

- hidden transcript scraping
- private reasoning inference
- external product/API access
- owner-repo mutation
- secret, deploy, Vercel, Supabase, or workflow authority
- model training or fine-tuning
- unbounded chat-history ingestion
- marker movement
- file additions beyond the admitted helper/test pair
- treating user-pasted closeout prose as final truth

## Expected Next Packet

Open only this next packet:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model implementation-readiness closeout and worker routing
```

That packet should decide whether the future worker has enough frozen contract, fixture, proof, and stop-condition detail to be routed for implementation.

## Marker Decision

No marker moves.

`Cortex Dual-Mode Replacement Readiness` remains `30%`.

Reason:

- this packet freezes the prompt-pack and worker handoff contract only
- no helper is implemented
- no closeout read model is generated
- no ingestion proof exists yet
- the `40%` milestone requires implementation, proof-backed reconciliation, and a separate marker-surface ratchet decision

## Completion

Completion: `100%` for the prompt-pack and worker handoff contract itself.

No owner repo was mutated.
No platform surface was mutated.
No hidden transcripts, secrets, deploy surfaces, workflow files, or protected surfaces were touched.
No marker moved.
