# AI Work Session Stability Auto-Sync Loop Projection Freshness Checker Implementation-Readiness Closeout And Worker Routing

- CODEX-MSG-ID: `CODEX-2026-07-02-AI-WORK-SESSION-STABILITY-PROJECTION-FRESHNESS-IMPLEMENTATION-READINESS`
- Date: `2026-07-02`
- Mode: `docs-only implementation-readiness closeout and worker-routing`
- Scope: `route one bounded read-only projection freshness checker worker without implementing it`
- Control-plane checkpoint: `main@28f2cab7`
- Worker implementation: `not included`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`
- Marker movement: `none`

## Readiness Decision

Decision: `implementation-ready`.

The projection freshness checker contract spine is durable enough to route exactly one bounded first-implementation worker packet.

## Contract Spine Check

1. Prior lane proof is durable: yes.
   - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-READ-ONLY-PREFLIGHT-AGGREGATOR-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-06-29.md`
   - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-READ-ONLY-CLOSEOUT-AGGREGATOR-FIRST-IMPLEMENTATION-WORKER-CLUSTER-RECONCILIATION-2026-07-02.md`
2. Admission is explicit: yes.
   - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PROJECTION-FRESHNESS-CHECKER-FIRST-IMPLEMENTATION-ADMISSION-2026-07-02.md`
3. Prompt-pack is explicit: yes.
   - `docs/ops/AI-WORK-SESSION-STABILITY-AUTO-SYNC-LOOP-PROJECTION-FRESHNESS-CHECKER-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-02.md`
4. Worker objective is explicit: yes.
   - Detect stale root projections and required refreshes without performing mutation.
5. CLI contract is explicit: yes.
6. JSON output contract is explicit: yes.
7. Exit-code policy is explicit: yes.
8. Forbidden mutation behavior is explicit: yes.
9. Stop conditions are explicit: yes.
10. Proof matrix is explicit: yes.

No blocking ambiguity remains before the bounded worker implementation.

## Routed Worker Packet

Route exactly:

`AI Work Session Stability & Auto-Sync Loop projection freshness checker first-implementation worker packet 1`

Allowed worker files:

- `ops/atlas/projection_freshness.py`
- `tests/test_atlas_projection_freshness.py`

No other committed files are admitted for that worker packet. Generated runtime validation receipts may be refreshed locally but must not be committed unless a later reconciliation packet explicitly admits them.

## Worker Boundaries

The worker packet may:

- implement the read-only projection freshness CLI
- add direct unit tests for the CLI and output contract
- read root git, stack lock, inventory, Book mirrors, receipts, manifests, marker selector output, validation receipts, protected-surface classes, optional PR metadata, and optional owner-lane status
- write JSON only to an admitted root-relative output path

The worker packet may not:

- mutate owner repos
- mutate Supabase, Vercel, BrowserStack, GitHub secrets, PR bodies, or deployment surfaces
- stage, commit, push, fetch, merge, or change branches from inside the worker
- move markers
- generate receipts
- edit Book, manifests, selector, or restart surfaces
- touch protected surfaces
- implement Playbook adoption or broader auto-sync behavior

## Post-Worker Reconciliation Package

After the worker lands and passes proof, route:

`AI Work Session Stability & Auto-Sync Loop projection freshness checker first-implementation worker cluster reconciliation`

That reconciliation package must decide marker movement from evidence. The expected ratchet is `40% -> 55%` only if the worker lands, tests pass, validation remains clean, the read-only contract is preserved, and restart surfaces are refreshed.

## Marker Decision

No marker moves from this readiness packet.

`AI Work Session Stability & Auto-Sync Loop` remains `40%`.

Reason: this packet closes routing ambiguity only. It does not land the projection freshness checker or proof-backed adoption.

## Validation Snapshot

Pre-routing validation held at:

- stack validation: `critical=0 error=0 warning=3 info=0`
- marker selector: active `Sandbox Simulation Readiness` remains held; first fallback is the projection freshness checker implementation packet
- continuity manifests: restart-ready and healthy before this receipt

## Rule

`Readiness Routes One Worker, Not A Refresh Family`

Implementation readiness admits only the two named worker files and the frozen first worker behavior. It does not admit root projection mutation, owner-lane cleanup, PR editing, platform proof, marker movement, or auto-sync.
