# ATLAS UI Standards Program

## Status

This document defines the root-owned foundation for the ATLAS UI Standards Program.

- Program version: `1.0.0`
- Registry: `docs/registry/ATLAS-UI-STANDARDS-REGISTRY.v1.json`
- Registry contract: `schemas/atlas.ui.standard-registry.v1.json`
- Current state: root foundation only
- Owner-repo adoption: not implied
- Board or Discord mutation: not authorized
- Program marker: not created

The program extends the existing QA LLEL, UI observation, drift, visual-proof, Atlas Contracts, owner-boundary, and Playbook-adoption systems. It does not replace them.

## Authority

The authority chain is fact-specific:

1. The UI standard registry owns standard IDs, versions, status, lifecycle mapping, profiles, and metric definitions.
2. QA LLEL owns evidence tiers, lenses, promotion semantics, release profiles, and waiver semantics.
3. Atlas Contracts owns card, evidence, marker, board-event, receipt, and knowledge-candidate meanings.
4. Each owner repo owns its routes, components, tokens, runtime behavior, product decisions, and repo-native verification.
5. Playbook owns promoted doctrine bodies and governed skill identity.
6. The Atlas Book projects accepted truth and receipts; it is not the normative registry.
7. DiscordOS is the single board and publication writer; it cannot infer engineering proof from prose.

Root validators may observe, compare, and report owner truth. They may not become a second implementation source.

## Stable IDs And Versioning

Standards use IDs in this form:

`ATLAS-UI-<FAMILY>-<NUMBER>`

Example: `ATLAS-UI-A11Y-001`.

Rules:

- A standard ID is never reused for a different meaning.
- Each standard carries its own semantic version.
- Additive optional clarification may increment a minor version.
- A required-field, lifecycle, status-meaning, or normative-meaning change requires a major version.
- Superseded standards name their successors and remain in provenance.
- `accepted` means root governance accepts the definition. It does not mean every owner repo adopted or enforces it.
- Owner adoption requires owner-produced evidence and root-readable verification for a target revision.

## Lifecycle

The program presents a UI-specific lifecycle while preserving the existing `atlas.card-record.v2` wire contract.

| Program lifecycle | Atlas CardRecord lifecycle | Meaning |
|---|---|---|
| `unplanned` | `intake` | Candidate exists but scope, owner, and acceptance are not admitted. |
| `planned` | `planning` | Scope and intended outcome are being shaped. |
| `ready` | `ready` | Objective and acceptance are complete, dependencies are satisfied, and blockers are empty. |
| `in_progress` | `in-progress` | Bounded owner implementation is active. |
| `review` | `review` | Implementation is terminal enough for evidence and acceptance review. |
| `completed` | `completed` | Evidence satisfies the adopted profile and all linked findings have a terminal governed disposition. |
| `blocked` | `blocked` | Progress is held on an explicit blocker and resumes through a recorded prior-state transition. |

`completed` is terminal for a remediation card. Sustainment does not keep one feature card open forever. A later audit creates new finding and remediation records linked to the previous audit lineage.

## Audit Finding Contract

`atlas.ui.audit-finding.v1` records one standards gap against a frozen audit scope.

Required semantics:

- stable finding, audit, standard, owner, route, surface, component, and lens identities
- severity and state
- automated, manual, or hybrid detection
- evidence bundle, QA result, runtime, and accessibility refs
- disposition, owner, rationale, and expiry when applicable
- zero or more linked remediation IDs

Findings remain durable after remediation. `verified` means the fix has accepted evidence. `waived` and `accept-risk` remain visible debt and do not become verified closure.

## Remediation Card Contract

`atlas.ui.remediation-card.v1` specializes, but does not replace, `atlas.card-record.v2`.

It carries:

- one or more audit finding IDs
- the UI program lifecycle plus the exact mapped Atlas CardRecord
- required evidence dimensions
- the requested-change checklist
- verification state and evidence refs

The validator rejects lifecycle drift between the UI profile and CardRecord. A completed remediation requires:

- CardRecord lifecycle `completed`
- verification status `verified`
- at least one evidence bundle or QA promotion ref
- a verified timestamp
- every checklist item `passed`

## Evidence Dimensions

| Dimension | Minimum contract |
|---|---|
| Routes | Freeze applicable route and state inventory; record a result for every touched family using stable IDs. |
| Devices | Use the adopted lens set with viewport and browser lineage; preserve physical or manual proof when the release profile requires it. |
| Accessibility | Target WCAG 2.2 AA for web UI; combine automated evidence with risk-appropriate keyboard, focus, zoom or reflow, screen-reader, contrast, and manual checks. |
| Visual | Use browser or device-backed captures and deterministic baselines or expected-change assertions with digest lineage. |
| Runtime | Preserve repo-native executable truth and interaction, console, network, trace, or API evidence required by the scenario. |
| Change checklist | Record every requested edit before mutation and reconcile each item with route-aware evidence. |

WCAG 2.2 is the normative accessibility target for web UI. The W3C ARIA Authoring Practices Guide may guide applicable widget semantics and keyboard behavior, but APG is not a normative standard and is not a UI design system.

Primary references:

- `https://www.w3.org/TR/WCAG22/`
- `https://www.w3.org/WAI/ARIA/apg/about/introduction/`

Tool selection remains owner-specific. The program defines capabilities and evidence, not a universal vendor stack. An owner may use Playwright, axe, Storybook, Lighthouse, platform-native tools, or another verified toolchain if it satisfies the same contract without duplicating healthy repo tooling.

## Enforcement Tiers

### Local

Local work proves the changed scope and keeps higher-tier gaps explicit.

- repo-native verification
- changed-route and changed-component evidence
- default emulated lenses required by the adopted profile
- accessibility smoke plus manual-gap status
- requested-change checklist

Local evidence may be sufficient for iteration. It is not automatically release proof.

### CI

CI uses the existing QA LLEL entrypoint and adopted release profile.

- repo-native deterministic checks
- profile-required lens matrix
- accessibility executable report
- targeted visual assertions
- artifact bundle and evaluation
- no silent skip for affected required UI jobs

CI configuration is root or repo orchestration. It must not become a second implementation of repo-specific QA behavior.

### Release

Release uses target-revision QA LLEL promotion and release readiness.

- required evidence dimensions current for the target revision
- profile-specific freshness and trusted-origin requirements
- physical-device or valid manual certification for release-critical profiles
- no expired exception
- no relabeling of waived or missing proof as passed

Production deployment remains separately approval-gated.

## Adoption Profiles

The registry defines four profiles:

- `atlas-ui-profile-web-standard-v1`
  Browser-facing UI with the default desktop Chromium, Android Chrome, and iPhone WebKit evidence triad.
- `atlas-ui-profile-web-release-critical-v1`
  Standard web requirements plus physical-device or valid manual certification for release-critical flows.
- `atlas-ui-profile-shared-ui-v1`
  Shared component or token packages with component, accessibility, visual, contract, and consumer compatibility evidence.
- `atlas-ui-profile-nonvisual-v1`
  Explicit not-applicable classification for scopes with no governed UI. This is evidence-backed, not a silent skip.

An owner selects or revises a profile. Root does not assign an unknown owner profile by inference.

## Objective Metrics And Markers

The report's weighted score and exception penalty are not adopted.

Program metrics use integer evidence units:

- verified required controls / applicable required controls
- current route-state evidence / frozen route-state inventory
- verified or superseded findings / accepted findings in a frozen audit snapshot
- enforced gates / required gates at one profile tier
- current target-revision evidence bundles / required bundles
- absolute open legacy-debt finding count

Rules:

- Freeze the denominator before measuring.
- Unknown does not become zero or healthy.
- Root-only config does not count as owner adoption.
- A skipped or warning-only gate is not enforced.
- Accepted risk and waivers remain separate from verified closure.
- Percentages, when displayed, are derived from numerator and denominator.
- No authored estimate, weight, penalty, or subjective completion score is allowed.
- Emit `atlas.marker-evidence.v2` only after a marker and denominator are accepted.

This foundation creates metric definitions only. It moves no existing marker.

## Migration Waves

1. Root foundation: registry, contracts, profiles, metrics, validator, and candidate packets.
2. Owner baseline: applicability, profile, route, state, component, gate inventory, and frozen findings.
3. Shared foundations: semantic tokens, canonical components, accessibility foundations, and repo-native adapters.
4. Critical flows: high-value route remediation and release gates.
5. Long tail: residual route and component findings.
6. Sustain: refresh audits, evidence freshness, regression control, and reviewed knowledge promotion.

These waves extend the QA LLEL rollout. They do not replace its root governance, owner adapter, screenshot and observability, and certification phases.

## Collision And Serialization Rules

- One root writer changes registry, schema, or program doctrine in a batch.
- One writer changes a selected owner repo at a time; separate repos may run independently.
- Canonical shared components land before dependent consumer migrations.
- Owner implementation precedes root proof reconciliation.
- Execution, proof or reconciliation, and marker ratchet remain one serial cluster.
- Board mutation waits for DiscordOS single-writer application and readback.
- Atlas Book projection follows executed state.
- Playbook promotion follows repeated verified findings and KnowledgeCandidate review.
- Existing healthy repo commands are wrapped before a new generic tool is introduced.

## Atlas Book Boundary

The Atlas Book may ingest:

- the accepted program version and canonical refs
- executed root receipts
- proof-backed owner adoption state
- accepted marker evidence

It must not duplicate the registry, copy owner runtime truth, or project candidate recommendations as current state.

## Playbook Boundary

Playbook may ingest reviewed, repeated, verified failure patterns through `atlas.knowledge-candidate.v2`.

Atlas must not:

- copy the raw research report into doctrine
- enforce an unreviewed finding as a Playbook rule
- republish Playbook doctrine bodies as a second registry
- promote one-off owner implementation details

Playbook remains the doctrine owner. Atlas records source-linked adoption and conformance evidence.

## Candidate Owner Packets

Candidate packets live at:

`docs/registry/ATLAS-UI-STANDARDS-CANDIDATE-CARDS.v1.json`

Every candidate:

- embeds an exact `atlas.card-record.v2` record
- starts at program `unplanned` / CardRecord `intake`
- carries percentage `null` and an unaccepted denominator
- authorizes no board, Discord, production, data, or secret mutation
- requires owner selection before execution

Candidate coverage includes Fitness, Trove, Mazer, Socials OS, Stream, Nat1 Games, DiscordOS applicability, and later Playbook knowledge review.

## Research And Encoding Provenance

The complete research report is preserved byte-for-byte at:

`data/imports/ui-standards/deep-research-2026-07-15/deep-research-report.md`

Its SHA-256 is:

`77f882e6af10eb4094e79033769ab8d8010ba2e6d473c620ef55750340941723`

The raw source is valid UTF-8 and contains typographic punctuation plus private-use citation delimiters. It is evidence, not normative text. All new normative program artifacts use stable ASCII text and are scanned by the validator for non-ASCII characters and common mojibake fragments. The raw report is the only digest-bound exception.

## Validation

Run:

```powershell
python ops/atlas/ui_standards/validate.py --json
python -m unittest tests.test_atlas_ui_standards -v
```

The validator checks schema conformance, semantic references, lifecycle mapping, embedded CardRecord validity, fixed-denominator policy, source hashes, portable refs, and the normative ASCII guard.

## Non-Goals

This foundation does not:

- edit owner repos
- create or move live cards
- post to Discord
- deploy preview or production
- mutate GitHub, Vercel, Supabase, or secrets
- claim owner adoption
- create a program completion percentage
- replace QA LLEL, Atlas Contracts, Playbook, or owner-repo truth
