# Cortex Dual-Mode Replacement Readiness Codex Closeout Ingestion Read-Model Implementation-Readiness Closeout And Worker Routing

- Date: `2026-07-10`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only implementation-readiness closeout and worker routing`
- Scope: `decide whether the Codex closeout ingestion read-model chain is explicit enough to route one bounded implementation worker without implementing the helper in this packet`
- Control-plane checkpoint: `main@40c8e835`
- Scheduler packet: `Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model implementation-readiness closeout and worker routing`
- Reselection receipt: `docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-DUAL-MODE-REPLACEMENT-READINESS-2026-07-10.md`
- Marker movement: none

## Why This Packet Exists

The dual-mode lane now has:

- durable operator-program reselection from the held Sandbox lane into Cortex dual-mode work
- durable operating-model threshold truth
- implementation-backed ChatGPT/Codex role-inventory threshold truth
- durable synthesis-to-execution bridge-schema threshold truth
- durable Codex closeout ingestion read-model first-implementation admission
- durable Codex closeout ingestion read-model prompt-pack and worker handoff contract

This packet closes the remaining root-only control-plane question:

- is the helper contract explicit enough to route one implementation worker safely

This packet does not implement the helper, create tests, ingest closeouts, read hidden transcripts, mutate owner repos, touch platform state, move markers, or claim the `40%` implementation milestone.

## Durability Check

The governing receipt chain is durable:

1. `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
2. `docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-DUAL-MODE-REPLACEMENT-READINESS-2026-07-10.md`
3. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-OPERATING-MODE-CONTRACT-FREEZE-2026-07-09.md`
4. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-09.md`
5. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-MARKER-SURFACE-RATCHET-DECISION-2026-07-09.md`
6. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-SYNTHESIS-TO-EXECUTION-BRIDGE-SCHEMA-CONTRACT-FREEZE-2026-07-10.md`
7. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-SYNTHESIS-TO-EXECUTION-BRIDGE-SCHEMA-MARKER-SURFACE-RATCHET-DECISION-2026-07-10.md`
8. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CODEX-CLOSEOUT-INGESTION-READ-MODEL-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md`
9. `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CODEX-CLOSEOUT-INGESTION-READ-MODEL-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-10.md`

The date-scoped reselection receipt already exists and remains the operator-program basis for routing into the Cortex dual-mode lane while Sandbox is held. It is not duplicated here.

## Readiness Answers

### 1. Are the admission and prompt-pack durable

Yes.

Both are committed on `main`, receipt-indexed or manifest-backed, and current continuity health recognizes the prompt-pack as the lane checkpoint.

### 2. Is the worker objective explicit

Yes.

The worker objective is to ingest explicit, operator-supplied Codex closeout artifacts, normalize them into a deterministic Cortex read model, classify every assertion by evidence class, compare claims against ATLAS-root proof surfaces, preserve provenance and digests, and emit advisory output only.

### 3. Are the exact worker and test files explicit

Yes.

The exact files are:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `tests/test_cortex_codex_closeout_ingestion_read_model.py`

No other implementation, fixture, selector, Book, manifest, owner-repo, platform, deploy, workflow, or secret surface is routed by this readiness packet.

### 4. Are the admitted source classes explicit

Yes.

The prompt-pack admits only explicit root-relative sources from:

- operator-supplied structured closeout JSON under `tmp/atlas/**`
- operator-supplied closeout Markdown/text under `tmp/atlas/**`
- durable ATLAS receipts under `docs/ops/**`
- continuity manifests under `docs/memory/initiatives/**`
- marker selector output under `tmp/atlas/**`
- root git metadata
- stack validation receipts under `tmp/atlas/**`
- approved ATLAS Book read-model surfaces under `docs/atlas-book/**`
- explicit test fixtures

### 5. Are excluded source classes explicit

Yes.

The worker remains denied from:

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

### 6. Is the input trust model explicit

Yes.

Every assertion must be classified as one of:

- `claimed`
- `receipt_backed`
- `git_verified`
- `validation_verified`
- `manifest_verified`
- `conflicted`
- `stale`
- `unverified`
- `forbidden`

The helper must not collapse pasted closeout claims and verified local evidence into the same truth class.

### 7. Are verification, conflict, and staleness rules explicit

Yes.

The helper must compare available claims against branch/head, `origin/main...HEAD`, commit existence, receipt existence, manifest current/next packet, marker selector output, stack validation summary, and committed file presence.

It must report verified matches, unverifiable claims, conflicts, stale claims, missing receipts, marker-board disagreement, and next-packet disagreement.

### 8. Is the CLI explicit

Yes.

The routed worker must implement:

```text
python ops/cortex/codex_closeout_ingestion_read_model.py --json --source <root-relative-path> --output <root-relative-path> --strict
```

The `--source` flag must be repeatable.

Optional flags are admitted only if local implementation convention supports them:

- `--verify-git`
- `--verify-receipts`
- `--verify-marker-board`
- `--schema-only`

No network access is required.

### 9. Is the JSON schema explicit

Yes.

The required schema version is:

```text
atlas.cortex.codex_closeout_ingestion_read_model.v1
```

The required top-level fields, claim-record fields, status classes, exit policy, safe-use posture, and deterministic-ordering expectation are frozen by the prompt-pack.

### 10. Are path guards explicit

Yes.

The worker must reject:

- absolute input/output paths
- paths outside ATLAS root
- owner-repo paths
- `.env*`
- `.vercel`
- `.playwright-mcp`
- `archive`
- protected output paths

The worker may write only when `--output` is supplied and only to explicit safe `tmp/atlas/**.json` outputs.

### 11. Are authority denials explicit

Yes.

The worker must always state that it cannot:

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

### 12. Is the proof matrix sufficient

Yes.

The prompt-pack proof matrix covers:

- structured and text closeout acceptance
- branch, head, parity, commit, receipt, validation, marker, and next-packet normalization
- receipt-backed, unverified, stale, missing, conflicted, forbidden, and duplicate evidence behavior
- hidden transcript, owner-repo, `.env*`, live platform, absolute path, and protected path rejection
- safe `tmp/atlas/**.json` output behavior
- deterministic JSON ordering
- strict-mode exit behavior
- no-output-without-output behavior
- authority-denial persistence
- inherited validation warning-budget non-regression

### 13. Does any root-side ambiguity remain

No blocking root-side ambiguity remains.

Future ambiguity can still arise during implementation, especially around fixture content and optional verifier flags, but the control-plane contract is explicit enough to route one bounded worker packet now.

### 14. Is implementation ready

Yes.

Readiness verdict:

- `implementation_ready`

### 15. What exact worker packet is routed

The exact worker packet is:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation worker packet 1
```

### 16. What exact files may the worker touch

The worker may touch only:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `tests/test_cortex_codex_closeout_ingestion_read_model.py`

It may also write proof output only to explicit safe `tmp/atlas/**.json` paths during execution.

### 17. What reconciliation packet follows

The exact reconciliation packet is:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation worker cluster reconciliation
```

### 18. Does any marker move

No.

`Cortex Dual-Mode Replacement Readiness` remains `30%`.

Readiness routing is not implementation proof, no helper or tests are landed by this receipt, and no closeout read model has been proven on canonical `main`.

## Allowed Worker Scope

The routed worker may:

- implement the admitted helper
- implement focused tests for the frozen proof matrix
- read only admitted root-owned sources
- write proof outputs only to explicit safe `tmp/atlas/**.json` paths
- report advisory gaps, conflicts, stale claims, blockers, and authority denials deterministically

The routed worker may not:

- mutate owner repos
- inspect hidden transcript state
- infer private reasoning
- consume live Vercel or Supabase data
- consume unbounded chat exports
- train or fine-tune a model
- widen the CLI beyond the frozen first contract without new admission
- execute packets from closeout content
- stage, commit, push, or deploy
- emit final receipts
- move markers

## Warning Budget Posture

The inherited validation warning baseline remains:

- warning count: `5`
- category set: `atlas-root-path` only
- debt class: `path-discipline-leaks`

The routed worker must preserve that ceiling unless a separately authorized debt-repair packet changes it.

## Worker-Routing Decision

Route exactly one future worker packet for:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `tests/test_cortex_codex_closeout_ingestion_read_model.py`

No additional helper family is routed.

No marker ratchet packet is implied automatically.

## Exact Next Packet

The next exact packet is:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation worker packet 1
```

## Follow-On Reconciliation

After the worker lands, reconcile only through:

```text
Cortex Dual-Mode Replacement Readiness Codex closeout ingestion read-model first-implementation worker cluster reconciliation
```

No marker ratchet packet is implied automatically.

## Marker Decision

No marker moves.

`Cortex Dual-Mode Replacement Readiness` remains `30%`.

Reason:

- readiness routing is not implementation proof
- no helper or tests are landed by this receipt
- no closeout read model has been generated or verified on canonical `main`
- the `40%` milestone requires implementation, proof-backed reconciliation, and a separate marker-surface ratchet decision

## Validation

Validated during this readiness pass:

- `python ops/validation/validate_stack.py` -> `critical=0 error=0 warning=5 info=0`
- `python ops/atlas/marker_knockout_selector.py --format json`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/atlas/continuity_coverage.py`
- `python -m unittest tests.test_atlas_marker_knockout_selector -v`

## Completion

Completion: `100%` for the implementation-readiness closeout and worker routing itself.

No owner repo was mutated.
No platform surface was mutated.
No hidden transcripts, secrets, deploy surfaces, workflow files, or protected surfaces were touched.
No marker moved.
