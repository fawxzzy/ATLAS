# Cortex Dual-Mode Replacement Readiness Chat-Style Synthesis Packet Generation First-Implementation Admission

- Date: `2026-07-10`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only first-implementation admission`
- Scope: `admit the future chat-style synthesis packet generator implementation boundary`
- Scheduler packet: `Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation first-implementation admission`
- Reselection receipt: `docs/ops/ATLAS-ROOT-OPERATOR-RESELECTION-TO-CORTEX-DUAL-MODE-REPLACEMENT-READINESS-2026-07-10.md`
- Branch basis: `main@177cb85a`
- Marker movement: none
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Why This Slice Exists

The frozen chat-style synthesis packet-generation contract names the next honest same-lane step as first-implementation admission. This receipt admits only the smallest safe implementation slice for a future read-only Cortex helper that turns governed ATLAS, Playbook, and Cortex read models into advisory decision context and one bounded Codex handoff.

It belongs to `Cortex Dual-Mode Replacement Readiness` because the lane is explicitly replacing external ChatGPT-style synthesis and Codex-style execution scaffolding with internal Cortex surfaces over time. This slice covers the synthesis side only.

## Synthesis, Not Execution

The future helper must synthesize decision packets. It must not execute the handoff, stage files, commit, push, deploy, dispatch workflows, call platform mutation surfaces, change markers, or write final authoritative receipts.

This is not a generic ChatGPT clone. It is a deterministic, evidence-aware ATLAS-root helper with explicit source refs, source digests, authority denials, trust labels, and a single bounded Codex-ready handoff section.

## Admitted Source Surfaces

The future helper may read only explicit root-owned and governed inputs:

- Cortex read-model outputs under safe `tmp/atlas/**`
- Codex closeout-ingestion read-model output
- ATLAS receipts under `docs/ops/**`
- continuity manifests under `docs/memory/initiatives/**`
- marker selector, planner, and scheduler output
- ATLAS Book read-model surfaces under `docs/atlas-book/**`
- Playbook doctrine, rules, patterns, and failure modes under root-owned `docs/**`
- root validation summaries
- explicit root-owned test fixtures

## Excluded Source Surfaces

The future helper must reject or ignore:

- hidden chat history
- private chain of thought
- arbitrary conversation exports
- owner-repo source trees
- raw customer, payment, or health data
- Vercel or Supabase live data
- secrets, tokens, environment files, and `.env*`
- browser profiles
- unbounded network or API input
- deployment logs unless a later contract explicitly admits sanitized aggregates
- `.vercel`, `.playwright-mcp`, `archive`, and `repos/**` paths by default

## Expected Synthesis Packet Structure

The generated packet should support:

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

Each option should support:

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

## Trust And Provenance Model

Every material statement must be classified as one of:

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

The helper must never present inference as verified fact. It must preserve source refs and source digests for material evidence.

## Playbook Integration

Playbook input is doctrine and decision support only. The helper may cite Playbook rules, patterns, and failure modes when they are present in admitted root-owned documents, but it must not call Playbook as a repo mutation surface and must not treat Playbook doctrine as proof that implementation landed.

## ATLAS Marker And Receipt Integration

Marker impacts in generated packets are advisory only. The helper may describe likely marker implications, but it cannot move marker percentages, emit final receipts, override selectors or manifests, or claim implementation ratchets.

Receipts remain durable ATLAS governance artifacts. A generated packet may propose a receipt path, but a later Codex execution packet must actually create and validate the receipt.

## Codex Handoff Boundary

The future helper must produce exactly one bounded Codex-ready handoff with:

- one objective
- allowed files
- forbidden files
- validation commands
- stop conditions
- authority denials
- expected output paths
- no automatic execution

The handoff is text. It does not execute itself.

## Authority Denials

The future helper cannot:

- execute a packet
- mutate files or repos except explicit output writes requested by the CLI
- stage, commit, or push
- deploy
- call Vercel or Supabase mutation surfaces
- access secrets
- dispatch workflows
- approve PRs
- change marker percentages
- emit final authoritative receipts
- override selectors or manifests
- treat ChatGPT-style prose as proof

## Exact Future Implementation Files

The frozen contract already names the implementation family. Use these exact files:

- `ops/cortex/chat_style_synthesis_packet_generator.py`
- `tests/test_cortex_chat_style_synthesis_packet_generator.py`

Do not create a parallel `chat_style_synthesis_packet_generation.py` family unless a later contract explicitly supersedes the frozen names.

## Expected Future CLI

Recommended command:

```text
python ops/cortex/chat_style_synthesis_packet_generator.py
```

Admitted options:

- `--json`
- `--source <root-relative-path>` repeatable
- `--mode strategy|architecture|decision|research|handoff`
- `--output <root-relative-json-path>`
- `--markdown-output <root-relative-markdown-path>`
- `--strict`

No network access should be required.

## Expected JSON Output

Deterministic top-level fields:

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

Status classes:

- `ok`
- `advisory_gap`
- `conflict`
- `blocker`
- `internal_error`

## Path Policy

The future helper must:

- reject absolute input paths
- reject absolute output paths
- reject owner-repo paths
- reject `.env*`, `.vercel`, `.playwright-mcp`, and `archive`
- allow safe `tmp/atlas/**` output only when explicit output flags are provided
- not write without explicit output flags
- not create runtime-latest files by default

## Required Proof Matrix

The future implementation packet must prove:

1. Valid root-owned source accepted.
2. Multiple source classes synthesized.
3. Facts and inferences remain distinct.
4. Assumptions are explicit.
5. Evidence gaps are surfaced.
6. Multiple options are compared.
7. Tradeoffs are deterministic.
8. One recommendation is produced.
9. Rejected options include reasons.
10. Playbook rules, patterns, and failure modes are surfaced.
11. Marker impacts remain advisory.
12. Codex handoff contains one bounded objective.
13. Codex handoff cannot execute itself.
14. Hidden transcript source rejected.
15. Owner-repo source rejected.
16. `.env*` source rejected.
17. Live Vercel/Supabase source rejected.
18. Absolute input path rejected.
19. Absolute output path rejected.
20. Protected output path rejected.
21. Safe `tmp/atlas/**` output accepted.
22. Deterministic JSON ordering.
23. Deterministic Markdown generation.
24. Conflict status emitted for contradictory evidence.
25. Strict mode exits nonzero on conflicts or blockers.
26. No output written without explicit flags.
27. Authority denials always emitted.
28. No marker mutation.
29. No network access.
30. Existing validation remains clean.

## Exact Next Packet

Open only this next same-lane packet:

```text
Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation prompt-pack and worker handoff contract
```

## Marker Decision

No marker movement.

`Cortex Dual-Mode Replacement Readiness` remains `40%`.

Admission alone does not satisfy the `50%` implementation ratchet because no generator has landed, no proof suite has passed for implementation behavior, no worker-cluster reconciliation exists, and no marker-surface ratchet decision has adopted the threshold.

## Completion

Completion: `100%` for this first-implementation admission.

No owner repo was mutated.
No platform surface was mutated.
No hidden transcript, secret, `.env*`, deploy, workflow, Vercel, Supabase, GitHub, Discord, or browser-profile surface was touched.
No implementation file was created.
No marker moved.
