# DiscordOS Command Restoration Closeout

Date: 2026-06-27

## Scope

- restore DiscordOS-owned feedback slash commands in the hosted bot runtime
- keep message-command execution fully hosted without any local process
- correct production deployment back onto the canonical `fawxzzy-discordos` Vercel project

## Landed

- DiscordOS interaction routing now admits these application commands directly in `C:\doscut`:
  - `/computa`
  - `/setup-feedback`
  - `/feedback`
  - `/feedback-status`
  - `/feedback-completion-review`
  - `/feedback-withdraw`
- DiscordOS guild command registration now publishes the full six-command set from the canonical DiscordOS project.
- DiscordOS feedback slash handlers now live in the extracted runtime package instead of the Fitness repo.
- The attempted Vercel minute cron path was rejected on 2026-06-27 because the project is on a Hobby plan and Vercel only allows daily cron there.
- Hosted message-command polling was moved to Supabase instead:
  - enabled `pg_cron`
  - enabled `pg_net`
  - added `discordos_private.trigger_message_command_poll(base_url text, bearer_token text)`
  - created live cron job `discordos_message_commands_poll` on `* * * * *`
- The canonical production deploy was corrected back to:
  - `https://fawxzzy-discordos.vercel.app`

## Verification

- local targeted tests passed:
  - `node --test tests\\discordos-feedback-runtime.test.js tests\\discord-interactions-api.test.js tests\\discord-message-commands-poll-cron.test.js tests\\discordos-computa-runtime.test.js`
- production Vercel deploy passed build verification on project `fawxzzy-discordos`
- Discord guild command registration completed with `Registered 6 DiscordOS guild commands.`
- direct hosted poll smoke returned `{"ok":true,"authMode":"secret","processed":[]}`
- live Supabase cron readback showed:
  - `jobname = discordos_message_commands_poll`
  - `schedule = * * * * *`
  - `active = true`

## Notes

- A stray deploy briefly landed on a separate Vercel project named `doscut`; the canonical deploy was immediately corrected back onto `fawxzzy-discordos`.
- The stray `doscut` Vercel project was removed after the canonical DiscordOS project was re-aliased.
- Fitness still contains historical Discord code residue, but the hosted command/runtime ownership moved further into DiscordOS during this pass.
