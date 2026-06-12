# Discord OS Infrastructure Separation Service-Role Readiness Guard Deployment Proof - 2026-06-12

- Date: `2026-06-12`
- Lane: `Discord OS Infrastructure Separation`
- Supporting lane: `Discord OS Feedback Workflow Canonicalization`
- Mode: `owner-repo readiness hardening and deployment proof without cutover`
- Marker posture: `hold at 99% / 72%`
- DiscordOS repo checkpoint: `codex/path-discipline-warning-slice-discordos@b145b30`
- Vercel deployment: `dpl_dDHaxkMcc4f4zd84z3RLBhcGNwhy`
- Vercel alias: `https://fawxzzy-discordos.vercel.app`
- Supabase project ref: `nwexsktuuenfdegzrbut`

## Objective

Continue the path toward `100%` by removing the last unsafe ambiguity in the readiness proof: a non-empty `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY` must no longer be enough. The readiness surface must prove the key metadata is both `role=service_role` and `ref=nwexsktuuenfdegzrbut`, so Fitness service-role keys, anon keys, publishable keys, malformed values, and placeholders all fail closed.

## Owner-Repo Change

DiscordOS commit `b145b30ef519a48fe0319d21acfb1f88a6b1383c` now includes:

- `api/readiness.js`
  - decodes JWT payload metadata without printing or returning secret values
  - reports `serviceRoleConfigured: true` only when the decoded role and project ref match the DiscordOS service-role contract
  - reports fail-closed diagnostic booleans:
    - `serviceRolePresent`
    - `serviceRoleRoleMatches`
    - `serviceRoleProjectRefMatches`
    - `serviceRoleReason`
- `tests/readiness.test.js`
  - covers missing key
  - covers malformed token
  - covers anon/publishable-style role mismatch
  - covers Fitness project service-role mismatch
  - covers exact DiscordOS service-role acceptance
- `package.json`
  - `npm run verify` now runs both feedback adapter verification and readiness tests
  - `vercel-build` now runs the full verification chain
- `docs/ops/discordos-service-role-readiness-guard-2026-06-12.md`
  - records the owner-repo boundary and remaining blocker

The test file was intentionally moved under `tests/` rather than `api/` before the final deployment, so Vercel exposes only `api/readiness` as a serverless function.

## Verification

Repo-local verification:

- command: `npm run verify`
- result: pass
- readiness tests: `5` passed, `0` failed

Vercel production build:

- deployment: `dpl_dDHaxkMcc4f4zd84z3RLBhcGNwhy`
- state: `READY`
- target: `production`
- GitHub commit: `b145b30ef519a48fe0319d21acfb1f88a6b1383c`
- build ran `npm run vercel-build`
- readiness tests: `5` passed, `0` failed
- serverless build output exposes `api/readiness`

Live readiness response:

- `ok: true`
- `supabaseProjectRefConfigured: true`
- `supabaseUrlConfigured: true`
- `serviceRoleConfigured: false`
- `serviceRolePresent: false`
- `serviceRoleRoleMatches: false`
- `serviceRoleProjectRefMatches: false`
- `serviceRoleReason: missing`
- `discordBotTokenConfigured: true`
- `liveCutover: false`
- `fitnessTrafficMoved: false`

Connector-backed proof:

- Supabase confirms the DiscordOS private schema tables remain present and RLS-enabled
- Supabase confirms Edge Function `discordos-readiness` remains `ACTIVE` with `verify_jwt=true`
- Vercel confirms deployment `dpl_dDHaxkMcc4f4zd84z3RLBhcGNwhy` is `READY`
- Vercel confirms the deployment metadata points at DiscordOS commit `b145b30ef519a48fe0319d21acfb1f88a6b1383c`
- GitHub confirms repo `fawxzzy/DiscordOS` remains accessible with admin/write permissions

ATLAS projection refresh:

- `stack.lock.yaml` repins `discordos` from `fb54f1cfda5ca96c3b0cfd79529930bf71d27747` to `b145b30ef519a48fe0319d21acfb1f88a6b1383c`
- `docs/registry/STACK-REPO-INVENTORY.json` regenerated
- `docs/audits/STACK-REPO-INVENTORY.md` regenerated

## Decision

`Discord OS Infrastructure Separation` holds at `99%`.

`Discord OS Feedback Workflow Canonicalization` holds at `72%`.

Why no `100%`:

- the readiness proof is now stronger, but the exact DiscordOS service-role secret is still absent
- no DiscordOS writer activation occurred
- no Fitness-to-DiscordOS traffic transfer occurred
- no rollback packet was executed
- no live workflow parity proof exists after transfer

This pass clears a false-positive risk, not the live cutover blocker.

## Exact Remaining Blocker Class

`DiscordOS-owned Supabase service-role provisioning for project nwexsktuuenfdegzrbut, followed by secret-backed writer activation, Fitness-to-DiscordOS traffic transfer, rollback proof, and live workflow parity proof`

## Next Executable Packet

`DiscordOS service-role provisioning and cutover parity packet`

Required first proof:

- `DISCORDOS_SUPABASE_SERVICE_ROLE_KEY` is provisioned to Vercel production with the exact DiscordOS project service-role key
- `/api/readiness` reports:
  - `serviceRoleConfigured: true`
  - `serviceRolePresent: true`
  - `serviceRoleRoleMatches: true`
  - `serviceRoleProjectRefMatches: true`
  - `serviceRoleReason: valid`
  - `discordBotTokenConfigured: true`

Only after that should writer activation, traffic transfer, rollback, and live parity proof execute.

## Health Check

- no Fitness files were modified
- no Fitness deployment changed
- no Fitness traffic moved
- no secret values were printed
- no `.env` file was created
- no service-role key was invented or substituted
- Vercel production readiness is hardened and live
- DiscordOS remains not cut over

## Rule

At the last percent, readiness must validate credential identity, not just credential presence.

## Pattern

missing service-role blocker -> readiness identity guard -> fail-closed tests -> production deployment -> exact remaining blocker preserved

## Failure Mode

`Presence-Only Secret Readiness`

If `serviceRoleConfigured` only means "some string exists", a Fitness service-role key, anon JWT, publishable key, malformed token, or placeholder can create a false `100%` claim.
