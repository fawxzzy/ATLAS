# Supabase Pro Platform Governance backup metadata first operator-export capture contract freeze

- Date: `2026-07-09`
- Lane: `Supabase Pro Platform Governance`
- Mode: `ATLAS-root docs-only contract freeze`
- Control-plane checkpoint: `4b64ba9c3254cea769da92b19ab0c0ae77d96f19`
- Marker movement: none

## Decision

Freeze one bounded operator-export capture contract for the first real Supabase backup metadata evidence at ATLAS root.

The next exact packet is:

```text
Supabase Pro Platform Governance backup metadata first operator-export capture execution packet
```

This packet does not call Supabase, handle a live token, restore a project, enable PITR, mutate any Supabase setting, mutate any owner repo, or move any marker.

## Why This Contract Exists

The current Supabase platform-governance chain already landed the two root-owned read-only helper families:

- `ops/atlas/supabase_backup_restore_posture.py`
- `ops/atlas/supabase_backup_metadata_intake.py`

The remaining gap is no longer doctrine, helper design, or validation. The remaining gap is real per-project backup metadata evidence recorded safely at ATLAS root for the currently governed confirmed project set.

The smallest safe next slice is therefore one contract that freezes:

- what an operator must export
- where that export may live
- which wrapper shape the current intake helper admits
- which fields must be rejected or kept out of the wrapper
- what later proof allows the lane to progress

## In-Scope Projects

The first real operator-export capture contract applies only to these confirmed projects:

| Project | Ref | Current posture |
| --- | --- | --- |
| `FawxzzyFitness` | `lpswxoyfniocuhljgzbc` | `daily_backup_unverified`, `backup_metadata_capture_missing` |
| `DiscordOS` | `nwexsktuuenfdegzrbut` | `daily_backup_unverified`, `backup_metadata_capture_missing` |
| `Mazer` | `geknvnrmktchljnyddwp` | `daily_backup_unverified`, `backup_metadata_capture_missing` |

Out of scope:

| Surface | Current posture | Reason |
| --- | --- | --- |
| `Nat1-Games` | `no_project_identity` | dependency exists, but no governed confirmed Supabase project identity is recorded at ATLAS root yet |

## Official Source Boundary

This contract preserves the already-frozen documented source boundary:

- human inspection may use the Dashboard `Database > Backups` surface
- machine-readable metadata may come only from the documented Management API backups read path `GET /v1/projects/{ref}/database/backups`

Contract consequence:

- the operator may use a secret-bearing access token outside committed files and outside Codex memory
- ATLAS root must consume only a non-secret exported wrapper JSON
- the wrapper must not include the token, headers, cookies, or shell transcript

## Operator Export Requirement

For each in-scope project, the operator must export one wrapper JSON file that contains:

- root-level wrapper metadata
- the documented Management API backup metadata response body under `payload`
- no secret-bearing request material

The operator export is an external human-run step. The token must stay only in local shell or session memory.

The contract does not require all three project wrappers in one execution. Partial coverage is allowed, but any missing confirmed project remains explicitly missing and unverified until its own admitted wrapper is supplied.

## Admitted Wrapper Shape

The current intake helper admits this wrapper contract:

```json
{
  "schema_version": "atlas.supabase.backup-management-export.v1",
  "captured_at": "<ISO timestamp>",
  "project_ref": "<project ref>",
  "source": "management_api.v1.projects.database.backups",
  "payload": {
    "region": "<region>",
    "walg_enabled": true,
    "pitr_enabled": false,
    "backups": [
      {
        "id": 123,
        "is_physical_backup": true,
        "status": "COMPLETED",
        "inserted_at": "<ISO timestamp>"
      }
    ],
    "physical_backup_data": {
      "earliest_physical_backup_date_unix": 0,
      "latest_physical_backup_date_unix": 0
    }
  }
}
```

The wrapper must preserve the current helper contract exactly for these root-level keys:

- `schema_version`
- `captured_at`
- `project_ref`
- `source`
- `payload`

The wrapper must preserve the current admitted values:

- `schema_version = atlas.supabase.backup-management-export.v1`
- `source = management_api.v1.projects.database.backups`

## Admitted Payload Fields

This contract admits only the payload fields already frozen by the intake helper and intake contract:

- `region`
- `walg_enabled`
- `pitr_enabled`
- `backups[].id`
- `backups[].is_physical_backup`
- `backups[].status`
- `backups[].inserted_at`
- `physical_backup_data.earliest_physical_backup_date_unix`
- `physical_backup_data.latest_physical_backup_date_unix`

Allowed derived intake-summary fields remain:

- `backup_count`
- `latest_backup_id`
- `latest_backup_status`
- `latest_backup_inserted_at`
- `latest_backup_is_physical`

This contract does not prescribe undocumented API fields and does not require speculative fields such as root-level `project_name`.

## Forbidden Fields And Surfaces

The export wrapper must not include:

- access tokens
- authorization headers
- cookies
- shell transcripts
- env dumps
- restore commands
- backup download URLs
- backup file contents
- secret values
- absolute file paths
- any project ref outside the confirmed governed set

The packet must not place exports anywhere except safe root-relative `tmp/**.json`.

## Placement Rule

Admitted placement is:

```text
tmp/atlas/supabase-backup-metadata/<descriptive-file>.json
```

The helper contract remains fail-closed:

- absolute paths are rejected
- parent traversal is rejected
- protected surfaces are rejected
- non-`tmp/**.json` paths are rejected

## Secret-Leakage Prevention Rule

The operator must:

- keep the Supabase access token only in shell or session memory
- avoid pasting the token into Codex, repo files, receipts, or committed docs
- export only the wrapper JSON response artifact
- verify the wrapper contains no token, headers, or transcript before placing it under `tmp/`

ATLAS root must continue to treat the token as operator-only secret material.

## PowerShell UTF-8-With-BOM Handling

The current intake helper already accepts Windows PowerShell UTF-8-with-BOM export encoding through `utf-8-sig` decoding.

Contract consequence:

- PowerShell-exported wrapper files are admitted as long as they otherwise satisfy the wrapper contract
- BOM presence is not a blocker by itself

## Duplicate And Unknown-Ref Rejection

The current intake helper contract remains binding:

- duplicate captures for the same `project_ref` in one run are rejected
- unknown `project_ref` values are rejected
- malformed or non-object payloads are rejected
- missing required wrapper keys are rejected

This packet does not widen those rules.

## Classification Meanings

This contract freezes these operator-export classification meanings:

- `daily_backup_verified`: a confirmed project has at least one admitted backup metadata capture that validates cleanly and exposes at least one backup row or otherwise confirmed admitted backup metadata
- `daily_backup_unverified`: a confirmed project still lacks admitted project-specific backup metadata proof, even if plan-level daily backup entitlement is already expected
- `backup_metadata_capture_missing`: no admitted wrapper has been supplied yet for that confirmed project
- `backup_metadata_capture_valid`: an admitted wrapper exists for that confirmed project and the intake helper accepts it without blockers
- `backup_metadata_capture_invalid`: a wrapper was supplied for that confirmed project but the intake helper rejects it for schema, path, project-ref, duplicate, or payload-shape reasons

Current posture after this packet:

- all three confirmed projects remain `daily_backup_unverified`
- all three confirmed projects remain `backup_metadata_capture_missing`
- the existing `tmp/atlas/supabase-backup-metadata/proof-sample.json` remains synthetic helper proof only, not production capture evidence

## Proof Required For Lane Progress

The lane may progress beyond this contract only when at least one operator-exported wrapper exists that:

- lives under admitted `tmp/**.json`
- contains no secrets
- names one confirmed governed project ref
- uses the admitted wrapper schema and source values
- passes `ops/atlas/supabase_backup_metadata_intake.py` cleanly for that supplied capture set

Stronger posture claims for all confirmed projects require admitted wrappers for each confirmed project, not synthetic fixtures alone.

## Explicitly Still Out Of Scope

This packet still does not admit:

- restore execution
- PITR enablement
- Supabase setting mutation
- live token handling inside Codex or repo automation
- owner-repo mutation
- Fitness implementation work
- Mazer implementation work
- Vercel or deploy work
- secret retrieval, printing, or commit
- marker creation or marker movement

## Operator Export Example

One safe local PowerShell pattern is:

```powershell
$headers = @{ Authorization = "Bearer $env:SUPABASE_ACCESS_TOKEN" }
$projectRef = "lpswxoyfniocuhljgzbc"
$payload = Invoke-RestMethod `
  -Method Get `
  -Uri "https://api.supabase.com/v1/projects/$projectRef/database/backups" `
  -Headers $headers

$wrapper = [ordered]@{
  schema_version = "atlas.supabase.backup-management-export.v1"
  captured_at    = (Get-Date).ToUniversalTime().ToString("o")
  project_ref    = $projectRef
  source         = "management_api.v1.projects.database.backups"
  payload        = $payload
}

$wrapper | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 "tmp/atlas/supabase-backup-metadata/$projectRef.json"
```

This example is local-only and illustrative. It must not be committed with a live token, and the token must not be echoed or stored in repo files.

## Marker Decision

No marker moves.

No Supabase governance marker is opened.

This remains root-side platform-governance doctrine only.

## Next

Open only this next packet:

```text
Supabase Pro Platform Governance backup metadata first operator-export capture execution packet
```

That packet may:

- validate one or more operator-exported wrappers already placed under admitted `tmp/**.json`
- classify which confirmed projects remain missing, valid, or invalid
- keep all Supabase mutation, restore, PITR, owner-repo, deploy, secret, and marker authority denied

If no real operator-exported wrapper exists yet, that execution packet must stop at the operator action request and must not fabricate metadata.
