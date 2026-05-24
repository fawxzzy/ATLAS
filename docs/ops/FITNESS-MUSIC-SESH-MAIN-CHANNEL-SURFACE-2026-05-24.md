# Fitness Music Sesh Main Channel Surface

Date: 2026-05-24
Owner: ATLAS / Fitness
Mode: governed Discord/runtime surface correction

## Scope

- Remove the dedicated public `music-sesh` text channel as a required runtime surface.
- Make Music Sesh setup follow the same source-channel model as feedback setup.
- Keep `computa setup music sesh` and `/setup-music-sesh` as the approved setup entrypoints.
- Move the canonical live Music Sesh panel into `#main`.

## Repo change

- Fitness repo commit: `5ad340e0df6e62c4afcfaeba223330d38861578a`
- Branch: `main`

Key code surfaces:

- `C:\ATLAS\repos\fawxzzy-fitness\src\app\api\discord\interactions\route.ts`
- `C:\ATLAS\repos\fawxzzy-fitness\src\lib\discord\interactions-route.test.ts`
- `C:\ATLAS\repos\fawxzzy-fitness\docs\ops\FITNESS-DISCORD-SPOTIFY-CLUB.md`
- `C:\ATLAS\repos\fawxzzy-fitness\docs\ops\FITNESS-DISCORD-FEEDBACK.md`

## Runtime behavior

- `computa setup music sesh` now refreshes the Music Sesh panel in the channel where the command is used.
- `/setup-music-sesh` now refreshes the Music Sesh panel in the invoking channel when Discord provides one.
- `DISCORD_SPOTIFY_CLUB_CHANNEL_ID` is now only a fallback when no source channel is available.
- Successful source-channel setup cleans older Music Sesh panel posts and deletes the legacy dedicated launcher channel when it still exists.

## Live rollout

Production deploy:

- Deployment id: `dpl_GrnkPnh5xXWts6cCCqqD2mdbtTr7`
- Production alias: `https://fawxzzy-fitness-local.vercel.app`
- Ready deployment URL: `https://fawxzzy-fitness-ajldsqei0-fawxzzy.vercel.app`

Live Discord surface move:

- Main channel id: `1504674484068552784`
- Deleted dedicated Music Sesh channel id: `1506131171208200302`
- Deleted old panel message id: `1508156385848721421`
- New canonical main-channel panel message id: `1508160798147608816`
- Latest lobby row id: `7fc341b3-e6ed-463c-9b53-b4a54e813690`

## Verification

Repo verification:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`
- `npm run sanity:quick`
- `npm run build`

Live verification:

- Guild channel inventory confirms no `music-sesh` text channel remains.
- `#main` contains the canonical `Music Sesh` panel.
- Latest `discord_spotify_lobbies` row points to:
  - `panel_channel_id = 1504674484068552784`
  - `panel_message_id = 1508160798147608816`

## Decision

Music Sesh now follows the same public setup pattern as feedback setup: the setup command posts or refreshes the canonical panel in the active source channel instead of depending on a dedicated public launcher channel. The removed `music-sesh` text channel is now treated as retired launcher residue rather than a required product surface.
