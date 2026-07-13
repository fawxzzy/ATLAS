# Cortex Dual-Mode Replacement Readiness Chat-Style Synthesis Packet Generation Prompt-Pack And Worker Handoff Contract

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only prompt-pack and worker handoff contract`
- Control-plane checkpoint: `main@d718d14c`
- Full Git head at contract freeze: `d718d14c5f23a08c402e9bd821db6526f541034a`
- Admission source: `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md`
- Historical evidence preserved: `the 2026-07-10 receipts remain historical evidence and retain their original checkpoint SHAs`
- Marker movement: none

## Decision And Boundary

Freeze the single docs-only worker contract for the next admitted same-lane slice. This packet does not implement the generator, does not update the continuity manifest, does not move any marker, does not touch an owner repository, and does not open another lane.

`Cortex Dual-Mode Replacement Readiness` remains `40%`.

The future helper is frozen as:

- deterministic
- evidence-aware
- advisory
- read-only by default
- not a generic ChatGPT clone

The future helper must emit exactly one bounded Codex handoff and must never execute that handoff.

Authority posture remains:

- ATLAS is the authority for receipts, manifests, marker truth, identity, and routing.
- Playbook is doctrine input and decision support only, not implementation proof.
- `_stack` and Codex remain the governed execution plane.
- Native-first remains frozen: do not introduce a custom SQLite execution queue or scheduler.

## Exact Future Files

Only these future implementation files are admitted:

- `ops/cortex/chat_style_synthesis_packet_generator.py`
- `tests/test_cortex_chat_style_synthesis_packet_generator.py`

This prompt-pack packet must not create either file.

No third committed implementation path is admitted.

## Exact Worker Objective

Freeze one implementation objective only:

Build the admitted helper and focused test so explicit governed root inputs can be synthesized into deterministic strategy, architecture, decision, research, or handoff packets with provenance, trust labels, options, tradeoffs, one recommendation, risk and evidence gaps, and exactly one bounded Codex handoff.

The worker objective is synthesis only. It does not authorize execution, marker movement, final authoritative receipts, owner-repo mutation, platform mutation, or scheduler invention.

## Admitted Sources And Excluded Sources

The future worker may consume only explicit governed root-relative inputs from these admitted source classes:

- ATLAS receipts under `docs/ops/**`
- continuity manifests under `docs/memory/initiatives/**`
- ATLAS Book projections under `docs/atlas-book/**`
- canonical workflow profile surfaces under `docs/memory/profiles/**`
- root-owned doctrine and governance references under `docs/**` when explicitly supplied
- explicit root-owned helper or planner outputs under `tmp/atlas/**`
- explicit root-owned validation summaries under `tmp/atlas/**`
- root git metadata
- explicit root-owned test fixtures constructed inside the admitted test file or under ignored `tmp/atlas/**`

The future worker must reject, ignore, or classify as forbidden these excluded source classes:

- hidden transcripts
- private reasoning or chain-of-thought inference
- arbitrary chat exports or pasted conversation logs treated as truth
- owner-repo paths, including `repos/**`
- absolute paths
- parent traversal paths
- `.env*`
- `secrets/**`
- `.vercel`
- `.playwright-mcp`
- `archive`
- raw browser profiles
- hidden transcript sources
- raw customer data
- raw health data
- raw payment data
- raw account data
- live Vercel input
- live Supabase input
- live Discord input
- live GitHub input
- arbitrary network or API input
- model training or fine-tuning input

## Source And Path Policy

The future worker contract requires all of the following:

- root-relative inputs only
- safe explicit outputs only under `tmp/atlas/**`
- no output without an explicit output flag
- no absolute paths
- no parent traversal
- no owner-repo paths
- no `.env*`, `secrets/**`, `.vercel`, `.playwright-mcp`, `archive`, raw browser profiles, or hidden transcript sources
- no raw customer, health, payment, or account data
- no live Vercel, Supabase, Discord, GitHub, or arbitrary network input
- no model training or fine-tuning

JSON writes are allowed only when `--output` is supplied. Markdown writes are allowed only when `--markdown-output` is supplied. Without those explicit flags, the helper must remain read-only and file-write silent.

## Trust And Conflict Model

Every material statement must be classified as exactly one of these trust classes:

- `verified_fact`
- `receipt_backed`
- `manifest_backed`
- `git_backed`
- `validation_backed`
- `reasoned_inference`
- `operator_assumption`
- `unverified`
- `conflicted`
- `forbidden`

Material statements must retain:

- `source_refs`
- `source_digests`

Inference, assumption, or conflict must never be serialized as verified fact.

Contradictory evidence must produce:

- statement class `conflicted` on the affected material statements
- top-level helper status `conflict`

Strict mode must exit nonzero on `conflict` or `blocker`.

## CLI Contract

Freeze this command surface:

```text
python ops/cortex/chat_style_synthesis_packet_generator.py
```

Freeze these flags:

- `--json`
- repeatable `--source <root-relative-path>`
- `--mode strategy|architecture|decision|research|handoff`
- `--output <root-relative-json-path>`
- `--markdown-output <root-relative-markdown-path>`
- `--strict`
- `--schema-only`

No other flag is admitted by this worker contract.

## Schema And Deterministic Output Contract

Freeze this schema version:

```text
atlas.cortex.chat_style_synthesis_packet.v1
```

The helper must emit deterministic JSON and deterministic Markdown for identical inputs.

Freeze this deterministic top-level JSON field order:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `mode`
- `source_refs`
- `source_digests`
- `trust_summary`
- `synthesis_packet`
- `options`
- `recommendation`
- `evidence_gaps`
- `risk_register`
- `playbook_refs`
- `marker_impacts`
- `codex_handoff`
- `authority_denials`
- `warnings`
- `blockers`
- `safe_to_use`
- `next_recommended_packet`

Freeze the deterministic `synthesis_packet` record fields:

- `title`
- `packet_id`
- `captured_at`
- `source_refs`
- `source_digests`
- `decision_problem`
- `current_state`
- `objective`
- `constraints`
- `facts`
- `inferences`
- `assumptions`
- `evidence_gaps`
- `options`
- `tradeoffs`
- `recommended_option`
- `rejected_options`
- `risk_register`
- `playbook_rule_refs`
- `pattern_refs`
- `failure_mode_refs`
- `marker_impacts`
- `authority_boundaries`
- `codex_handoff`
- `verification_requirements`
- `next_recommended_packet`

Freeze the deterministic per-option record fields:

- `option_id`
- `description`
- `benefits`
- `costs`
- `risks`
- `proof_available`
- `external_input_required`
- `authority_required`
- `score`
- `rejection_reason`

Freeze the helper statuses:

- `ok`
- `advisory_gap`
- `conflict`
- `blocker`
- `internal_error`

Freeze the exit policy:

- `ok`: exit `0`
- `advisory_gap`: exit `0`
- `conflict`: exit `0` unless `--strict`, then nonzero
- `blocker`: exit nonzero
- `internal_error`: exit nonzero

Freeze schema-only behavior:

- `--schema-only` emits the deterministic schema shape without requiring implementation execution inputs
- `--schema-only` does not widen read authority
- `--schema-only` does not write files unless an explicit admitted output flag is also supplied

## Codex Handoff Contract

The helper must emit exactly one bounded `codex_handoff` record. Zero handoffs or more than one handoff is a blocker.

Freeze the required `codex_handoff` content:

- one objective
- exact allowed files
- exact forbidden files
- verification commands
- stop conditions
- authority denials
- expected output paths
- no automatic execution

The handoff must remain text or structured advisory output only. It must not execute itself, enqueue work, call Codex, mutate files outside explicit helper outputs, or claim completion.

The helper must fail closed if one bounded handoff cannot be produced safely.

## Authority Denials And Stop Conditions

The future worker and the generated handoff must explicitly deny:

- repo mutation beyond the admitted helper and test pair during future implementation
- stage, commit, push, PR approval, deploy, or platform mutation by the helper
- secret access
- hidden transcript scraping or private reasoning inference
- owner-repo reads as unrestricted synthesis input
- live external system queries
- marker movement
- final authoritative receipt emission
- packet execution
- custom execution queue or scheduler implementation

The future worker must stop rather than widen if any denied authority or any third committed path is required.

Stop immediately and return a blocker instead of widening if the future worker would require:

- a third committed implementation path
- hidden transcript scraping
- private reasoning inference
- unrestricted owner-repo reads
- live external system queries
- secret or environment-file access
- platform mutation
- packet execution
- marker movement
- custom SQLite queue or scheduler implementation
- model training or fine-tuning

## Diff-Addressable Proof Matrix

The future implementation diff must satisfy all 30 proof requirements below. These tighten the 2026-07-10 admission into implementation acceptance criteria that are directly testable or smoke-testable from the final diff:

1. The helper accepts at least one valid explicit governed root-owned `--source` input and preserves that source ref in deterministic output.
2. The helper accepts multiple explicit admitted source classes in one run and preserves deterministic source ordering for identical inputs.
3. Verified facts remain serialized separately from inferences in the generated synthesis packet.
4. Operator assumptions are surfaced explicitly rather than implied.
5. Evidence gaps are emitted explicitly when the sources do not fully prove the decision problem.
6. The helper emits multiple bounded options for the admitted synthesis modes when the sources support comparison.
7. Tradeoffs are deterministic for identical inputs and mode selection.
8. Exactly one recommendation is produced when the packet is `safe_to_use`.
9. Rejected options include explicit rejection reasons.
10. Playbook rules, patterns, and failure modes from admitted root docs are preserved as doctrine refs, not as implementation proof.
11. Marker impacts remain advisory and never claim marker movement authority.
12. The helper emits exactly one bounded Codex handoff objective.
13. The Codex handoff cannot execute itself and never claims implementation completion.
14. A hidden transcript source is rejected or classified as forbidden.
15. An owner-repo source is rejected or classified as forbidden.
16. A `.env*` source is rejected or classified as forbidden.
17. A live Vercel, Supabase, Discord, or GitHub source is rejected or classified as forbidden.
18. An absolute input path is rejected.
19. An absolute JSON output path is rejected.
20. A protected or out-of-scope output path is rejected.
21. A safe explicit `tmp/atlas/**` JSON output path is accepted.
22. Deterministic JSON field ordering is preserved.
23. Deterministic Markdown generation is preserved for identical inputs.
24. Contradictory evidence yields `conflict` status and `conflicted` statement classification.
25. `--strict` exits nonzero on `conflict` or `blocker`.
26. No JSON or Markdown file is written without an explicit admitted output flag.
27. Authority denials are always emitted.
28. The helper does not mutate markers, receipts, manifests, owner repos, or platforms.
29. The helper does not require network access for admitted proofs and smokes.
30. The implementation diff and proof run do not increase stack-validation warnings or errors.

Fixtures for these proofs may be created only inside the admitted test file or inside explicit ignored `tmp/atlas/**` smoke paths. No committed third file is admitted.

## Exact Future Proof Commands

The future implementation worker must run exactly these proof commands:

1. `python -m unittest tests.test_cortex_chat_style_synthesis_packet_generator -v`
2. `python ops/cortex/chat_style_synthesis_packet_generator.py --json --mode strategy --source docs/memory/profiles/zachariah_workflow_profile.md --source docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md --output tmp/atlas/cortex-chat-style-synthesis-smoke.json`
3. `python ops/cortex/chat_style_synthesis_packet_generator.py --json --mode handoff --source docs/memory/profiles/zachariah_workflow_profile.md --source docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md --markdown-output tmp/atlas/cortex-chat-style-synthesis-smoke.md`
4. `python ops/cortex/chat_style_synthesis_packet_generator.py --json --schema-only`
5. `python ops/cortex/chat_style_synthesis_packet_generator.py --json --mode decision --source tmp/atlas/cortex-chat-style-synthesis-conflict-fixture.json --output tmp/atlas/cortex-chat-style-synthesis-conflict.json --strict`
6. `python ops/validation/validate_stack.py`
7. `git diff --check`
8. `git status --short`
9. `git diff --name-only`

The strict conflict fixture named in command 5 may exist only as test-created or ignored `tmp/atlas/**` smoke data. It does not admit a third committed fixture path.

## Reusable Governance Findings

Record these reusable findings for future doctrine reuse:

- `RULE - Evidence-Class Separation`: inference, assumption, and conflict must never be serialized as verified fact.
- `PATTERN - Synthesis Before Governed Execution`: Cortex produces one bounded advisory handoff; `_stack` and Codex execute under a separate authority-bearing job.
- `FAILURE MODE - Chat Prose As Truth`: conversational fluency or pasted summaries are treated as implementation evidence without Git, receipt, manifest, or validation backing.
- `RULE - Diff-Addressable Acceptance Criteria`: every criterion consumed by spec-to-diff must have literal final-diff evidence; runtime safety belongs in tests and receipts.

## Exact Next Packet

Name only this next packet:

```text
Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation implementation-readiness closeout and worker routing
```

Do not open or implement that next packet in this task.

## Marker Decision

No marker moves.

`Cortex Dual-Mode Replacement Readiness` remains `40%`.

Reason:

- this packet freezes the prompt-pack and worker handoff contract only
- no generator or test has been implemented
- no continuity manifest has been updated
- no reconciliation or marker-ratchet receipt has been created
- the native-first decision remains unchanged and no custom SQLite execution queue or scheduler is introduced

## Completion

Completion: `100%` for this docs-only prompt-pack and worker handoff contract.

No owner repo was mutated.
No platform surface was mutated.
No continuity manifest was edited.
No marker moved.
No custom queue or scheduler was introduced.
