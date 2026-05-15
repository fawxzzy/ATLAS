# Discord Fitness Verification Ops

## Purpose

Short operator runbook for app-gated Discord verification where `fawxzzy-fitness` is the identity authority and Discord consumes signed proof.

## Operator flow

1. Create the Discord app in the Discord Developer Portal.
2. Create the server roles and channels:
   `Verified`
   `Unverified` if used
   verify channel
3. Add the Fitness production env vars:
   `DISCORD_PUBLIC_KEY`
   `DISCORD_APPLICATION_ID`
   `DISCORD_GUILD_ID`
   `DISCORD_VERIFY_CHANNEL_ID`
   `DISCORD_VERIFIED_ROLE_ID`
   `DISCORD_UNVERIFIED_ROLE_ID` optional
   `DISCORD_BOT_TOKEN`
   `DISCORD_VERIFICATION_BOT_SECRET`
   `DISCORD_VERIFICATION_TOKEN_PEPPER`
   `SUPABASE_SERVICE_ROLE_KEY`
4. Add the Supabase migration for `discord_verification_tokens` with hash-only storage and one-time consume semantics.
5. Set the Discord Interactions Endpoint URL to:
   `https://<fitness-domain>/api/discord/interactions`
6. Register `/setup-verify` if needed.
7. Test the token flow end to end.

## Test token flow

1. Generate a token in `Settings -> Account -> Discord Access`.
2. Click the Discord verify button.
3. Paste the token into the Discord modal.
4. Confirm the Verified role is granted.
5. Confirm reused tokens fail.
6. Confirm expired tokens fail.
7. Confirm the local Gateway bot is stopped and the flow still works.

## Debug matrix

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Discord rejects endpoint verification | Public key mismatch, auth redirect, endpoint not deployed, or malformed signature handling | Verify `DISCORD_PUBLIC_KEY`, confirm `/api/discord/interactions` is live, confirm unsigned `POST` returns `401` with `{ error: "Invalid request signature." }`, confirm no redirect to `/login` |
| Verify button works but modal submit fails | Token invalid, expired, reused, or consume path broken | Generate a fresh token, verify short TTL logic, verify one-time consume behavior |
| Modal submit succeeds but role is not granted | Missing bot token, missing Manage Roles, or role hierarchy issue | Verify `DISCORD_BOT_TOKEN`, confirm the app has Manage Roles, confirm bot role is above Verified |
| Flow only works while local bot is running | Old Gateway path is still in use | Confirm production path is Fitness-hosted `/api/discord/interactions` and stop the local bot |
| Discord endpoint was previously accepted but later fails | Route classification or deploy drift | Reconfirm authless server-route exception and redeploy after env or middleware changes |

## Doctrine

- Rule: The source app owns identity; Discord consumes proof.
- Rule: Email knowledge is not identity proof.
- Rule: Unsigned Discord interactions must never reach role-grant logic.
- Pattern: Authenticated app session -> one-time token -> signed Discord modal submit -> token consume -> role grant.
- Failure Mode: Local Gateway bots, email-only checks, or auth middleware redirects make Discord verification unavailable or unsafe.
