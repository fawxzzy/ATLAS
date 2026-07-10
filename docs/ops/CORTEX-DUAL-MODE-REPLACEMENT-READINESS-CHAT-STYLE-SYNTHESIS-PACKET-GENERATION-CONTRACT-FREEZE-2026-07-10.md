# Cortex Dual-Mode Replacement Readiness Chat-Style Synthesis Packet Generation Contract Freeze

- Date: `2026-07-10`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only contract freeze`
- Scope: `freeze the bounded contract for future chat-style Cortex synthesis packet generation from durable Cortex/ATLAS memory`
- Branch basis: `main@1d4ea671`
- Marker movement: none
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`

## Goal

Freeze the first contract for a root-owned Cortex synthesis generator that can turn durable ATLAS/Cortex memory into a chat-style execution packet.

This packet is the pre-implementation boundary for the published `50%` threshold:

- `50%`: Chat-style synthesis packet generation from Cortex memory implemented

This contract does not implement the generator, run a model, mutate owner repos, move markers, deploy, touch secrets, dispatch workflows, or claim Cortex execution authority.

## Decision

Adopt this future output schema:

```text
atlas.cortex.chat_style_synthesis_packet.v1
```

The future generator must produce a deterministic advisory packet that can be read by a human operator, a Codex external adapter, or the existing synthesis-to-execution bridge contract.

The generator is not an executor. It is an evidence-bound synthesis surface.

## Required Top-Level Fields

Every generated packet must preserve this field order:

- `schema_version`
- `packet_id`
- `created_at`
- `source_interface`
- `target_interface`
- `operator_intent`
- `source_memory_refs`
- `source_receipt_refs`
- `source_profile_refs`
- `source_helper_outputs`
- `selected_marker`
- `selected_lane`
- `selected_packet`
- `packet_phase`
- `routing_mode`
- `memory_summary`
- `reasoning_summary`
- `execution_prompt`
- `bridge_packet_candidate`
- `scope_lock`
- `authority_denials`
- `allowed_surfaces`
- `forbidden_surfaces`
- `verification_plan`
- `receipt_plan`
- `risk_register`
- `stop_conditions`
- `safe_for_bridge`
- `warnings`
- `blockers`

## Admitted Inputs

The future generator may read only explicit root-owned sources:

- ATLAS receipts under `docs/ops/**`
- continuity manifests under `docs/memory/initiatives/**`
- ATLAS Book projections under `docs/atlas-book/**`
- canonical workflow profiles under `docs/memory/profiles/**`
- root-owned Cortex helper outputs under `tmp/atlas/**.json` when explicitly supplied
- root-owned helper source under `ops/cortex/**`
- root-owned tests under `tests/**`
- Playbook doctrine references under `docs/**` when cited by a manifest, receipt, or planner output

The future generator must not infer hidden state from:

- hidden transcripts
- browser tabs or screenshots
- external chat memory as canonical truth
- owner-repo worktrees except through explicit read-only advisory receipts
- Vercel, Supabase, Stripe, GitHub, or Discord live data except through explicit read-only receipts
- secrets or `.env*`
- local machine absolute paths as durable source truth

## Output Contract

The future packet must include two separate synthesis layers:

- `memory_summary`: concise durable-state summary derived only from admitted source refs.
- `reasoning_summary`: bounded explanation of why the selected packet is next, including alternatives rejected and blockers preserved.

The future packet must include one `execution_prompt` that is:

- copy-paste-ready for Codex-style execution
- limited to one selected packet
- explicit about files allowed to change
- explicit about files forbidden to touch
- explicit about verification commands
- explicit about receipt/index/manifest updates
- explicit about commit/push expectations
- explicit about stop conditions

The future packet may include one `bridge_packet_candidate` shaped for the frozen bridge schema, but it must remain advisory until a later bridge validator/generator implementation admits it.

## Scope Lock

The default scope lock for generated packets is:

- `scope=root-only`
- `one_packet_only=true`
- `owner_repo_mutation_allowed=false`
- `platform_mutation_allowed=false`
- `secret_access_allowed=false`
- `deploy_allowed=false`
- `workflow_dispatch_allowed=false`
- `marker_movement_allowed=false`
- `final_receipt_authority=false`

Any generated packet that requests a wider permission must set `safe_for_bridge=false` unless a source receipt explicitly grants that permission.

## Authority Denials

Every generated packet must deny:

- `owner-repo-mutation`
- `platform-mutation`
- `deploy`
- `secret-handling`
- `workflow-dispatch`
- `hidden-transcript-ingestion`
- `final-receipt-authority`
- `marker-movement-authority`
- `unbounded-agent-routing`

An omitted denial is a blocker.

## Determinism Rules

The future generator must:

- sort source references deterministically unless source order is part of the input contract
- emit stable packet IDs for identical inputs
- reject absolute output paths
- reject parent traversal paths
- write only to explicitly requested `tmp/**.json` output paths
- preserve the top-level field order
- preserve exact source refs in the output
- distinguish generated synthesis from verified proof
- fail closed when required source refs are missing

## Failure-Closed Conditions

The future generator must set `safe_for_bridge=false` when:

- the selected packet is missing
- source memory refs are absent
- source receipts are missing
- root validation has critical or error findings outside an admitted cleanup packet
- branch/parity is unsafe
- the packet mixes multiple lanes
- the packet touches owner repos without an explicit owner-lane packet
- the packet touches secrets, deploy, workflows, Vercel, Supabase, Stripe, GitHub, or Discord without explicit authority
- the packet claims marker movement without a separate marker-surface ratchet decision
- the packet claims final receipt authority
- hidden transcript or chat session state is treated as canonical truth

## First Implementation Admission

The next implementation admission may touch only:

- `ops/cortex/chat_style_synthesis_packet_generator.py`
- `tests/test_cortex_chat_style_synthesis_packet_generator.py`

It may optionally use existing read-only helpers as inputs, but it must not modify them in the first implementation slice:

- `ops/cortex/codex_closeout_ingestion_read_model.py`
- `ops/atlas/marker_aware_next_packet_planner.py`
- `ops/atlas/continuity_manifest_health.py`

## Required Proof For Implementation

The first implementation slice must prove:

- deterministic schema output
- text and JSON source-memory handling
- explicit source-ref preservation
- missing-source failure behavior
- path guard behavior
- authority-denial preservation
- one-packet-only enforcement
- owner-repo denial behavior
- deploy/secret/workflow/platform denial behavior
- bridge-candidate output stays advisory
- strict-mode behavior
- safe output writes only under explicit `tmp/**.json`

Required verification commands for the implementation packet:

- `python -m unittest tests.test_cortex_chat_style_synthesis_packet_generator -v`
- `python ops/cortex/chat_style_synthesis_packet_generator.py --json --schema-only`
- `python ops/validation/validate_stack.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/marker_aware_next_packet_planner.py --json`

## Marker Decision

No marker moves in this packet.

`Cortex Dual-Mode Replacement Readiness` remains `40%`.

Reason:

- this packet freezes the future chat-style synthesis packet-generation contract
- it does not implement a generator
- it does not produce a proof-backed generated packet
- it does not reconcile a worker cluster
- it does not adopt the `50%` threshold through a marker-surface ratchet decision

## Exact Next Packet

Open only this next same-lane packet:

```text
Cortex Dual-Mode Replacement Readiness chat-style synthesis packet generation first-implementation admission
```

That packet should admit the exact implementation files, proof matrix, and worker boundary for the future generator without widening into execution, owner repos, platform mutation, hidden transcript ingestion, secrets, deploys, workflows, marker movement, or final receipt authority.

## Completion

Completion: `100%` for this contract freeze.

No owner repo was mutated.
No platform surface was mutated.
No hidden transcript, secret, `.env*`, deploy, workflow, Vercel, Supabase, Stripe, GitHub, or Discord surface was touched.
No marker moved.
