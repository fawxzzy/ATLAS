# ADR: Canonical AI Naming and Cortex Boundary

- Status: Accepted
- Date: 2026-04-26

## Context

ATLAS needed a settled naming lane for the AI umbrella and a clear boundary between AI interpretation surfaces and owner-truth surfaces.

Existing stack language already gives `Cortex` strong gravity:

- the active runtime surface is `runtime/cortex/**`
- stack docs already use Cortex for context, observation, query, catalog, and supervisor lanes
- `Link` is available but overloaded as a generic noun and does not already own a concrete stack surface

The active rail is still Fitness owner adoption after the Configure Goal catch-up. This decision is meant to park naming churn, not to start a broad consolidation pass.

## Decision

ATLAS remains the overall control plane and operating system.

Cortex is the canonical AI umbrella inside ATLAS.

Link is reserved only for a future connector sublayer inside Cortex if a real connector surface emerges.

Use this rule when classifying ownership:

- Cortex owns AI interpretation, observation, context, and proof intelligence.
- Cortex does not own product truth, governance truth, receipt truth, or enforcement truth.

## Boundary

Cortex is read-only coordination, interpretation, observation, context, and proof intelligence.

Cortex may own or coordinate:

- semantic observation
- drift and proof intelligence
- worker context extraction
- AI summaries and context packets
- future connector mesh surfaces, if they become real, under `Cortex Link`

Cortex must not absorb owner-truth boundaries:

- governance stays Playbook
- completion enforcement stays `_stack`
- receipts and approval stay Lifeline
- product UI truth stays Fitness

Rule: Cortex owns AI interpretation and proof, not system ownership.

## Reserved Name

Do not use `Link` as the umbrella name.

`Link` is reserved for a future branded Cortex connector sublayer only if a concrete connector surface becomes real enough to justify a distinct name.

## Consequences

- The stack gets a stable umbrella name that matches current runtime and document gravity.
- Future AI-adjacent work can route under Cortex without implying ownership of product or governance truth.
- Connector branding stays optional and deferred until there is an actual connector surface to name.
- Naming is now settled enough to keep the active rail on Fitness owner adoption instead of naming debate.

## Known Cleanup

Normalize stale stack docs that still describe `repos/cortex` or `repos/fawxzzy-atlas` as active AI/platform surfaces when the active Cortex runtime surface is `runtime/cortex/**`.

This cleanup is backlog work, not an active consolidation rail.

## Failure Mode To Avoid

Renaming the umbrella to `Link` would fight existing stack language, weaken the root-owned Cortex boundary, and blur the line between AI interpretation and system ownership.

## Summary

- Canonical AI umbrella: `Cortex`
- Reserved future connector slice: `Cortex Link`
- System umbrella: `ATLAS`
- Active next rail: Fitness owner adoption, not naming consolidation implementation
