# Fitness Discord Access Path

Date: 2026-06-18

Purpose:
- Prevent future Codex chats from re-discovering the Discord access path problem when working on the Fitness feedback board or any Fitness feature card/thread.

Current verified state:
- Re-proved on `2026-06-30` that the canonical DiscordOS readiness check still returns `status: ready`:
  - `npm run ops:production-env:run -- npm run ops:discordos:env-readiness:json`
- Surfaced this path into the startup guidance actually read by future sessions:
  - `AGENTS.md`
  - `repos/fawxzzy-fitness/AGENTS.md`
  - `repos/DiscordOS/AGENTS.md`
- Future sessions should now hit the DiscordOS bot path first instead of reclassifying the task as blocked for lack of a generic Discord connector.

Canonical live-update path:
1. Enter `repos/DiscordOS`.
2. Prove operator env admission with:
   - `npm run ops:production-env:run -- npm run ops:discordos:env-readiness:json`
3. If readiness returns `status: ready`, use the admitted DiscordOS bot-backed publication path:
   - `npm run ops:discord:forum-card-release-check:json -- ...`
   - `npm run ops:discord:forum-card-lifecycle -- ... --apply`
   - use `ops:discord:update-*` commands for `#updates` posts when the task is an update post rather than a card lifecycle event
4. Only if DiscordOS readiness is blocked should the session fall back to browser or desktop automation checks.

Local Discord paths:
- Desktop updater: local-only `%LOCALAPPDATA%\Discord\Update.exe`
- Desktop app versions:
  - local-only `%LOCALAPPDATA%\Discord\app-1.0.9238\Discord.exe`
  - local-only `%LOCALAPPDATA%\Discord\app-1.0.9241\Discord.exe`
- User data root: local-only `%APPDATA%\discord`

Local board artifacts already present:
- `discord-fitness-board.yml`
- `discord-search-8ed05d76.yml`
- `discord-search-8ed05d76-closeout.md`

Why live feature-card updates were repeatedly misclassified:
- There is no installable first-class Discord connector/plugin surfaced directly to Codex in this environment.
- That absence was being mistaken for `no live Discord path exists`.
- The actual first-class live path is the admitted DiscordOS bot workflow in `repos/DiscordOS`, not a generic connector.

Important implication:
- The problem was not that Discord could not be located on disk.
- The primary gate is not browser control.
- The real gate is whether the current session can prove DiscordOS operator-env admission and then use the repo-owned bot publication commands.

Preferred future-chat workflow:
1. If the task is read-only lookup or context recovery, use the ATLAS-root local board artifacts in `discord-*.yml`.
2. If the task requires a live Discord edit, first run the DiscordOS readiness proof from `repos/DiscordOS`.
3. If readiness is `ready`, use the bot-backed DiscordOS publication commands and do not claim `blocked for lack of browser control`.
4. If DiscordOS readiness is blocked, then check for Chrome-session reuse or desktop-app automation as fallback paths.
5. If neither the admitted DiscordOS bot path nor a live browser/desktop path is available, do not claim the live card was updated; record the drafted update locally and state the exact blocked path.

What future chats should check first:
- Whether `npm run ops:production-env:run -- npm run ops:discordos:env-readiness:json` returns `status: ready`
- Which DiscordOS command class matches the task:
  - `ops:discord:forum-card-*` for feature card lifecycle updates
  - `ops:discord:update-*` for curated `#updates` posts
- Only after that, whether browser or desktop fallback is needed

Current known legacy fitness card:
- Board/channel: `fawxzzy-fitness`
- Feature card id: `8ed05d76`
- Card title seen in local export:
  - `Feature: Routines / Templates - Add per-day exercise templates for easy copy, paste, and modification`

Current active fitness card during the mobile normalization lane:
- Board/channel: `fawxzzy-fitness`
- Feature card id: `bea397b0`
- Forum thread id: `1521542046329077932`
- Title:
  - `Run a mobile UI normalization pass across every Fitness screen`
