# Runtime Placement

## Authority

The canonical machine-readable placement and activation contract is
[`docs/registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json`](../registry/ATLAS-RUNTIME-PLACEMENT-REGISTRY.v1.json).
This chapter is its human projection. Owner repositories remain authoritative
for their implementation and activation proof.

No new general-purpose ATLAS server is admitted.

## Current placement

| Surface | Intended placement | Current availability | Authority |
| --- | --- | --- | --- |
| Foundation portfolio | Vercel | Available; production UI returned HTTP 200 on 2026-07-15 | Foundation |
| DiscordOS runtime | Hybrid Vercel, Supabase, and GitHub Actions | Operational; runtime health reported every component ready and the latest scheduled poll succeeded on 2026-07-15 | DiscordOS |
| Playbook CLI | No server / on demand | Unavailable; compiled output is present after a later generated-state refresh, but direct invocation fails on an incomplete dependency install | Playbook |
| Playbook Observer | Local persistent on `127.0.0.1:4300` | Unavailable; no listener or canonical root-runtime Observer state | Playbook |
| Lifeline | Local persistent supervisor and current-user logon restore | Unavailable; dependencies, build, runtime state, and startup registration are absent | Lifeline |
| `_stack` inbox sweep | Local scheduled | Inactive; no scheduled task or active runner, with only stale inbox evidence | `_stack` |
| Cortex read models | No server / event-triggered on demand | Stale; principal `latest` state/context/operator surfaces remain dated 2026-07-06 | ATLAS root |
| Atlas root, Atlas Book, contracts, registries, and Playbook CLI doctrine | No server / on demand | Source surfaces are available locally; runtime claims still require their own proof | ATLAS root or named owner |
| Fitness, Mazer, Socials OS, Trove, Stream, Nat1, and other products | Owner lane | Owner-managed; not root-operated services | Named owner lane |

Foundation is the hosted read-only portfolio. Playbook Observer is the private
local operator cockpit. They must not become competing dashboards.

DiscordOS is the hosted Discord API and logical writer. Vercel owns its public
edge, Supabase owns durable writer state, and GitHub Actions owns bounded
scheduled polling. Component health is not yet the five-scenario
interaction-first reliability proof.

Cortex refreshes after accepted state changes or digests. It is not a daemon,
scheduler, or competing execution authority.

## Activation order

Owner-side activation is serialized in this exact order:

1. Playbook bootstrap and foreground Observer proof.
2. Lifeline bootstrap and state-placement contract.
3. Lifeline supervised restart proof.
4. Lifeline current-user logon restore proof.
5. One `_stack` bounded scheduled worker proof.
6. One event-triggered Cortex refresh.
7. DiscordOS interaction-first reliability review.
8. Owner export integration.

The exact next packet is `Playbook bootstrap and foreground Observer health
proof`.

## Fixed marker lanes

The current marker values are intentionally unset:

- Runtime Activation Readiness: fixed eight binary gates.
- Runtime Correlation Reliability: fixed five scenarios.
- Operator Surface Adoption: fixed four roles.

No percentage or completed-unit count is assigned until every unit in the
corresponding lane has directly admissible current proof. Source presence,
implementation prose, or partial hosted health does not count.

## Do not deploy

This placement program does not deploy:

- Atlas root
- `_stack`
- Playbook Observer
- Lifeline
- Cortex artifacts
- Atlas Book
- Socials OS
- Playbook Demo
- the external-model sidecar
- the Lifeline pilot/Caddy stack

Local activation of the explicitly admitted Observer, Lifeline, and single
scheduled-sweep path is separate from public deployment and requires the ordered
owner-side proof above. Every Vercel production deployment or promotion remains
explicitly current-thread, per-project, and per-deploy approval-gated.

## Rules, pattern, and failure modes

Rule:
Deploy only capabilities that require shared or continuous availability. Keep
doctrine, contracts, CLIs, and private operator state local or on demand.

Rule:
One component owns each runtime responsibility. Foundation, Playbook, Atlas
Book, and `_stack` must not duplicate authority.

Pattern:
Use a hosted edge for public callbacks and state, supervised loopback services
for private operator tooling, and event-triggered recomputation for read models.

Failure Mode — Serverizing the Control Plane:
Deploying local or private doctrine and operator machinery merely because a
server command exists.

Failure Mode — Duplicate Cockpit:
Foundation and Playbook become competing operational dashboards.

Failure Mode — Poller Proliferation:
Multiple permanent watchers replace one serialized, lease- and
idempotency-controlled sweep.
