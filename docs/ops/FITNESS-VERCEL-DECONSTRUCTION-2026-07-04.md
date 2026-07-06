# Fitness Vercel Deconstruction Receipt - 2026-07-04

## Scope

Resolve duplicate Vercel project confusion for `fawxzzy/fawxzzy-fitness` without printing, copying, or moving secret values.

## Canonical Local Link

ATLAS-relative local link file:

`repos/fawxzzy-fitness/.vercel/project.json`

```json
{
  "projectId": "prj_rtlFVOMFAWCRoJ3SQjHloi89881K",
  "orgId": "team_CMJn7MvzFZZBnhNnjVUZF2RD",
  "projectName": "fawxzzy-fitness"
}
```

## Keep Project

- Project: `fawxzzy-fitness`
- Project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- Owner/scope: `fawxzzy`
- Framework: `nextjs`
- Root directory: repository root
- Formal GitHub link after repair: `fawxzzy/fawxzzy-fitness`
- Production branch: `main`
- Project domain: `fawxzzy-fitness-local.vercel.app`
- Recent production deployment alias observed: `fawxzzy-fitness-m2l0wvzzw-fawxzzy.vercel.app`

### Keep Project Environment Inventory

Only key names, target scopes, and storage types were inspected. No secret values were printed or copied.

Observed required environment families on the keep project:

- Stripe: `STRIPE_*`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- Supabase: `NEXT_PUBLIC_SUPABASE_*`, `SUPABASE_SERVICE_ROLE_KEY`, legacy migration keys
- Discord: `DISCORD_*`, `DISCORDOS_*`
- Cron: `CRON_SECRET`
- Spotify: `SPOTIFY_*`
- Vercel deployment hooks: `VERCEL_*`
- App/operator: `FITNESS_ZAC_EMAIL`

## Deconstruct Candidate

- Project: `fawxzzy-fitness-local`
- Project id: `prj_TG5iYMBrruEIRbuJGyOLBGcdJqOS`
- Owner/scope: `fawxzzy`
- Framework: `nextjs`
- Root directory: repository root
- Formal GitHub link before deconstruction: `fawxzzy/fawxzzy-fitness`
- Production branch before deconstruction: `main`
- Project domain: `fawxzzy-fitness-local-six.vercel.app`
- Recent deployment aliases observed:
  - `fawxzzy-fitness-local-qyh7dqjxc-fawxzzy.vercel.app`
  - `fawxzzy-fitness-local-bzi8nnwu2-fawxzzy.vercel.app`
- Environment variables returned by API: none
- Custom/user-facing domains returned by project-domain API: none

## Actions

1. Confirmed local repo remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`.
2. Confirmed local repo branch: `main`.
3. Confirmed local Vercel link points to `fawxzzy-fitness`.
4. Confirmed two Vercel fitness projects existed:
   - keep: `fawxzzy-fitness`
   - duplicate: `fawxzzy-fitness-local`
5. Connected GitHub repo `https://github.com/fawxzzy/fawxzzy-fitness.git` to the keep project.
6. Re-verified keep project now has formal GitHub link to `fawxzzy/fawxzzy-fitness` on `main`.
7. Confirmed duplicate project has no env vars and only generated Vercel project domain before removal.
8. Deleted duplicate project `fawxzzy-fitness-local` / `prj_TG5iYMBrruEIRbuJGyOLBGcdJqOS`.
9. Re-verified only `fawxzzy-fitness` remains in Vercel project list for the fitness app.
10. Re-verified local `.vercel/project.json` still points to `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`.
11. Re-verified keep project GitHub link is `fawxzzy/fawxzzy-fitness` with production branch `main`.
12. Re-verified keep project domain remains `fawxzzy-fitness-local.vercel.app`.
13. Re-verified keep project env inventory remains present by key count: `62`.
14. Re-verified duplicate project lookup returns `Project not found (404)`.

## Safety Notes

- Secret values were not printed, copied, or moved.
- The duplicate project name was not used as the source of truth. Project id, local `.vercel/project.json`, env inventory, domains, and deployment metadata were used.
- `localhost:3002` and `127.0.0.1:3002` are separate browser origins; this was handled as local browser state, not a Vercel deployment/link issue.

## Final State

- Main/only Fitness Vercel project: `fawxzzy-fitness` / `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- Removed duplicate project: `fawxzzy-fitness-local` / `prj_TG5iYMBrruEIRbuJGyOLBGcdJqOS`
- GitHub production source: `fawxzzy/fawxzzy-fitness` on `main`
- Local review origin standard: `http://localhost:3002`
