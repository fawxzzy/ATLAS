# ATLAS MAIN — FAWXZZY PLATFORM IDENTITY, AUTH, BILLING, AND SUPABASE CONSOLIDATION PROGRAM

**Date:** 2026-07-16  
**Operator authority:** Zachariah / Fawxzzy  
**Coordination owner:** ATLAS Main  
**Owner threads to inspect and coordinate:** `ATLAS MAIN`, `FAWXZZY MESSAGES`, `Fitness`, `Mazer`, `Socials OS`, `FawxzzyWeb`, plus the active DiscordOS, Foundation, Lifeline, `_stack`, Playbook, and repository/project tasks discoverable from the workspace.

---

## 0. Operator intent

Fawxzzy is now the platform.

`fawxzzy.com` is the canonical public entry point. FawxzzyWeb owns the public website and contains the former Trove capability as its internal `/apps` catalog. Fitness, Mazer, DiscordOS, Socials OS, and future products remain distinct owner systems, but public users should experience one coherent Fawxzzy identity, account, billing, and entitlement layer.

The intended user experience is:

- A user creates one Fawxzzy account.
- That same account can be used at:
  - `fawxzzy.com`
  - `fitness.fawxzzy.com`
  - `mazer.fawxzzy.com`
  - future Fawxzzy services
- Each service may ask for service-specific onboarding only when the user first enters that service.
- Shared account data, verified identity, billing customer identity, subscriptions, entitlements, and preferences are reusable across services.
- Service-owned data remains clearly bounded.
- A user should not create separate unrelated Supabase identities for every Fawxzzy service.
- Device convenience must use explicit, secure “remember this device,” passkey/WebAuthn, and session mechanisms. Do **not** build covert browser/device fingerprinting.

The operator asked ATLAS Main to:

1. Read and understand all currently open owner threads and their full relevant histories.
2. Determine exactly what each thread has done, is doing, and plans to do.
3. Pause or constrain conflicting work where required.
4. Allow non-conflicting work to continue.
5. Coordinate and execute the platform migration through the correct owner threads and repositories.
6. Keep ATLAS Main as the canonical coordination and evidence surface.
7. Notify every affected thread when it is safe to resume.
8. Retire old Supabase projects only after the new platform is fully proven and after explicit final deletion approval.

Do not make the operator manually repeat context already available in threads, repositories, connected services, cards, receipts, or documentation.

---

# 1. Critical correction and target architecture

Do **not** create a fourth blank Supabase project by default.

The preferred platform seed is the existing **FawxzzyFitness** Supabase project because it already contains the largest real user population, shared-profile data, billing mappings, entitlements, and extensive production migrations.

### Live baseline observed on 2026-07-16 — reverify before execution

#### FawxzzyFitness

- Project ID/ref: `lpswxoyfniocuhljgzbc`
- Region: `us-west-2`
- Status observed: `ACTIVE_HEALTHY`
- Auth users observed: 95
- Profiles observed: 75
- Existing Fitness session/routine/exercise data
- Existing Stripe/billing state:
  - billing customers: 11
  - billing purchases: 15
  - user entitlements: 9
- Existing Discord integration/feedback/update/moderation/music tables
- Large established migration history

#### Mazer

- Project ID/ref: `geknvnrmktchljnyddwp`
- Region: `us-west-2`
- Status observed: `ACTIVE_HEALTHY`
- Auth users observed: 6
- Domain tables observed:
  - Mazer progression states
  - Mazer profiles
  - Mazer AI progression states
  - Mazer cycle receipts
- Mazer cycle receipts observed: 1,184

#### DiscordOS

- Project ID/ref: `nwexsktuuenfdegzrbut`
- Region: `us-east-1`
- Status observed: `ACTIVE_HEALTHY`
- Auth users observed: 0
- Custom `discordos` schema contains active runtime, feedback, board, moderation, music-session, and update-draft state
- Six active Edge Functions were observed
- Existing migrations and extraction/live-transfer contracts indicate intentional DiscordOS ownership and separation work

These values are a starting receipt only. Re-read live truth and record the exact current counts and configuration.

## Preferred end state

### Supabase project 1 — `FawxzzyPlatform`

Rename or repurpose the current FawxzzyFitness Supabase project as the canonical public platform project while preserving its project ref, region, users, history, and rollback path.

It owns:

- Supabase Auth for all public Fawxzzy services
- shared account/profile data
- service membership and onboarding state
- central billing customer identity
- products, prices, subscriptions, purchases, and entitlements
- Fitness-owned schema/data
- Mazer-owned schema/data
- shared public-platform integrations
- audit and migration identity maps

### Supabase project 2 — `DiscordOS`

Keep DiscordOS physically separate by default.

Reason:

- DiscordOS is an internal/community/control-plane service.
- It has active private runtime state and Edge Functions.
- Its trust model and secrets differ from public applications.
- Supabase secret/service-role keys bypass RLS across an entire project.
- Combining it into the public user project would expand blast radius and could undo existing separation work.

DiscordOS should integrate through explicit contracts, signed events, scoped APIs/RPCs, and stable identity mappings.

### Decision gate

ATLAS may propose merging DiscordOS physically into `FawxzzyPlatform` only if it proves all of the following:

1. No conflict with current accepted separation plans and receipts.
2. No service-role or secret-key path gives DiscordOS unrestricted access to public platform data.
3. Equivalent least-privilege isolation is proven.
4. Edge Functions, cron, runtime health, board state, feedback, moderation, and music state can migrate without regression.
5. Region and latency effects are acceptable.
6. Failure/blast-radius analysis supports the merge.
7. Rollback is proven.
8. The operator explicitly approves this deviation.

Without that proof, the final target is **two projects**, not one.

The old Mazer project should be retired after migration. The old Fitness identity becomes the renamed/repurposed platform project rather than being deleted. DiscordOS remains unless the decision gate above is explicitly passed.

---

# 2. ATLAS ownership and execution boundary

ATLAS Main is the canonical coordinator, not the universal implementation repo.

ATLAS Main must:

- read all relevant thread histories
- build the truth map
- establish migration leases and holds
- reconcile plans
- dispatch bounded owner packets
- track dependencies
- ingest receipts
- detect drift
- control cutover gates
- publish operator-facing status
- notify threads to resume
- preserve evidence and restart order

ATLAS Main must not silently implement owner-repo changes itself.

Use the existing architecture:

- **FawxzzyWeb:** public account portal, auth UX, cross-service navigation, website
- **Fitness:** Fitness schema, Fitness application integration, Fitness migrations
- **Mazer:** Mazer schema, Mazer application integration, Mazer migrations
- **DiscordOS:** Discord/community/control-plane data and integration contracts
- **Foundation:** secret references, credentials, security primitives, platform config contracts
- **Lifeline:** supervision and runtime restoration
- **`_stack`:** governed jobs, single-writer execution, receipts, verification
- **Socials OS:** public distribution/account messaging affected by the migration
- **Playbook:** Rules, Patterns, Failure Modes, Decisions, runbooks
- **ATLAS:** coordination, graph, markers, receipts, divergence, truth

If a shared backend/migration repository does not already exist, propose a new owner repo such as:

- `fawxzzy-platform`

This repo would own the canonical Supabase migration ledger, shared schemas, generated types, compatibility contracts, migration tools, and platform integration tests.

Do not put the shared platform database under FawxzzyWeb merely because the website is the public entry point.

Do not put product-owned application behavior in ATLAS or Foundation.

---

# 3. Required first action — read every active thread and establish a migration control plane

Inspect the complete relevant histories and current states of:

- `ATLAS MAIN`
- `FAWXZZY MESSAGES`
- `Fitness`
- `Mazer`
- `Socials OS`
- `FawxzzyWeb`
- DiscordOS owner thread/task
- Foundation owner thread/task
- Lifeline owner thread/task
- `_stack` owner thread/task
- Playbook owner thread/task
- current FawxzzyWeb project tasks
- all active Supabase-related tasks, PRs, worktrees, and cards

For each surface, extract:

- current objective
- completed work
- active work
- next planned work
- current branch/worktree
- open PRs
- dirty state
- active writers
- Supabase project used
- database migrations in flight
- auth work in flight
- billing work in flight
- storage work in flight
- Edge Function work in flight
- environment/configuration work in flight
- deployment state
- collision risk
- safest checkpoint
- what may continue
- what must pause

Create a canonical migration registry with stable identities for:

- source projects
- target project
- schemas
- tables
- functions
- triggers
- policies
- storage buckets
- Edge Functions
- cron jobs
- secrets
- applications
- environments
- users
- identity mappings
- billing mappings
- migration runs
- validation receipts
- cutover status
- rollback status

---

# 4. Thread hold and continuation protocol

Send a clear coordination message to every affected thread.

## Hold name

`FAWXZZY PLATFORM MIGRATION — DATABASE/AUTH WRITE HOLD`

## Work that must pause or checkpoint

Pause new production mutations involving:

- Supabase schemas
- tables
- columns
- constraints
- indexes
- functions
- triggers
- RLS policies
- grants
- Auth settings
- identity creation semantics
- OAuth callback configuration
- billing schema
- entitlement schema
- payment webhooks
- Storage buckets/policies
- Realtime configuration
- Edge Functions
- cron jobs
- Supabase project secrets
- Supabase URLs and keys
- generated database types that would conflict with migration

Do not discard work.

Each owner thread must:

1. Reach the safest bounded checkpoint.
2. Commit or preserve all work.
3. Report branch/worktree/PR/commit.
4. Report planned database/auth mutations.
5. Report whether it can continue read-only or in unrelated paths.
6. Acknowledge the hold.

## Work that may continue

Allow work to continue when it is proven non-conflicting, such as:

- isolated UI work
- content work
- documentation not asserting stale DB truth
- read-only analysis
- tests against frozen interfaces
- Socials OS publishing unrelated to account migration
- ATLAS main/root coordination work
- other owner work with exact unchanged database/auth boundaries

Do not freeze the whole ecosystem without evidence.

## One-writer rule

During migration:

- one canonical database migration ledger
- one admitted production schema writer
- one cutover coordinator
- no dashboard-only schema edits
- no competing `db push`
- no hidden manual SQL
- every mutation represented by committed migration files and receipts

---

# 5. Shared identity architecture

## 5.1 Canonical identity

Use the existing FawxzzyFitness Auth population as the initial canonical identity population unless live evidence proves a safer alternative.

Canonical identity:

- `auth.users.id`

Create a shared platform account table:

- `platform.accounts`

Preferred contract:

- `platform.accounts.id` is the canonical user UUID and references `auth.users.id`
- one row per canonical Fawxzzy person/account
- service tables reference the canonical account ID

Create:

- `platform.profiles`
- `platform.account_emails` if needed for verified history
- `platform.service_memberships`
- `platform.service_onboarding`
- `platform.account_preferences`
- `platform.identity_source_map`
- `platform.account_merge_reviews`
- `platform.remembered_devices`
- `platform.security_events`
- `platform.account_deletion_requests`

Do not overload `auth.users.raw_user_meta_data` as the platform database.

## 5.2 Service membership

A Fawxzzy account exists once.

Entering a service should create or activate a service membership lazily:

- `fitness`
- `mazer`
- future service IDs

Service-specific onboarding remains service-owned.

Examples:

- Fitness may ask goals, units, experience, and training preferences.
- Mazer may ask display name, game settings, and player preferences.
- FawxzzyWeb may ask only shared profile information.

Do not force every user to fill every service’s onboarding at signup.

## 5.3 Mazer identity reconciliation

Export and reconcile all Mazer Auth users.

Build a deterministic mapping:

- source project
- source user UUID
- canonical user UUID
- verified email
- verified phone where present
- provider identity
- migration decision
- conflict status
- review evidence

Matching order should be conservative:

1. Exact verified provider identity.
2. Exact verified email with compatible provider/account evidence.
3. Exact verified phone where legitimate and supported.
4. Manual review.
5. New canonical identity only when no safe match exists.

Do not merge users solely because unverified email strings match.

Preserve password hashes if the supported migration path allows it.

Expect existing Mazer sessions/tokens to require reauthentication because source-project signing identity differs.

Do not promise invisible session continuity.

## 5.4 Cross-subdomain sign-in

Using one Supabase project does not automatically share browser sessions across origins.

Design a real cross-service auth contract.

Preferred public domains:

- `fawxzzy.com`
- `fitness.fawxzzy.com`
- `mazer.fawxzzy.com`

Evaluate:

- central auth UI at `fawxzzy.com/account` or `auth.fawxzzy.com`
- Supabase OAuth 2.1 first-party client support
- authorization-code flow with PKCE
- secure server-side session cookies
- shared parent-domain cookie only if safely implemented and framework-compatible
- short-lived, single-use authorization codes for app handoff
- return URL allowlist
- CSRF protection
- replay protection
- state/nonce validation
- session rotation
- logout propagation

Never place long-lived access or refresh tokens in URLs.

Never assume localStorage is shared across subdomains.

## 5.5 Remembered devices

The operator wants convenient recognition on previously used devices.

Implement only transparent, consented mechanisms:

- passkeys/WebAuthn
- “remember this device”
- refresh-token/session management
- device/session list visible to the user
- device naming
- last-used timestamp
- revoke device/session
- security notifications

Do not use covert browser fingerprinting.

Do not silently populate sensitive personal data on a device merely because probabilistic attributes match.

---

# 6. Database schema boundaries inside FawxzzyPlatform

The target may be one physical Postgres database for public services, but it must behave as several explicit owned capabilities.

Preferred schemas:

## `platform`

Owns:

- accounts
- shared profiles
- service memberships
- shared preferences
- onboarding state
- identity mappings
- remembered devices
- security events
- account lifecycle

## `billing`

Owns:

- payment customers
- products
- prices
- subscriptions
- purchases
- invoices/receipts references
- entitlements
- entitlement grants/revocations
- webhook event ledger
- idempotency
- billing audit

## `fitness`

Owns:

- Fitness sessions
- exercises
- sets
- routines
- progression
- workout templates
- Fitness-specific profile extension
- Fitness-specific jobs
- Fitness-specific product data

## `mazer`

Owns:

- player profile extension
- human progression
- AI progression
- sync revisions
- cycle receipts
- game-owned settings
- future leaderboard/challenge state

## `integrations`

Owns shared external identity mappings and event outboxes where appropriate:

- Discord member mapping
- external provider references
- service event outbox
- webhook delivery state

Do not move DiscordOS private control-plane state here by default.

## `audit`

Owns:

- migration receipts
- security/audit facts
- identity merge decisions
- data repair receipts
- cutover verification

## `ops`

Owns bounded operational state only when it belongs in this project.

Keep high-volume logs/telemetry out of primary relational tables unless retention and scale are explicitly designed.

## `public`

Keep minimal.

Options:

- compatibility views
- safe RPC entry points
- deliberately exposed public API surfaces

Do not continue placing every product table in `public`.

---

# 7. Security and RLS

For every exposed table/view/function:

- explicit grants
- RLS enabled where user access exists
- least-privilege policies
- negative tests
- cross-service isolation tests
- ownership tests
- admin/service tests
- anonymous tests
- authenticated tests
- deleted/suspended account tests

Use service membership and entitlement checks where appropriate.

Avoid repeated expensive RLS subqueries through stable helper functions only when proven safe.

Security-definer functions must:

- use fixed `search_path`
- validate caller and inputs
- have minimal grants
- revoke public execution by default
- have dedicated tests
- emit audit evidence for privileged changes

Do not expose Supabase secret/service-role keys to browsers.

Do not give every backend the same unrestricted project secret by default.

Where a service needs privileged work:

- prefer user JWT plus RLS
- prefer narrowly scoped RPC/Edge Function
- prefer explicit backend authorization
- use separate named secret keys for rotation, while recognizing they still map to elevated project-wide access
- keep the secret in Foundation/1Password runtime injection
- audit every privileged call path

---

# 8. Central billing and entitlements

Build one platform billing identity.

Migrate the existing Fitness billing state into the `billing` schema while preserving IDs, provider references, and receipts.

Canonical model should include equivalents of:

- `billing.customers`
- `billing.products`
- `billing.prices`
- `billing.subscriptions`
- `billing.purchases`
- `billing.entitlements`
- `billing.entitlement_events`
- `billing.webhook_events`
- `billing.checkout_sessions`
- `billing.refunds` where relevant

Requirements:

- one payment-provider customer mapping per canonical account/provider
- service/product-specific SKUs
- shared entitlement evaluation
- idempotent webhook processing
- immutable provider event IDs
- replay-safe processing
- explicit grant and revoke events
- no secret payment data in Auth metadata
- no duplicate customer creation during migration
- backward-compatible Fitness entitlement behavior

Example future entitlements:

- `fitness.pro`
- `fitness.custom_plan`
- `mazer.supporter`
- `mazer.cosmetics.<id>`
- `platform.founder`
- future bundles

Service owners define product behavior.

The platform owns customer identity and entitlement truth.

---

# 9. Canonical migration-repository decision

A single physical database requires one canonical migration ledger.

During the initial truth pass, determine whether an existing repo already safely owns cross-service migrations.

If not, create a proposal for:

- `fawxzzy-platform`

Suggested structure:

```text
fawxzzy-platform/
  README.md
  AGENTS.md
  docs/
    architecture/
    auth/
    billing/
    migrations/
    runbooks/
  supabase/
    config.toml
    migrations/
    seed.sql
    tests/
    functions/
  packages/
    database-types/
    auth-contract/
    entitlement-contract/
    migration-tools/
  scripts/
    inventory/
    export/
    validate/
    cutover/
    rollback/
```

The repo owns:

- canonical migration history
- shared schemas
- database functions
- RLS policies
- generated types
- migration tools
- cross-service integration tests
- cutover/rollback runbooks

Product repos own:

- application code
- service-specific UX
- consuming generated types/contracts
- product-level tests
- service-owned change proposals

Changes to service-owned schemas should be proposed by the service owner and landed through the canonical platform migration ledger.

Do not let Fitness and Mazer independently push unrelated migration histories into the same production project after convergence.

---

# 10. Migration strategy

Use expand → migrate → verify → cut over → contract.

Do not perform a blind big-bang dump into production.

## Phase A — inventory and freeze

Inventory all source objects:

- schemas
- tables
- columns
- constraints
- indexes
- functions
- triggers
- policies
- grants
- extensions
- cron jobs
- realtime publications
- storage buckets/objects
- Edge Functions
- secrets references
- Auth users
- identities
- sessions
- MFA
- OAuth providers
- email templates
- redirect URLs
- webhooks
- database webhooks
- network restrictions
- custom domains
- backups

Capture row counts and checksums.

## Phase B — backup and rehearsal

For every source project:

- dashboard/physical backup where available
- logical schema dump
- data dump
- Auth export
- storage inventory/export
- function source
- migration history
- project configuration receipt

Store backups securely outside the source project.

Test restoration.

Run a complete rehearsal in a development branch, temporary project, local Supabase, or equivalent isolated environment.

Do not use the production target as the first rehearsal.

## Phase C — platform schema expansion

In the target platform project:

- create new schemas
- create canonical account model
- create identity mapping
- create billing model
- create service membership
- create Mazer target tables
- create audit tables
- establish RLS and grants
- add compatibility views/functions where needed

Do not move current Fitness tables destructively before compatibility is proven.

## Phase D — Auth reconciliation

- preserve current Fitness canonical users
- import/map Mazer users
- detect duplicates
- preserve password hashes when supported
- mark conflicts
- require human resolution for ambiguous merges
- record every decision
- test sign-in methods
- test password reset
- test OAuth
- test email verification
- test MFA if present
- test account deletion

Expect source Mazer sessions to be invalidated.

## Phase E — data migration

Migrate:

- Mazer profile/progression/AI/receipt state
- shared profile fields
- billing state to new schema
- shared Discord identity mappings as appropriate
- any Fitness table moves required by the final design

Use deterministic source-to-target ID maps.

Preserve:

- source IDs
- canonical IDs
- timestamps
- ownership
- provider IDs
- audit evidence

## Phase F — compatibility

Provide compatibility layers so current application code can move incrementally:

- views
- RPCs
- generated types
- temporary aliases
- read adapters
- write adapters

Avoid long-lived dual-write unless it is proven idempotent and observable.

If dual-write is used:

- one source remains authoritative
- retries are idempotent
- drift is measured
- reconciliation exists
- time box is explicit
- removal gate is defined

## Phase G — application integration

### FawxzzyWeb

Implement:

- account creation
- login
- logout
- recovery
- account/profile management
- service membership
- app entry
- entitlement display
- security/device/session management
- account deletion flow
- central auth handoff

### Fitness

Update:

- Supabase client configuration
- shared auth/session
- profile mapping
- billing schema usage
- entitlement checks
- existing Discord integration
- generated database types
- tests
- Vercel secrets

Preserve existing users and data.

### Mazer

Update:

- Supabase client configuration
- shared auth/session
- account mapping
- profile/progression schema
- local-first sync
- generated types
- tests
- Vercel secrets

Preserve offline/local-first behavior.

### DiscordOS

Update integration contracts to reference canonical platform account IDs and the new platform endpoint.

Do not give DiscordOS unrestricted platform secret access.

### Socials OS

Update only where it uses:

- account/contact data
- app links
- analytics identity
- user communication
- website/app routes

Do not pause unrelated content work.

## Phase H — cutover

Cutover requires:

- rehearsal passed
- backups proven
- row counts/checksums passed
- RLS tests passed
- auth tests passed
- billing tests passed
- application previews passed
- production configs prepared
- rollback tested
- owner threads acknowledged
- operator approval

Use a bounded maintenance/cutover window if writes cannot be safely synchronized.

## Phase I — observation

After cutover:

- old projects remain intact
- disable new signups/writes as appropriate
- make old projects read-only where feasible
- monitor errors
- monitor auth
- monitor billing
- monitor sync
- compare source/target data
- verify user support
- verify background jobs
- verify Discord integration

Recommended quarantine:

- at least 30 days
- longer if backups/plan support it

## Phase J — retirement

Do not delete a Supabase project automatically.

Retirement requires:

- explicit operator approval
- final backup
- restore test
- no production traffic
- no active keys
- no active webhooks
- no active cron
- no active Edge Functions
- no environment references
- no unresolved data mismatch
- no rollback need
- final ATLAS receipt

Delete only the truly retired source projects.

The preferred plan does **not** delete the platform-seed Fitness project; it renames/repurposes it.

DiscordOS remains unless the explicit merge decision gate was passed.

---

# 11. DiscordOS-specific reconciliation

Inspect both sides of the current Fitness ↔ DiscordOS relationship.

Known live hints:

- Fitness still contains several Discord-related tables.
- DiscordOS contains extracted runtime tables in a private `discordos` schema.
- DiscordOS has live-transfer/status proof migrations and active Edge Functions.
- Existing architecture intended DiscordOS to own feedback/runtime data through a governed migration.

Build a current truth table:

- Fitness-owned Discord tables
- DiscordOS-owned tables
- source of truth per table
- dual-written tables
- shadow tables
- migrated tables
- functions
- Edge Functions
- cron jobs
- card/board integration
- feedback integration
- update drafts
- moderation
- Spotify/music-session state
- member/account links

Resolve divergence.

Preferred relationship:

- FawxzzyPlatform owns canonical Fawxzzy accounts and public-service identity.
- DiscordOS owns Discord/community/control-plane runtime.
- Integration uses canonical account IDs, Discord IDs, signed events, and governed APIs.
- No raw shared database table ownership.
- No DiscordOS secret key with full platform-project access.

Update existing sync/transfer contracts rather than inventing a second competing integration.

---

# 12. Owner-thread messages

ATLAS Main must send exact bounded packets.

## To Fitness

Include:

- migration hold scope
- current source project baseline
- target project identity
- schema ownership
- auth preservation
- billing movement
- compatibility requirements
- files/paths to inspect
- tests
- preview/cutover gates
- work that may continue
- required checkpoint receipt

## To Mazer

Include:

- migration hold scope
- source project baseline
- user mapping
- data migration
- local-first preservation
- reauthentication expectation
- target schema
- generated types
- tests
- work that may continue
- required checkpoint receipt

## To FawxzzyWeb

Include:

- central account portal
- auth UX
- cross-service SSO/handoff
- service membership
- security/device page
- entitlements
- account deletion
- app routing
- domain/session constraints
- tests
- required checkpoint receipt

## To DiscordOS

Include:

- preserve separate project by default
- reconcile transfer/extraction state
- canonical account mapping
- event/API contracts
- no unrestricted platform secrets
- update Edge Functions and cron only through owner plan
- tests
- required checkpoint receipt

## To Foundation

Include:

- Supabase secrets inventory
- 1Password references
- runtime injection
- per-app configuration contracts
- rotation
- revocation
- redaction
- break-glass
- no raw secret exposure
- required checkpoint receipt

## To Lifeline and `_stack`

Include:

- single migration writer
- job envelopes
- migration lease
- execution ordering
- backup jobs
- validation jobs
- rollback jobs
- idempotency
- restart
- receipts
- required checkpoint receipt

## To Socials OS

Include:

- links and account messaging affected by migration
- calendar/operator communication
- work that remains safe
- no unrelated content freeze
- required checkpoint receipt

## To FAWXZZY MESSAGES

Use for concise operator-facing:

- hold acknowledged
- current gate
- blockers
- approvals needed
- cutover state
- resumption state

Do not dump raw implementation logs there.

## To Playbook

Capture reusable doctrine and runbooks.

---

# 13. DiscordOS card/epic plan

Reconcile existing cards before creating new ones.

Likely epics:

1. Fawxzzy Platform Supabase Truth Audit
2. Database/Auth Migration Control Plane
3. Canonical Platform Migration Repository
4. Shared Account and Profile Model
5. Cross-Subdomain Authentication
6. Mazer User Identity Reconciliation
7. Mazer Data Migration
8. Fitness Schema Compatibility
9. Central Billing and Entitlements
10. Remembered Devices and Passkeys
11. RLS and Service Isolation
12. DiscordOS Integration Reconciliation
13. Supabase Configuration and Secret Rotation
14. Application Preview Migration
15. Production Cutover
16. Post-Cutover Verification
17. Source-Project Quarantine
18. Source-Project Retirement
19. Documentation and Playbook Capture
20. Thread Resume and Program Closeout

Every card needs:

- stable ID
- owner
- dependencies
- Definition of Ready
- numbered acceptance criteria
- expected changed paths
- explicit unchanged paths
- proof required
- rollback
- completion review
- migration/run receipt

---

# 14. Execution authority and approval gates

ATLAS may proceed without further operator input for:

- read-only inspection
- thread history reconciliation
- repo/worktree/PR inventory
- database inventory
- backup planning
- local exports
- secure backups
- temporary rehearsal environments where no new paid commitment is created
- branches/worktrees
- migration code
- tests
- compatibility adapters
- documentation
- Discord cards
- owner packets
- preview deployments
- non-production verification
- draft cutover plans

ATLAS must obtain explicit operator approval before:

- creating a new paid Supabase project
- changing production Auth configuration
- changing production OAuth provider callback configuration
- production data cutover
- production maintenance window
- rotating production secrets where clients may break
- destructive schema contraction
- disabling a source project
- deleting any Supabase project
- merging DiscordOS physically into the public platform project
- any irreversible action

Bundle approvals into the fewest coherent gates.

Do not ask for approval on every harmless step.

---

# 15. Thread resumption protocol

When the migration is proven stable:

Send a `FAWXZZY PLATFORM MIGRATION — RESUME` packet to every affected thread.

It must contain:

- canonical Supabase project name/ref
- canonical schemas
- generated type/package versions
- new environment-variable references
- auth contract
- account ID contract
- billing/entitlement contract
- Discord integration contract
- deployed commit/PR/preview/production receipts
- old project status
- compatibility period
- remaining restrictions
- migrations now permitted
- migration-owner process going forward
- rollback location
- support/escalation path

Require each thread to acknowledge:

- configuration updated
- tests passed
- no stale project refs
- no stale keys
- no stale generated types
- no hidden source-project dependencies
- safe resumption

Only then release the migration hold.

---

# 16. Acceptance criteria

The program is not complete until all applicable criteria pass.

## Identity

- One canonical Fawxzzy account is used by Web, Fitness, and Mazer.
- Existing Fitness users can sign in.
- Migrated Mazer users can sign in or complete a clearly explained reauthentication.
- Duplicate users are reconciled safely.
- No ambiguous automatic identity merges.
- Account recovery works.
- Email verification works.
- OAuth works where configured.
- Logout and session revocation work.
- Service membership is lazy and deterministic.
- Device/session management is visible and revocable.
- No covert fingerprinting.

## Data

- Fitness data preserved.
- Mazer data preserved.
- Billing data preserved.
- IDs mapped deterministically.
- Row counts/checksums documented.
- Foreign keys valid.
- constraints valid.
- indexes valid.
- functions/triggers valid.
- migrations reproducible.
- backups restorable.

## Security

- RLS enabled and tested.
- Cross-service negative tests pass.
- no secret/service key in browser.
- no raw secrets in Git, ATLAS, Discord, prompts, or logs.
- privileged functions hardened.
- audit trail exists.
- old keys rotated/revoked at the correct gate.

## Billing

- Existing purchases and subscriptions preserved.
- Entitlements evaluate correctly.
- Webhooks idempotent.
- Duplicate customers not created.
- Fitness Pro behavior does not regress.
- Future service entitlements can be added without separate identity systems.

## Applications

- FawxzzyWeb auth/account UX works.
- Fitness works against platform project.
- Mazer works against platform project.
- DiscordOS integration works.
- Socials OS links/messaging remain correct.
- preview and production tests pass.
- old project references are removed or intentionally retained for quarantine.

## Operations

- One canonical migration ledger.
- One writer process.
- owner threads resumed.
- ATLAS updated.
- Discord cards updated.
- Playbook capture complete.
- rollback proven.
- old projects quarantined.
- deletion requires explicit approval.

---

# 17. Required first ATLAS Main response

Do not begin with a generic summary.

Return:

## Done

- Threads read.
- Repos inspected.
- Supabase projects inspected.
- Current facts verified.
- Existing plans/receipts found.

## Now

- Active writer map.
- Migration collision map.
- Proposed hold scope.
- Work allowed to continue.
- Current source-of-truth map.

## Next

- Exact Wave 0 sequence.
- Owner packets to send.
- Rehearsal plan.
- Approval gates.
- Earliest safe cutover path.

## Health

- Repo/worktree health.
- PR health.
- deployment health.
- Supabase advisor/security health.
- migration-history health.
- Auth health.
- billing health.
- DiscordOS integration health.
- secret/configuration health.
- backup/restore readiness.

## Architecture decision

Explicitly state:

- whether FawxzzyFitness remains the target seed
- whether `fawxzzy-platform` repo is needed
- whether DiscordOS remains separate
- schema boundaries
- auth flow
- billing flow
- migration strategy
- reasons and evidence

## Thread coordination messages

Provide or send the exact hold/checkpoint packets for:

- Fitness
- Mazer
- FawxzzyWeb
- DiscordOS
- Foundation
- Lifeline/_stack
- Socials OS
- FAWXZZY MESSAGES
- Playbook

## DiscordOS cards

- reused cards
- new cards
- dependencies
- owners
- IDs where available

## Blocking questions

Ask only what cannot be resolved from live truth.

Then proceed through the governed work after review and required approvals.

---

# 18. Playbook capture

## Rule — Unified identity does not require unified blast radius

Use one public platform identity while preserving physically separate internal/control-plane systems where security and operations justify it.

## Rule — Reuse the dominant identity project

When consolidating auth projects, prefer the project containing the dominant real-user population and billing truth unless evidence supports a clean replacement.

## Rule — One database means one migration ledger

Multiple repositories must not independently push competing migrations to one production database.

## Rule — Logical boundaries remain real inside one Postgres project

Schemas, RLS, grants, owner contracts, generated types, and tests must preserve service ownership.

## Rule — Never delete the rollback before the replacement is proven

Source projects remain quarantined until restore, traffic, and dependency evidence support retirement.

## Rule — Device convenience must be explicit

Use passkeys and remembered sessions, not covert fingerprinting.

## Pattern — Platform account plus lazy service membership

Create the user once and provision service-specific state only when needed.

## Pattern — Expand, migrate, verify, cut over, contract

Avoid big-bang destructive migration.

## Pattern — ATLAS coordinator, owner-thread execution

ATLAS controls the graph and gates; owner systems implement and prove.

## Failure Mode — Blank-project purity migration

Creating a new project for cleanliness can needlessly migrate the dominant user base, billing truth, and sessions.

## Failure Mode — Shared service-role blast radius

A secret/service-role path in one project bypasses RLS across all schemas.

## Failure Mode — Same project assumed to mean automatic SSO

Browser sessions remain origin-bound unless an explicit cross-domain auth design exists.

## Failure Mode — Premature source-project deletion

Deleting old projects removes the strongest rollback and forensics path.

## Decision — FawxzzyFitness is the preferred platform seed

Reverify before execution.

## Decision — DiscordOS remains separate by default

Merge only after explicit proof and approval.

## Decision — FawxzzyWeb, Fitness, and Mazer share one canonical public account

Service-owned data and onboarding remain bounded.
