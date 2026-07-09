# Cortex Dual-Mode And Simulation Substrate Marker Admission

- Date: `2026-07-09`
- Lane: `ATLAS-root Cortex future-lane governance`
- Mode: `ATLAS-root docs-only marker admission`
- Scope: `admit two future-facing Cortex supporting markers at 0 percent, freeze their meaning, and route the next exact contract packets without implementing helpers or mutating owner/platform surfaces`
- Control-plane checkpoint: `main@73080d98`
- Marker movement:
  - admit `Cortex Dual-Mode Replacement Readiness: 0%`
  - admit `Cortex Simulation Substrate Readiness: 0%`
  - no other marker moves

## Why This Packet Exists

These two Cortex markers were already proposed in operator reasoning, but they were not durable because no ATLAS-root receipt, marker-table admission, or selector surface had adopted them yet.

That created a real drift class:

- the ideas were live
- the intended lanes were real
- but the marker board could drop them from view because they had not crossed from chat-only proposal into durable ATLAS truth

This packet closes that gap.

## Why They Were Proposed Earlier But Not Durable

They were proposed earlier because the long-term architecture direction is already clear:

- ChatGPT and Codex are current external scaffolding
- Cortex is the intended long-term internal substrate
- synthesis, execution, and simulation should become interfaces on that substrate rather than permanently separate external tools

They were not durable yet because no marker-admission receipt had:

1. named both markers explicitly
2. defined their threshold models
3. stated their non-goals and risks
4. assigned exact next packets
5. updated the root marker table and selector policy

## Strategic Reading

The strategic read is now:

- Codex represents the current execution-worker role: isolated task environments, file edits, command/test execution, and verifiable logs/results
- ChatGPT-style systems represent the current synthesis/reasoning role: packet framing, broad reasoning, tradeoff compression, and operator-facing synthesis
- Cortex should eventually absorb both of those roles as internal interfaces rather than depending on them as permanent primaries
- Showrunner/Fable suggests a second future branch beyond synthesis and execution: simulation as an interactive substrate for worlds, characters, workflows, failures, and scenario replay
- the generative-agents architecture suggests the right substrate primitives are memory, reflection, retrieval, planning, and sandboxed interaction, not just text generation

## Source Notes

This packet is grounded in:

- [Introducing Codex](https://openai.com/index/introducing-codex/)
- [Amazon-Backed Showrunner Courts Hollywood for AI Streamer: Pitch Deck](https://www.businessinsider.com/fable-amazon-funding-showrunner-platform-pitch-deck-hollywood-studios-2025-7)
- [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)

Source posture:

- the Codex source is used for the current execution-interface silhouette
- the Showrunner coverage is used for strategic product-direction evidence, not as an implementation spec
- the generative-agents paper is used for architectural substrate guidance, not as a claim that ATLAS should reproduce the paper directly

## What Fable/Showrunner Suggests Strategically

The Showrunner direction suggests that AI-native systems can become:

- world substrates
- character substrates
- scene and episode substrates
- user-steerable interactive story systems
- remixable social creation systems

That matters for ATLAS because the same substrate idea can be translated into:

- product workflow simulation
- failure-mode replay
- launch-path rehearsal
- project-specific scenario planning
- agent/world interaction surfaces for future Cortex work

## What Generative-Agent Research Suggests Architecturally

The generative-agents work suggests that believable simulation systems need more than prompting.

The important architectural cues are:

- durable memory
- retrieval over prior experience
- reflection that compresses experience into higher-level abstractions
- planning against current context
- sandboxed interaction inside a governed environment

That is directly relevant to Cortex because it implies a shared substrate can support:

- synthesis
- execution planning
- scenario simulation
- replay/evaluation

without splitting into disconnected systems.

## Why ATLAS Should Not Clone Fable

ATLAS should not try to clone Fable or Showrunner.

Reasons:

- the problem domain is different
- ATLAS needs governance-safe planning and simulation more than consumer media generation
- ATLAS needs receipt-backed, doctrine-aware, owner-boundary-safe outputs
- direct cloning would import unnecessary IP, product, and labor-risk baggage

The right move is to extract the architectural lesson:

- one substrate can expose interactive simulation interfaces

without copying the media product itself.

## Why Cortex Should Be One Substrate With Multiple Interfaces

ATLAS should not build two disconnected Cortexes.

The stronger long-term architecture is:

- one shared Cortex substrate
- one shared memory/proof/read-model base
- multiple interfaces on top

Those interfaces are currently best understood as:

- Cortex Synthesis Interface
- Cortex Execution Interface
- Cortex Simulation Interface
- Cortex Bridge

This avoids split-brain drift between:

- reasoning truth
- execution truth
- scenario truth
- memory truth

## Current Role Of ChatGPT

Right now ChatGPT-style systems are the external synthesis scaffold.

They are best used for:

- packet framing
- broad reasoning
- research synthesis
- tradeoff articulation
- operator-facing explanation

They are not the intended permanent source of truth.

## Current Role Of Codex

Right now Codex is the external execution scaffold.

It is best used for:

- bounded implementation
- file mutation
- focused test execution
- proof capture
- reconciliation work

It is not the intended permanent execution substrate either.

## Future Role Of Cortex Synthesis Interface

The future Cortex Synthesis Interface should:

- read ATLAS memory and doctrine
- synthesize next packets from durable truth
- compress receipts into bounded operator-facing decisions
- generate bridge-safe execution packets without owning deploy or marker authority by default

## Future Role Of Cortex Execution Interface

The future Cortex Execution Interface should:

- consume bounded packets from Cortex state
- route implementation against governed source surfaces
- preserve logs, proof, and receipts
- remain authority-bounded by ATLAS governance contracts

## Future Role Of Cortex Simulation Interface

The future Cortex Simulation Interface should:

- model workflows, scenarios, and failure modes
- replay project histories and hypothetical branches
- run world or agent-style scenario projections against governed substrate inputs
- stay explicitly separate from live product mutation and live user-data mutation

## Future Role Of Cortex Bridge

The Cortex Bridge should connect:

- memory
- doctrine
- synthesis
- execution
- simulation
- replay/evaluation

without allowing any one surface to silently widen authority.

## Shared Memory / Proof Substrate

ATLAS receipts, manifests, Book surfaces, and governed read models should become the shared substrate for all three future interfaces.

That means:

- receipts are execution/proof truth
- manifests are retrieval/restart truth
- the Book is operator-facing canonical read truth
- Playbook doctrine is reusable contract truth

## How Playbook Doctrine Enters Both Sides

Playbook doctrine should feed:

- synthesis-side packet generation
- execution-side bounded implementation
- simulation-side scenario governance

This keeps Cortex aligned to the same reusable contract model instead of creating one free-form reasoning system and one disconnected worker system.

## Marker 1

`Cortex Dual-Mode Replacement Readiness: 0%`

Purpose:

Track the path from external ChatGPT/Codex dependence toward internal Cortex Synthesis and Cortex Execution interfaces.

Threshold model:

- `0%`: marker admitted
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

## Marker 2

`Cortex Simulation Substrate Readiness: 0%`

Purpose:

Track Fable-inspired simulation/storyworld/agent substrate capability for ATLAS, Fitness, Mazer, DiscordOS, product workflows, failure modes, launch paths, and future interactive systems.

Threshold model:

- `0%`: marker admitted
- `10%`: Fable/Showrunner/generative-agent research contract frozen
- `20%`: simulation substrate requirements mapped to ATLAS/Playbook/Cortex
- `30%`: agent memory/reflection/planning schema frozen
- `40%`: first read-only scenario simulation helper implemented
- `50%`: simulated workflow/failure-mode replay from ATLAS receipts
- `60%`: project-specific simulation adapters selected
- `70%`: one project has a safe scenario simulator prototype
- `80%`: simulation output feeds Playbook/Cortex recommendations
- `90%`: simulation replay/evaluation loop implemented
- `100%`: simulation substrate is operational and governance-safe

## Non-Goals

- no helper implementation
- no model training
- no transcript scraping
- no owner-repo mutation
- no Vercel mutation
- no Supabase mutation
- no secret handling
- no deploy or workflow mutation
- no marker ratchet above `0%`

## Risks

- IP misuse
- low-quality synthetic output
- labor or user exploitation
- hidden authority creep
- prompt or agent workflow injection
- secret or deploy authority widening
- owner-repo mutation creep
- split-brain state divergence across synthesis, execution, and simulation layers

## Marker Decision

Admit both supporting open markers at `0%`:

- `Cortex Dual-Mode Replacement Readiness: 0%`
- `Cortex Simulation Substrate Readiness: 0%`

No marker ratchet above `0%` is justified in this packet.

## Mirror Update Posture

This packet should land with:

- one new receipt
- one marker-table update
- one receipt-index addition
- selector and selector-test updates required to recognize the new durable marker names

This packet intentionally does not update:

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- continuity manifests

Reason:

- `01-current-state.md` and `12-restart-and-handoff-guide.md` already contain unrelated dirty residue in the shared root worktree
- the current ATLAS convention does not require continuity manifests for supporting markers admitted at `0%`
- the lane can become durable through the marker table, receipt spine, and selector surfaces without adopting unrelated dirt

## Exact Next Packets

For `Cortex Dual-Mode Replacement Readiness`:

```text
Cortex Dual-Mode Replacement Readiness operating-model contract freeze
```

For `Cortex Simulation Substrate Readiness`:

```text
Cortex Simulation Substrate Readiness Fable/generative-agent research contract freeze
```

## Completion

Completion: `100%` for the marker-admission packet itself.

No owner repo was mutated.
No Vercel or Supabase surface was mutated.
No secrets or `.env*` surfaces were touched.
