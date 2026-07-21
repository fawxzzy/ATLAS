# ATLAS autonomous scheduler conflict-group lease and standing continuation v2

## Decision

The autonomous scheduler selects a dependency-satisfied execution wave, not a
single global packet. Safety is enforced by exclusive conflict-group leases:

- one canonical-root writer;
- one mutating writer per owner repository or declared external-resource group;
- concurrent writers across distinct scopes only when declared resource claims
  are disjoint;
- bounded read-only work only when it does not collide with an exclusive claim.

This supersedes the v1 one-packet scheduling rule. It does not supersede exact
authority, scope, review, merge, provider, deployment, production, or data
gates.

## Standing packet contract

A standing packet is schedulable only when it carries:

- `state` equal to `READY`, `ADMITTED`, or `QUEUED`;
- a stable `packet_id` and bounded packet description;
- `logical_role_id`, `repository`, `writer_scope`, and `execution_class`;
- a canonical `onv1_` SHA-256 event ID and `sha256:` payload digest;
- explicit dependencies and resource claims when applicable.

Owner-like prose without this metadata is not inferred into authority. The
scheduler fails closed instead of treating a textual owner reference as a
license to mutate that repository.

The runtime bridge consumes an explicit standing-role binding snapshot plus
canonical Inbox JSON or JSONL envelopes. It verifies that each `onv1_` event ID
and `sha256:` digest matches the canonical payload bytes, deduplicates immutable
events, and upgrades the runtime work program to v2. The bridge never scrapes
task transcripts. `idle` and `notLoaded` bindings are resumable; `active`,
archived, missing, and unknown bindings are lane-local blockers and are never
steered.

## Lease behavior

An active lease blocks only its exact `writer_scope`. Multiple active leases
for one scope remain a collision and block that scope. A terminal correlated
receipt releases only its exact lease; blocked, latency-bound, or unknown work
does not release a lease by implication.

Selection is not dispatch authority until the scheduler atomically persists
the reservation. Under an exclusive program lock it transitions every selected
standing packet from `READY` to `ACTIVE`, acquires the exact lease for each
mutating writer scope, atomically replaces the program file, and only then emits
the dispatch plan. A concurrent invocation fails closed on the lock or observes
the `ACTIVE` state, so it cannot expose the same packet twice.

The same transaction records a `prepared` delivery intent containing the exact
event, digest, packet, role, thread, and writer-scope identities. After the
app-native send returns, MAIN settles that intent with the returned turn ID. An
ambiguous result becomes `recovery-required`; MAIN must inspect complete thread
history for the exact event ID and must not retry blindly. Active work without
a correlated lease becomes a derived `scope_hold`, never an invented lease.

Every release receipt must carry `terminal=true`, a successful terminal state,
the exact `packet_id`, `writer_scope`, reservation ID, and delivered turn ID. No
prose classification or uncorrelated terminal receipt releases capacity.

`atlas.worker-lease.v2` now requires `writer_scope`; a lease without its
conflict-group identity is invalid and cannot reserve global capacity by
accident.

The default scope for a `repo_worktree` job is derived from its repository. A
`canonical_workspace` job always claims the ATLAS root. Explicit narrower
conflict groups remain responsible for complete, non-overlapping file,
worktree, port, browser, and external-writer claims.

## Continuation behavior

`ATLAS MAIN` consumes all newly READY packets, selects the largest deterministic
conflict-free wave within configured writer and read-only limits, and routes
each packet to its existing standing logical role. `IDLE` and `notLoaded` are
resumable binding states, not terminal states.

When a receipt arrives, MAIN persists it, releases the correlated lease, and
immediately selects the next eligible wave. It does not wait for the next
heartbeat. Heartbeats recover interrupted coordination only.

MAIN writes changed canonical envelopes to
`tmp/atlas/autonomous-inbox-events.jsonl` and a fresh app-native role snapshot
to `tmp/atlas/standing-role-bindings.latest.json`, runs the bridge and scheduler,
then sends only the persisted `dispatch_plan` through the native task API.
Program generation and selection are deterministic local code; task delivery
remains app-native and uses the resolved `runtime_thread_id`. MAIN writes the
app result to a bounded delivery-result JSON/JSONL input and reruns settlement
under the same program lock before consuming later receipts.

## Stop conditions

The affected lane stops on missing or malformed authority, identity or scope
drift, unmet dependencies, active lease collision, undeclared protected
surface access, or resource overlap. Unrelated conflict groups continue.

Protected-surface wording is evaluated as a mutation guard only for mutating
execution classes. A canonical `read_only` packet may name those surfaces as
inspection boundaries or explicit exclusions; that wording does not expand
the packet beyond read-only authority.

No scheduler output grants GitHub workflow dispatch, provider access,
Supabase/SQL/Auth/data mutation, deployment, production, secret access, or
canonical-root mutation beyond the exact admitted packet.

## Verification surface

- `tests/test_cortex_execution_planner.py` proves implicit writer-scope claims,
  same-scope serialization, and distinct-repository parallel waves.
- `tests/test_atlas_autonomous_lane_scheduler.py` proves canonical standing
  authority, binding-aware idle and notLoaded resumption, active-task
  suppression, dependency gating, atomic reservation, exact terminal release,
  zero-capacity preservation, protected-term-safe read-only routing,
  active-lease isolation, and deterministic multi-scope wave selection.
- `tests/test_atlas_workflow_recovery.py` and the generated workflow view prove
  that the durable manifest retains per-scope collision handling and standing
  continuation rules.
