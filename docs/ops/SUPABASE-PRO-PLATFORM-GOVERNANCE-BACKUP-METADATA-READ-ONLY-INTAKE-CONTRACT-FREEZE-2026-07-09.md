# Supabase Pro Platform Governance backup metadata read-only intake contract freeze

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `072cd5a10467533369219b58031bee7d9d9f45fd`
- Marker movement: none

## Decision

Freeze one bounded read-only backup metadata intake contract for the currently confirmed Supabase Pro project set.

The next exact packet is:

```text
Supabase Pro Platform Governance backup metadata read-only intake first-implementation admission
```

This packet does not call Supabase, handle access tokens, download backups, restore projects, enable PITR, change backup schedules, or move any marker.

## Why This Contract Exists

The landed root-owned posture helper now makes the current backup posture machine-readable, but its strongest remaining evidence gap is still the same for all confirmed projects:

- `daily_backup_unverified`

The next smallest useful slice is therefore not restore execution or PITR planning. It is one contract that says exactly what backup metadata may be collected, from which officially documented source, and under which ATLAS-root safety boundary.

## In-Scope Projects

Confirmed project-bound surfaces for this intake contract:

| Project | Ref | Intake status |
| --- | --- | --- |
| `FawxzzyFitness` | `lpswxoyfniocuhljgzbc` | in scope once read-only metadata is exported safely |
| `DiscordOS` | `nwexsktuuenfdegzrbut` | in scope once read-only metadata is exported safely |
| `Mazer` | `geknvnrmktchljnyddwp` | in scope once read-only metadata is exported safely |

Dependency-only surface:

| Surface | Intake status | Reason |
| --- | --- | --- |
| `Nat1-Games` | out of scope | no confirmed project identity is governed at ATLAS root yet |

## Official Source Boundary

The current Supabase documentation checked on `2026-07-09` establishes two relevant official read surfaces:

- the Dashboard `Database > Backups` surface for human inspection
- the Management API `GET /v1/projects/{ref}/database/backups`

The current Management API reference also documents these read constraints for the backups endpoint:

- OAuth scope: `database:read`
- fine-grained permission: `backups_read`

The documented response example includes:

- `region`
- `walg_enabled`
- `pitr_enabled`
- `backups`
- `physical_backup_data`

The documented backup item example includes:

- `id`
- `is_physical_backup`
- `status`
- `inserted_at`

The documented `physical_backup_data` example includes:

- `earliest_physical_backup_date_unix`
- `latest_physical_backup_date_unix`

## Enterprise-Only Schedule Boundary

The Management API reference also documents `GET /v1/projects/{ref}/database/backups/schedule`, but it is explicitly Enterprise-only.

Contract consequence:

- backup schedule reads are out of scope for this Pro-plan governance packet
- schedule mutation is also out of scope
- the current intake contract concerns inventory metadata only, not backup window control

## Root-Safe Intake Artifact

This lane freezes one root-safe collection boundary:

Future machine-readable backup metadata intake must consume an operator-exported wrapper JSON artifact, not a live token-handling helper.

The artifact location is:

```text
tmp/atlas/supabase-backup-metadata/<project-ref>.json
```

The wrapper schema version is:

```text
atlas.supabase.backup-management-export.v1
```

The wrapper must contain:

- `schema_version`
- `captured_at`
- `project_ref`
- `source`
- `payload`

`source` is frozen to:

```text
management_api.v1.projects.database.backups
```

`payload` is the exported response body from `GET /v1/projects/{ref}/database/backups` without request headers, tokens, cookies, or surrounding shell transcript.

## Admitted Metadata Fields

The future intake surface may read or summarize only these documented payload fields:

- `region`
- `walg_enabled`
- `pitr_enabled`
- `backups[].id`
- `backups[].is_physical_backup`
- `backups[].status`
- `backups[].inserted_at`
- `physical_backup_data.earliest_physical_backup_date_unix`
- `physical_backup_data.latest_physical_backup_date_unix`

Allowed derived summary fields are:

- `backup_count`
- `latest_backup_id`
- `latest_backup_status`
- `latest_backup_inserted_at`
- `latest_backup_is_physical`

The intake surface must not invent:

- download URLs
- restore-point guarantees beyond the documented timestamps
- retention beyond what the docs already state
- project identity for unnamed dependencies

## Required Safety Boundary

The future intake surface must:

- stay read-only
- read only root-relative `tmp/**.json` capture files
- reject absolute paths, parent traversal, and protected surfaces
- reject any capture wrapper that does not name one of the currently confirmed project refs
- reject duplicate captures for the same project in one run
- keep missing-project capture gaps explicit
- avoid any claim that metadata capture alone proves restore readiness

## Explicitly Not Admitted

This contract does not admit:

- PAT creation or storage
- OAuth token handling
- live HTTP calls from an ATLAS helper
- Dashboard scraping
- backup download execution
- restore execution
- PITR enablement
- backup schedule reads or writes
- owner-repo mutation
- Vercel, workflow, or secret-surface changes

## Operator Decision Boundary

Future operator approval is still required before:

- issuing or using any secret-bearing Management API token in an automated path
- recording real backup metadata from a production project
- downloading a backup file
- restoring a backup
- enabling PITR
- changing compute size or backup schedule

## Marker Decision

No marker moves.

No Supabase marker is opened.

This remains root-side platform-governance work only.

## Next

Open only this next packet:

```text
Supabase Pro Platform Governance backup metadata read-only intake first-implementation admission
```

That packet must admit only:

- one root-owned helper
- one focused test file
- a read-only wrapper-validation and metadata-summary objective
- no live token handling
- no live Supabase calls
