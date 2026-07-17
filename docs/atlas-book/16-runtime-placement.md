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
| Foundation portfolio | Vercel | Available; production UI returned HTTP 200 on 2026-07-16 | Foundation |
| DiscordOS runtime | Hybrid Vercel, Supabase, and GitHub Actions | Operational; runtime health returned HTTP 200, `ok=true`, and `posture=operational` on 2026-07-16 | DiscordOS |
| Playbook CLI | No server / on demand | Available on demand from merged Playbook PR `#27` proof | Playbook |
| Playbook Observer | Local persistent on `127.0.0.1:4300` | Foreground proof accepted; currently intentionally stopped/restorable with no listener | Playbook |
| Lifeline | Local persistent supervisor and current-user logon restore | Registered/restorable; task enabled, ready, and last result `0` | Lifeline |
| `_stack` inbox sweep | Local scheduled | Exactly one bounded task enabled/ready; latest observed sweep succeeded with zero pending work and no active lease residue | `_stack` |
| Cortex read models | No server / event-triggered on demand | Principal Cortex event artifacts remain the accepted step-6 snapshot; generated Atlas/Cortex owner exports now carry the current step-8 runtime readback | ATLAS root |
| Atlas root, Atlas Book, contracts, registries, and Playbook CLI doctrine | No server / on demand | Source surfaces are available locally; runtime claims still require their own proof | ATLAS root or named owner |
| Fitness, Mazer, Socials OS, Trove, Stream, Nat1, and other products | Owner lane | Owner-managed; not root-operated services | Named owner lane |

Foundation is the hosted read-only portfolio. Playbook Observer is the private
local operator cockpit. They must not become competing dashboards.

DiscordOS is the hosted Discord API and logical writer. Vercel owns its public
edge, Supabase owns durable writer state, and GitHub Actions owns bounded
scheduled polling. The exact reviewed DiscordOS PR #104 Preview supplies the
five-scenario interaction-first reliability proof. Production-path adoption
and real-user coverage remain UNKNOWN because the PR is draft and unmerged.

Cortex refreshes after accepted state changes or digests. It is not a daemon,
scheduler, or competing execution authority.

## Activation order

Owner-side activation is serialized in this exact order:

1. Playbook bootstrap and foreground Observer proof — `accepted`.
2. Lifeline bootstrap and state-placement contract — `accepted`.
3. Lifeline supervised restart proof — `accepted`.
4. Lifeline current-user logon restore proof — `accepted` from deterministic
   owner proof; actual later new-logon restoration remains `unknown`.
5. One `_stack` bounded scheduled worker proof — `accepted`.
6. One event-triggered Cortex refresh — `accepted` from an immutable activation
   event, exact source blobs, and byte-stable replay receipt.
7. DiscordOS interaction-first reliability review - `accepted` from exact
   reviewed draft PR #104 Preview evidence without a merge or production claim.
8. Owner export integration - `accepted` from deterministic Atlas/Cortex
   runtime readback, schema, semantic, and exact replay proof.

Each step has structured status and evidence. The selector is the first step
whose status is not `accepted`; accepted steps must form a contiguous prefix.
All eight steps are accepted, so the derived selector is `null`. The next
runtime activation packet does not exist, and the canonical root planner
currently reports `no_immediate_root_packet`. The Atlas Full-System
Re-evaluation closing audit remains a separately authorized hold excluded from
selector routing.

## Fixed marker lanes

Only directly evidenced fixed units are counted:

- Runtime Activation Readiness: `8 / 8`, `100%`.
- Runtime Correlation Reliability: `5 / 5`, `100%`.
- Operator Surface Adoption: `4 / 4`, `100%`.

Unit status is structured as `accepted`, `pending`, `blocked`, or `unknown`.
Only `accepted` counts; prose never implies completion, and a genuinely blocked
unit is not collapsed into unknown. These deterministic markers do not claim
that Observer is currently running or that actual later new-logon restoration
or sustained unattended uptime has been observed.

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
