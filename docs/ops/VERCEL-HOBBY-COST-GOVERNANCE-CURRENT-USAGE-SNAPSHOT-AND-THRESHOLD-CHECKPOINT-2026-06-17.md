# Vercel Hobby Cost Governance Current Usage Snapshot And Threshold Checkpoint - 2026-06-17

- Date: `2026-06-17`
- Lane: `Vercel Hobby Cost Governance`
- Owner: `ATLAS/root`
- Mode: `root governance, live read-only usage snapshot, and marker ratchet`
- Governing app: `Fawxzzy Fitness`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/VERCEL-HOBBY-COST-GOVERNANCE-MARKER-ADMISSION-PASS-1-2026-06-13.md`
  - [Vercel pricing](https://vercel.com/pricing)
  - [Vercel limits](https://vercel.com/docs/limits)
  - [Vercel Hobby plan](https://vercel.com/docs/plans/hobby)
  - [Fluid compute pricing](https://vercel.com/docs/functions/usage-and-pricing)
  - [Observability Plus](https://vercel.com/docs/observability/observability-plus)
  - [Speed Insights limits and pricing](https://vercel.com/docs/speed-insights/limits-and-pricing)
  - [Web Analytics pricing](https://vercel.com/docs/analytics/limits-and-pricing)
  - Vercel connector read surfaces: project lookup, deployment listing, runtime-log listing
- Control-plane checkpoint: `main@7079e83d`

## Objective

Land the first durable root receipt that combines:

- the current official Hobby thresholds
- the current Fitness Vercel usage-snapshot categories
- one explicit cost-governance read

This pass stays read-only and does not mutate Vercel settings, billing, deploy state, or the Fitness repo.

## Official Plan Checkpoint Revalidated On 2026-06-17

From the current official Vercel docs and pricing surfaces:

- Hobby includes `1M / month` Edge Requests and `100 GB / month` Fast Data Transfer
- Hobby Vercel Functions include `4 hours / month` Active CPU, `360 GB-hrs / month` Provisioned Memory, and `1M / month` Invocations
- Hobby includes `6,000` build-execution minutes
- Hobby includes `10,000 / month` Speed Insights data points on one project
- Hobby includes `50,000 / month` Web Analytics events
- Hobby runtime logs retain only `1 hour`
- Observability is available on all plans, but Observability Plus is a paid add-on available only on Pro and Enterprise
- Observability Plus currently shows `Pro: $10/month` base pricing and `30 days` retention
- Pro currently starts at `$20/month`

These figures were rechecked on `2026-06-17` and remain date-sensitive. Future ratchets must re-check the official docs again rather than inheriting old numbers as permanent truth.

## Current Read-Only Fitness Snapshot

The live read-only connector surfaces show:

- project lookup resolves the canonical Fitness Vercel project and active team scope
- the last `7` days include `7` production deployments
- the last `30` days return at least `20` deployments in the first connector page
- several recent deployment records still carry `gitDirty: "1"` metadata
- the sampled recent production runtime logs are dominated by repeated `GET /api/discord/interactions 200` lines at roughly `30` second cadence

Important limits on this snapshot:

- the connector surfaces used here do not expose a trustworthy month-to-date billing total
- they also do not expose direct month-to-date counters for Active CPU, Provisioned Memory, or total Function Invocations
- this pass is therefore a governance checkpoint, not a billing statement

## Pressure Read

### Edge and invocation pressure

- The repeated `/api/discord/interactions` sample is a real usage surface and should stay on the watch list.
- If that `30` second cadence persisted continuously for `30` days, that one endpoint alone would imply about `86,400` requests over `30` days.
- That would be about `8.64%` of the current `1M / month` Edge Requests allowance.

That figure is an inference from the sampled cadence, not a measured monthly counter.

Current read:

- `Green` on direct threshold evidence
- `Yellow watch-item` on recurring polling shape

### Compute and memory pressure

- No current read-only surface here proves the team is near the Hobby `4` Active CPU hours or `360` GB-hrs Provisioned Memory ceilings.
- No evidence in this pass forces a Pro move or a paid observability move.

Current read:

- `Green from available evidence`
- still missing direct counter proof

### Build and deployment churn

- `7` production deployments in `7` days and at least `20` deployments returned in the first `30`-day connector page mean Fitness remains a moderately active deploy surface.
- The `gitDirty` metadata is governance debt because it weakens provenance clarity even when it does not prove cost exhaustion.
- This is a build-pressure watch item, but not a current spend-escalation proof.

Current read:

- `Yellow watch-item`

### Observability and retention gating

- Hobby runtime-log retention is only `1 hour`, so cost and incident proof cannot depend on long-lived Vercel-hosted runtime logs alone.
- Observability Plus is a paid Pro/Enterprise add-on, so the cheap-by-design posture must prefer bounded external receipts and targeted snapshots before paid retention is treated as necessary.

Current read:

- `Yellow governance watch-item`

## Marker Movement

- `Vercel Hobby Cost Governance` moves from `35%` to `45%`

Why `45%` is honest:

- the first durable root usage-snapshot categories now exist
- the official Hobby and Pro thresholds were revalidated today
- the current polling and deployment pressure shapes are now explicit rather than remembered context

Why the lane stops at `45%`:

- no route, middleware, and fetch inventory exists yet
- no repeat snapshot trend exists yet
- no no-secret rerunnable guardrail report exists yet
- no Fitness release or readiness flow yet includes a cost-governance check

## Exact Next Honest Moves

- `55%`: durable route, middleware, and fetch pressure inventory
- `65%`: one Hobby guardrail report can be rerun without secrets
- `75%`: Fitness release or readiness flow includes a cost-governance checkpoint
- `85%`: at least two preserved usage snapshots prove trend discipline

## Non-Goals

- no Vercel project setting mutation
- no billing-setting mutation
- no Pro upgrade
- no Observability Plus enablement
- no Fitness repo mutation
- no deploy

## Validation

- Vercel connector project lookup succeeded for Fitness
- Vercel connector deployment listing succeeded for `7`-day and `30`-day windows
- Vercel connector runtime-log listing succeeded for a recent production sample
- local root validation is run separately with this docs bundle before closeout

