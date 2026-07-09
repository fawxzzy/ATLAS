# Cortex Dual-Mode Replacement Readiness operating-mode contract freeze

- Date: `2026-07-09`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only operating-model contract freeze`
- Scope: `freeze the first durable Cortex dual-mode operating model that maps current ChatGPT/Codex scaffolding into future internal Cortex synthesis, execution, and bridge interfaces without widening authority`
- Control-plane checkpoint: `main@05107070`
- Marker movement:
  - no marker movement

## Goal

Freeze the operating model for how ATLAS should gradually replace external ChatGPT and Codex dependence with internal Cortex interfaces while preserving one shared memory, proof, and doctrine substrate.

This packet does not:

- implement helpers
- train models
- scrape hidden transcripts
- mutate owner repos
- mutate Vercel or Supabase
- touch secrets, `.env*`, deploy surfaces, workflow surfaces, or protected surfaces
- move any marker

## Why This Marker Exists

`Cortex Dual-Mode Replacement Readiness` exists because the stack already depends on two distinct external scaffolding modes:

- ChatGPT-style synthesis for framing, compression, and operator-facing reasoning
- Codex-style execution for bounded edits, tests, proof, and reconciliation

That split is productive now, but it is not the intended long-term endpoint. The durable target is one governed Cortex substrate with multiple interfaces, so the stack can preserve its own memory, doctrine, and execution contracts internally rather than outsourcing the primary operating model forever.

## Source Notes

This contract uses official OpenAI product pages as current external-scaffolding references:

- [Introducing Codex](https://openai.com/index/introducing-codex/)
- [Introducing ChatGPT agent: bridging research and action](https://openai.com/index/introducing-chatgpt-agent/)

Source posture:

- the Codex source is used only to characterize the current execution-worker silhouette
- the ChatGPT agent source is used only to characterize the current action-capable synthesis scaffold
- neither source is treated as a product requirement for Cortex

## Why ChatGPT And Codex Are Current Scaffolding, Not The Endpoint

Current external scaffolding is strong enough to build the replacement:

- Codex can work in isolated task environments, read and edit files, run commands and tests, and return verifiable evidence such as logs and test outputs
- ChatGPT can combine reasoning, browsing, terminal work, connectors, and iterative operator interaction

Those strengths are useful now because they let ATLAS keep moving while Cortex is immature.

They are still scaffolding because:

- ATLAS does not own their long-term product boundaries
- the durable truth for Zachariah's workflows should live in ATLAS memory and doctrine, not in any external product session
- using separate external primaries forever increases split-brain risk across synthesis truth, execution truth, and memory truth

## Why Cortex Must Be One Substrate, Not Two Disconnected Cortexes

ATLAS should not build one Cortex for reasoning and a separate Cortex for execution.

The stronger operating model is:

- one shared Cortex substrate
- one shared ATLAS memory and proof substrate
- one shared Playbook doctrine substrate
- multiple governed interfaces on top

This avoids divergence between:

- planning truth
- execution truth
- restart truth
- doctrine truth
- evaluation truth

## Cortex Synthesis Interface

The Cortex Synthesis Interface is the future replacement for the current ChatGPT-style planning and compression role.

It should:

- read ATLAS memory and receipts as canonical context
- synthesize bounded next packets from durable truth
- compress multiple receipts into operator-facing tradeoff summaries
- produce bridge-safe execution packets without inheriting deploy, secret, marker, or owner-truth authority

It should not:

- treat hidden transcript state as canonical memory
- mutate repos directly
- move markers without a receipt-backed contract
- bypass owner-lane separation

## Cortex Execution Interface

The Cortex Execution Interface is the future replacement for the current Codex-style implementation and proof role.

It should:

- consume bounded packets from Cortex or operator selection
- perform implementation against governed source surfaces
- run focused verification
- emit receipts, logs, and proof artifacts back into ATLAS
- remain explicitly bounded by stack governance contracts

It should not:

- self-authorize broader scopes
- mutate owner repos outside the selected packet
- treat its own output as truth without receipt adoption
- own final marker authority

## Cortex Bridge

The Cortex Bridge is the governed seam between synthesis and execution.

It should:

- translate synthesis outputs into execution-safe packet contracts
- preserve doctrine, path, and authority constraints
- attach explicit scope, mode, risks, and verification expectations
- preserve a two-way feedback loop from execution proof back into synthesis memory

It exists to prevent free-form synthesis from turning into unbounded execution and to prevent execution outputs from drifting away from doctrine.

## Shared ATLAS Memory And Proof Substrate

The operating model assumes that ATLAS remains the durable memory backbone.

Shared substrate roles:

- receipts are execution and decision truth
- manifests are restart and continuity truth
- Book surfaces are operator-facing canonical read truth
- governed read models are machine-consumable truth

This means Cortex should consume and produce ATLAS truth surfaces rather than inventing a second private memory system.

## Shared Playbook Doctrine Substrate

Playbook doctrine, patterns, and failure modes should feed both synthesis and execution.

That doctrine should govern:

- packet structure
- authority boundaries
- proof requirements
- reusable patterns
- known failure-mode handling

Without shared doctrine, Cortex would collapse into one reasoning system and one worker system with incompatible rules.

## Current ChatGPT Mapping

Current ChatGPT-style usage maps primarily to synthesis duties:

- framing goals
- reconciling ambiguity
- summarizing research
- comparing options
- drafting packet language
- helping the operator decide where to spend execution time

This packet treats broader ChatGPT action capabilities as optional scaffolding, not as the canonical long-term source of truth.

## Current Codex Mapping

Current Codex usage maps primarily to execution and proof duties:

- bounded file mutation
- test execution
- validation runs
- reconciliation against repo state
- commit and push work
- evidence-bearing closeout

This is the closest current external analogue to the future Cortex Execution Interface.

## Gradual Absorption Model

The migration should be gradual, not theatrical.

Phase shape:

1. Keep using ChatGPT and Codex as scaffolding while ATLAS captures durable contracts, receipts, and doctrine.
2. Let Cortex Synthesis consume ATLAS memory and draft bounded execution packets.
3. Let Cortex Execution consume those packets in narrow, authority-denying slices.
4. Add replay and evaluation so ATLAS can compare external scaffolding outputs to Cortex outputs.
5. Reduce dependence on external primaries only after Cortex proves it can preserve truth quality, authority boundaries, and proof quality.

## Migration Milestones

These are the dual-mode lane milestones, carried forward without claiming progress in this packet:

- `10%`: dual-mode operating model contract frozen
- `20%`: ChatGPT/Codex role inventory completed
- `30%`: synthesis-to-execution bridge schema frozen
- `40%`: Codex closeout ingestion into Cortex read model implemented
- `50%`: Chat-style synthesis packet generation from Cortex memory implemented
- `60%`: execution planner can route bounded packets from Cortex state
- `70%`: replay/evaluation harness compares Chat/Codex outputs against Cortex outputs
- `80%`: one ATLAS lane planned or executed with Cortex-assisted bridge
- `90%`: multiple lanes use the Cortex bridge safely
- `100%`: ChatGPT/Codex are optional external adapters, not required primary operators

This packet intentionally freezes only the operating model. It does not claim the `10%` milestone as landed because marker movement is explicitly out of scope here.

## Authority Boundaries

The dual-mode operating model must preserve:

- no hidden transcript scraping
- no autonomous owner-repo mutation
- no secret or deploy mutation
- no workflow dispatch widening
- no marker movement without receipt-backed adoption
- no split-brain truth between synthesis, execution, and memory surfaces

The bridge must fail closed when:

- source truth is ambiguous
- packet boundaries are missing
- owner-lane scope is mixed into root scope
- protected surfaces are requested without explicit authority

## Non-Goals

- no implementation worker
- no evaluation harness
- no role-ingestion pipeline
- no simulation design
- no owner-side adoption claim
- no marker ratchet
- no product UI or model training work

## Risks

- hidden authority creep through the bridge
- split-brain state divergence between external scaffolding and ATLAS truth
- doctrine drift between synthesis and execution contracts
- over-automation before receipts and verification are mature
- prompt-injection or connector-style contamination if future interfaces widen beyond governed local truth
- premature migration away from external scaffolding before Cortex has equivalent proof quality

## Selector And Routing Posture

The live root selector still ranks `Vercel Platform Observability Governance` earlier in generic after-current priority once the held Sandbox lane falls through.

This packet is still valid because it is treated as an operator-selected bounded root packet, not a claim that the global marker priority has changed.

Selector truth that must remain after this packet:

- global marker priority is unchanged
- the dual-mode lane's next exact packet advances from operating-model freeze to role inventory admission

## Exact Next Packet

`Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory first-implementation admission`

Why this is next:

- the operating model must exist before role inventory can be bounded cleanly
- the next honest step is to inventory current external scaffolding duties against the frozen interface model
- that inventory should stay implementation-admission scoped rather than immediately widening into automation or marker ratchets

## Mirror Update Posture

This packet should land with:

- one new receipt
- one isolated receipt-index addition
- selector and selector-test updates required to route the dual-mode lane to its next exact packet after this freeze

This packet intentionally does not update:

- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- continuity manifests

Reason:

- the marker remains at `0%`
- existing root worktree dirt still exists on shared Book surfaces
- current `0%`-marker convention still excludes new continuity manifest requirements

## Completion

Completion: `100%` for the operating-model contract freeze itself.

No owner repo was mutated.
No platform surface was mutated.
No secrets, `.env*`, deploy surfaces, or workflow files were touched.
