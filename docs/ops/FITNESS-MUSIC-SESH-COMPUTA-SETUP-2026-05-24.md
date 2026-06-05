# Fitness Music Sesh Computa Setup

Date: 2026-05-24
Owner: ATLAS / Fitness
Mode: governed Discord/operator rollout

## Scope

- Rename the live Discord-facing Spotify Club setup surface to Music Sesh.
- Add commander-gated `computa setup music sesh` message-command support.
- Update public and owner Computa command cards to advertise the Music Sesh setup path.
- Keep backward compatibility for the legacy slash setup name during rollout.
- Reset the stale public setup post and align the public channel name with Music Sesh.

## Repo change

- Fitness repo commit: `0521de73a48ad09a786bf7c842f3132992b281a7`
- Branch: `main`

Key code surfaces:

- `repos/fawxzzy-fitness/src/app/api/discord/interactions/route.ts`
- `repos/fawxzzy-fitness/src/lib/discord/interactions.ts`
- `repos/fawxzzy-fitness/scripts/discord-feedback-gateway-worker.mjs`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-FEEDBACK.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-SPOTIFY-CLUB.md`

## Live rollout

Production deploy:

- Deployment id: `dpl_43KCRRdqERtYim7dQ6F5pzf6uWhf`
- Production alias: `https://fawxzzy-fitness-local.vercel.app`
- Ready deployment URL: `https://fawxzzy-fitness-oj4r13btp-fawxzzy.vercel.app`

Discord command registration:

- Guild command registration rerun successfully.
- Live setup slash command now registers as `setup-music-sesh`.
- Legacy `setup-spotify-club` remains accepted in the route during the transition.

Public Music Sesh surface:

- Channel id `1506131171208200302` renamed from `spotify-club` to `music-sesh`.
- Old setup post deleted: `1506416009412743278`
- New setup post created: `1508156385848721421`
- Live panel title: `Music Sesh`
- Live launcher button: `Open Music Sesh Controls`

Computa command cards in `#main`:

- Public Computa card updated in place: `1508034894260080671`
- Owner Computa card updated in place: `1508143826764828725`
- Older duplicate owner card deleted: `1508033258850353302`

## Runtime rules now enforced

- `computa setup music sesh` is a commander-gated main-channel trigger.
- `computa music sesh setup` is a supported alias.
- Legacy aliases `computa setup spotify club` and `computa spotify club setup` still resolve during transition.
- Music Sesh is now the live public product name across the panel, lobby, queue, and control-hub copy.
- The runtime surface stays a standard text channel; no setup-only side channel remains canonical.

## Verification

Repo verification:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions.test.ts`
- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `npm run verify`
- `npm run sanity:quick`
- `npm run build`

Live verification:

- Guild commands confirm `setup-music-sesh`.
- Public channel confirms `music-sesh`.
- Public panel confirms title `Music Sesh`.
- Public panel confirms button `Open Music Sesh Controls`.

## Decision

The old Spotify Club setup post was treated as stale runtime residue and replaced in place after the public channel was renamed. The public runtime surface remains the renamed `music-sesh` channel so the new Computa setup path has a live target instead of deleting the active product surface outright.
