# AI Repetition-to-Automation Pipeline Receipt-Derived Automation Candidate Extractor Contract Freeze

Date: 2026-07-07

## Scope

This receipt freezes the contract for a future root-owned read-only extractor that identifies automation candidates from committed ATLAS receipts.

This is a contract freeze only. It does not implement the worker.

## Selected From

`docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-POST-AI-WORK-SESSION-AND-CORTEX-HELPERS-NEXT-SLICE-SELECTION-2026-07-07.md`

## Definition

A receipt-derived automation candidate is a repeated, receipt-backed manual operator or Codex pattern that can later become one of these without owner mutation:

- a helper
- a prompt pack
- a selector or routing rule
- a validation or governance check
- a read-model or manifest projection

The candidate must be supported by committed ATLAS root evidence. It must not be inferred from hidden chat transcript memory, uncommitted local residue, platform state, or owner-repo truth that ATLAS root does not own.

## Admitted Inputs

The future extractor may read:

- `docs/ops/**` receipts committed under the ATLAS root
- ATLAS Book mirrors under `docs/atlas-book/**`
- continuity manifests under `docs/memory/initiatives/continuity-manifest-*.json`
- root-owned helper contracts and source surfaces under `ops/atlas/**`
- Cortex advisory helper contracts and source surfaces under `ops/cortex/**`
- stack validation receipts under `runtime/receipts/validation/**` as read-only validation context only

## Excluded Inputs

The future extractor must not read or rely on:

- `repos/**`
- owner-repo receipts when they require owner-truth interpretation or owner mutation
- `secrets/**`
- `.env`
- `.env.*`
- `archive/**`
- `.vercel/**`
- `.playwright-mcp/**`
- hidden transcript, chat, or session state
- deploy or platform state

## Candidate Categories

The future extractor may classify candidates into these categories:

- `helper`
- `prompt_pack`
- `selector_or_routing_rule`
- `validation_or_governance_check`
- `read_model_or_manifest_projection`

## Repetition Counting

The future extractor may count repetition only when a pattern appears in committed durable evidence:

- exact repeated receipt titles or packet shapes across at least two committed receipts
- semantic receipt families with the same blocker class or same manual action chain across at least two committed receipts
- repeated packet-chain shapes such as selector, contract freeze, owner-surface admission, prompt pack, implementation-readiness, worker reconciliation, and projection refresh
- repeated blocker classes such as proof-gated hold, owner-lane separation, stale projection, advisory drift, manifest freshness, or current-head proof freshness

The extractor must prefer implemented or proof-backed helper families over narration-only candidate families.

## False-Positive Controls

The future extractor must fail closed or reject candidates when:

- fewer than two committed receipts support the pattern
- the candidate depends on hidden transcript memory
- the candidate needs owner-repo mutation
- the candidate needs Supabase, Vercel, deploy, publication, or secret mutation
- the candidate would infer marker movement
- the candidate would claim owner truth or final proof freshness
- the candidate lacks explicit owner and non-claim boundaries
- the candidate is only wording cleanup

## Allowed Output Fields

The future extractor may emit only these top-level fields:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `source_refs`
- `candidate_count`
- `candidates`
- `rejected_candidates`
- `warnings`
- `blockers`
- `safe_to_use`

Candidate entries may include only:

- `id`
- `title`
- `category`
- `status`
- `supporting_receipts`
- `pattern_summary`
- `repeat_count`
- `recommended_next_packet`
- `boundaries`
- `rejection_reason`

## Forbidden Authority

The future extractor must not have authority to:

- execute work
- approve work
- claim owner truth
- finalize receipts
- deploy
- handle secrets
- scrape transcripts
- dispatch `_stack`
- mutate repos
- mutate platforms
- move markers

## Future Implementation Path

If a later admission packet approves implementation, the expected files are:

- `ops/atlas/receipt_automation_candidate_extractor.py`
- `tests/test_atlas_receipt_automation_candidate_extractor.py`

## Required Proof Matrix For A Later Implementation

A later implementation must prove:

- success on at least one repeated helper-family candidate from committed ATLAS receipts
- rejection when only one receipt supports a pattern
- rejection of owner-repo paths
- rejection of hidden transcript or session inputs
- rejection of secret, deploy, platform, archive, `.vercel`, and `.playwright-mcp` paths
- deterministic output ordering
- no marker movement fields in output
- no `_stack` dispatch or mutation authority
- valid JSON output

## Marker Decision

No marker moves from this receipt.

`AI Repetition-to-Automation Pipeline` remains `38%` because this packet freezes a contract but does not yet land the extractor, prove execution, widen adoption, or clear a blocker.

## Exact Next Packet

`AI Repetition-to-Automation Pipeline receipt-derived automation candidate extractor first-implementation admission`

## Boundaries Preserved

- No owner-repo mutation
- No Fitness app mutation
- No Mazer game mutation
- No Supabase mutation
- No Vercel mutation
- No deploy or publication mutation
- No secret or `.env*` access
- No protected-surface mutation
- No marker movement claim
- No worker implementation
