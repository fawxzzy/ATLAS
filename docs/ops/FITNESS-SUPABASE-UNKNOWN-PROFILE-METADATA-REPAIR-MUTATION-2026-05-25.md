# Fitness Supabase Unknown Profile Metadata Repair Mutation

Date: 2026-05-25  
Mode: approval-gated Supabase mutation  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Goal

Repair profile-side metadata for exactly the three approved unknown profiles from:

- `docs/ops/FITNESS-SUPABASE-UNKNOWN-PROFILE-METADATA-REPAIR-APPROVAL-2026-05-25.md`

This lane mutated only the approved profile-side metadata fields.

## Exact Mutation Class

Approved labels mutated:

- `unknown-profile-01`
- `unknown-profile-02`
- `unknown-profile-03`

Mutation class:

- profile-side metadata repair only

## Preflight Result

Final preflight immediately before write confirmed:

- the three approved labels still resolved unambiguously
- all three still mapped to live auth users
- none hit the automation heuristic
- none had app-owned dependent rows
- none appeared in Discord-linked tables
- none had direct Music Sesh references
- `show_qa_llel_data` was still `false` for all three
- target member numbers `18`, `19`, and `20` were still available
- rollback posture was present before mutation

No stop condition was hit.

## Fields Changed

The mutation changed only:

- `user_kind`
- `user_number`
- `user_number_assigned_at`

Applied mapping:

| Profile | New `user_kind` | New `user_number` | `user_number_assigned_at` |
| --- | --- | ---: | --- |
| `unknown-profile-01` | `human` | `18` | mutation timestamp because field was null |
| `unknown-profile-02` | `human` | `19` | mutation timestamp because field was null |
| `unknown-profile-03` | `human` | `20` | mutation timestamp because field was null |

## Fields Intentionally Unchanged

The mutation did **not** change:

- `show_qa_llel_data`
- auth metadata
- any unrelated profile fields

Post-mutation confirmation:

- `unknown-profile-01`: `show_qa_llel_data = false`
- `unknown-profile-02`: `show_qa_llel_data = false`
- `unknown-profile-03`: `show_qa_llel_data = false`

## Before / After Counts

| Count | Before | After |
| --- | ---: | ---: |
| unknown profiles | `3` | `0` |
| profiles | `37` | `37` |
| auth-only users | `19` | `19` |
| automation profiles | `16` | `16` |
| automation auth-unknown mismatches | `4` | `4` |

Remaining automation auth-unknown mismatches still remain only:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

## Export Artifact Paths

Committed redacted summary:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-mutation-summary.redacted.json`

Committed redacted approval/reference artifacts already in lane:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-candidates.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-proposed-rows.redacted.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-reference-scan.redacted.json`

Local-only rollback and raw snapshots, intentionally not committed:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-pre.raw.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-post.raw.json`
- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/unknown-profiles.metadata-repair-rollback-map.json`

## Rollback Posture

If this repair is later judged incorrect, restore each mutated profile row to:

- `user_kind = 'unknown'`
- `user_number = null`
- `user_number_assigned_at = null`
- `show_qa_llel_data = false`

Rollback remains profile-side only for this class.

## Discord / Music Sesh Untouched Confirmation

This mutation did not touch:

- Discord-linked tables
- Music Sesh / Spotify tables
- auth users
- auth metadata
- triggers
- RLS
- policies

Final preflight and post-pass reasoning both stayed consistent with the earlier case review:

- app-owned dependent rows remained `0` for all three
- Discord-linked references remained `0` for all three
- no direct Music Sesh references were implicated by this class

## Validation Result

Executed:

- `python .\\ops\\validation\\validate_stack.py`

Result:

- `critical=0 error=0 warning=306`

## Outcome

This exact mutation pass resolved the last direct unknown-profile repair class inside the Fitness profile-data hygiene lane.

What remains after this pass is no longer unknown-profile repair work. The remaining explicit boundaries are:

- governed heuristic automation identities already closed as no-op
- Discord/Music Sesh-owned surfaces that stay deferred to DiscordOS separation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: stays `99%` pending final closeout confirmation
- `Inventory & Truth Map`: stays `73%`
- `Full Stack Re-sync, Clean & Closeout`: stays `84%`
- `Discord OS Infrastructure Separation`: stays `95%` as the unchanged downstream gate

## Next Package

`Fitness Supabase Profile/Data Hygiene Final Closeout`

That closeout lane should decide whether:

1. the lane can move from `99%` to `100%`
2. the only remaining work is explicitly owned by DiscordOS separation
3. any residual Discord or Music Sesh concerns should stay outside Fitness profile hygiene permanently
