# AI Work Session Stability Auto-Sync Loop Root-Plus-Owner Adoption Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-04-AI-WORK-SESSION-STABILITY-ROOT-PLUS-OWNER-ADOPTION-PROMPT-PACK`
- Date: `2026-07-04`
- Mode: `docs-only root-plus-owner adoption prompt-pack and worker handoff contract`
- Scope: `freeze the future root-plus-owner adoption proof contract without implementing owner-repo work`
- Control-plane checkpoint: `main@352dfcff`
- Worker implementation: `not included`
- Owner-repo mutation: `none`
- Fitness mutation: `none`
- Mazer mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`
- Marker movement: `none`

## Objective

Freeze the implementation handoff for one future root-plus-owner adoption proof cluster that answers:

`Has the AI work-session loop been used across ATLAS root plus at least two owner repos while preserving owner-lane separation and avoiding root-owned mutation of owner repos?`

This packet does not implement that proof. It only defines what a later implementation-readiness packet may route.

## Required Adoption Shape

The future proof cluster must include:

- one ATLAS root proof surface
- at least two separately authorized owner-lane proof surfaces
- one root reconciliation receipt that reads the owner-lane outputs as evidence
- clean blocking-level root validation
- explicit no-mutation boundaries for owner repos from the root lane

Fitness and Mazer may be eligible owner lanes only if their own owner-lane packets authorize the work. They must not be mutated from an ATLAS root packet.

## Eligible Owner-Lane Candidates

Eligible owner-lane proof candidates include repos listed in `stack.yaml` and `docs/registry/STACK-REPO-INVENTORY.json` when all of these are true:

- the owner repo has a repo-local packet or receipt naming the AI work-session loop adoption proof
- the owner repo packet authorizes its own mutation or proves read-only use
- the owner repo proof is committed in that owner repo or exported through a durable, cited receipt
- the proof does not require ATLAS root to stage, commit, push, deploy, or edit that owner repo
- the proof does not require secrets, `.env*`, platform state, BrowserStack, Supabase, Vercel, or PR-body mutation by root

Fitness and Mazer remain separate owner lanes. Root may read their exported evidence only after their owner-lane packet exists.

## Root-Owned Proof Fields

The future root reconciliation must record:

- `root_head`
- `root_branch`
- `root_parity`
- `root_validation_summary`
- `selector_packet_before`
- `selector_packet_after`
- `projection_freshness_status`
- `adoption_owner_count`
- `owner_evidence_refs`
- `owner_mutation_from_root`
- `platform_mutation_from_root`
- `protected_surface_mutation`
- `marker_decision`
- `next_packet`

## Owner-Owned Proof Fields

Each owner-lane evidence ref must provide or cite:

- owner repo id
- owner branch
- owner head
- owner parity when available
- owner packet or receipt id
- proof command or workflow used
- files touched by the owner lane
- validation result or explicit validation limit
- whether the four AI work-session helpers were used
- whether root mutated the owner repo
- whether platform state was mutated
- whether protected surfaces or secrets were touched

Owner evidence is advisory until a later root reconciliation reads and classifies it.

## Helper Participation

The future adoption proof must show how each landed helper participates:

- `ops/atlas/ai_work_session_preflight.py`: establishes safe start/continue posture before root or owner-lane work.
- `ops/atlas/ai_work_session_closeout.py`: records exact stop state, blockers, next action, and no-duplicate-package guard.
- `ops/atlas/projection_freshness.py`: verifies projected root truth does not falsely claim owner proof or protected readiness.
- `ops/atlas/playbook_adoption_matrix.py`: distinguishes documented doctrine, referenced doctrine, consumed doctrine, enforced doctrine, owner-lane advisory evidence, and Cortex-substrate candidates.

The future proof may not count owner adoption if these helpers are merely mentioned but not used or cited by the owner-lane proof.

## Allowed Read-Only Root Checks

The later implementation-readiness or worker packet may read:

- root git branch, HEAD, parity, staged names, unstaged names, and untracked names
- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- ATLAS Book current-state, marker, receipt-index, system-map, restart, and vision surfaces
- continuity manifests under `docs/memory/initiatives/`
- latest stack validation receipts under `runtime/receipts/validation/`
- marker selector output
- projection freshness output
- Playbook adoption matrix output
- owner-lane exported receipts named explicitly by the packet

Read-only owner repo status checks are allowed only when the future packet names the owner repo and states the check is advisory.

## Forbidden Behavior

The future proof cluster may not:

- mutate Fitness from ATLAS root
- mutate Mazer from ATLAS root
- mutate any owner repo from ATLAS root
- treat owner-lane dirt as root-owned proof
- treat dry-run CI as protected proof
- mutate Supabase, Vercel, BrowserStack, GitHub secrets, deploys, or PR bodies from this lane
- stage, commit, push, merge, fetch, or change branches in owner repos from root
- clean runtime residue
- touch `archive/`, `.playwright-mcp/`, `.vercel/`, `secrets/`, `.env`, or `.env*`
- move markers without a reconciliation receipt
- claim the `85%` threshold from root-only docs or wording

## Stop Conditions

The future packet must stop without marker movement when:

- fewer than two eligible owner-lane proofs exist
- owner-lane proof is not separately authorized
- owner-lane proof is uncommitted, ambiguous, stale, or contradictory
- root validation has `critical` or `error`
- projection freshness reports a blocker
- owner evidence requires root mutation to inspect or complete
- owner proof relies on secrets or protected surfaces
- Fitness or Mazer work would be required from this ATLAS root lane
- the proof would imply protected BrowserStack readiness without a protected run or approved manual fallback
- marker movement cannot be tied to an executed, receipt-backed adoption threshold

## Proof Matrix

The future implementation or reconciliation packet must prove:

1. root preflight ran or was cited and returned no blocker
2. root closeout ran or was cited and named the next action
3. projection freshness ran or was cited and did not misclassify dry-run/protected proof
4. Playbook adoption matrix ran or was cited and separated owner-lane advisory evidence from root-owned proof
5. at least two owner-lane proof refs exist
6. each owner-lane proof ref is separately authorized
7. root did not mutate owner repos
8. root validation has no critical or error
9. owner evidence count is deterministic
10. Fitness/Mazer remain separate unless their owner-lane receipts explicitly opt in
11. no secrets or protected surfaces are touched
12. marker movement, if any, is tied to the reconciliation receipt

## Marker Decision

No marker moves from this prompt-pack.

`AI Work Session Stability & Auto-Sync Loop` remains `70%`.

Movement toward `85%` requires a later implementation-readiness packet, separately authorized owner-lane adoption proof across at least two owner repos, root-side reconciliation, clean blocking-level validation, preserved owner-lane separation, and a reconciliation receipt.

## Exact Next Package

`AI Work Session Stability & Auto-Sync Loop root-plus-owner adoption implementation-readiness closeout and worker-routing`

Why:

- the adoption family is admitted
- the root-plus-owner proof contract is now frozen
- owner-lane eligibility and proof fields are explicit
- root-owned proof fields are explicit
- stop conditions and forbidden behavior are explicit
- the next honest step is to decide whether any implementation or reconciliation worker can be routed without mutating owner repos from root

## Rule

`Owner Adoption Requires Owner-Lane Proof`

Root may reconcile owner evidence, but root may not manufacture it. Fitness, Mazer, and any other owner repo count only through their own separately authorized owner-lane packets.

## Pattern

admission -> prompt-pack and worker handoff contract -> implementation-readiness closeout and worker-routing -> separately authorized owner-lane proof -> root reconciliation receipt and marker decision

## Failure Mode

`Root-Owned Owner Proof Inflation`

The lane fails if ATLAS root treats advisory owner-repo status, stale inventory, PR-body text, dry-run CI, or repeated handoff narration as proof of owner adoption. Owner adoption must come from owner-lane receipts or exported proof, and root may only reconcile those proofs.
