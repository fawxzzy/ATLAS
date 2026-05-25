## Fitness Discord Feedback Live Rollout

Date:
- 2026-05-25

Scope:
- production-backed Discord rollout only
- no DiscordOS migration
- no Supabase schema mutation
- no Vercel cutover
- no bot restart

Precondition:
- Fitness production was first moved onto commit `52cdb7e3f96381e70ad89b057c820f725d3ebb1b`
- rollout was intentionally blocked until production matched the intended feedback-submission behavior

Completed live actions:
1. Refreshed the member-facing feedback launcher using the canonical Fitness panel payload.
2. Created the dedicated `feedback-submission` channel because the previously configured launcher channel id no longer existed.
3. Updated feedback card `16d98fc2` through the live Fitness feedback workflow state:
   - status: `fixed`
   - completion review: `approved`
4. Synced the forum thread title, tags, starter body, audit comments, and final starter-post reaction state.
5. Published the single governed `Update:` post in `#updates`.

Live Discord proof:
- launcher channel id: `1508391092662567013`
- launcher channel name: `feedback-submission`
- launcher message id: `1508391095300526100`
- feedback thread id: `1508273950700867645`
- feedback starter message id: `1508273950700867645`
- updates channel id: `1504671871512346695`
- updates post id: `1508391706507350197`

Feedback card result:
- short id: `16d98fc2`
- full id: `16d98fc2-49a9-46f5-8223-cfae968173f7`
- report type: `feature`
- final status: `fixed`
- final completion review status: `approved`
- final starter-post visible status label: `Resolved`
- final starter-post reaction state: success emoji only

Update post content:

```txt
Update: Feature: Discord Feedback - Separate general feedback intake from main-chat command flow has been completed and cleaned up.

The post now includes:
a dedicated <#1508391092662567013> launcher channel for normal member intake
clearer Bug and Feature card wording, including better Acceptance Criteria guidance
the same public feedback board visibility without relying on main-chat command flow by default

Report ID: `16d98fc2`
```

Observed issue during rollout:
- `DISCORD_FEEDBACK_PANEL_CHANNEL_ID` in the current Discord worker env points to stale channel id `1505418608795320563`
- direct `/setup-feedback` style recovery through the configured channel id would currently fail until that env value is corrected or the route is hardened to fall back when the configured channel is missing
- the live rollout succeeded by creating the current dedicated channel directly and posting the canonical launcher there

Verification:
- confirmed launcher message exists in `feedback-submission`
- confirmed launcher embed title is `Feedback Submission`
- confirmed launcher buttons are `Submit` and `Edit`
- confirmed report `16d98fc2` reads `fixed` + `approved` in Supabase
- confirmed starter post now shows `Status: Resolved`
- confirmed starter post keeps only the success reaction
- confirmed governed `Update:` post exists in `#updates`
- stack validation remained green on blockers

No-change notes:
- no Fitness source code changed in this rollout pass
- no DiscordOS repo changes were needed
- `archive/` remained untouched
