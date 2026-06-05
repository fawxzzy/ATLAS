# Local Data Gateway Repo Naming Real-Workflow Proof Lane Selection - 2026-05-29

- Date: `2026-05-29`
- Owner: ATLAS root
- Mode: `docs-only control-plane decision`
- Scope: `first post-naming Local Data Gateway proof-lane selection`
- Source surfaces:
  - `docs/ops/LOCAL-DATA-GATEWAY-WORKFLOW-ADOPTION-EXPANSION-PASS-2-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-RENAME-MANIFEST-PROOF-ADMISSION-DECISION-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-BOUNDED-PROOF-SHAPE-REVIEW-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PROOF-FAMILY-REAL-WORKFLOW-DECISION-2026-05-28.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-REPO-NAMING-PROOF-FAMILY-REUSE-THRESHOLD-REVIEW-2026-05-28.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-NEXT-5-2026-05-29.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-PLAYBOOK-RENAME-PROOF-RECONCILIATION-PASS-1-2026-05-29.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MAZER-RENAME-PROOF-RECONCILIATION-PASS-1-2026-05-29.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `runtime/receipts/validation/stack-validation.latest.md`
- Control-plane checkpoint: `main@9bb230c`

## Objective

Decide whether the first post-naming Local Data Gateway packet can now select one exact real-workflow proof lane from root-visible evidence alone, without widening the marker or reopening any owner-side execution lane.

This pass does not:

- modify `_stack`
- write into any owner repo
- reopen repo naming execution
- imply send-capable behavior
- imply generic repo-naming workflow adoption
- move the `Local Data Gateway` marker by itself
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `9bb230c`
- status before drafting: shared root spines already carry the just-landed naming closeout chain, plus intentional untracked `archive/`
- latest validation reference: green at `critical=0 error=0 warning=478`

## Current Local Data Gateway Posture Recomputed

Current durable read before this decision:

- `Local Data Gateway: 65%`
- full no-send local chain is proven
- current `adoptable now` set remains exactly:
  - Supabase export / approval-prep packet workflows
  - Vercel dependency / deletion decision workflows
  - DiscordOS trust-boundary / provenance proof workflows
- repo naming already stood at:
  - `proof-admitted later`
  - `real-workflow proof-admitted later`
  - reuse threshold frozen and not yet met at the time of the last review

The exact open question is narrower now:

- has root-visible reality changed enough after the admitted local naming family closed to seed one honest proof-backed Local Data Gateway lane

## Root-Visible Repo-Naming Evidence Now Available

The local naming family is no longer represented by one blocked anchor instance.

It now has six exact executed-and-reconciled local instances visible from root receipts:

- `repos/fawxzzy-stream -> repos/stream`
- `repos/fawxzzy-foundation -> repos/foundation`
- `repos/fawxzzy-trove -> repos/trove`
- `repos/fawxzzy-lifeline -> repos/lifeline`
- `repos/fawxzzy-mazer -> repos/mazer`
- `repos/fawxzzy-playbook -> repos/playbook`

Root-visible family proof now includes:

- bounded rewrite and rollback planning
- bounded execution approval packets
- executed-and-reconciled proof / reconciliation packets
- one durable naming-family ratchet closing the admitted local family at `79%`
- preserved local-only and no-remote posture throughout the family

That means the old reuse-threshold blocker is no longer "missing second candidate."

It is now only "has one bounded Local Data Gateway proof lane been selected and gated honestly."

## Decision Standard

One honest seedable proof lane exists only if all of the following are true:

1. the lane can be justified from root-visible evidence only
2. the lane remains strictly local-only and no-send
3. the lane is narrower than family-wide `adoptable now`
4. the lane has one exact proof contract and acceptance gate rather than broad roadmap sprawl
5. the lane does not require hidden gateway-specific repo-naming logic to be legible

If any of those fail, the correct result is no seedable lane yet.

## Decision

Yes.

One honest seedable proof lane now exists:

- `Local Data Gateway repo naming real-workflow proof admission lane`

Equivalent bounded read:

- the family is still below `adoptable now`
- but root-visible evidence is now strong enough to admit one exact proof lane for repo naming real-workflow packets

## Why This Lane Is Honest

This lane is now honest because the root-visible repo-naming family no longer depends on hypothetical second-instance language.

It already has:

- multiple distinct candidates using the same bounded family shape
- at least one strong executed-and-reconciled class, not only blocked truth
- proof / reconciliation receipts that stay local-only
- no-send and no-remote semantics preserved across the family

That is enough to justify one exact proof-lane admission packet.

It is not enough to justify:

- family-wide operational reuse
- generic helper admission
- `adoptable now`
- marker movement

## Frozen Acceptance Criteria

The next packet may admit this lane only if it proves all of the following from root-visible evidence:

1. at least two distinct repo-naming candidates used the same minimum proof-family shape without adding new mandatory contract fields
2. the family now includes executed-and-reconciled truth under the same no-send boundary, not only blocked-before-rename truth
3. the packet can cite canonical root receipts for candidate identity, bounded execution, proof / reconciliation, and control-plane closeout
4. all remote-facing assumptions remain explicitly out of scope
5. the result stays below `adoptable now` and below marker movement unless the admitted workflow set itself widens later

## Frozen Proof Requirements

The next packet must explicitly prove:

- which exact candidate receipts count toward the lane
- that the proof-family shape stayed bounded across the multi-candidate set
- that the local naming family is closed except the preserved `fawxzzy-fitness` exception
- that the lane remains local-only, no-send, and no-remote
- that the result changes control-plane read state, not marker value

The next packet must not claim:

- generic repo-naming workflow adoption
- helper implementation need
- send-capable maturity
- GitHub-side rename authority

## Why The Marker Stays Flat

No marker move is justified in this packet.

Hold:

- `Local Data Gateway: 65% -> 65%`

Why:

- this pass selects one proof lane and freezes its gate
- it does not widen the proven `adoptable now` set
- it does not introduce a new send-authorized or reusable operational class

## Result

Current Local Data Gateway posture after this decision:

- `Local Data Gateway` remains `65%`
- one exact seedable proof lane now exists
- that lane is:
  - `repo naming real-workflow proof admission`
- the lane remains below `adoptable now`

## Exact Next Package

`Local Data Gateway repo naming real-workflow proof-lane admission pass 1`

Why:

- the seedable lane is now selected
- the acceptance criteria are now frozen
- the next honest move is to admit or reject that one bounded lane against those exact criteria instead of broadening the family again

## Rule

Control-plane packets select one honest proof lane or stop; they do not silently turn lane selection into marker movement.

## Pattern

closed adjacent family -> root-visible proof-family evidence recomputed -> one exact seedable lane selected -> acceptance criteria frozen -> one bounded admission pass next

## Failure Mode

The lane gets over-read as broader workflow adoption just because the local naming family closed cleanly.
