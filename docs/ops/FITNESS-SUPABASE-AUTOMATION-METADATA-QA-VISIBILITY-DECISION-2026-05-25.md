# Fitness Supabase Automation Metadata And QA-Visibility Decision

- Date: `2026-05-25`
- Lane: `Fitness Supabase Profile/Data Hygiene`
- Mode: `read-only decision packet`
- Status: `policy decision recorded`

## Goal

Decide the correct policy for the four Pass 1 profiles that were created as automation-classified by the existing DB trigger, and decide how future create-profile passes should treat auth rows matching the automation heuristic.

Affected labels:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

## Decision Summary

The correct immediate policy is:

1. keep all four new profiles as `automation`
2. do **not** roll them back
3. do **not** align auth metadata yet
4. keep `show_qa_llel_data = false` for these four for now
5. exclude similar heuristic-automation auth rows from future human-style create-profile repair passes
6. require a trigger-side-effect precheck in all future profile-creation approval packets
7. route any broader automation cleanup into a separate automation-consolidation/owner-review lane

This is a policy clarification packet, not a mutation packet.

## Why This Is The Right Policy

The prior decision already established:

- the trigger behavior was correct under current DB policy
- rollback is not the preferred immediate move

This packet resolves the remaining policy question:

- how those four rows should be treated from now on
- and how future passes should avoid repeating the same ambiguity

## Decision Per Candidate Label

All four labels receive the same decision:

| Candidate | Keep profile? | Keep `user_kind=automation`? | Change auth metadata now? | Change `show_qa_llel_data` now? | Reason |
| --- | --- | --- | --- | --- | --- |
| `candidate-01` | yes | yes | no | no | heuristic-automation identity, not a human-profile repair target |
| `candidate-02` | yes | yes | no | no | heuristic-automation identity, not a human-profile repair target |
| `candidate-03` | yes | yes | no | no | heuristic-automation identity, not a human-profile repair target |
| `candidate-04` | yes | yes | no | no | heuristic-automation identity, not a human-profile repair target |

## Answered Questions

### 1. Should `candidate-01` through `candidate-04` remain automation-classified?

Decision:

- `yes`

Reason:

- they matched the existing automation heuristic
- the trigger behaved correctly
- keeping the profiles avoids restoring auth-only drift

### 2. Should their auth metadata be aligned to automation?

Decision:

- `not yet`

Reason:

- aligning auth metadata would be a real identity-classification mutation
- that would ratify these four rows as intentionally retained automation identities
- the current canonical automation policy still favors one verified writable automation identity by default
- this needs a separate owner-aware consolidation/review lane

Operational meaning:

- current mismatch count should be treated as partly intentional trigger-policy drift, not as pure error

### 3. Should `show_qa_llel_data` remain false or be repaired for automation-classified profiles?

Decision:

- `remain false for now`

Reason:

- product logic distinguishes automation classification from QA visibility
- `src/lib/qa-data-visibility.ts` allows explicit `show_qa_llel_data = false` to override the automation default
- the repo's documented canonical QA automation posture centers on a named Codex QA profile and similar explicit QA identities, not every heuristic-automation auth row
- turning QA visibility on for these four by default would widen QA/LLEL exposure without a named product/testing purpose

Interpretation:

- these four are best treated as automation-classified but not yet QA-visible automation identities

### 4. Should future create-profile passes exclude auth rows matching the automation heuristic?

Decision:

- `yes`

Reason:

- the current human-style repair lane should not silently create new automation-classified profiles
- any auth row predicted to hit `is_automation_auth_user()` belongs in a separate automation review class, not the generic sign-in-bearing auth-only repair class

New future rule:

- any create-profile candidate that matches the automation heuristic must be excluded from the normal auth-only repair subset unless the approval packet explicitly reclassifies it as an automation-targeted pass

### 5. Should future approval packets include a trigger-side-effect precheck?

Decision:

- `yes`

Required precheck items:

1. whether `is_automation_auth_user()` will return true
2. predicted `user_kind`
3. predicted `user_number`
4. predicted `show_qa_llel_data` posture after application logic and explicit insert shape
5. whether the row belongs in a human repair lane or an automation lane

### 6. Should the automation-profile/auth-unknown mismatch definition change now that profile rows exist?

Decision:

- `yes`

New distinction needed:

1. `heuristic automation, auth metadata not yet aligned`
2. `ambiguous automation mismatch needing owner review`

Current mismatch counts should no longer treat those as one undifferentiated debt class.

### 7. Should there be exactly one canonical AI automation profile, or are multiple automation profiles valid by class?

Decision:

- `one canonical writable automation profile by default`
- `multiple automation profiles may exist, but only when they are named, purposeful, and governed`

Implication:

- multiple automation profiles are not banned
- they should not accumulate accidentally through generic cleanup passes

### 8. Does any answer depend on DiscordOS Infrastructure Separation?

Decision:

- `no`

Reason:

- this is a Fitness-local auth/profile/QA-visibility policy question
- Discord and Music Sesh deferral remains intact and unchanged

### 9. Does any answer require owner approval before mutation?

Decision:

- `yes`

Future mutations that require owner approval:

- aligning auth metadata for the four new rows
- changing `show_qa_llel_data` for those rows
- consolidating or deleting automation identities
- changing the trigger heuristic itself

## Trigger-Side-Effect Precheck Requirement

This packet promotes a durable rule:

- any future profile-creation mutation approval must include an explicit trigger-side-effect prediction section

Minimum required fields:

- candidate label
- expected `is_automation_auth_user()` result
- trigger basis:
  - auth metadata
  - raw user metadata
  - email heuristic
- expected `user_kind`
- expected `user_number`
- expected QA-visibility handling
- lane classification:
  - human repair
  - automation review

## QA/LLEL Visibility Recommendation

Policy recommendation:

- keep `show_qa_llel_data = false` for the four Pass 1 profiles
- reserve `show_qa_llel_data = true` for:
  - the canonical writable automation identity
  - named QA/LLEL automation accounts
  - explicit owner-approved exceptions

Reason:

- this keeps QA/LLEL product surfaces intentionally narrow
- and avoids turning every heuristic automation row into a visible QA account

## Auth Metadata Recommendation

Policy recommendation:

- do not align auth metadata for `candidate-01` through `candidate-04` in this lane

Reason:

- metadata alignment is a separate identity ratification action
- it should happen only after deciding whether these four should become named retained automation identities or remain tolerated heuristic artifacts

## Unchanged Classes

Still unchanged by this decision packet:

- `19` older sign-in-bearing auth-only rows
- `1` never-signed-in auth-only delete-later candidate
- `3` unknown profiles
- Discord tables
- Music Sesh tables
- RLS/policy surfaces
- trigger code

## Exact Next Package

Next package should be:

- `Fitness Supabase Automation Identity Consolidation Review Packet`

That packet should answer:

1. whether the four new heuristic-automation profiles should be ratified as retained automation identities
2. whether any existing automation mismatches should be grouped with them
3. whether a later auth-metadata alignment mutation is desirable
4. whether a later QA-visibility repair mutation is desirable for any subset

This should still be a review/decision packet first, not an immediate mutation.

## Non-Goals

This packet does not:

- mutate Supabase
- update auth metadata
- update profile rows
- delete profiles
- delete auth users
- change triggers
- change RLS or policies
- touch Discord or Music Sesh data
- change app code
- deploy

## Marker Recommendation

This packet is a policy clarification pass, not a repair pass.

Recommended movement:

- `Fitness Supabase Profile/Data Hygiene`: `62% -> 66%`
- `Inventory & Truth Map`: stays `64%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

Reason:

- the Supabase lane now has a governed forward policy for trigger-side automation cases
- but no repair or consolidation mutation has happened yet
