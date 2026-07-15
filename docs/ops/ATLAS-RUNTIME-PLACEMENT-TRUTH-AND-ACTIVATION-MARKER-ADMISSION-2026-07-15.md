# ATLAS Runtime Placement Truth And Activation Marker Admission

Date: `2026-07-15`

Mode: root-owned placement, projection, and measurement contract only.

Source scout: Codex task `019f66ec-36a4-7740-b1c8-60c774b8f12e`, terminal and
archived after read-only review.

## Result

ATLAS now has one canonical machine-readable placement registry:

- `docs/registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json`
- schema: `schemas/atlas.runtime-placement.registry.v1.json`
- semantic validator: `ops/validation/runtime_placement_contract.py`

No dependency was installed. No service, scheduled task, startup registration,
listener, persistent process, Vercel deployment, Supabase mutation, GitHub
workflow mutation, Discord mutation, or owner-repository source mutation was
performed.

## Accepted placement decisions

- No new general-purpose ATLAS server.
- Foundation is the existing hosted read-only portfolio surface.
- DiscordOS is the existing hosted API and logical writer, split across Vercel
  public edge, Supabase durable state/writer, and GitHub Actions bounded polling.
- Playbook Observer is the intended private operator cockpit on
  `127.0.0.1:4300`.
- Lifeline is the intended local supervisor, restart, log, and current-user
  logon restoration mechanism for Playbook Observer.
- `_stack` may activate exactly one serialized bounded scheduled inbox sweep,
  not multiple permanent pollers.
- Atlas root, Playbook CLI, Cortex, Atlas Book, contracts, registries, and
  Socials OS remain local/on-demand or owner-lane surfaces.
- Fitness, Mazer, Socials OS, Trove, Stream, Nat1, and other products remain
  owner lanes and are not root-operated services.
- Cortex refreshes on accepted state changes or digests; it does not become a
  competing daemon or scheduler.

## Fresh availability readback

Observed during this packet:

| Surface | Readback | Current classification |
| --- | --- | --- |
| Foundation production | `https://fawxzzy-foundation.vercel.app` returned HTTP `200` at `2026-07-15T18:51:06Z` | available |
| DiscordOS runtime health | HTTP `200` at `2026-07-15T18:51:08Z`; `ok=true`; `posture=operational`; `readinessPercent=100`; Supabase, service role, bot, activation guard, persisted writer, and transfer status all `ready` | operational |
| ATLAS QA | GitHub Actions run `29439213282` completed `success` on 2026-07-15 | active/successful bounded run |
| DiscordOS scheduled poll | GitHub Actions run `29442036556` completed `success` on 2026-07-15 | active/successful hosted poll |
| Playbook CLI | compiled `packages/cli/dist/main.js` is present after a later generated-state refresh, but direct help exits `1` because `minimatch` is missing; local dependencies are incomplete | unavailable |
| Playbook Observer | no listener on port `4300`; no canonical `runtime/playbook/observer` registry | unavailable |
| Lifeline | no `node_modules`, no `dist/cli.js`, no state/startup state, no registered task | unavailable |
| `_stack` scheduled sweep | no matching scheduled task or active node runner; one `_stack` inbox file is dated `2026-04-08T06:34:58Z` | inactive/stale evidence |
| Cortex principal surfaces | `current-state/latest.json`, `context/latest.json`, and `operator-surface/latest.json` were generated on 2026-07-06 | stale |
| Windows integration | zero matching ATLAS, Playbook, Lifeline, DiscordOS, CodexInbox, or `_stack` scheduled tasks and services | inactive |

The Playbook generated-state observation is newer than the accepted scout: a
compiled CLI entrypoint is now present, but executable readiness remains false
because the dependency boundary is incomplete. The registry records the fresh
readback rather than preserving the stale artifact-absence claim.

## Fixed-denominator marker admissions

The following lanes are added to
`docs/registry/ATLAS-FULL-SYSTEM-REEVALUATION-LANES.json` and projected into the
Atlas Book and established owner exports:

### Runtime Activation Readiness

Fixed denominator: `8` binary gates.

1. placement contract
2. Playbook build
3. Observer foreground health
4. Lifeline build/doctor
5. Lifeline state placement
6. Lifeline supervision/restart
7. logon restore
8. `_stack` single-worker proof

### Runtime Correlation Reliability

Fixed denominator: `5` scenarios.

1. successful task
2. failed task
3. duplicate task
4. interrupted/restarted task
5. stale receipt rejection

### Operator Surface Adoption

Fixed denominator: `4` roles.

1. Foundation portfolio
2. Playbook operations
3. Atlas Book doctrine
4. `_stack` action routing

All three percentages and completed-unit counts remain `null`. No unit is
credited from source presence, implementation prose, this placement contract,
or partial hosted health.

## Ordered owner-side activation

1. Playbook bootstrap and foreground Observer proof.
2. Lifeline bootstrap and root-runtime state contract.
3. Lifeline supervised restart proof.
4. Lifeline current-user logon restore proof.
5. One `_stack` bounded scheduled worker proof.
6. One event-triggered Cortex refresh.
7. DiscordOS interaction-first reliability review.
8. Owner export integration.

Exact next packet: `Playbook bootstrap and foreground Observer health proof`.

## Do not deploy

- Atlas root
- `_stack`
- Playbook Observer
- Lifeline
- Cortex artifacts
- Atlas Book
- Socials OS
- Playbook Demo
- external-model sidecar
- Lifeline pilot/Caddy stack

This packet authorizes no production deployment. Every Vercel production
deployment or promotion remains explicit, current-thread, per-project, and
per-deploy approval-gated.

## Governance capture

**RULE — Deploy only capabilities that require shared/continuous availability;
keep doctrine, contracts, CLIs, and private operator state local/on-demand.**

**RULE — One component owns each runtime responsibility; Foundation, Playbook,
Atlas Book, and `_stack` must not duplicate authority.**

**PATTERN — Hosted edge for public callbacks/state, supervised loopback services
for private operator tooling, event-triggered recomputation for read models.**

**FAILURE MODE — Serverizing the Control Plane:** deploying local/private
doctrine or operator machinery merely because a server command exists.

**FAILURE MODE — Duplicate Cockpit:** Foundation and Playbook both becoming
competing operational dashboards.

**FAILURE MODE — Poller Proliferation:** multiple permanent watchers replacing
one serialized lease/idempotency-controlled sweep.

## Projection corrections

The Atlas Book and architecture projection now distinguish:

- hosted availability from implemented-but-inactive local surfaces
- current DiscordOS ownership from superseded Fitness-hosted Discord claims
- active DiscordOS GitHub Actions polling from the inactive future local
  `_stack` scheduled sweep
- shipped Lifeline implementation from current local Lifeline availability
- event-triggered Cortex read models from daemon/scheduler behavior
- historical closed lane receipts from current activation truth

Historical receipts remain preserved. Their marker values are not rewritten.

## Marker invariants

- Atlas Contracts Mesh remains `11 / 11` and `100%`.
- Atlas Full-System Re-evaluation remains `1 / 2` and `50%`.
- Marker Integrity remains `51 / 51` and `100%`.
- No unrelated marker percentage, completed-unit count, denominator, or status is
  intentionally changed.

## Verification outcome

- Runtime placement schema and semantic validation reports `issue_count=0`.
  Schema definition, required fields, and date-time formats use the shared
  Draft 2020-12 validator with its dependency-free supported-subset fallback.
- Runtime placement plus read-only-cleanup unit coverage passes `20` tests.
- Project-board owner export and projection coverage passes `25` tests; the
  deterministic export check reports `34` Atlas cards, `2` Cortex cards,
  `discord_mutation_authorized=false`, and source revision
  `sha256:2e299105e883c9640bcb83dd4e040873377286ede98923be4dd5540a6dc6546d`.
- Combined focused Python coverage passes `45` tests. Marker evidence admission
  coverage separately passes `10` tests.
- Canonical root validation with `--skip-generated-state-cleanup` reports
  `0 critical / 0 error / 5 warning / 0 info`. All warnings are pre-existing:
  one untracked root capture; three committed absolute-path findings across two
  root files; and one committed absolute-path warning inside the read-only
  DiscordOS owner repository.
- Every touched registry, schema, and generated export parses as JSON.
- `git diff --check` passes; the exact staged scope is `25` root-owned paths and
  no path under `repos/**`.
- Added-line credential-pattern scan reports zero matches. The bounded private
  identifier review finds loopback `127.0.0.1` only. The staged machine-specific
  committed-path scan reports zero matches.
- The root scratch inventory remains exactly `69` unstaged entries with normal
  status hash
  `4d72fd2970fdd82a684dda1b334c0a8a5c758a7b8907087014e8af6253cd3da9`
  and path hash
  `7ad120b3b17b5a8b3eb210eecc33666763cdd8e62406e23cc1c804d5cc3a4388`.
- Twelve of thirteen nested owner repositories retain their exact pre-packet
  heads and status. `repos/socials-os` changed concurrently under its owner
  lane: its head advanced from `78c1330f` through `12c0e41b` to clean
  `7ee8a25c1a9258d0228ae84ba6db0b7d95a4b994` in owner commits at
  `2026-07-15T18:33:56Z` and `2026-07-15T18:56:03Z`; its standing owner
  receipt reports `origin/main` parity `0 / 0`. This root packet did not touch,
  fetch, stage, revert, or commit that repository.

Canonical validation reports no stack-lock or stack-inventory drift, so neither
generated truth surface is refreshed. Established generators own the refreshed
Atlas and Cortex project-board exports; neither export is hand-edited.
