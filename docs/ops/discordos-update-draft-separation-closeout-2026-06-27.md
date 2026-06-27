# DiscordOS Update Draft Separation Closeout

Date: 2026-06-27

## Scope

- finish separating DiscordOS production update-draft handling from Fitness-owned runtime paths
- keep the update-draft flow fully hosted on DiscordOS infrastructure with no local worker dependency
- restore the hosted DiscordOS command surface and deployment-triggered update-draft creation

## Landed

- DiscordOS now owns dedicated hosted runtime packages under DiscordOS-owned paths:
  - `src/extractions/discordos-feedback-runtime/`
  - `src/extractions/discordos-update-draft-runtime/`
- DiscordOS slash command registration includes the hosted update-draft command set:
  - `/update-latest`
  - `/update-publish`
  - `/update-skip`
- DiscordOS now stores update drafts in its own Supabase project `nwexsktuuenfdegzrbut`:
  - table: `discordos.discord_update_drafts`
  - RPC wrappers:
    - `public.discordos_list_update_drafts`
    - `public.discordos_get_update_draft_by_deployment_id`
    - `public.discordos_get_update_draft_by_id`
    - `public.discordos_get_update_draft_by_prefix`
    - `public.discordos_insert_update_draft`
    - `public.discordos_update_update_draft`
- DiscordOS edge bridge `discordos-update-drafts` was deployed live as version `5` and uses RPC-backed access instead of direct private-schema REST access.
- Vercel deployment webhook ownership now lives on the canonical DiscordOS project `fawxzzy-discordos`:
  - project id: `prj_C2RSEa34OblHfhuEpVChRQQZSjuG`
  - active webhook id: `account_hook_HmPBqjMDiA8xwiTnnIuZeOnr`
  - active webhook URL: `https://fawxzzy-discordos.vercel.app/api/discord-interactions`
- The webhook handler was intentionally merged into the existing Discord interactions API route because Vercel Hobby rejected a 13th Serverless Function. This preserves hosted behavior without adding another function slot.
- Old webhook ownership was cleaned up:
  - removed stale DiscordOS webhook pointing at `/api/vercel/deployment-webhook`
  - removed old Fitness-local deployment webhook

## Verification

- local regression cluster passed after the route merge and DiscordOS-owned path rename:
  - `node --test tests\\discordos-feedback-runtime.test.js tests\\discordos-update-draft-runtime.test.js tests\\discord-interactions-api.test.js tests\\vercel-deployment-webhook.test.js tests\\discord-message-commands-poll-cron.test.js tests\\discordos-computa-runtime.test.js`
- live Supabase migrations applied successfully:
  - `discordos_update_drafts_runtime`
  - `discordos_update_draft_rpcs`
- live edge bridge proof passed from DiscordOS production env:
  - `action = list_latest` returned `200`
  - `action = find_by_deployment_id` returned `200`
  - `action = find_by_id` returned `200`
- canonical production Vercel deployment succeeded:
  - deployment id: `dpl_8w23hqk76rV2q5gThBbjZAvnwf6A`
  - aliased production URL: `https://fawxzzy-discordos.vercel.app`
- hosted guild command registration succeeded:
  - `Registered 9 DiscordOS guild commands.`
- manual end-to-end webhook proof succeeded against production:
  - signed webhook POST target: `https://fawxzzy-discordos.vercel.app/api/discord-interactions`
  - proof deployment id: `dpl_manual_proof_1782595547555`
  - webhook response: `200`, `created: true`
  - stored draft id: `47c5bb41-d3b6-4c3f-915f-b3e828e30a41`
  - proof draft was then marked `ignored` with reason `manual hosted webhook proof cleanup`
- post-rename production proof also succeeded after the DiscordOS-owned extraction path rename:
  - proof deployment id: `dpl_manual_proof_rename_1782595958383`
  - stored draft id: `953165c2-1734-4f05-b1f7-64d26ba9e8a8`
  - cleanup status: draft marked `ignored` with reason `manual rename proof cleanup`

## Notes

- DiscordOS production Vercel env now carries the DiscordOS-specific webhook/project routing values and does not rely on the old Fitness service-role secret.
- The update-draft hosted path is now DiscordOS-only:
  - Vercel webhook -> DiscordOS production route -> DiscordOS Supabase edge bridge -> DiscordOS RPC wrappers -> DiscordOS draft table
