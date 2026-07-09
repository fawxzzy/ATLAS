# Vercel Platform Observability Capability Audit

Date: 2026-07-09
Mode: read-only platform-governance audit
Status: completed

## Goal

Record what Vercel observability and deployment-read access is actually visible from the current ATLAS root session, separate safe read-only evidence from unsafe mutation authority, and select one exact no-mutation follow-up packet.

This audit does not:

- print, copy, or rotate any Vercel token
- read or print environment-variable values
- change Vercel settings
- deploy, redeploy, promote, or roll back
- mutate aliases, domains, or project config
- mutate owner repos
- move markers

## Why this audit exists

The operator reported a new DiscordOS-linked Vercel monitoring/token path. That is a material platform capability change, but it does not automatically mean ATLAS root has governed "full observability."

The first useful move is a root-side audit:

1. confirm whether authenticated Vercel access is actually visible from this session
2. identify which projects and deployment surfaces are readable
3. separate read-only observability from broader mutation risk
4. choose one exact next governance packet

## Read-only evidence used

### Root and stack surfaces

- `docs/memory/profiles/zachariah_workflow_profile.md`
- `stack.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- prior Vercel receipts under `docs/ops/`

### Local non-secret runtime checks

- `git -C . status -sb`
- `python ops/validation/validate_stack.py`
- `Get-ChildItem Env: | Where-Object { $_.Name -like 'VERCEL*' }`
- `Get-Command vercel`
- `vercel --version`
- `vercel whoami`
- `vercel project ls`

### Read-only Vercel connector surfaces

- team listing
- project listing
- project detail
- deployment listing
- runtime log counts
- runtime error grouping
- deployment build logs
- agent-run project listing

## Root session baseline

- root branch: `main`
- carried root head during audit: `689b83e293929deccc4128f4ec17942f7f18ebf4`
- root validation result: `critical=0 error=0 warning=0 info=0`
- visible `VERCEL_*` environment-variable names in this shell: none
- Vercel CLI present: `50.41.0`
- `vercel whoami`: `zachariahredfield`

Interpretation:

- no raw Vercel token was exposed through shell env inspection in this packet
- this root session still has authenticated Vercel access through at least one already-configured path because both CLI identity and the Vercel connector answered successfully

## Visibility posture

### Posture classes selected

- `vercel_observability_connector_visible`
- `vercel_observability_atlas_visible`
- `vercel_observability_partial`
- `vercel_observability_mutation_risk`

### Why these classes fit

`vercel_observability_connector_visible`

- the connected Vercel app returned the live team, project inventory, deployment lists, runtime-log counts, runtime-error grouping, and build-log samples

`vercel_observability_atlas_visible`

- the root shell itself is authenticated enough for `vercel whoami` to succeed as `zachariahredfield`

`vercel_observability_partial`

- this packet proved deployment/build/runtime visibility for a subset of surfaces
- it did not prove safe governed access to analytics, speed insights, drains, alerts, or env-name-only inventory
- it did not prove a long-retention observability posture

`vercel_observability_mutation_risk`

- the same authenticated posture that enables read access is broad enough that careless follow-on work could cross into deploy, domain, env, or other project mutation

### What this audit does not claim

This audit does not claim:

- raw token visibility in ATLAS root
- full observability across all Vercel products
- env-name inventory access
- observability-plus entitlement
- analytics, speed-insights, or drain visibility
- mutation safety by default

## Confirmed team and project inventory

### Visible Vercel team

| Team | Team id |
| --- | --- |
| `fawxzzy` | `team_CMJn7MvzFZZBnhNnjVUZF2RD` |

### Visible projects from the connector

| Project | Project id | Repo mapping in ATLAS | Audit relevance |
| --- | --- | --- | --- |
| `fawxzzy-discordos` | `prj_C2RSEa34OblHfhuEpVChRQQZSjuG` | `repos/DiscordOS` | high |
| `fawxzzy-fitness` | `prj_rtlFVOMFAWCRoJ3SQjHloi89881K` | `repos/fawxzzy-fitness` | high |
| `fawxzzy-mazer` | `prj_t3zothbtj9DExrh3FjMsH98hwwSZ` | `repos/mazer` | high |
| `fawxzzy-trove` | `prj_vhUyajI4AL6BgCF40VnKtdxrBLuV` | `repos/trove` | inventory-only in this packet |
| `fawxzzy-foundation` | `prj_o37CPLlESB6Zybe8GB74BX3wrkpy` | `repos/foundation` | inventory-only in this packet |

### CLI scope note

The CLI authenticated successfully, but `vercel project ls` returned `No projects found under fawxzzy`.

Interpretation:

- CLI auth is real
- connector inventory is currently the more trustworthy root-side discovery surface for project truth in this packet
- future governance should not assume CLI list behavior and connector list behavior are equivalent

## Confirmed deployment and alias visibility

### DiscordOS

Project summary:

- project: `fawxzzy-discordos`
- project id: `prj_C2RSEa34OblHfhuEpVChRQQZSjuG`
- node version: `24.x`
- canonical domains returned by project detail:
  - `fawxzzy-discordos.vercel.app`
  - `fawxzzy-discordos-fawxzzy.vercel.app`
  - `fawxzzy-discordos-zachariahredfield-fawxzzy.vercel.app`

Most recent visible production deployments:

| Deployment id | Created (UTC) | State | Target | Commit |
| --- | --- | --- | --- | --- |
| `dpl_6Xk98KCzVzqtiYJ1JJXmHnTJBeJW` | `2026-07-09T16:05:20Z` | `READY` | `production` | `967b69fe694bccbc8a9587ccf357332192c00010` |
| `dpl_6rDThLRXMWM4ti6ySTJ719uBuEvJ` | slightly earlier same day | `READY` | `production` | `967b69fe694bccbc8a9587ccf357332192c00010` |
| `dpl_8Cg1tGv4ym4Zt6R6gjGM3MLiQaeD` | slightly earlier same day | `READY` | `production` | `967b69fe694bccbc8a9587ccf357332192c00010` |

### Fitness

Project summary:

- project: `fawxzzy-fitness`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- framework: `nextjs`
- node version: `24.x`
- canonical domains returned by project detail:
  - `fawxzzy-fitness-local.vercel.app`
  - `fawxzzy-fitness-fawxzzy.vercel.app`
  - `fawxzzy-fitness-zachariahredfield-fawxzzy.vercel.app`

Most recent visible production deployments:

| Deployment id | Created (UTC) | State | Target | Commit |
| --- | --- | --- | --- | --- |
| `dpl_8CuUJWAK1VHZFHhKmm46zj3ECji6` | `2026-07-09T15:56:02Z` | `READY` | `production` | `d3f3e88645b7ee878d57f2bf242e1c7eb9f1eeb3` |
| `dpl_CP5E5FCaB6Ce8A5zSPWwr3bqfAYT` | earlier same day | `READY` | `production` | `d3f3e88645b7ee878d57f2bf242e1c7eb9f1eeb3` |
| `dpl_ChzYfyQjfdagrpdYaev28LvQHert` | `2026-07-09` | `READY` | `production` | `d3f3e88645b7ee878d57f2bf242e1c7eb9f1eeb3` |

### Mazer

Project summary:

- project: `fawxzzy-mazer`
- project id: `prj_t3zothbtj9DExrh3FjMsH98hwwSZ`
- framework: `vite`
- node version: `24.x`
- canonical domains returned by project detail:
  - `fawxzzy-mazer.vercel.app`
  - `fawxzzy-mazer-fawxzzy.vercel.app`
  - `fawxzzy-mazer-zachariahredfield-fawxzzy.vercel.app`

Most recent visible production deployments:

| Deployment id | Created (UTC) | State | Target | Commit |
| --- | --- | --- | --- | --- |
| `dpl_J4KJ9u2eZzHK6m5qSxq19qCPYTfT` | `2026-07-09T05:34:32Z` | `READY` | `production` | `845446266347be19524fbe36f39e688db804e9e8` |
| `dpl_C1rmS4VvvwBw1umHWozcu18M7RUN` | `2026-07-09` | `READY` | `production` | `9dcab1be4904a285615405334a15ee80276c7d9b` |
| `dpl_3z3NC5HUMGCL12vbR1JpDuGShpbJ` | `2026-07-09` | `READY` | `production` | `ef2c5a95a2ab2a26ec76cff8aaae5199aacb08dd` |

## Confirmed log and deployment-event surfaces

### Build logs

Build-log access is confirmed from the connector.

Sample successful retrievals:

- DiscordOS latest deployment `dpl_6Xk98KCzVzqtiYJ1JJXmHnTJBeJW`
- Fitness latest deployment `dpl_8CuUJWAK1VHZFHhKmm46zj3ECji6`
- Mazer latest deployment `dpl_J4KJ9u2eZzHK6m5qSxq19qCPYTfT`

Observed proof shape:

- recent build tail lines returned successfully
- deployment completion timestamps were readable
- no mutation was required to inspect them

### Runtime log counts

Runtime-log access is confirmed from the connector, but current activity differs by project.

Observed grouped counts over recent production windows:

| Project | Result |
| --- | --- |
| DiscordOS | connector returned an empty grouped table for `24h` by log level |
| Fitness | connector returned `info: 5` for `24h` by log level |
| Mazer | connector returned an empty grouped table for `24h` by log level |

Interpretation:

- the runtime-log surface is queryable
- an empty grouped table should be treated as "no grouped results returned for that window," not as proof that the app has no runtime activity in all contexts

### Runtime error grouping

Runtime-error grouping is confirmed from the connector.

Observed results:

- DiscordOS: no grouped runtime errors in the selected `24h` window
- Mazer: no grouped runtime errors in the selected `24h` window
- Fitness: one grouped runtime error family was returned

Fitness grouped error evidence:

- error group label: `billing-webhook-stripe`
- occurrences: `168`
- affected users: `7`
- route: `/api/billing/webhook/stripe`
- first seen: `2026-07-01T20:54:17.000Z`
- last seen: `2026-07-09T05:34:02.000Z`
- last deployment referenced by the error cluster: `dpl_HUsDUbhofhJFEKxLCazcDfQk8pTM`

Implication:

- this session can retrieve useful production-runtime fault summaries from Vercel without touching owner repos
- that is materially more than project inventory alone

### Agent-run observability

The connector surface for agent-run project listing returned no production projects in the selected `7d` window.

Interpretation:

- no agent-run observability evidence was surfaced from this team through that endpoint in this packet
- do not infer that agent-run observability is globally unavailable; only that this query returned no current project data

## Surfaces confirmed visible

Confirmed visible in this packet:

- team identity
- project inventory
- project detail and canonical domains
- recent deployments
- deployment commit metadata
- build-log tails
- grouped runtime-log queries
- grouped runtime-error queries

## Surfaces not proven in this packet

Not proven in this packet:

- env-name-only inventory
- Web Analytics visibility
- Speed Insights visibility
- traces
- alerts
- drains
- billing detail
- retention tier beyond what prior historical receipts already described
- Observability Plus entitlement

These remain governance questions, not settled facts.

## Surfaces explicitly unsafe to access in this lane

The following remain outside the allowed boundary for this packet:

- environment-variable values
- secrets
- token values
- deploy, redeploy, promote, or rollback actions
- alias/domain mutation
- team billing mutation
- project setting mutation

## DiscordOS monitoring integration posture

Current safe statement:

- there is now a real Vercel observability path that benefits DiscordOS governance
- the current root session can read DiscordOS project, deployment, and build-log state
- this packet did not inspect DiscordOS env names or secret-backed monitoring config
- this packet therefore proves observability capability presence, not full DiscordOS monitoring configuration truth

## ATLAS/Codex visibility posture

The correct root-side statement after this audit is:

- ATLAS root has authenticated read access to meaningful Vercel deployment observability surfaces
- Codex can use the connected Vercel app and existing CLI auth for bounded read-only governance work
- ATLAS root does not need raw token visibility to perform this audit
- ATLAS root should still treat the underlying auth path as potentially mutation-capable

This means:

- "no observability" is false
- "full safe observability" is also false

## Risks

### 1. Overclaiming "full observability"

This packet does not prove access to every observability product or every project surface. Treating connector success on deployments and logs as universal observability would be inaccurate.

### 2. Mutation authority hidden behind the same auth path

The effective auth available to this session is strong enough that future careless CLI or connector use could cross into write operations.

### 3. Secret and env-value spill risk

Future packets that mix inventory and env inspection could drift into secret handling unless they stay name-only and receipt-bounded.

### 4. Connector and CLI surface mismatch

The successful connector project inventory and the CLI `project ls` empty result prove that different Vercel access surfaces can disagree operationally. Governance should record those differences rather than smoothing them away.

### 5. Owner-lane bleed

The visible projects include owner repos outside the immediate DiscordOS trigger. Root governance must keep this family read-only and inventory-focused unless the operator explicitly selects owner-lane work.

## Root-side wins from this packet

This audit established that ATLAS root can safely do the following in future bounded packets:

1. project inventory governance
2. deployment freshness snapshots
3. build-log proof capture
4. grouped runtime-error posture checks
5. domain and alias read-only mapping

Without this packet:

- Vercel monitoring would still be only a vague capability claim

With this packet:

- Vercel observability is now a documented partial read-only governance surface

## Recommended follow-up packets

Recommended order:

1. `Vercel Platform Observability Governance read-only project inventory contract freeze`
2. `Vercel Platform Observability Governance deployment and log proof contract freeze`
3. `Vercel Platform Observability Governance env-name-only intake boundary contract freeze`
4. `Vercel Platform Observability Governance analytics and drain visibility contract freeze`

## Marker decision

No marker moves in this pass.

Reason:

- the audit proves a real root-governed Vercel observability surface exists
- but this is still the first packet in the family
- one audit receipt is enough to justify follow-up governance, not enough to ratchet or open a new durable marker by itself

## Exact next packet

`Vercel Platform Observability Governance read-only project inventory contract freeze`

Why this is the next packet:

- effective root-visible read access already exists through the connector and CLI auth path
- the highest-value next move is to freeze what counts as canonical project truth, safe inventory fields, and proof boundaries
- that must happen before broader log, env-name, analytics, or drain discovery work

## Mirror and commit posture

This packet lands with:

- the standalone audit receipt
- one isolated receipt-index entry

Current-state and restart-guide updates were deferred in this pass because:

- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`

already contain unrelated dirty residue in the current root worktree, and mixing that residue into this audit packet would weaken staging safety.

## Completion

Completion: `100%` for the audit packet itself.

No Vercel mutation was performed.
No owner repo was mutated.
No token value was printed.
No env values were read or committed.
