# Cortex Dual-Mode Replacement Readiness Chat-Style Synthesis Packet Generation Implementation-Readiness Closeout And Worker Routing

- Date: `2026-07-13`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only readiness`
- Current root checkpoint: `main@a801ed94`
- Scope: `close implementation readiness for the chat-style synthesis packet-generation helper and route one bounded worker`
- Scheduler packet: `Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation first-implementation worker packet 1`
- Marker movement: none
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Readiness Verdict

The durable source chain is consistent and no new blocker is found. The explicit verdict is `implementation_ready`.

This is a docs-only readiness receipt. It does not implement the helper or tests, execute a packet, move a marker, update a manifest, emit an implementation receipt, touch an owner repository, or mutate a platform.

The durable source chain is:

- `AGENTS.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/memory/initiatives/continuity-manifest-cortex-dual-mode-replacement-readiness.json`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-CONTRACT-FREEZE-2026-07-10.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-13.md`
- prior role-inventory closeout and worker-cluster reconciliation receipts for role inventory and Codex closeout ingestion

The source chain preserves evidence classes: `verified_fact`, `receipt_backed`, `manifest_backed`, `git_backed`, `validation_backed`, `reasoned_inference`, `operator_assumption`, `unverified`, `conflicted`, and `forbidden`. Synthesis must precede execution, and chat prose is not implementation proof without Git, receipt, manifest, or validation backing.

## Exact Worker Boundary

The exact worker objective is:

> Build the admitted helper and focused test so explicit governed root inputs can be synthesized into deterministic strategy, architecture, decision, research, or handoff packets with provenance, trust labels, options, tradeoffs, one recommendation, risk and evidence gaps, and exactly one bounded Codex handoff.

Only these worker files are admitted:

- `ops/cortex/chat_style_synthesis_packet_generator.py`
- `tests/test_cortex_chat_style_synthesis_packet_generator.py`

No third committed implementation path is admitted. The worker is synthesis-only; it does not execute the handoff, stage, commit, push, deploy, dispatch workflows, change markers, or write final authoritative receipts.

## Sources, Trust, And Output Boundary

Admitted sources are explicit root-relative inputs from:

- ATLAS receipts under `docs/ops/**`
- continuity manifests under `docs/memory/initiatives/**`
- ATLAS Book projections under `docs/atlas-book/**`
- canonical workflow profile surfaces under `docs/memory/profiles/**`
- root-owned doctrine and governance references under `docs/**` when explicitly supplied
- explicit root-owned helper, planner, and validation outputs under `tmp/atlas/**`
- root git metadata
- explicit root-owned test fixtures inside the admitted test file or ignored `tmp/atlas/**`

Every material statement must retain `source_refs` and `source_digests` and exactly one trust class. Inference, assumption, or conflict must never be serialized as verified fact. Contradictory evidence yields `conflict` status and `conflicted` statement classification.

Excluded or forbidden source classes are hidden transcripts, private reasoning or chain-of-thought inference, arbitrary chat exports treated as truth, owner-repo paths including `repos/**`, absolute paths, parent traversal paths, `.env*`, `secrets/**`, `.vercel`, `.playwright-mcp`, `archive`, raw browser profiles, raw customer, health, payment, or account data, live Vercel, Supabase, Discord, or GitHub input, arbitrary network or API input, and model training or fine-tuning input.

The path contract is root-relative inputs only; safe optional output only under `tmp/atlas/**`; no output without explicit flags; no absolute paths, parent traversal, owner-repo paths, protected paths, runtime-latest files, or forbidden source reads. JSON writes require `--output`; Markdown writes require `--markdown-output`; without those flags the helper is read-only and file-write silent.

## Frozen Contract

The schema is `atlas.cortex.chat_style_synthesis_packet.v1`.

The five statuses are `ok`, `advisory_gap`, `conflict`, `blocker`, and `internal_error`, with exit policy:

- `ok`: exit `0`
- `advisory_gap`: exit `0`
- `conflict`: exit `0` unless `--strict`, then nonzero
- `blocker`: exit nonzero
- `internal_error`: exit nonzero

The deterministic top-level JSON order is `schema_version`, `status`, `root`, `branch`, `head`, `mode`, `source_refs`, `source_digests`, `trust_summary`, `synthesis_packet`, `options`, `recommendation`, `evidence_gaps`, `risk_register`, `playbook_refs`, `marker_impacts`, `codex_handoff`, `authority_denials`, `warnings`, `blockers`, `safe_to_use`, `next_recommended_packet`. The synthesis packet preserves its frozen fields, including `source_refs`, `source_digests`, facts, inferences, assumptions, evidence gaps, options, tradeoffs, risks, authority boundaries, verification requirements, and `codex_handoff`.

The exact CLI is:

    python ops/cortex/chat_style_synthesis_packet_generator.py

The exact flags are `--json`, repeatable `--source <root-relative-path>`, `--mode strategy|architecture|decision|research|handoff`, `--output <root-relative-json-path>`, `--markdown-output <root-relative-markdown-path>`, `--strict`, and `--schema-only`. No other flag is admitted.

The helper emits deterministic JSON and deterministic Markdown for identical inputs. `--schema-only` emits the deterministic schema shape, does not widen read authority, and does not write without an explicit admitted output flag.

The helper emits exactly one bounded `codex_handoff`. Zero or more than one handoff is a blocker. The handoff contains one objective, exact allowed and forbidden files, verification commands, stop conditions, authority denials, expected output paths, and no automatic execution. It remains advisory text or structured output and cannot enqueue work, call Codex, mutate files outside explicit helper outputs, or claim completion.

## Authority And Native-First Denials

The worker and handoff deny repo mutation beyond the admitted helper/test pair, stage, commit, push, PR approval, deploy, platform mutation, secret access, hidden transcript scraping, private reasoning inference, unrestricted owner-repo reads, live external queries, marker movement, final authoritative receipt emission, packet execution, and any third committed path. Native-first remains frozen: do not introduce a custom SQLite queue or scheduler.

Stop and return a blocker if implementation requires a third path, hidden transcripts, private reasoning, unrestricted owner-repo reads, live external queries, secrets or environment files, platform mutation, packet execution, marker movement, a custom SQLite queue or scheduler, or model training/fine-tuning.

## Full Proof Posture

The future implementation must prove, in order:

1. At least one valid explicit governed root-owned source is accepted and its ref is preserved.
2. Multiple admitted source classes are synthesized with deterministic source ordering.
3. Verified facts remain separate from inferences.
4. Operator assumptions are explicit.
5. Evidence gaps are explicit.
6. Multiple bounded options are emitted when comparison is supported.
7. Tradeoffs are deterministic.
8. Exactly one recommendation is produced when safe.
9. Rejected options include reasons.
10. Playbook rules, patterns, and failure modes remain doctrine refs, not implementation proof.
11. Marker impacts remain advisory.
12. Exactly one bounded Codex handoff objective is emitted.
13. The handoff cannot execute itself or claim completion.
14. Hidden transcript sources are rejected or forbidden.
15. Owner-repo sources are rejected or forbidden.
16. `.env*` sources are rejected or forbidden.
17. Live Vercel, Supabase, Discord, or GitHub sources are rejected or forbidden.
18. Absolute input paths are rejected.
19. Absolute JSON output paths are rejected.
20. Protected or out-of-scope output paths are rejected.
21. Safe explicit `tmp/atlas/**` JSON output is accepted.
22. Deterministic JSON field ordering is preserved.
23. Deterministic Markdown generation is preserved.
24. Contradictory evidence yields `conflict` and `conflicted` classification.
25. `--strict` exits nonzero on `conflict` or `blocker`.
26. No JSON or Markdown file is written without an explicit output flag.
27. Authority denials are always emitted.
28. Markers, receipts, manifests, owner repos, and platforms are not mutated.
29. Admitted proofs and smokes require no network access.
30. The implementation diff and proof run do not increase stack-validation warnings or errors.

Exact proof commands are:

    python -m unittest tests.test_cortex_chat_style_synthesis_packet_generator -v
    python ops/cortex/chat_style_synthesis_packet_generator.py --json --mode strategy --source docs/memory/profiles/zachariah_workflow_profile.md --source docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md --output tmp/atlas/cortex-chat-style-synthesis-smoke.json
    python ops/cortex/chat_style_synthesis_packet_generator.py --json --mode handoff --source docs/memory/profiles/zachariah_workflow_profile.md --source docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHAT-STYLE-SYNTHESIS-PACKET-GENERATION-FIRST-IMPLEMENTATION-ADMISSION-2026-07-10.md --markdown-output tmp/atlas/cortex-chat-style-synthesis-smoke.md
    python ops/cortex/chat_style_synthesis_packet_generator.py --json --schema-only
    python ops/cortex/chat_style_synthesis_packet_generator.py --json --mode decision --source tmp/atlas/cortex-chat-style-synthesis-conflict-fixture.json --output tmp/atlas/cortex-chat-style-synthesis-conflict.json --strict
    python ops/validation/validate_stack.py
    git diff --check
    git status --short
    git diff --name-only

Validation posture for this readiness closeout is `critical=0 error=0 warning=9 info=0`.

## Routing And Marker Posture

The exact worker packet only is:

    Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation first-implementation worker packet 1

The exact post-worker packet only is:

    Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation first-implementation worker cluster reconciliation

No other worker or post-worker packet is routed. Keep `Cortex Dual-Mode Replacement Readiness` at `40%`. No marker movement occurs in this receipt. Completion: `100%` for this docs-only readiness receipt.

## Reusable Governance Findings

- `RULE - Evidence-Class Separation`: inference, assumption, and conflict must never be serialized as verified fact.
- `PATTERN - Synthesis Before Governed Execution`: Cortex produces one bounded advisory handoff; `_stack` and Codex execute under a separate authority-bearing job.
- `FAILURE MODE - Chat Prose As Truth`: conversational fluency or pasted summaries are treated as implementation evidence without Git, receipt, manifest, or validation backing.
- `RULE - Diff-Addressable Acceptance Criteria`: every criterion consumed by spec-to-diff must have literal final-diff evidence; runtime safety belongs in tests and receipts.

## Closeout

This receipt is the one admitted Markdown path for the docs-only readiness closeout. It preserves pre-existing dirt and changes no expected-unchanged path. The worker remains unimplemented and the lane remains at `40%` pending implementation-backed proof, reconciliation, and a later marker-surface ratchet decision.
