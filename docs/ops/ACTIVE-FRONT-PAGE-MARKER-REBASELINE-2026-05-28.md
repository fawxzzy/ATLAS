# Active Front-Page Marker Rebaseline - 2026-05-28

- Date: `2026-05-28`
- Lane: `ATLAS active front-page marker rebaseline`
- Mode: `docs-only marker rebaseline`
- Source surfaces:
  - `docs/ops/MARKER-SYSTEM-HYGIENE-PASS-2-2026-05-28.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/ops/ATLAS-OWNED-REPO-NAMING-MARKER-RATCHET-CHECKPOINT-2-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-MARKER-RATCHET-CHECKPOINT-9-2026-05-27.md`
  - `docs/ops/DURABLE-CONTEXT-EXTERNALIZATION-MARKER-RATCHET-CHECKPOINT-4-2026-05-27.md`
  - `docs/ops/DISCORD-OS-FEEDBACK-WORKFLOW-MARKER-RATCHET-CHECKPOINT-6-2026-05-27.md`
  - `docs/ops/DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`
  - `docs/ops/FULL-STACK-RESYNC-FINAL-CLOSEOUT-2026-05-27.md`
  - `docs/ops/FULL-STACK-RESYNC-CLOSEOUT-REFRESH-2026-05-27.md`
  - `docs/ops/PLAYBOOK-LIFELINE-RETAINED-RESIDUE-DISPOSAL-2026-05-25.md`
  - `docs/ops/FITNESS-BRAND-GENERATOR-ALIGNMENT-2026-05-25.md`
  - `docs/ops/OPERATOR-SECRET-PATH-HYGIENE-WARNING-DELTA-2026-05-24.md`
- Control-plane checkpoint: `main@d22d850`

## Objective

Recompute only the active front-page marker set after marker-system hygiene pass 2, and move values only where the current durable evidence changes operator reality.

This pass does not:

- mass-renumber the system
- reopen supporting markers without contradiction
- change any closed / locked ratchet
- mutate runtime, schema, env, or repo code
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `d22d850`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=310`

## Rebaselined Active Front-Page Set

Reviewed active front-page markers only:

- `_stack` Readiness: `60%`
- `Atlas-owned Repo Naming Canonicalization`: `60%`
- `Local Data Gateway`: `65%`
- `Dependency Untangling`: `70%`
- `Truth Map & ATLAS Book`: `85%`
- `Inventory & Truth Map`: `74%`
- `Knowledge Capture & Transfer`: `81%`
- `Durable Context Externalization`: `72%`
- `Discord OS Infrastructure Separation`: `95%`
- `Discord OS Feedback Workflow Canonicalization`: `72%`

## Marker Decision

No active front-page value changes.

Hold:

- `_stack` Readiness: `60%`
- `Atlas-owned Repo Naming Canonicalization: 60%`
- `Local Data Gateway: 65%`
- `Dependency Untangling: 70%`
- `Truth Map & ATLAS Book: 85%`
- `Inventory & Truth Map: 74%`
- `Knowledge Capture & Transfer: 81%`
- `Durable Context Externalization: 72%`
- `Discord OS Infrastructure Separation: 95%`
- `Discord OS Feedback Workflow Canonicalization: 72%`

## Why The Active Set Stays Flat

### Marker-system hygiene changed scan order, not lane evidence

Pass 2 changed:

- what counts as front-page
- what counts as supporting
- how cluster reads are consumed

It did not change the underlying durable evidence for the active markers themselves.

### The four recent ratchet lanes already price their latest durable evidence

Already durably ratcheted and still current:

- `Atlas-owned Repo Naming Canonicalization: 60%`
  - latest durable reasoning already includes marker admission, execution gate, dependency map, and explicit no-safe-first decision
- `Local Data Gateway: 65%`
  - latest durable reasoning already includes proven no-send full local chain plus bounded adoption inventory and proof
- `Durable Context Externalization: 72%`
  - latest durable reasoning already includes seeded manifests, refresh discipline, and first applied refresh pass
- `Discord OS Feedback Workflow Canonicalization: 72%`
  - latest durable reasoning already includes stronger proof classification while explicitly holding flat because the hardest positive proof class is still missing

### The book / truth-map lanes already have explicit latest durable holds

Explicit latest durable holds already exist for:

- `Truth Map & ATLAS Book: 85%`
  - held in `FULL-STACK-RESYNC-CLOSEOUT-REFRESH` and `FULL-STACK-RESYNC-FINAL-CLOSEOUT`
- `Inventory & Truth Map: 74%`
  - held in `FULL-STACK-RESYNC-CLOSEOUT-REFRESH` and `FULL-STACK-RESYNC-FINAL-CLOSEOUT`

### Knowledge transfer already has its latest durable increase priced in

`Knowledge Capture & Transfer` already moved to `81%` in:

- `PLAYBOOK-LIFELINE-RETAINED-RESIDUE-DISPOSAL-2026-05-25.md`

No later durable receipt changed that lane's operator reality enough to justify another move.

### DiscordOS separation remains paused at the same high-confidence boundary

`Discord OS Infrastructure Separation` remains correctly held at `95%` because:

- the contract and seam chain exists
- the live runtime still remains Fitness-owned
- no runtime/schema/data cutover has occurred

That is the same pause boundary frozen in `DISCORD-OS-INFRASTRUCTURE-SEPARATION-CHECKPOINT-2026-05-25.md`.

### `_stack` Readiness and Dependency Untangling do not yet have new direct ratchet evidence

Current adjacent progress is real, but it is already priced into other lanes:

- Local Data Gateway helper and wrapper maturity were correctly ratcheted into `Local Data Gateway`, not `_stack` Readiness
- naming-policy and Discord/continuity governance progress were correctly ratcheted into their own lanes, not `Dependency Untangling`

Without a direct readiness or untangling checkpoint, the honest rebaseline is a hold.

## Supporting-Marker Contradiction Check

Supporting markers were spot-checked only for contradiction, not reopened for fresh ratchets.

Result:

- `Preview Cache & Surface Consistency: 78%`
  - unchanged; latest explicit durable move already priced `70% -> 78%`
- `Operator Secret Path Hygiene: 60%`
  - unchanged in this pass; no newer direct lane ratchet forces a canonical-table correction here
- `Discord Workflow, Publication & Docs Reliability: 25%`
  - unchanged; no new reliability-specific ratchet has landed

## Why This Is Not Mass-Renumbering Theater

This rebaseline is intentionally conservative:

- no active marker rose because the read model got cleaner
- no active marker fell just to make the front page look sharper
- no supporting or closed marker was renumbered by association

The current active marker set is therefore a revalidated hold, not a fresh renumbering wave.

## Exact Next Package

`Atlas-owned Repo Naming bounded rewrite-order and rollback planning pass 1`

Why:

- the active marker set is now revalidated at current values
- the naming lane remains the clearest active governance blocker with an explicit next missing artifact

## Rule

Rebaseline active markers only where current durable evidence changes operator decisions.

## Failure Mode

Mass-renumber the whole system because the read model changed, even though the underlying lane evidence did not.
