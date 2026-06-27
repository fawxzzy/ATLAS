# Fitness Discord Access Path

Date: 2026-06-18

Purpose:
- Prevent future Codex chats from re-discovering the Discord access path problem when working on the fitness feedback board and feature card `8ed05d76`.

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

Why live feature-card updates failed in this Codex session:
- There is no installable Discord connector/plugin available to Codex in this environment.
- The actual available install candidates did not include Discord.
- Because of that, Codex had only local filesystem access plus browser/automation fallbacks, not a first-class authenticated Discord tool.

Important implication:
- The problem was not that Discord could not be located on disk.
- The problem was that Codex lacked a live authenticated Discord control path.

Preferred future-chat workflow:
1. If the task is read-only lookup or context recovery, use the ATLAS-root local board artifacts in `discord-*.yml`.
2. If the task requires a live Discord edit and Chrome control tools are available in the session, prefer using the existing Chrome/Discord web session so authentication can be reused.
3. If Chrome-session control is unavailable but desktop-app automation is available, target the local Discord install paths above.
4. If neither live browser control nor desktop automation is available, do not claim the live card was updated; record the drafted update locally and state the missing capability explicitly.

What future chats should check first:
- Whether a live Chrome/browser control tool is available in the session
- Whether the user is already authenticated in Discord on the browser route being controlled
- Whether the session has only the local export files and no live control path

Current known fitness card:
- Board/channel: `fawxzzy-fitness`
- Feature card id: `8ed05d76`
- Card title seen in local export:
  - `Feature: Routines / Templates — Add per-day exercise templates for easy copy, paste, and modification`
