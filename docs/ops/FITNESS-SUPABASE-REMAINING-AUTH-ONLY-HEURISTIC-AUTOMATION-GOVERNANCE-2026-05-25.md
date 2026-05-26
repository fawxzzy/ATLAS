# Fitness Supabase Remaining Auth-Only Heuristic Automation Governance

Date: 2026-05-25  
Mode: read-only governance packet  
Project: Fitness Supabase (`lpswxoyfniocuhljgzbc`)

## Objective

Govern the remaining `19` sign-in-bearing auth-only users as automation-heuristic rows so they are no longer treated as unresolved human-style profile repair candidates.

No Supabase write happened in this lane.

## Current Counts

Live read-only snapshot:

- auth-only users: `20`
- sign-in-bearing auth-only users: `19`
- never-signed-in auth-only users: `1`
- approved human-style profile-create candidates in this class: `0`

Redacted governance artifact:

- `runtime/exports/fitness-supabase-profile-data-hygiene/2026-05-24/remaining-auth-only-heuristic-automation-governance.redacted.json`

## Scope Reviewed

Reviewed:

- the `19` older sign-in-bearing auth-only rows only

Explicitly excluded:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`
- the `1` never-signed-in delete-later candidate
- unknown profiles
- Discord tables
- Music Sesh tables
- RLS or policy changes
- trigger changes
- profile creation
- auth deletion

## Redacted Row Labels

- `auth-only-01`
- `auth-only-02`
- `auth-only-03`
- `auth-only-04`
- `auth-only-05`
- `auth-only-06`
- `auth-only-07`
- `auth-only-08`
- `auth-only-09`
- `auth-only-10`
- `auth-only-11`
- `auth-only-12`
- `auth-only-13`
- `auth-only-14`
- `auth-only-15`
- `auth-only-16`
- `auth-only-17`
- `auth-only-18`
- `auth-only-19`

## Durable Heuristic Shape

The class remains fully automation-heuristic-shaped in the current live snapshot:

- all `19` still hit `is_automation_auth_user()`
- all `19` remain auth-side `account_kind = unknown`
- `18` rows match heuristic tokens:
  - `codex`
  - `example`
- `1` row matches heuristic tokens:
  - `qa`
  - `example`

Controlling implication:

- these rows do **not** belong in future human-style profile repair lanes

## Review Answers

### 1. Should the `19` sign-in-bearing auth-only heuristic rows remain auth-only for now?

Yes.

They should remain auth-only for now because there is still no named retained-purpose evidence that justifies creating automation profiles for them, and there is no clean human-style profile-repair basis for creating human profiles.

### 2. Are any of the `19` named or purposeful automation identities?

No named or purposeful retained automation identities are proven inside this `19`-row class.

Current durable evidence supports only:

- heuristic automation exclusion
- not named retained automation identity

### 3. Are any of the `19` safe future metadata-alignment candidates?

Not yet.

Auth-metadata alignment only makes sense after a row is ratified as a named or purposeful retained automation identity. That approval does not exist for any member of this class.

### 4. Are any of the `19` stale or manual-review candidates?

As a class:

- not stale-cleanup-ready
- not delete-ready
- manual review is only needed if a future owner wants to promote or dispose of a specific row

That means the class is not unresolved drift, but it is also not an approved mutation set.

### 5. Should future human-style create-profile passes permanently exclude all rows that hit the automation heuristic?

Yes.

Durable rule after this packet:

- all rows predicted to satisfy `is_automation_auth_user()` are excluded from human-style profile-create repair lanes unless a later packet explicitly reclassifies them

### 6. Is a future automation-profile creation lane needed for any of these rows?

Not currently.

A future automation-profile creation lane would only be justified if one or more rows are later given an explicit retained purpose.

### 7. Does any decision depend on DiscordOS separation?

Not for this class as currently understood.

DiscordOS separation remains the defer boundary for Discord-owned and Music Sesh-owned data, but it is not needed to govern these `19` auth-only heuristic rows.

### 8. What is the next safe mutation class, if any?

No new mutation class is approved from this packet for the `19` reviewed rows.

The next safe packet should move to a different remaining class.

### 9. Should this class close as governed no-op, manual-review, or future mutation?

Selected closeout posture:

- governed no-op by class
- manual-review only if a future row is proposed for named retained automation, cleanup, or explicit profile creation
- no immediate future mutation class

## Class Decision Table

| Reviewed class | Count | Decision | Why |
| --- | ---: | --- | --- |
| heuristic automation auth-only holdouts | `19` | governed no-op | every row still hits the automation heuristic and none has named retained purpose |
| named retained automation candidates | `0` | none approved | no row-scoped retained-purpose evidence exists |
| human-style profile-create candidates | `0` | permanently excluded unless reclassified | profile creation would enter the wrong lane under current trigger policy |
| metadata-alignment candidates | `0` | none approved | auth metadata should not be aligned for heuristic-only rows without explicit purpose |
| stale cleanup candidates | `0` | none proven | no row is cleanup-ready from current evidence |

## Future Exclusion Rule

Future durable rule for this lane:

- human-style profile-create repair must exclude any auth-only row predicted to hit `is_automation_auth_user()`
- heuristic automation auth-only rows must first pass through row-purpose governance before any profile creation, metadata alignment, or cleanup packet

## Named Retained Automation Candidates

None approved from this class.

The only currently governed automation identities remain elsewhere:

- `automation-anchor-01` as canonical writable automation identity
- the legacy aligned automation class
- `candidate-01` through `candidate-04` as tolerated heuristic automation profiles

## Mutation Candidates

No mutation candidate emerges from this packet for the `19` reviewed rows.

If any row is later reopened, it should be through one of these narrower future lanes:

1. named retained automation identity review
2. row-specific cleanup review
3. row-specific DiscordOS mapping review if ownership evidence appears

## Unchanged / Deferred Classes

Still unchanged and deferred:

- `candidate-01` through `candidate-04`
- the `1` never-signed-in delete-later candidate
- the `3` unknown profiles
- Discord tables
- Music Sesh tables
- trigger changes
- RLS or policy changes

## DiscordOS Deferral Boundary

This class does not require DiscordOS separation to close as governed no-op.

DiscordOS separation remains the correct boundary for:

- Discord-owned runtime/data migration
- Music Sesh-owned runtime/data migration
- any later identity mapping that depends on Discord runtime ownership

## No-Mutation Confirmation

This packet performed:

- no Supabase writes
- no profile creation
- no auth deletion
- no profile deletion
- no metadata updates
- no trigger, RLS, or policy changes
- no Discord or Music Sesh mutation

## Marker Recommendation

- `Fitness Supabase Profile/Data Hygiene`: `91% -> 94%`
- `Inventory & Truth Map`: `69% -> 70%`
- `Full Stack Re-sync, Clean & Closeout`: `80% -> 81%`

## Exact Next Package

`Fitness Supabase Never-Signed-In Auth-Only Delete-Later Approval Packet`

Why this is next:

- the `19` sign-in-bearing heuristic rows are now governed as exclusion/no-op rather than unresolved repair work
- the next remaining narrow auth class is the single never-signed-in delete-later candidate
- that class can be reviewed independently without reopening the governed automation-exclusion posture

## Validation

Expected validation after this packet:

- `python .\\ops\\validation\\validate_stack.py`
