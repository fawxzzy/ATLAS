# Vercel Hobby Cost Governance Route, Middleware, And Fetch Pressure Inventory - 2026-06-17

- Date: `2026-06-17`
- Lane: `Vercel Hobby Cost Governance`
- Owner: `ATLAS/root`
- Mode: `root governance, repo inventory, and live Vercel pressure read`
- Governing app: `Fawxzzy Fitness`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/VERCEL-HOBBY-COST-GOVERNANCE-MARKER-ADMISSION-PASS-1-2026-06-13.md`
  - `docs/ops/VERCEL-HOBBY-COST-GOVERNANCE-CURRENT-USAGE-SNAPSHOT-AND-THRESHOLD-CHECKPOINT-2026-06-17.md`
  - `repos/fawxzzy-fitness/.vercel/project.json`
  - `repos/fawxzzy-fitness/vercel.json`
  - `repos/fawxzzy-fitness/src/middleware.ts`
  - `repos/fawxzzy-fitness/src/app/**/route.ts`
  - Vercel connector live reads:
    - project `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
    - deployment `dpl_6jSoMDyVuCbbhP7Ep2dPremrVVtE`
    - production runtime-log samples through `2026-06-17`
- Control-plane checkpoint: `main@771b2196`

## Objective

Advance the lane from usage-shape watch items to one durable route, middleware, and fetch pressure inventory for the current Fitness Vercel surface.

This pass stays read-only:

- no Fitness repo mutation
- no Vercel setting mutation
- no billing mutation
- no deploy

## Live Deployment Shape

The current linked Fitness Vercel project still resolves as:

- project: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- team: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- framework: `nextjs`
- latest production deployment: `dpl_6jSoMDyVuCbbhP7Ep2dPremrVVtE`
- deployment type: `LAMBDAS`
- region: `iad1`
- source: `cli`

The deployment metadata still reports:

- `lambdaRuntimeStats: {"nodejs":5}`

That does not identify exact route bundles by itself, but it confirms the deployed surface is not static-only and still includes multiple Node runtime functions.

## Repo Route Inventory

Current `src/app/**/route.ts` inventory:

- total route handlers: `31`
- `/api/**` routes: `22`
- `/auth/**` routes: `5`
- `/dev/**` routes: `4`
- routes with explicit `dynamic = "force-dynamic"`: `29`
- routes with explicit `runtime = "nodejs"`: `4`
- routes exposing `GET`: `18`
- routes exposing `POST`: `15`
- routes exposing `DELETE`: `1`

Explicit Node runtime routes:

- `/api/discord/interactions`
- `/api/spotify/oauth/callback`
- `/api/spotify/oauth/start`
- `/api/vercel/deployment-webhook`

Pressure read:

- the Fitness Vercel surface is overwhelmingly dynamic rather than static-cached
- the deployed runtime shape is still function-heavy enough that edge-request, invocation, and active-CPU discipline matter

## Middleware Pressure Inventory

`repos/fawxzzy-fitness/src/middleware.ts` applies one broad matcher to nearly every non-static request path.

Important boundary:

- static assets and `_next` static/image paths are excluded at the matcher
- middleware still executes for most application, route-handler, and auth traffic
- the session-refresh branch then short-circuits only for public authless paths and public authless prefixes

Public authless exceptions currently include:

- `/api/app-version`
- `/api/discord/interactions`
- `/auth/**`
- `/dev/**`
- `/login`
- `/signup`
- `/forgot-password`
- `/reset-password`
- `/install`

Protected-path consequence:

- most authenticated app traffic still crosses middleware and can trigger `recoverSupabaseSessionFromCookies(...)`
- that helper calls `supabase.auth.refreshSession(...)` when the access token is stale or force-refresh is requested

Cost-governance read:

- middleware is not just a routing seam; it is a runtime pressure multiplier because it sits in front of most non-static app requests
- the live recurrent hot endpoint `/api/discord/interactions` is exempt from the auth refresh branch, which is good, but it still traverses the broad matcher family

## Internal Fetch Pressure Inventory

Current source scan finds `34` total `fetch(...)` sites under `src/`:

- `17` literal internal app fetch sites
- `17` external-or-dynamic fetch sites

The internal app fetch family is concentrated and durable:

- `/auth/session-keepalive`
  - called by `src/components/ServiceWorkerBootstrap.tsx`
  - route forces session refresh work through `handleSessionKeepaliveRequest(...)`
- `/api/app-version`
  - called by `src/components/ServiceWorkerBootstrap.tsx`
  - live production logs already show this route firing alongside keepalive
- `/auth/session-sync`
  - called by `src/components/SignOutButton.tsx`
  - also called inside `src/lib/supabase/client.ts`
- `/api/history/sessions`
  - called by `src/app/history/HistorySessionsClient.tsx`
- `/api/history/exercises`
  - called by `src/app/history/exercises/ExerciseBrowserClient.tsx`
- `/api/sessions/start`
  - called by `src/app/today/TodayStartButton.tsx`
- `/api/sessions/resume`
  - called by `src/app/today/TodayStartButton.tsx`
- `/api/account/export` and `/api/account/export/preview`
  - called by `src/components/settings/DataSettingsSection.tsx`
- `/api/migration/export`, `/api/migration/import`, and `/api/migration/parity`
  - called by `src/components/settings/LegacyMigrationSettings.tsx`
- `/api/discord/verification-token`
  - called by `src/components/settings/DiscordAccessSettings.tsx`
- `/api/ecosystem/fitness/pilot-shadow`
  - called by `src/app/today/TodayRecoveryShadowPlacement.tsx`
- `/api/exercise-info/[exerciseId]`
  - called by `src/lib/exercise-info-client.ts`
  - also used by `src/app/dev/exercise-info-live/page.tsx`

Cost-governance read:

- the internal fetch graph is not huge, but it is dense around auth/session, history, export/migration, and exercise-info surfaces
- `ServiceWorkerBootstrap.tsx` is a real recurring pressure source because it reaches both keepalive and app-version routes

## External Integration Fetch Inventory

The external-or-dynamic fetch family is dominated by a small set of integrations:

- Discord REST fetches in `src/lib/discord/rest.ts`
- Spotify token/profile/search/player/queue fetches in:
  - `src/lib/spotify/oauth.ts`
  - `src/lib/spotify/profile.ts`
  - `src/lib/spotify/player.ts`
  - `src/lib/spotify/queue.ts`
  - `src/lib/spotify/search.ts`
- dynamic host-based or non-literal fetches in:
  - `src/app/dev/exercise-info-live/page.tsx`
  - `src/components/error/safeRecoveryNavigation.ts`

Route implication:

- the explicit Node-runtime routes line up with the external integration surfaces that most plausibly deserve closer runtime budget watch
- Spotify and Discord operations are the parts most likely to create higher-cost bursts if they widen materially

## Live Runtime Pressure Read

Recent production runtime-log samples still show:

- repeated `GET /api/discord/interactions 200` at about `30` second cadence
- at least one live `GET /auth/session-keepalive 200`
- at least two live `GET /api/app-version 200`

That means the current pressure stack is now durably visible as:

1. recurring Discord interaction polling
2. middleware-covered authenticated traffic
3. service-worker-driven keepalive and app-version chatter
4. user-driven history, session, export, and migration fetches
5. external Discord and Spotify integration calls behind the relevant route families

## Governance Read

What this inventory proves:

- the Fitness Vercel surface is not just “a few routes”
- the cost story is shaped by one broad middleware seam plus a mostly force-dynamic route family
- the current hottest known path is still `/api/discord/interactions`
- the secondary steady-state chatter is auth/session plus app-version work
- the deployment remains function-backed and Node-runtime-bearing, not static-first

What this inventory does not yet prove:

- no month-to-date billed invocation total
- no month-to-date active CPU total
- no month-to-date provisioned-memory total
- no trend proof across multiple preserved snapshots

## Marker Movement

- `Vercel Hobby Cost Governance` moves from `45%` to `55%`

Why `55%` is honest:

- the previously missing route, middleware, and fetch pressure inventory is now durable
- the live route-pressure read is now tied to the actual deployed Fitness project and latest production deployment
- the lane now distinguishes broad matcher pressure, internal fetch chatter, and external integration fetch classes

Why the lane still stops here:

- no rerunnable no-secret guardrail report exists yet
- no release or readiness flow consumes this cost-governance check yet
- no preserved multi-snapshot trend proves stabilization or drift over time

## Exact Next Honest Moves

- `65%`: one Hobby guardrail report can be rerun without secrets
- `75%`: Fitness release or readiness flow includes a cost-governance checkpoint
- `85%`: at least two preserved usage snapshots prove trend discipline

## Validation

- local repo inventory commands completed against `repos/fawxzzy-fitness`
- Vercel connector project read succeeded
- Vercel connector deployment read succeeded for `dpl_6jSoMDyVuCbbhP7Ep2dPremrVVtE`
- Vercel connector runtime-log queries succeeded for:
  - general production sample
  - `/auth/session-keepalive`
  - `/api/app-version`
