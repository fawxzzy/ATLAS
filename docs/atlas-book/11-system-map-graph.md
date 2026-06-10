# Current System Map / Graph

## Purpose

This chapter is the compact cross-system map for the current stack.

It shows:

- which repos exist and who owns them
- which runtime and data surfaces are live today
- which future surfaces are planned but not active
- which contracts and approval gates block the next mutations

## Repo Map

### Current canonical repo surfaces

- `ATLAS`
  - stack coordination, receipts, markers, and book truth
- `repos/_stack`
  - governed deploy authority and shared operator execution
- `repos/fawxzzy-fitness`
  - Fitness app/runtime truth
  - current Discord-hosted runtime truth
- `repos/trove`
  - Trove repo-local runtime truth
- `repos/mazer`
  - Mazer repo-local runtime truth
- `repos/foundation`
  - Foundation repo-local runtime truth
- `repos/lifeline`
  - Lifeline repo-local operator and execution truth
  - manifest/runtime/release/startup/proof surface owner
- `repos/DiscordOS`
  - canonical DiscordOS repo surface now exists locally
  - governance scaffold only
  - no migrated runtime code yet

## Runtime Map

### Current live runtime shape

- Fitness Vercel hosts:
  - Fitness app runtime
  - current Discord interaction/runtime
  - current feedback/update/moderation runtime
  - current Music Sesh runtime
- Lifeline provides:
  - local execution/operator runtime for manifest-defined apps
  - manifest validation and resolution
  - local runtime lifecycle, release, startup, and proof surfaces
- `_stack` remains the governed deploy authority
- ATLAS root does not host product runtime
- ATLAS root may host bounded continuation-classification helpers such as the guarded Codex continuation gate, but those remain control-plane receipt surfaces rather than product runtime; even its admitted live-command path stays operator-enabled, wrapper-bound, preserves the historical packaged WindowsApps blocker as a machine-readable host-runtime boundary, proves the active npm-installed Codex CLI surface is non-packaged and launchable, records the narrower `resume_requires_stdin_prompt` blocker when the bare resume command starts without prompt payload, separately freezes the help-surface truth that the broader resume family exposes `[PROMPT]` plus dash-stdin support, admits only the smaller prompt-bearing branch `codex exec resume --last <inline-prompt>` while still deferring dash-stdin prompt injection, owns the timeout boundary inside the gate itself so one hung live proof yields `resume_command_timeout` instead of an outer-shell-only failure, and now closes the root ladder for that blocker class after the timeout-boundary recheck packet lands

### Future runtime shape

- Fitness runtime stays Fitness-owned
- Discord runtime moves to DiscordOS-owned surfaces later
- Lifeline stays a narrow local execution/operator plane rather than widening into a hosted control plane
- `_stack` remains shared deploy and execution authority

## Lifeline System Role

Use [Lifeline](15-lifeline.md) for the full Book-level boundary.

Current Lifeline role:

- local execution/operator plane
- manifest plus optional Playbook export consumer
- deterministic receipt and proof emitter
- ATLAS systems lane component

Current non-goals:

- hosted control plane
- multi-node orchestrator
- generic data platform

Later work stays clearly separate:

- Vercel/service-health classification
- deploy provenance visibility
- stale-surface pressure signals
- broader ATLAS-facing health projection

## Supabase Project Map

### Current

- Fitness Supabase: `lpswxoyfniocuhljgzbc`
  - live Fitness auth/profile truth
  - verification issuance truth
  - current live Discord/Music Sesh operational tables

### Future

- DiscordOS Supabase: `nwexsktuuenfdegzrbut`
  - healthy
  - empty
  - no schema landing implemented yet
  - future home for Discord-owned runtime/workflow tables

## Vercel Project Map

### Canonical active surfaces

- `fawxzzy-fitness`
  - current live operational hotspot
  - canonical Fitness runtime truth
- `fawxzzy-trove`
  - active product surface
- `fawxzzy-mazer`
  - quieter active product surface
- `fawxzzy-foundation`
  - quieter systems/product surface

### Known stale or duplicate-pressure surfaces

No helper Vercel project remains in the active live set after the 2026-05-25 helper-surface deletion pass.

Historical note:

- the stale Spotify-era Vercel projects were deleted on 2026-05-25 after dependency clearance
- the helper projects `fitness-deploy-green-panels` and `fitness-prod-rollout-20260525` were also deleted on 2026-05-25 after a clean dependency check

## DiscordOS / Fitness Shared-Seam Map

### Current shared seams

- verification bridge
- `discord_member_links`
- member-number sync
- deploy-to-update handoff
- current Discord/Music Sesh tables inside Fitness Supabase

### Future target posture

- Fitness keeps:
  - verification issuance
  - Fitness auth/profile truth
  - Fitness release proof
- DiscordOS later owns:
  - feedback runtime
  - update draft/publication runtime
  - moderation runtime
  - Music Sesh runtime

## `_stack` Command Ownership Map

`_stack` currently owns or should later own:

- governed deploy authority
- `stack validate` validation-summary command execution for ATLAS-owned validation posture
- admitted current-snapshot and delta-baseline validation-summary evidence discipline
- receipt-ready validation-summary report contract and contradiction routing
- bounded first validation-summary implementation slice plus proof-and-receipt closeout discipline
- `stack marker checkpoint` command execution for ATLAS-owned marker posture
- admitted marker-checkpoint restart-surface and cited-receipt discipline for ATLAS-owned marker posture
- receipt-ready marker-checkpoint report contract and contradiction routing for ATLAS-owned marker posture
- admitted marker-checkpoint implementation boundary and no-execution guard for ATLAS-owned marker posture
- bounded first marker-checkpoint implementation slice plus proof-and-receipt closeout discipline for ATLAS-owned marker posture
- admitted marker-checkpoint fixture/static proof boundary for ATLAS-owned marker posture
- admitted marker-checkpoint first implementation slice and proof matrix for ATLAS-owned marker posture
- admitted marker-checkpoint first implementation prompt-pack and handoff contract for ATLAS-owned marker posture
- admitted marker-checkpoint implementation-readiness closeout and worker-routing boundary for ATLAS-owned marker posture
- validation and receipt packaging helpers
- release-prep to deploy handoff
- stale-surface audit helpers
- future Vercel health classification helper

`_stack` does not own product or Discord runtime truth.

## Playbook Doctrine Flow

Current doctrine flow:

1. repeated receipt-backed rule appears in owner workflows
2. ATLAS records the pattern and convergence consequence
3. doctrine routing classifies it
4. operator-grade doctrine hardening ratifies only the receipt-backed, boundary-safe subset
5. restart and book mirrors may restate that doctrine without redefining it
6. Playbook later owns the reusable governance framing

Playbook does not become runtime owner at any step.

## Cortex Planning-Context Flow

Current planning-context flow:

1. ATLAS and receipt surfaces record durable state
2. ownership and seam docs create planning context
3. Cortex can later consume that planning context
4. Cortex does not currently mutate runtime or govern deploys

## Receipt / Proof Flow

Canonical flow:

1. owner repo or owner lane creates proof
2. `_stack` performs governed deploy where needed
3. owner repo records release or runtime proof
4. Discord publication consumes proof only after that
5. ATLAS records the cross-repo checkpoint
6. Playbook later extracts reusable doctrine

### Blocked consequence flow

When owner proof or release-readiness evidence freshness fails:

1. the owner repo stays not release-ready
2. `_stack` governed deploy authority stays blocked
3. owner release-ledger narration may record blocked state only
4. Discord publication stays blocked
5. ATLAS root may package blocked consequence only
6. blocked-work routing returns to the owner-side evidence-refresh packet

## Continuity / Retrieval Map

Retrieval-first continuity should be reconstructed in this order:

1. ATLAS canonical retrieval surfaces
   - marker table
   - receipt index
   - restart guide
   - system map
   - endgame surface
2. owner-repo truth-owner surfaces
   - repo READMEs
   - repo-owned workflow docs
   - repo-owned verification or adoption surfaces
3. governed summary and promotion surfaces
   - promoted doctrine notes
   - lane receipts
4. non-authoritative transcript residue last

Rule:

- ATLAS owns the retrieval spine
- owner repos own repo-local truth
- chat recap is optional nuance, not restart authority

## Approval-Gated Lanes

Current approval-gated lanes:

- remote preview / unfurl verification

Historical note:

- the Fitness Supabase mutation gate chain was fully exercised and then closed by `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-FINAL-CLOSEOUT-2026-05-25.md`
- any future Fitness Supabase work must reopen as a new, narrower lane instead of treating profile/data hygiene as still generally open

## Future Split

### Fitness app lane

- product and UX
- QA/LLEL
- local/mobile proof
- Fitness profile/data hygiene when approved

### Discord work lane

- DiscordOS
- bot/runtime
- feedback/update/moderation workflows
- Music Sesh
- DiscordOS Supabase

### ATLAS systems lane

- ATLAS root
- `_stack`
- Foundation
- Lifeline
- Playbook
- Cortex planning surfaces
- markers, receipts, validation, and governance automation

## System Graph

```mermaid
flowchart LR
  ATLAS["ATLAS Root\nReceipts, markers, book, coordination"]
  STACK["_stack\nGoverned deploy authority\nOperator execution"]
  PLAYBOOK["Playbook\nDoctrine and governance"]
  CORTEX["Cortex\nPlanning-context consumer"]
  LIFELINE["Lifeline\nLocal execution/operator plane\nDeterministic receipts"]
  FITNESS_REPO["Fitness Repo\nrepos/fawxzzy-fitness"]
  FITNESS_VERCEL["Fitness Vercel\nLive app + current Discord runtime"]
  FITNESS_DB["Fitness Supabase\nlpswxoyfniocuhljgzbc"]
  DISCORDOS_REPO["DiscordOS Repo\nrepos/DiscordOS\nbootstrapped scaffold"]
  DISCORDOS_VERCEL["DiscordOS Vercel\nfuture runtime owner"]
  DISCORDOS_DB["DiscordOS Supabase\nnwexsktuuenfdegzrbut\nhealthy, empty"]
  DISCORD["Discord Surfaces\nFeedback, updates, moderation,\nMusic Sesh"]
  STALE["Historical stale/helper Vercel cleanup\nclosed on 2026-05-25"]

  FITNESS_REPO --> FITNESS_VERCEL
  FITNESS_VERCEL --> DISCORD
  FITNESS_REPO --> FITNESS_DB
  STACK --> FITNESS_VERCEL
  PLAYBOOK --> LIFELINE
  LIFELINE --> ATLAS
  FITNESS_REPO --> ATLAS
  FITNESS_VERCEL --> ATLAS
  ATLAS --> PLAYBOOK
  ATLAS --> CORTEX

  FITNESS_DB -. "verification bridge,\nmember links,\nmember-number sync,\ndeploy-update handoff" .- DISCORDOS_DB
  DISCORDOS_REPO -. "future code + runtime landing" .- DISCORDOS_VERCEL
  DISCORDOS_VERCEL -. "future cutover" .- DISCORD
  DISCORDOS_REPO -. "future schema + runtime move" .- DISCORDOS_DB

  FITNESS_VERCEL -. "helper-surface pressure" .- STALE
```

## Machine-Readable Appendix

| Lane / surface | Owner | Source of truth | Current status | Blocker | Next package |
| --- | --- | --- | --- | --- | --- |
| Fitness app lane | Fitness | `repos/fawxzzy-fitness` plus Fitness release proof | release-readiness lane now resting green on clean preserved truth | stale evidence, governed QA auth secret-lane consumption, protected-route auth consumption, seam-proof aborts, proof-run drift, the linked Supabase migration-validator crash, clean-state preservation, and the governed notes gate are now all cleared; no exact owner-side release-readiness blocker remains | none immediate inside the owner-side release-readiness family; await fresh root-bounded lane selection |
| Discord work lane | Fitness-hosted now, DiscordOS later | Fitness repo/runtime now; `repos/DiscordOS` plus ATLAS separation receipts as future target | scaffold complete, bridge-independent DiscordOS work may resume, but the old root named-port planning ladder is already consumed and live runtime migration has not started | live Fitness Discord proof still depends on external/session bridge recovery; the May 26 planning and lookup-boundary chain already consumed the old generic next-package class; higher-level authorization is still required before any transport-aware, externally-executing, schema, or runtime follow-on | `none by default at ATLAS root; reopen only on explicit new DiscordOS named scope or higher-level authorization` |
| ATLAS systems lane | ATLAS root plus `_stack` and Playbook boundaries | ATLAS docs, receipts, and canonical inventory surfaces | active governance lane most recently routes through `AI Repetition-to-Automation Pipeline`, whose first five safe families are now closed or held and whose sixth-family selection now proves no honest further named family remains at the current threshold; validation summary and delta reporting remain the first safe family but are now closed at their current threshold for this slice, marker checkpoint rendering remains the selected second safe family and is now also closed at its current threshold for this slice with one exact ATLAS-side contract freeze plus one admitted `_stack` helper home plus one bounded `_stack` command-design spine plus one bounded `_stack` evidence-admission and restart-surface discipline spine plus one bounded `_stack` report-contract and contradiction-routing spine plus one bounded `_stack` implementation-admission and no-execution-guard spine plus one bounded `_stack` fixture/static-input proof spine plus one bounded `_stack` first-implementation-slice and proof-matrix spine plus one bounded `_stack` first-implementation prompt-pack and handoff-contract spine plus one bounded `_stack` implementation-readiness closeout and exact worker-routing spine plus one reconciled first implementation worker landing and one reconciled proof-and-receipt hardening follow-on, the first family remains backed by one bounded `_stack` command-design spine plus one bounded admitted-evidence and delta-baseline discipline spine plus one bounded report-contract/contradiction-routing spine plus one bounded implementation-admission/no-execution-guard spine plus one bounded fixture/static-input proof spine plus one bounded first-implementation-slice/proof-matrix spine plus one bounded first-implementation prompt-pack and handoff-contract spine plus one bounded implementation-readiness closeout and exact worker-routing spine plus one reconciled first implementation worker landing and one reconciled proof-and-receipt hardening follow-on, and `receipt skeleton and doctrine-routing drafts` is now the selected third safe family with one exact ATLAS-side contract freeze plus one exact split owner-facing admission boundary that now separates into `receipt skeleton drafts` and `doctrine-routing drafts`, with `receipt skeleton drafts` chosen as the first exact subfamily to advance and now carrying one exact bounded subfamily contract freeze plus one exact supporting-lane admission boundary plus one exact `_stack` command-design spine plus one exact evidence-admission spine plus one exact report-contract spine plus one exact implementation-admission spine plus one exact fixture-proof boundary spine plus one exact first-implementation-slice and proof-matrix spine plus one exact first-implementation prompt-pack and handoff-contract spine plus one exact implementation-readiness closeout and worker-routing spine plus one reconciled first implementation worker landing and one reconciled proof-and-receipt hardening follow-on, one bounded root-side restart-surface reconciliation packet now aligns the derivative mirrors for that scaffold path so filled-context draft packaging is restart-safe again, one bounded post-PR-73 merge closeout packet now clears the stale merged-main narration so the route no longer points at a closed PR family, one bounded scaffold-defaults packet now removes the remaining `REPLACE_ME_OBJECTIVE` / `REPLACE_ME_SCOPE` burden from the live helper for the current lane story, one bounded verification-defaults packet now removes the remaining `REPLACE_ME_VERIFICATION` burden from the live helper for the same draft-only lane story, one bounded date-defaults packet now removes the remaining routine same-day `--date` burden from that draft-only lane story, one bounded title-defaults packet now removes the remaining routine `--title` burden from that draft-only lane story, one bounded output-path-defaults packet now removes the remaining routine persisted-output path invention from that draft-only lane story while still keeping writes explicit, one bounded live default-write adoption checkpoint now proves that one operator command on canonical `main` can emit a durable agreed-context draft receipt with no placeholder objective, scope, verification, date, title, or output-path fields, one bounded post-PR-80 merge closeout packet now clears the stale merge-judgment restart truth while refreshing the live day-of scaffold proof on merged `main`, one bounded next-capability selection packet now ranks the remaining scaffold seams and selects current-lane default resolution as the next execution slice, one bounded current-lane default packet now proves the helper can read that lane from durable restart truth when `--lane` is omitted, PR `#83` is now merged and closed on `main`, PR `#84` is now merged and closed on `main`, one bounded doctrine-routing subfamily contract-freeze packet now makes the deferred Playbook-side sibling restart-safe without implying doctrine admission or implementation authority, one bounded doctrine-routing owner-surface admission packet now admits Playbook as the exact future doctrine-facing home for that branch while ATLAS root retains truth projection and draft-only labeling, one bounded doctrine-routing supporting-lane decision packet now proves that no separate support seam honestly reopens from current truth so the third safe family closes at its current threshold, one bounded fourth-safe family selection packet now picks `release-proof to update-draft packaging helpers` as the strongest remaining safe family because the release-to-update handoff spine is already hardened while QA/LLEL proof-packet preparation remains the more proof-shape-sensitive deferred helper, one bounded fourth-family contract-freeze packet now makes that release-proof packaging seam restart-safe without implying proof creation, deploy approval, publication approval, or final update wording authority, one bounded fourth-family owner-surface admission packet now admits `_stack` as the exact helper home for that seam while keeping owner proof upstream and Discord-facing draft/publish surfaces downstream consumers only, one bounded fourth-family supporting-lane admission packet now admits `_stack Readiness` as the exact direct support lane because future helper-home work for this seam must route through one shared `_stack` command surface rather than ATLAS-only truth packaging, one bounded fourth-family command-design packet now freezes the exact `stack update draft <repo>` seam around explicit repo identity, proof reference, release-ledger reference, downstream-package outputs, fail-closed exits, and the no-proof-creation/no-publication guard, one bounded fourth-family evidence-admission packet now keeps that seam Fitness-only until broader proof-plus-ledger handoff truth exists while freezing owner proof, owner ledger, subordinate receipt-context, and fail-closed contradiction rules, one bounded fourth-family report-contract packet now freezes package-ready output, package-ready-plus-context output, receipt-context ignore-as-inadmissible behavior, and bounded failure routing without implying publication authority or implementation permission, one bounded fourth-family implementation-admission packet now freezes admitted repo-target validation, one cited owner-proof load, one cited owner-ledger load, one optional receipt-context comparison, contradiction classification, downstream-only rendering, and the explicit no-execution guard without implying execution landing, one bounded fourth-family fixture-proof packet now freezes admitted repo-target fixtures, admitted proof and ledger fixtures, admitted contradiction and receipt-context fixtures, provenance labeling, truth-limit notes, and the exact local proof ceiling without implying live owner release truth, one bounded fourth-family first-slice packet now freezes admitted repo-target validation, one cited owner-proof load, one cited owner-ledger load, one optional cited-receipt comparison, fail-closed package-basis and contradiction routing, downstream-only rendering, and the exact required proof cases without implying execution landing, one bounded fourth-family prompt-pack packet now freezes the worker objective, inherited passes 47 through 52 as frozen inputs, exact preserved payload surface, proof obligations, allowed-touch surfaces, forbidden surfaces, and stop conditions without implying execution landing, one bounded fourth-family implementation-readiness closeout packet now freezes that no control-plane prerequisite remains for the admitted first slice, the exact rule for leaving root docs-only, continuing guard boundaries, and one bounded worker-routing result without implying execution landing, one reconciled fourth-family first implementation worker landing now proves the admitted `_stack` helper can render downstream package-ready output from the real Fitness proof-plus-ledger basis without widening repo scope, owner truth, or publication authority, one reconciled fourth-family proof-and-receipt hardening follow-on now locks required-field presence, optional-field absence unless triggered, malformed-proof fail-closed handling, missing cited-receipt invalid-input handling, bounded `--receipt-context` path discipline, and proof-ledger contradiction ref discipline for that same first slice, one bounded fifth-safe family selection packet now picks `QA/LLEL proof-packet preparation` as the strongest remaining safe family because the stronger release-proof packaging seam is already fully consumed while the remaining candidate set is now narrow, one bounded fifth-family contract-freeze packet now makes that QA/LLEL proof-packet preparation seam restart-safe without implying fresh proof capture, repo-blocker bypass, release-readiness approval, or deploy/publication authority, one bounded fifth-family owner-surface admission packet now admits `Fitness owner repo local QA/LLEL proof surfaces` as the exact helper home for that seam while keeping ATLAS root at truth projection only and keeping `_stack`, Playbook, and Discord out of local-proof ownership, one bounded fifth-family supporting-lane decision packet now proves no separate ATLAS-side or shared support lane honestly reopens from that owner admission because the family remains owner-local proof preparation rather than shared execution, one bounded sixth-family selection packet now proves no honest sixth safe family remains inside the current named AI-pipeline family set because the remaining candidate classes are already consumed elsewhere, materially held, blocked, or owner-side, one bounded root lane-selection closeout packet now proves no broader ATLAS-root immediate lane is honestly open from current canonical truth either because every near-alternative already declares `no immediate packet`, `materially held`, `approval-gated`, or `owner-side only`, one bounded non-Fitness marker knockout selector surface now consumes fresh operator authorization to classify the current non-Fitness marker field, one bounded `AI Long-Run Batch Orchestration queue-or-registry contract-freeze pass 1` now lands as the first exact root-bounded packet for that family, one bounded queue-or-registry owner-surface admission packet now admits `ATLAS root control-plane surfaces` as the exact home for that pre-execution contract while still deferring queue placement, runtime state placement, `_stack` execution semantics, and Playbook doctrine ownership, one bounded queue-or-registry supporting-lane admission packet now proves no separate support lane honestly reopens because the family remains root-local contract truth rather than shared execution, storage, or doctrine semantics, one bounded first-implementation-slice selection packet now picks `batch-entry validator` as the smallest reusable implementation slice because it enforces required fields, bounded statuses, single-owner boundaries, and protected-surface exclusions before any scaffold, storage, or supervisor behavior is admitted, one bounded batch-entry validator first-slice admission packet now freezes the exact one-entry validator scope, fail-closed result vocabulary, forbidden storage and supervisor elements, and proof matrix without yet implementing code or creating queue state, one bounded batch-entry validator prompt-pack packet now freezes the worker objective, inherited passes 1 through 5 as frozen inputs, exact preserved payload surface, proof obligations, allowed-touch surfaces, forbidden surfaces, and stop conditions without yet implying storage, supervisor, or execution-home behavior, one bounded batch-entry validator implementation-readiness closeout packet now freezes that no further root-only design ambiguity remains for that admitted slice, the exact rule for leaving root docs-only, continuing guard boundaries, and one bounded worker-routing result without yet implying queue mutation, runtime-state discovery, or execution-home proof, one reconciled batch-entry validator first implementation worker cluster now proves the admitted root-local validator slice can land plus harden proof for optional-field discipline, cited-receipt failure, and multi-entry invalid-input handling without widening into queue mutation, runtime-state discovery, or supervisor behavior, one bounded next-slice selection packet now picks `draft entry scaffold renderer` as the strongest remaining post-validator slice because it improves operator authoring utility while staying storage-agnostic, single-entry, and below execution-home semantics, one bounded draft-entry scaffold contract-freeze packet now makes one exact partial proposed-entry seam restart-safe with explicit missing-field markers, single-entry scope, no inferred defaults, and no queue-home, registry-home, or execution-home semantics, one bounded draft-entry scaffold owner-surface admission packet now admits `ATLAS root control-plane surfaces` as the exact home for that partial scaffold seam because the family is still pre-storage authoring and boundary truth rather than shared execution semantics, one bounded draft-entry scaffold supporting-lane admission packet now proves no separate shared support seam honestly reopens because the family remains root-local authoring truth rather than shared helper-runtime, storage, or doctrine semantics, one bounded draft-entry scaffold first-implementation admission packet now freezes the exact one-entry scaffold renderer scope, placeholder rendering for unresolved required fields, admitted and forbidden input shapes, fail-closed output contract, and proof matrix without implying persistence, queue mutation, registry writes, or execution-home semantics, one bounded draft-entry scaffold prompt-pack and handoff-contract packet now freezes the worker objective, inherited passes 9 through 12 as frozen inputs, exact preserved payload surface, proof obligations, allowed-touch surfaces, forbidden surfaces, and stop conditions without implying persistence, queue mutation, registry writes, or execution-home behavior, one bounded draft-entry scaffold implementation-readiness closeout packet now freezes that no further root-only design ambiguity remains for that admitted slice, the exact rule for leaving root docs-only, continuing guard boundaries, and one bounded worker-routing result without implying persistence, queue mutation, registry writes, or execution-home proof, one reconciled draft-entry scaffold first-implementation worker cluster now proves the admitted root-local scaffold slice can land plus harden proof for partial-candidate placeholders, explicit proposed-status acceptance, optional-field misuse rejection, unsupported input-mode rejection, and multi-entry invalid-input handling without widening into persistence, queue mutation, registry writes, or execution-home behavior, one bounded post-scaffold next-slice selection packet now picks `scaffold-to-validator handoff` as the strongest remaining bounded seam because it converts the already-proven scaffold output plus validator input into one explicit local handoff below persistence, storage-home, status-transition, and execution-home semantics, one bounded scaffold-to-validator handoff contract-freeze packet now makes the exact ready-versus-not-ready routing seam restart-safe around scaffold payload preservation, validator-input preservation, fail-closed not-ready routing, and the no-validator-execution boundary without implying storage-home, status-transition, or execution-home behavior, one bounded scaffold-to-validator handoff owner-surface admission packet now admits `ATLAS root control-plane surfaces` as the exact home for that pre-validation handoff seam because the family remains readiness truth rather than shared execution semantics or runtime state, one bounded scaffold-to-validator handoff supporting-lane admission packet now proves no separate shared support seam honestly reopens because the family remains root-local readiness truth rather than shared helper-runtime, validator execution, storage, or doctrine semantics, one bounded scaffold-to-validator handoff first-implementation admission packet now freezes explicit scaffold-payload intake, contradiction checks, ready-versus-not-ready routing, exact payload preservation, and the proof matrix for that pre-validation seam without implying validator execution, persistence, or execution-home behavior, one bounded scaffold-to-validator handoff prompt-pack and handoff-contract packet now freezes the worker objective, inherited passes 16 through 19 as frozen inputs, exact route payload surface, exact proof obligations, allowed-touch surfaces, forbidden surfaces, and the verbatim no-execution guard without implying validator execution, persistence, or execution-home behavior, one bounded scaffold-to-validator handoff implementation-readiness closeout packet now freezes that no further root-only design ambiguity remains for that admitted slice, the exact rule for leaving root docs-only, continuing guard boundaries, and one bounded worker-routing result without implying validator execution, storage, or execution-home proof, one reconciled scaffold-to-validator handoff first-implementation worker cluster now proves the admitted root-local handoff slice can land plus harden proof for exact scaffold-payload preservation, exact candidate-entry preservation, contradictory readiness-state rejection, explicit non-`proposed` status rejection, unsupported top-level-input rejection, and multi-entry fail-closed handling without widening into validator execution, queue mutation, runtime-state discovery, or supervisor behavior, one bounded post-handoff next-slice selection packet now picks `entry status summary renderer` as the strongest remaining bounded seam because it reopens entry-set truth only as explicit local input while staying below storage-home, validator execution, status-transition, and execution-home semantics, one bounded entry-status summary renderer contract-freeze packet now makes one explicit local-input handoff-summary seam restart-safe around admitted handoff payloads, bounded row and count vocabulary, fail-closed unsupported-shape handling, and no-storage/no-execution guards, one bounded entry-status summary renderer owner-surface admission packet now admits `ATLAS root control-plane surfaces` as the exact home for that explicit local-input summary seam because the family is still pre-storage read-model truth rather than shared execution semantics or runtime state, one bounded entry-status summary renderer supporting-lane admission packet now proves no separate shared support seam honestly reopens because the family remains root-local read-model truth rather than shared helper-runtime, storage, execution, or doctrine semantics, one bounded entry-status summary renderer first-implementation admission packet now freezes explicit ordered handoff-set intake, admitted route-shape discipline, bounded row and count projection, and fail-closed unsupported-input behavior without widening into validator execution, queue mutation, runtime-state discovery, or supervisor behavior, one bounded entry-status summary renderer prompt-pack and handoff-contract packet now freezes the worker objective, inherited passes 23 through 26 as frozen inputs, exact preserved summary payload surface, exact proof obligations, allowed-touch surfaces, forbidden-touch surfaces, and the verbatim no-execution guard without widening into validator execution, queue mutation, runtime-state discovery, or supervisor behavior, one bounded entry-status summary renderer implementation-readiness closeout packet now freezes that no further root-only design ambiguity remains for that admitted slice, the exact rule for leaving root docs-only, continuing guard boundaries, and one bounded worker-routing result without widening into validator execution, queue mutation, runtime-state discovery, or supervisor behavior, one reconciled entry-status summary renderer first-implementation worker cluster now proves the admitted root-local summary slice can land plus harden proof for ordered mixed-route rendering, bounded row and count output, exact `proposed` status discipline, unsupported raw payload rejection, unsupported input-mode rejection, discovered multi-source rejection, and malformed-route fail-closed handling without widening into validator execution, queue mutation, runtime-state discovery, or supervisor behavior, one bounded post-summary next-slice selection packet now picks `scaffold persistence or queue-home selection` as the strongest remaining bounded seam because explicit local entry-set truth is now real while storage-home, lifecycle, and execution-home semantics remain deferred, one bounded scaffold persistence or queue-home selection contract-freeze packet now makes the storage-home seam restart-safe around runtime-state class, forbidden top-level home classes, deferred concrete path layout, and continued no-execution/no-lifecycle guards, one bounded scaffold persistence or queue-home selection owner-surface admission packet now admits `ATLAS root control-plane surfaces` as the exact home for that storage-home seam because the family remains path-class control-plane truth rather than runtime-store implementation or shared execution semantics, one bounded scaffold persistence or queue-home selection supporting-lane admission packet now proves no separate shared support seam honestly reopens because the family remains root-local path-class truth rather than shared helper-runtime, runtime-store implementation, storage-layout, or doctrine semantics, one bounded scaffold persistence or queue-home selection first-implementation admission packet now freezes one explicit candidate-path classifier around root-relative normalization, top-level home-class checks, admitted `runtime/` classification, forbidden root-class rejection, and continued no-write/no-layout guards, one bounded scaffold persistence or queue-home selection prompt-pack and handoff-contract packet now freezes the worker objective, inherited passes 30 through 33 as frozen inputs, exact preserved decision payload surface, exact proof obligations, allowed-touch surfaces, forbidden-touch surfaces, and the verbatim no-execution guard without widening into queue mutation, concrete runtime layout, runtime-state discovery, or execution-home behavior, and the exact next package is now `AI Long-Run Batch Orchestration queue-or-registry scaffold persistence or queue-home selection implementation-readiness closeout and worker-routing pass 35` | the verification bridge seam remains frozen as an external/session-scoped Codex-to-Chrome blocker outside this lane; root validation proof is now closed at the blocking level after the canonical `_stack` lock refresh, while validator runtime remains deterministic but still above the older `10s` local budget, unrelated Trove brand-consumer verify drift remains outside this lane, archive follow-on, Operator Secret Path Hygiene, Playbook Everywhere + Cortex Interface, Durable Context Externalization, Knowledge Capture & Transfer, Inventory & Truth Map, Truth Map & ATLAS Book, Local Data Gateway, `Unified Workflow Convergence`, the materially closed `stabilize-root-worktree` root-docs ladder, Cortex authority widening, and Atlas-owned Repo Naming Canonicalization all remain held rather than reopened; `_stack Readiness` now supports the first two admitted families plus the held receipt-skeleton subfamily and the newly admitted fourth-family release-proof packaging seam, Playbook Everywhere + Cortex Interface remains materially held rather than reopened because no new exportable family, cleared blocked family, or contract drift appeared here, and ratchet authority remains in ATLAS | `AI Long-Run Batch Orchestration queue-or-registry scaffold persistence or queue-home selection implementation-readiness closeout and worker-routing pass 35` |
| Post-convergence lane split readiness | ATLAS root | lane-split receipts plus ATLAS Book restart surfaces | open at `61%`; one compact lane-owned decisive receipt spine, one fully shaped blocker-family chain, one manifest-backed continuity map, and a shaped chain that has now passed one coherent refresh cycle as a single restart unit | no immediate docs-only blocker family remains inside the lane | no immediate docs-only follow-on packet; reopen only with a distinct restart-truth, marker, approval, or execution-surface change |
| Fitness Supabase hygiene | Fitness | Fitness Supabase plus ATLAS closeout and governance receipts | closed at `100%`; remaining Discord/Music Sesh concerns transferred out of lane scope | none inside Fitness profile-core cleanup scope | defer any Discord/Music Sesh follow-on to Discord OS Infrastructure Separation |
| DiscordOS bootstrap | DiscordOS | `repos/DiscordOS` | completed with governance scaffold only | no migrated code yet | bounded post-bootstrap implementation plan |
| Helper Vercel decommission | ATLAS systems lane with owner confirmation | Vercel inventory and deletion receipts | stale Spotify-era and helper Fitness projects deleted | provenance clarity and future health classification only | preview/unfurl verification or Vercel health-design lane |
| Lifeline local execution/operator plane | Lifeline | `repos/lifeline` plus repo-local README, architecture, operator-surface, and startup-contract docs | shipped as a narrow local-first execution plane for manifest validation/resolution, runtime lifecycle, release, startup, proof, and deterministic receipts; consumes optional Playbook exports from disk and emits ATLAS-visible consequence without becoming a hosted control plane | broader Vercel/service-health classification, deploy provenance visibility, stale-surface pressure signals, and richer ATLAS-facing health projection remain later work; `_stack` still owns governed deploy authority | start with [Lifeline](15-lifeline.md), then the Lifeline repo truth surfaces; no immediate root-only Lifeline mutation packet is opened by this Book pass |

## Non-Goals

- no repo creation
- no code movement
- no data migration
- no Vercel mutation
- no Discord runtime change
