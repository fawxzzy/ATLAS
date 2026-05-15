# Fawxzzy Fitness Discord Verification Handoff

Date:
- 2026-05-15

Workspace:
- `repos/fawxzzy-fitness`

Canonical implementation proof:
- Fitness PR #21: Fitness-hosted Discord interactions endpoint

Scope covered in this receipt:
- project goal and final architecture
- build history and decision sequence
- implementation phases
- production environment checklist
- operator test checklist
- failure modes and reusable doctrine

## Goal

Build Discord server access verification where users must be signed up / authenticated in Fawxzzy Fitness before gaining Discord access.

## Final architecture

Final system:

```text
Fitness app authenticated session
-> generates short-lived one-time Discord verification token
-> user pastes token into Discord modal
-> Discord sends signed interaction to Fitness app
-> Fitness verifies Discord signature
-> Fitness consumes token once
-> Fitness grants Discord Verified role through Discord REST API
```

## Key decisions

- Rejected email-only verification because email knowledge is not identity proof.
- Built one-time token flow instead.
- Built Gateway bot first for speed.
- Discovered Gateway bot requires an always-running process.
- Considered always-on worker hosting.
- Chose final Option B: Fitness-hosted Discord HTTP Interactions Endpoint.
- Kept Discord as consumer of Fitness identity proof, not identity authority.
- Kept token ephemeral and display-once in UI state.
- Kept old bot repo only as fallback/debug, not active path.

## Implementation phases

### Phase 1: Fitness token backend

- Supabase `discord_verification_tokens` table
- token hash storage only
- token pepper
- bot shared secret for legacy verify endpoint
- atomic token consume function
- `/api/discord/verification-token`
- `/api/discord/verify`

### Phase 2: Discord Gateway bot prototype

- Discord developer app
- roles/channels
- `/setup-verify`
- verify button
- token modal
- bot calls Fitness verify endpoint
- role assignment

### Phase 3: Fitness Settings UI

- `Settings -> Account -> Discord Access`
- Generate token
- readonly token field
- right-side copy button
- expiry text
- no localStorage / URL / profile persistence

### Phase 4: Option B HTTP interactions endpoint

- `/api/discord/interactions`
- Ed25519 signature verification before JSON parse
- PING returns `{ type: 1 }`
- `/setup-verify` handled by Fitness
- verify button opens modal
- modal consumes token
- Fitness grants Verified role through Discord REST
- old local bot no longer required

### Phase 5: Production blockers fixed

- Endpoint initially redirected to `/login` due auth middleware / auth-session classification.
- Patched Discord server routes as authless server routes.
- Hardened malformed signatures to fail closed with `401`.
- Verified unsigned `POST` returns `{ error: "Invalid request signature." }` with HTTP `401`.
- Discord Developer Portal endpoint was accepted after fix.

## Env vars checklist

Fitness production:

- `DISCORD_PUBLIC_KEY`
- `DISCORD_APPLICATION_ID`
- `DISCORD_GUILD_ID`
- `DISCORD_VERIFY_CHANNEL_ID`
- `DISCORD_VERIFIED_ROLE_ID`
- `DISCORD_UNVERIFIED_ROLE_ID` optional
- `DISCORD_BOT_TOKEN`
- `DISCORD_VERIFICATION_BOT_SECRET`
- `DISCORD_VERIFICATION_TOKEN_PEPPER`
- `SUPABASE_SERVICE_ROLE_KEY`

Manual Discord portal:

- Interactions Endpoint URL:
  `https://<fitness-domain>/api/discord/interactions`

## Operational test checklist

- Generate token in `Fitness Settings -> Account`.
- Click Discord verify button.
- Paste token.
- Verified role is granted.
- Reusing token fails.
- Expired token fails.
- Local Gateway bot is stopped and flow still works.
- Bot role is above Verified role.
- Discord app has Manage Roles.

## Failure modes

Rule: Email knowledge is not identity proof.
Pattern: Fitness session creates proof; Discord consumes proof.
Failure Mode: Email-only verification lets someone unlock Discord using another member's email.

Rule: Gateway bots require an always-running process.
Pattern: Fast prototype can use a Gateway bot, but production availability needs either worker hosting or signed HTTP interactions.
Failure Mode: Local-only bot works during setup, then breaks when the terminal closes.

Rule: Unsigned Discord interactions must never reach role-grant logic.
Pattern: Verify Discord Ed25519 signature before parsing or executing payloads.
Failure Mode: Accepting unsigned interaction payloads lets arbitrary callers attempt Discord role grants.

Rule: Verification tokens are display-once session UI state, not account data.
Pattern: Generate token from authenticated Fitness session, show readonly copy box, then consume once.
Failure Mode: Persisting tokens turns short-lived proof into reusable account state.

Rule: Auth middleware must not redirect Discord server routes.
Pattern: Server-to-server interaction routes are explicit authless exceptions protected by signature/secret verification.
Failure Mode: Discord endpoint verification fails because the app redirects signed PING probes to /login.

## References

Reference:
- Fitness PR #20: Discord verification token flow
- Fitness PR #21: Fitness-hosted Discord interactions endpoint
- Production endpoint path: `/api/discord/interactions`
- Token generation path: `Settings -> Account -> Discord Access`

## High-signal summary

- Rule: The source app owns identity; Discord consumes proof.
- Pattern: Authenticated app session -> one-time token -> signed Discord interaction -> token consume -> role grant.
- Failure Mode: Local-only Gateway bots make verification unavailable when the process dies.
