# Vercel Hobby Guardrail Report

- report id: `vercel-hobby-guardrail-fitness`
- generated at: `2026-06-18T03:51:55.386406+00:00`
- repo id: `fitness`
- repo path: `repos/fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- team id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- thresholds revalidated on: `2026-06-17`

## Summary

- total routes: `31`
- api routes: `22`
- auth routes: `5`
- dev routes: `4`
- force-dynamic routes: `29`
- explicit nodejs routes: `4`
- fetch sites: `34`
- internal fetch sites: `17`
- external-or-dynamic fetch sites: `17`

## Guardrail Posture

- deployment posture: `ok`
- route pressure posture: `watch`
- middleware pressure posture: `watch`
- integration pressure posture: `watch`
- hot route watch posture: `watch`

## Middleware

- present: `True`
- broad non-static matcher: `True`
- refresh-session call present: `True`
- public authless paths: `/api/app-version, /api/discord/interactions`

## Node Routes

- `/api/discord/interactions`
- `/api/spotify/oauth/callback`
- `/api/spotify/oauth/start`
- `/api/vercel/deployment-webhook`

## Watch Targets

- `/api/discord/interactions` refs: `1`
- `/auth/session-keepalive` refs: `4`
- `/api/app-version` refs: `2`
- `/auth/session-sync` refs: `4`
- `/api/history/sessions` refs: `1`
- `/api/history/exercises` refs: `1`
- `/api/sessions/start` refs: `1`
- `/api/sessions/resume` refs: `1`
- `/api/account/export` refs: `2`
- `/api/account/export/preview` refs: `1`
- `/api/migration/export` refs: `1`
- `/api/migration/import` refs: `1`
- `/api/migration/parity` refs: `1`
- `/api/discord/verification-token` refs: `2`
- `/api/ecosystem/fitness/pilot-shadow` refs: `1`
- `/api/exercise-info/` refs: `4`

## Notes

- This report is repo-local and no-secret by design; it does not read live billing counters.
- Threshold values are local checkpoint constants last revalidated on 2026-06-17.
- Watch postures are governance hints, not spend claims or upgrade recommendations.
