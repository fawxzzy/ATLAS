# Supabase Pro Platform Governance backup and restore posture contract freeze

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `d2c3303c2f24b017e6d04af24cda95b9ce2b017c`
- Marker movement: none

## Decision

Freeze the root-side backup and restore posture contract for the known Supabase Pro project set without mutating Supabase, owner repos, or secrets.

The next exact packet is:

```text
Supabase Pro Platform Governance backup inventory and restore-readiness first-implementation admission
```

This receipt does not enable PITR, trigger a restore, create a branch, create a log drain, apply network restrictions, configure custom domains, or move any marker.

## Why This Contract Exists

The July 9 Supabase Pro audit proved that ATLAS root now has one real platform-governance surface:

- `FawxzzyFitness` is a confirmed project with mature app-data risk
- `DiscordOS` is a confirmed project with active edge-function-backed runtime risk
- `Mazer` is a confirmed project with early-stage remote-sync data risk
- `Nat1-Games` is dependency-only until project identity is confirmed

That audit selected backup and restore posture as the smallest useful next packet because it is:

- relevant to every confirmed project
- foundational for PITR, compute, and later incident doctrine
- safe to govern from ATLAS root without touching the live platform

## In-Scope Projects

Confirmed project-bound surfaces:

| Project | Ref | Initial posture classes | Reason |
| --- | --- | --- | --- |
| `FawxzzyFitness` | `lpswxoyfniocuhljgzbc` | `daily_backup_covered`, `daily_backup_unverified`, `restore_process_unverified`, `pitr_candidate`, `pitr_not_approved`, `manual_dump_plan_needed`, `storage_restore_gap`, `custom_role_password_gap`, `operator_decision_required` | customer and payment-adjacent app data, existing direct DB operational surfaces, and no governed restore drill or backup inventory proof yet |
| `DiscordOS` | `nwexsktuuenfdegzrbut` | `daily_backup_covered`, `daily_backup_unverified`, `restore_process_unverified`, `pitr_candidate`, `pitr_not_approved`, `manual_dump_plan_needed`, `storage_restore_gap`, `custom_role_password_gap`, `operator_decision_required` | active workflow/runtime data, visible Edge Function usage, and no governed restore drill or backup inventory proof yet |
| `Mazer` | `geknvnrmktchljnyddwp` | `daily_backup_covered`, `daily_backup_unverified`, `restore_process_unverified`, `pitr_not_approved`, `manual_dump_plan_needed`, `storage_restore_gap`, `custom_role_password_gap`, `operator_decision_required` | newly admitted project with lower current production criticality but no governed restore drill, backup inventory proof, or dump plan yet |

Dependency-only surface:

| Surface | Initial posture classes | Reason |
| --- | --- | --- |
| `Nat1-Games` | `no_project_identity` | real `supabase-js` dependency exists, but the current root-owned evidence does not identify a visible project ref in the current org |

## Posture-Class Meanings

The contract freezes these class meanings:

- `daily_backup_covered`: the current Pro-plan posture should provide automatic daily backups by platform entitlement
- `daily_backup_unverified`: this lane has not yet produced project-specific backup inventory proof such as visible backup metadata or timestamps
- `restore_process_unverified`: no governed restore path, duration expectation, dependency checklist, or rehearsal proof has been recorded yet
- `pitr_candidate`: the project has enough write-frequency or recovery-window importance that PITR may be worth a later operator decision
- `pitr_not_approved`: no PITR cost or compute decision has been authorized yet
- `manual_dump_plan_needed`: ATLAS still needs one explicit logical-dump or export doctrine for operator-controlled off-platform backup confidence
- `storage_restore_gap`: Supabase database backups do not restore deleted Storage objects because they preserve metadata, not object contents
- `custom_role_password_gap`: Supabase daily backups do not preserve custom role passwords in downloadable backup files
- `operator_decision_required`: later live changes require explicit operator approval
- `no_project_identity`: dependency exists, but the project cannot yet be governed as a known Supabase project

`daily_backup_covered` and `daily_backup_unverified` may coexist temporarily. The first is plan-level entitlement truth; the second is missing per-project inventory proof.

## Daily Backup Posture

The current official Supabase backup documentation checked on `2026-07-09` establishes:

- Pro projects receive automatic daily backups
- Pro projects can access the last `7` days of daily backups
- restoring from a daily backup causes project downtime
- restoring to an older backup may lose data written after that backup point

This contract therefore treats daily backups as expected platform coverage for the three confirmed projects, but not yet as proven restore readiness.

## Restore Posture

The restore posture remains unverified for every confirmed project.

Before any future restore-ready claim, later packets must collect:

1. one read-only project-specific backup inventory proof if available
2. one restore dependency checklist
3. one project-specific downtime and data-loss warning record
4. one decision on whether a non-production restore drill path exists

ATLAS root cannot claim restore readiness from entitlement alone.

## PITR Candidate Posture

The current official Supabase backup documentation checked on `2026-07-09` also establishes:

- PITR is a separate add-on for Pro, Team, and Enterprise
- PITR requires at least `Small` compute
- PITR replaces daily backups while enabled
- PITR adds separate retention-based cost

Contract consequence:

- `FawxzzyFitness` and `DiscordOS` are frozen as `pitr_candidate`
- `Mazer` is not yet treated as a current PITR candidate
- no project is approved for PITR in this packet

## Manual Logical Dump Posture

This lane freezes one additional rule: automatic daily backups do not eliminate the need for one governed logical-dump posture.

Reason:

- daily backups are platform-managed, not operator-shaped
- daily backup restore has downtime and restore-point tradeoffs
- Storage objects and custom-role passwords have known gaps

Every confirmed project therefore remains `manual_dump_plan_needed` until a later packet defines the read-only doctrine for logical dumps or equivalent operator-held exports.

## Evidence Required In Later Packets

The following evidence is required before any stronger platform claim:

1. read-only backup inventory metadata if the available connector or API can expose it safely
2. explicit confirmation of which projects use custom roles that would need password reset after restore
3. explicit Storage-object risk notes for each project
4. known direct database or pooler clients that would affect restore and network-restriction decisions
5. operator recovery-window expectations for each confirmed project
6. operator cost tolerance for any later PITR or compute upgrade decision

## Operator Decisions Required

Future operator approval is required before:

- enabling PITR
- changing compute size
- restoring any production project
- restoring any branch or alternate project using production-derived state
- creating a new restore-drill environment from live project state
- changing any backup setting or retention-affecting platform setting

## Data-Loss And Downtime Risks

Every future restore packet must explicitly restate:

- project downtime is expected during restore
- restore chooses a point before the failure and may discard later writes
- the larger the database, the longer the expected downtime
- project-side consumers may need coordination after restore if they depend on database state continuity

## Storage-Object Limitation

This contract freezes one cross-project rule:

Database backups cover Storage metadata, not Storage object contents.

Project consequence:

- `FawxzzyFitness`: any file or asset dependence must assume deleted Storage objects are not restored by database backup alone
- `DiscordOS`: any asset or attachment dependence must assume deleted Storage objects are not restored by database backup alone
- `Mazer`: any future game-sync or profile asset dependence must assume deleted Storage objects are not restored by database backup alone

## Custom-Role-Password Limitation

This contract freezes one second cross-project rule:

Daily backups do not preserve custom-role passwords in downloadable backup files.

Project consequence:

- any confirmed custom-role use must be inventoried before restore-ready claims
- any future restore drill or production restore packet must include password-reset steps for those roles after restore

## Safe Restore Drill Plan

The only currently safe restore-drill posture is design, not execution.

Any later restore drill must:

1. stay outside live production mutation unless explicitly approved
2. prefer a non-production or disposable target that does not expose production user data broadly
3. record the exact restore point, expected downtime, and rollback posture beforehand
4. record custom-role password reset requirements beforehand
5. record Storage-object limitations beforehand
6. stop if the drill would require secrets, owner-repo mutation, or production-side cutover not explicitly admitted

## Explicitly Out Of Scope

This contract does not admit:

- live backup inventory pulls that require secrets or mutation
- Management API mutation
- PITR enablement
- branch creation
- restore execution
- restore drill execution
- logical dump execution
- owner-repo changes
- deploy or Vercel changes

## Authority Denials

This lane continues to deny:

- Supabase setting mutation
- restore authority
- PITR authority
- Management API mutation authority
- secret printing or retrieval authority
- owner-repo mutation
- Fitness or Mazer fallback work
- deploy, workflow, or protected-surface authority
- marker-write authority
- final-receipt authority outside ATLAS rules

## Marker Decision

No marker moves.

No new Supabase marker is opened.

This remains root-side platform-governance doctrine only.

## Next

Open only this next packet:

```text
Supabase Pro Platform Governance backup inventory and restore-readiness first-implementation admission
```

Expected admission contents:

- admit one future read-only helper/test pair only
- keep all Supabase mutation authority denied
- freeze the smallest implementation slice for posture inventory and restore-readiness classification
- keep project identity gaps and backup inventory gaps explicit rather than narrated away
