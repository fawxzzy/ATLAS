# Supabase Pro Platform Capability Adoption Audit

Date: 2026-07-09
Mode: read-only platform-governance audit
Status: completed

## Goal

Record what Supabase Pro unlocks for the governed ATLAS stack, identify which current projects are actually in scope, and select one exact no-mutation follow-up packet.

This audit does not:

- mutate any Supabase project
- enable PITR
- enable network restrictions
- create log drains
- configure custom domains
- change compute sizing
- rotate keys
- create projects
- touch secrets or `.env*`
- mutate owner repos

## Why this audit exists

Supabase Pro is now a real operator-available platform capability. That changes ATLAS platform posture even though no project setting was changed in this pass.

The right first move is governance, not toggles:

1. confirm which projects are actually present
2. map Pro-era capabilities to those projects
3. separate safe root-side prep from operator-only actions
4. pick one exact follow-up packet

## Read-only evidence used

### Root and stack surfaces

- `stack.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- prior Supabase receipts under `docs/ops/`

### Repo-local Supabase surfaces

- `repos/DiscordOS/api/readiness.js`
- `repos/DiscordOS/supabase/functions/**`
- `repos/DiscordOS/supabase/migrations/**`
- `docs/ops/DISCORD-OS-SUPABASE-SCHEMA-LANDING-PLAN-2026-05-24.md`
- `repos/fawxzzy-fitness/supabase/migrations/**`
- `repos/fawxzzy-fitness/scripts/sync-prod-to-local.mjs`
- `repos/fawxzzy-fitness/supabase/.temp/linked-project.json`
- `docs/ops/FITNESS-SUPABASE-PROFILE-DATA-HYGIENE-FINAL-CLOSEOUT-2026-05-25.md`
- `repos/mazer/supabase/migrations/**`
- `repos/Nat1-Games/nat1-games/src/shared/infrastructure/supabaseClient.js`

### Read-only Supabase connector surfaces

- project listing
- project detail for each visible project
- edge-function listing for each visible project
- branch listing where the connector would answer

### Current Supabase docs checked on 2026-07-09

- Changelog: https://supabase.com/changelog
- Database Backups: https://supabase.com/docs/guides/platform/backups
- Branching: https://supabase.com/docs/guides/deployment/branching
- Log Drains: https://supabase.com/docs/guides/telemetry/log-drains
- Network Restrictions: https://supabase.com/docs/guides/platform/network-restrictions
- Custom Domains: https://supabase.com/docs/guides/platform/custom-domains
- Compute and Disk: https://supabase.com/docs/guides/platform/compute-and-disk
- Production Checklist: https://supabase.com/docs/guides/deployment/going-into-prod
- Access Control: https://supabase.com/docs/guides/platform/access-control

## Confirmed project inventory

### Confirmed projects in the current Supabase org

| Project | Ref | Region | Connector status | Local evidence | Current operational posture |
| --- | --- | --- | --- | --- | --- |
| FawxzzyFitness | `lpswxoyfniocuhljgzbc` | `us-west-2` | `ACTIVE_HEALTHY` | repo-local `supabase/migrations/**`, admin/client scripts, QA runbooks, local mirror guard | mature app data plane with direct DB mirror and many service-role-backed scripts |
| DiscordOS | `nwexsktuuenfdegzrbut` | `us-east-1` | `ACTIVE_HEALTHY` | repo-local `supabase/functions/**`, migrations, runtime-health and transfer receipts | live Discord runtime and workflow data plane with active edge-function use |
| Mazer | `geknvnrmktchljnyddwp` | `us-west-2` | `ACTIVE_HEALTHY` | repo-local `supabase/migrations/**` for progression/profile/receipt sync | newly created remote sync surface for a local-first game; early governance stage |

### Dependency-only or indirect surfaces

| Surface | Evidence | Audit interpretation |
| --- | --- | --- |
| Nat1-Games | `@supabase/supabase-js` in `package.json` plus `src/shared/infrastructure/supabaseClient.js` | real app dependency, but no visible project ref or visible project in the current Supabase org listing; do not treat as a confirmed governed project yet |
| `_stack` | Fitness QA runbook env examples only | operational documentation, not a Supabase project |
| Playbook | detector/test coverage for Supabase dependency discovery | product/tooling support, not a Supabase project |
| Foundation | references to `docs/operations/SUPABASE_INVENTORY.md` | documentation linkage only, not a Supabase project |

## What Pro unlocks and where it matters

### 1. Daily backups and restore posture

Relevance:

- Fitness: high
- DiscordOS: high
- Mazer: medium

Current read:

- the operator states Pro is now available
- this audit did not verify backup settings directly because the read-only connector surface here does not expose that configuration
- official docs say paid-plan projects get daily backups, while PITR is a separate add-on decision

Implication:

- backup posture should be treated as immediately governable
- restore procedure and restore-test doctrine are still missing from ATLAS root

### 2. PITR eligibility and cost posture

Relevance:

- Fitness: high
- DiscordOS: medium-high
- Mazer: low-medium for now

Current read:

- PITR is a separate paid add-on
- current docs require at least Small compute
- PITR replaces daily backups while enabled

Implication:

- this is not a default "turn it on" choice
- it needs project-by-project cost and recovery-window decisions

### 3. Branching and migration preview environments

Relevance:

- Fitness: high
- DiscordOS: high
- Mazer: medium

Current read:

- Fitness and DiscordOS both have repo-local migrations
- Mazer already has migration-based remote-sync schema work
- Fitness branch listing returns only `main`
- DiscordOS and Mazer branch listing could not be confirmed from the connector because the branch endpoint returned a permission-validation error instead of branch state
- none of the three repos currently expose a committed `supabase/config.toml`, so branch configuration-as-code is not yet governed

Implication:

- branching is relevant, but branch governance is not implementation-ready
- the right root move is a contract freeze around migration preview rules before any feature enablement

### 4. Log drains and observability

Relevance:

- DiscordOS: highest
- Fitness: medium
- Mazer: low for now

Current read:

- DiscordOS has six active Edge Functions visible in the connector:
  - `discordos-readiness`
  - `discordos-feedback-persist`
  - `discordos-live-transfer-status`
  - `discordos-runtime-health-cron-audit`
  - `discordos-product-workflow-rpc`
  - `discordos-update-drafts`
- Fitness has no visible Edge Functions in the connector, but it has a substantial data plane and admin/script surface
- Mazer currently has no visible Edge Functions

Implication:

- DiscordOS is the strongest first log-drain candidate because the gain is cross-runtime observability, not just SQL visibility
- destination, retention, secret handling, and cost all need operator doctrine before activation

### 5. Network restrictions

Relevance:

- Fitness: high
- DiscordOS: medium-high
- Mazer: medium

Current read:

- official docs say restrictions apply to Postgres and pooler connections, not HTTPS APIs such as PostgREST, Auth, Storage, or `supabase-js`
- official docs also say direct DB access from Edge Functions is blocked when network restrictions are enabled
- Fitness has confirmed direct database flows in `scripts/sync-prod-to-local.mjs` and migration-chain validation surfaces
- DiscordOS primarily presents as API, service-role, and Edge Function usage

Implication:

- network restrictions are real value, but only after direct DB and pooler clients are inventoried
- Fitness is the highest risk of self-breakage if restrictions are enabled casually

### 6. Custom domains

Relevance:

- DiscordOS: high
- Fitness: medium
- Mazer: low-medium

Current read:

- official docs position custom domains as useful for OAuth consent, Edge Function and webhook URLs, and long-term API portability
- DiscordOS is the most obvious project where stable API identity could matter soon because it already uses edge-function-backed operational surfaces

Implication:

- worth governing, not worth enabling yet
- callback, webhook, and migration side effects must be planned first

### 7. Compute and disk posture

Relevance:

- Fitness: high
- DiscordOS: medium-high
- Mazer: low for now

Current read:

- compute sizing is paid-plan operational posture, not just an emergency knob
- PITR, restore timing, and load posture all intersect with compute choices

Implication:

- compute should be audited as part of backup/restore and performance posture, not treated as an isolated toggle

### 8. Auth, MFA, access control, and ownership

Relevance:

- all confirmed projects

Current read:

- official production checklist recommends MFA, multiple owners, and strong auth configuration review
- this audit did not inspect organization membership or MFA settings

Implication:

- this is operator/manual work, but it belongs in the governed adoption plan

### 9. Edge Functions and webhook reliability surfaces

Relevance:

- DiscordOS: highest
- Fitness: low from connector evidence
- Mazer: low from connector evidence

Current read:

- DiscordOS is already using Edge Functions as real product/runtime surfaces
- that makes backups, log drains, custom domains, and network-restriction doctrine more urgent there than in the other two projects

### 10. Project ownership, access, and secrets handling

Relevance:

- all confirmed projects

Current read:

- local repo evidence shows env-name usage, project refs, and service-role dependency patterns
- no secret values were read or committed in this audit

Implication:

- root-side governance should keep documenting names and contracts, not values

## Security and compatibility observations

### Mazer is already aligned with the current Supabase public-schema exposure change

The current Supabase changelog says new projects now default toward explicit table exposure rather than automatic public-schema Data API exposure.

Why it matters here:

- Mazer was created on `2026-07-09`, after that default change took effect for new projects
- its committed migrations already use explicit `REVOKE`, explicit `GRANT`, and RLS policies

That is good evidence that new project work should keep explicit grant discipline as the standard.

### Fitness already has direct DB operational surfaces

The local mirror script proves Fitness still has operator workflows that use direct database URLs. That makes backup, restore, and network-restriction planning more foundational there than log drains or custom domains.

### DiscordOS is the strongest observability and domain-governance candidate

The active Edge Function inventory makes DiscordOS the project where Pro-era observability and stable API identity will pay off first.

## Unsafe or manual actions

The following remain operator-only or explicitly manual after this audit:

- enabling PITR
- changing compute size
- creating or activating log drains
- applying network restrictions
- configuring custom domains
- changing org membership, owner count, or MFA enforcement
- rotating service-role, anon, or publishable keys
- creating branch config or branch integrations without repo-owner review

## Root-side no-mutation wins

These are safe next-step classes because they improve governance without touching Supabase settings:

1. backup and restore posture contract freeze
2. branching and migration preview contract freeze
3. log-drain destination and secret-handling contract freeze
4. network restriction readiness inventory contract freeze
5. custom-domain callback and webhook impact contract freeze

## Cost and risk matrix

| Capability | Primary upside | Main risk if rushed | Audit stance |
| --- | --- | --- | --- |
| daily backups / restore plan | foundational recovery | false confidence without restore drill | do next |
| PITR | tighter recovery window | add-on cost plus compute requirement | defer pending decision |
| branching | safer schema change testing | half-configured preview drift | govern before enabling |
| log drains | cross-runtime observability | recurring cost, secret sprawl, noisy exports | prepare after backup posture |
| network restrictions | DB hardening | breaking direct DB clients or edge access patterns | inventory first |
| custom domains | stable API/OAuth/webhook identity | callback/domain migration mistakes | contract first |
| compute/disk changes | performance and PITR eligibility | downtime and cost | couple to restore/perf review |

## Recommended follow-up packets

Recommended order:

1. `Supabase Pro Platform Governance backup and restore posture contract freeze`
2. `Supabase Pro Platform Governance branching and migration preview contract freeze`
3. `Supabase Pro Platform Governance log-drain observability contract freeze`
4. `Supabase Pro Platform Governance network restriction readiness contract freeze`
5. `Supabase Pro Platform Governance custom-domain portability contract freeze`

## Marker decision

No marker is opened in this pass.

Reason:

- the audit proves a real platform-governance surface exists
- but this is still the first root-owned packet in the family
- one receipt-backed audit is enough to open a governed follow-up sequence, not yet enough to justify a new durable marker lane

Re-open marker admission only if:

- at least one follow-up contract freeze lands cleanly
- and the remaining follow-up surface is still clearly broader than a one-off checklist

## Exact next packet

`Supabase Pro Platform Governance backup and restore posture contract freeze`

Why this is the next packet:

- it is the lowest-risk Pro-era capability to govern first
- it is relevant to all three confirmed projects
- it informs PITR, compute, restore testing, and later incident posture
- it does not require any live platform mutation

## Completion

Completion: `100%` for the audit packet itself.

No Supabase project was mutated.
No owner repo was mutated.
No secrets were printed or committed.
