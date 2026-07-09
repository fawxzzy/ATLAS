# Supabase Pro Platform Governance backup inventory and restore-readiness implementation-readiness closeout and worker routing

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only implementation-readiness closeout`
- Marker movement: none

## Objective

Close the remaining root-only readiness question for the Supabase backup posture helper and freeze the exact bounded worker-routing result.

This packet does not implement the helper. It proves that the prior control-plane chain is complete enough to route one later implementation worker without widening into owner repos, workflow authority, deploy surfaces, live Supabase mutation, or marker movement.

## Source Chain

The readiness decision rests on this durable chain:

- `docs/ops/SUPABASE-PRO-PLATFORM-CAPABILITY-ADOPTION-AUDIT-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-AND-RESTORE-POSTURE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-INVENTORY-AND-RESTORE-READINESS-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/ops/SUPABASE-PRO-PLATFORM-GOVERNANCE-BACKUP-INVENTORY-AND-RESTORE-READINESS-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md`

## Readiness Decision

The Supabase backup inventory and restore-readiness helper is `implementation_ready`.

Why:

- the audit froze the in-scope project inventory and the safe follow-up order
- the contract freeze defined the backup and restore posture classes and authority boundaries
- the first-implementation admission named the exact helper and test files
- the prompt-pack froze the worker objective, command, output schema, proof obligations, allowed inputs, forbidden surfaces, forbidden authority, and stop conditions
- the remaining gap is executed helper behavior plus tests, not root-side design ambiguity

## Exact Worker-Routing Result

The exact next worker packet is:

```text
Supabase Pro Platform Governance backup inventory and restore-readiness first-implementation worker-cluster reconciliation
```

That worker may pursue exactly one objective:

```text
Implement one bounded, read-only Supabase backup posture helper that consumes only admitted ATLAS-root receipts and stack inventory surfaces, emits deterministic advisory JSON for the known project set, preserves no-project-identity and backup-unverified gaps explicitly, denies platform mutation authority, and proves the behavior through direct unit coverage.
```

## Exact Allowed Touch Surfaces

The worker may touch only:

- `ops/atlas/supabase_backup_restore_posture.py`
- `tests/test_atlas_supabase_backup_restore_posture.py`

If an output-file option is implemented, the helper may write only to an explicitly supplied safe `tmp/**.json` path at runtime. That runtime output path is not a committed surface.

## Exact Required Helper Authority

The helper must remain read-only by default.

It may read only the admitted root-owned inputs from the prompt-pack:

- the July 9 Supabase audit receipt
- the July 9 backup-and-restore posture contract freeze
- ATLAS Book current-state, receipt-index, and restart-guide surfaces
- stack repo inventory JSON

## Exact Required Output

The helper must emit deterministic JSON with schema version:

```text
atlas.supabase_backup_restore_posture.v1
```

The output must include:

- `schema_version`
- `status`
- `safe_to_use`
- `basis_receipts`
- `project_count`
- `projects`
- `dependency_only_surfaces`
- `missing_evidence`
- `operator_decisions_required`
- `blockers`
- `warnings`

Allowed `status` values:

- `ok`
- `blocker`
- `internal_error`

## Exact Required Proof Commands

The worker must run:

1. `python -m unittest tests.test_atlas_supabase_backup_restore_posture -v`
2. `python ops/validation/validate_stack.py`
3. `python ops/atlas/supabase_backup_restore_posture.py --json`
4. `git status --short`
5. `git diff --name-only`

## Exact Forbidden Touch Surfaces

The worker must not touch:

- `repos/**`
- Fitness owner repo files
- Mazer owner repo files
- any owner repo files
- `secrets/**`
- `.env*`
- `.vercel/**`
- `.playwright-mcp/**`
- `archive/**`
- `.github/workflows/**`
- live Supabase platform state
- hidden transcript/session state

## Exact Forbidden Authority

The worker must not:

- stage, commit, or push
- mutate Supabase settings
- restore databases
- enable PITR
- create branches
- mutate owner repos
- touch Fitness or Mazer owner-lane work
- touch secrets
- deploy
- dispatch workflows
- emit final receipts
- move markers
- infer backup metadata or project identity that is not present in admitted root inputs

## Exact Stop Conditions

Stop and return without implementation if the worker would require:

- live Supabase mutation or live backup restore
- owner repo mutation
- Fitness or Mazer owner-lane work
- workflow dispatch or `.github/workflows/**` edits
- secret, `.env*`, deploy, Vercel, archive, or protected-surface touch
- hidden transcript/session scraping
- marker movement
- final receipt authority
- broad mirror edits to make the helper pass

## Exact Post-Worker Package

If the worker lands cleanly, the exact next package is:

```text
Supabase Pro Platform Governance backup inventory and restore-readiness first-implementation worker-cluster reconciliation
```

That reconciliation may add one bounded reconciliation receipt and exact Book/restart/receipt-index mirrors only after focused proof, live helper output, and stack validation pass.

## Marker Decision

No marker moves from this readiness closeout.

No Supabase marker is opened.

## Rule

When the audit, contract freeze, first-implementation admission, and prompt-pack already freeze a root-only helper's objective, files, inputs, output schema, proof matrix, and authority denials, route one bounded worker packet before adding more Supabase backup narration.

## Failure Mode

`Supabase Backup Readiness Drift`

If the lane keeps adding docs-only backup posture receipts after the prompt-pack and readiness closeout, it delays real classification proof and risks turning platform governance into wording churn instead of reusable operator tooling.
