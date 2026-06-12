# Discord OS Feedback Workflow Edge Persisted Writer Proof

Date: 2026-06-12

## Decision

`Discord OS Feedback Workflow Canonicalization` moves from `76%` to `80%`.

This is not a `100%` closeout. The exact remaining blocker class is still `Fitness-to-DiscordOS traffic transfer, rollback execution proof, and live workflow parity proof`.

## Proof

- Owner repo: `repos/DiscordOS`
- Owner commit: `1c4a0ac0f47953cabe2559e10f44df9170198abf`
- Owner receipt: `repos/DiscordOS/docs/ops/discordos-edge-persisted-writer-proof-2026-06-12.md`
- Supabase project: `nwexsktuuenfdegzrbut`
- Supabase Edge Function: `discordos-feedback-persist`
- Edge Function deployment: version `2`, `ACTIVE`, `verify_jwt: true`
- Supabase migration: `discordos_feedback_proof_rpc`
- Local migration: `repos/DiscordOS/supabase/migrations/20260612162500_discordos_feedback_proof_rpc.sql`
- Vercel deployment: `dpl_4FUNXwMZDSPH3BLFJEaakA2mk9eg`
- Vercel production alias: `https://fawxzzy-discordos.vercel.app`
- GitHub commit title: `Add Edge-backed DiscordOS persisted writer proof`

## Live Persistence Evidence

Direct Supabase Edge proof:

- endpoint: `https://nwexsktuuenfdegzrbut.supabase.co/functions/v1/discordos-feedback-persist`
- report id: `edge-persist-proof-2026-06-12-004`
- response: `ok: true`, `persisted: true`, `runtime: supabase-edge-function`
- boundaries: `writesDiscord: false`, `writesFitness: false`, `trafficMoved: false`, `proofOnly: true`

Vercel-to-Supabase Edge proof:

- endpoint: `https://fawxzzy-discordos.vercel.app/api/feedback-persist`
- report id: `edge-persist-proof-2026-06-12-005`
- response: `ok: true`, `persisted: true`, `persistenceAttempted: true`, `persistenceRuntime: supabase-edge-function`
- writer posture: `writerMode: shadow`
- boundaries: `writesDiscord: false`, `writesFitness: false`, `trafficMoved: false`

Supabase connector table proof after the Vercel proof:

- `discordos.discord_feedback_reports`: `rows: 2`
- `discordos.discord_feedback_audit_events`: `rows: 0`
- `discordos.discord_completion_reviews`: `rows: 0`
- RLS remains enabled on all inspected DiscordOS tables.

## Activation Boundary

Live `/api/activation` still reports:

- `writerMode: shadow`
- `trafficTransferMode: none`
- `rollbackMode: fitness-primary`
- `liveWorkflowParityProved: false`
- `writerActivationAllowed: false`
- `liveCutover: false`
- `fitnessTrafficMoved: false`

Live `/api/readiness` reports the writer can use the Supabase Edge runtime path:

- `serviceRoleConfigured: true`
- `serviceRoleRuntime: supabase-edge-function`
- `serviceRolePresent: false`
- `edgeServiceRoleConfigured: true`
- `discordBotTokenValid: true`

## Scope Boundary

This pass did not modify Fitness, did not send Discord messages, did not move Fitness traffic, did not open direct production cutover, and did not print or commit secret values.

The old blocker slice `persisted writer activation plus backend service-role availability` is narrowed: the DiscordOS production endpoint can now persist proof-only rows through the Supabase Edge service-role runtime while remaining in `shadow` mode. The remaining blocker is no longer Vercel project setup, GitHub access, Supabase project setup, bot-token readiness, activation-guard existence, no-persistence shadow validation, persisted endpoint existence, or Edge-backed proof-only persistence.

## Remaining Blocker

The exact remaining blocker class is:

`Fitness-to-DiscordOS traffic transfer, rollback execution proof, and live workflow parity proof`.

The next honest package must be owner-side cutover proof under explicit scope. It must prove traffic transfer or governed mirroring, rollback execution, and live parity without treating the proof-only synthetic rows as release traffic.
