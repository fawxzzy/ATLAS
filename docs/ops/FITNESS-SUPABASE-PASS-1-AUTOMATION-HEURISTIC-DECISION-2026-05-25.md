# Fitness Supabase Pass 1 Post-Pass Automation-Heuristic Decision

- Date: `2026-05-25`
- Lane: `Fitness Supabase Profile/Data Hygiene`
- Mode: `read-only decision pass`
- Status: `decision recorded`

## Goal

Decide whether the four newly created Pass 1 profiles being classified as automation is correct under current DB policy, and determine whether rollback, repair, or pure documentation follow-up is the safer next move.

Pass 1 created profile rows for:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

Observed post-pass state:

- auth-only count: `24 -> 20`
- sign-in-bearing auth-only: `23 -> 19`
- profile count: `33 -> 37`
- automation profiles: `12 -> 16`
- automation-profile/auth-unknown mismatches: `11 -> 15`
- Discord and Music Sesh table counts unchanged

## Trigger Side-Effect Explanation

The side effect came from the existing trigger contract in `044_real_user_numbers.sql`.

### Relevant trigger path

`public.assign_real_user_number_on_profile_insert()` calls:

- `public.is_automation_auth_user(new.id)`

That function returns true when **any** of the following are true:

1. `auth.users.raw_app_meta_data.account_kind = automation`
2. `auth.users.raw_user_meta_data.account_kind = automation`
3. the auth email matches the heuristic regex containing any of:
   - `codex`
   - `test`
   - `qa`
   - `example`
   - `preview`
   - `local`

If the function returns true, the trigger forces:

- `user_kind = automation`
- `user_number = null`
- `user_number_assigned_at = null`

### What happened for Pass 1

For all four candidates:

- auth metadata stayed `unknown`
- raw user metadata stayed `unknown`
- the email heuristic matched

Redacted heuristic classification summary:

| Candidate | Auth metadata says automation? | Email heuristic matched? | Heuristic tokens matched | Resulting profile `user_kind` | Resulting `user_number` | Resulting `show_qa_llel_data` |
| --- | --- | --- | --- | --- | --- | --- |
| `candidate-01` | no | yes | `codex`, `example` | `automation` | `null` | `false` |
| `candidate-02` | no | yes | `codex`, `example` | `automation` | `null` | `false` |
| `candidate-03` | no | yes | `codex`, `example` | `automation` | `null` | `false` |
| `candidate-04` | no | yes | `codex`, `example` | `automation` | `null` | `false` |

## Classification Decision

### Is the automation classification correct?

Decision:

- `correct under current DB policy`

Reason:

- the trigger behaved exactly as currently designed
- the four rows are Codex/example-style identities, which the database intentionally treats as automation candidates

### Is the result still desired for this lane?

Decision:

- `expected but undesired for the original Pass 1 framing`

Reason:

- Pass 1 was framed as a narrow profile-core repair for sign-in-bearing auth-only users
- the approval packet did not model trigger-side classification
- the result is therefore operationally valid but lane-semantically surprising

### Is the result wrong?

Decision:

- `no`

The trigger did not malfunction.

### Is the result ambiguous?

Decision:

- `partially`

What is ambiguous is not the trigger result, but the intended governance meaning of these four users:

- should they remain part of the automation cohort permanently
- or should the automation heuristic be considered too broad for future human-profile repair lanes

## Candidate Labels Affected

Affected labels:

- `candidate-01`
- `candidate-02`
- `candidate-03`
- `candidate-04`

All four were affected in the same way.

## Row Count Impact

### Helpful effect

- auth-only rows decreased by `4`
- recent sign-in-bearing auth-only drift for Pass 1 dropped from `4` to `0`

### New debt created

- automation profiles increased by `4`
- automation-profile/auth-unknown mismatches increased by `4`

### Deferred classes remained stable

Confirmed unchanged:

- `19` older sign-in-bearing auth-only rows
- `1` never-signed-in auth-only candidate
- `3` unknown profiles
- Discord tables by count
- Music Sesh tables by count

So the Discord/Music Sesh deferral boundary remains intact.

## Rollback Risk

Rollback would:

- remove the four new profiles
- restore the auth-only count from `20` back to `24`
- restore the recent sign-in-bearing auth-only drift from `0` back to `4`

Rollback would **not** fix the underlying trigger policy.

Operationally, rollback would produce:

- a cleaner automation-mismatch count
- but a worse auth/profile drift state

Decision:

- rollback is **not** the better immediate state

## Keep / Repair / Rollback Decision

### Keep all four automation classifications

Decision:

- `yes, keep them for now`

Reason:

- current DB policy explicitly classifies them as automation
- they are Codex/example-style users rather than clear human-owner candidates
- deleting the new profiles would reintroduce auth-only drift without improving the policy

### Repair metadata or classification for some/all four

Decision:

- `yes, likely later`

But not by changing `user_kind` on the profiles first.

Safer repair direction:

- decide whether the auth metadata should be brought into alignment with the existing automation heuristic
- decide whether `show_qa_llel_data` should be corrected for automation-classified profiles created through this path

### Rollback created profiles

Decision:

- `not recommended now`

## Does the mismatch definition need revision?

Decision:

- `yes`

The current mismatch class is too coarse after Pass 1.

It now contains at least two distinct subclasses:

1. profiles intentionally classified as automation by the DB trigger through email heuristic
2. profiles that are likely automation drift but not yet policy-ratified

The hygiene lane should distinguish:

- `heuristic automation, metadata not yet aligned`
- from
- `ambiguous mismatch needing owner review`

## Does the approval packet need amendment for future writes?

Decision:

- `yes`

Future approval packets should include a trigger-side-effects section for any profile creation write.

Minimum requirement:

1. evaluate whether the candidate auth rows match `is_automation_auth_user()`
2. predict resulting `user_kind`
3. predict resulting `user_number`
4. predict whether `show_qa_llel_data` will need follow-up repair
5. reject or reclassify candidates before write if the side effect conflicts with lane intent

## Pass 1 Acceptance Verdict

Decision:

- `partially accepted`

Why:

- the write was bounded, reversible, and did not touch deferred tables
- but it did not produce a clean human-style profile repair result
- instead, it converted four auth-only rows into heuristic-automation profiles with metadata drift

So Pass 1 should be kept as durable history, but not treated as a full clean-success mutation.

## Recommended Next Mutation Class

Do **not** open generic `Mutation Pass 2` next.

Recommended next package:

- `Fitness Supabase Automation Metadata And QA-Visibility Decision Packet`

That packet should decide, for the four new rows and the broader mismatch class:

1. whether auth metadata should be aligned to automation
2. whether automation-created profiles should have `show_qa_llel_data = true`
3. whether the email heuristic should stay as broad as it is now for future profile creation lanes
4. whether future create-profile passes should exclude any auth user that matches the automation heuristic

## Fitness Supabase Marker Decision

This decision pass justifies a modest advance because the post-pass behavior is now understood and governed.

Recommended marker posture:

- `Fitness Supabase Profile/Data Hygiene`: `58% -> 62%`
- `Inventory & Truth Map`: stays `64%`
- `Full Stack Re-sync, Clean & Closeout`: stays `76%`

Reason:

- the pass is no longer ambiguous
- rollback is not the preferred immediate move
- but a repair/metadata decision lane still exists before more Supabase hygiene writes should continue
