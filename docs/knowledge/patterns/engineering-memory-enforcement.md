# Engineering Memory Enforcement

Status: accepted ATLAS-root policy; Playbook promotion remains a reviewed
candidate rather than an automatic doctrine write.

Canonical machine policy:
`docs/registry/ATLAS-ENGINEERING-MEMORY-POLICY.v1.json`.

## Rules

### Precedent Lookup Before Implementation

Before implementing a change, search the current repository and Atlas knowledge
surfaces for the same or similar problem. Reuse the prior solution, adapt it,
reject it with an explicit reason, or record that this is the first durable
pattern. A source edit cannot start while the lookup is pending.

### Visual Work Requires Visual Evidence

Code inspection cannot close UI work. Required routes and states need browser,
device, DOM, screenshot, or visual-diff evidence at the bound revision. Missing
evidence keeps the task `implemented`, `partial`, or `blocked`; it does not
become `verified` through prose.

### Do Not Fragment Task State

Every active item maps to one stable `atlas.card-record.v2` identity and one
correlated `atlas.job-envelope.v2`. Checklists and incidental lists are views of
that task, not independent sources of truth.

## Patterns

### Shared Semantic Control

When multiple screens or states expose the same product control—Settings,
Pause, Account, Save, Start—prefer a shared component or shared style/token
contract. If the variant is intentional, document it and prove it. For parity
work, identify the canonical source surface, every target surface, and the
properties that must remain shared.

### PWA Standalone Safe-Area Layout

Browser and installed standalone modes share a shell-owned viewport and
safe-area contract. Standalone mode must not reserve phantom browser-toolbar
space. Verify the same route at equivalent mobile dimensions in browser and
standalone modes; use physical-device evidence where OS/browser behavior is part
of the claim.

## Failure Modes

### Claimed Carryover Without Parity

An agent reports that a visual pattern was copied while source and target still
differ in color, shape, animation, container, spacing, or behavior. Prevent
closure until both surfaces have property-level, route-aware evidence.

### Expanding Task Erases Queue

A parent task absorbs newly discovered work until other queued items disappear.
Freeze the parent's acceptance criteria before mutation and create stable linked
child tasks for every independently verifiable discovery.

## Decision

### Atlas Is Enforcement, Not Memory Alone

Atlas does not rely on model recollection. The engineering lifecycle requires
explicit precedent lookup, application or rejection, verification, and archival
at the corresponding gates. The additive engineering-memory profile lives
inside the canonical job envelope; it does not create another queue, scheduler,
or task protocol.

## Promotion Boundary

These entries are accepted for ATLAS-root workflow enforcement. They become
Playbook doctrine only through the existing reviewed `atlas.knowledge-candidate.v2`
promotion path with provenance and owner-side adoption proof.
