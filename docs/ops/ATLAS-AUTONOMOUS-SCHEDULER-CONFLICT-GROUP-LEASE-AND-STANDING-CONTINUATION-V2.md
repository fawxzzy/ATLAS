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

### Standing local source preparation

The operator may keep idle owner tasks productive through the exact authority
class `standing_local_source_preparation`. This is not generic owner-repository
authority. A valid packet must originate from `atlas.main` or
`fawxzzy.questions`, target an `owner.*` logical role, use `repo_worktree`, and
carry all of the following:

- `source_preparation.mode` equal to `LOCAL_ONLY_UNSTAGED`;
- `source_preparation.publication` equal to `HELD`;
- one immutable lowercase 40-character parent commit;
- one to 32 exact repository-relative paths, mirrored exactly by `files`
  resource claims;
- exactly one explicit non-wildcard isolated-worktree claim, resolved relative
  to the scheduler root without symlink or junction indirection;
- live Git proof that the resolved path is the exact top level of a registered
  linked worktree whose normalized `origin` matches the declared repository and
  whose `HEAD` equals the packet's immutable parent commit;
- no protected workflow, secret, environment, port, browser, or external-writer
  claim.

The class admits bounded local edits, tests, documentation, and deterministic
generation only. It never admits staging, commit, push, branch or pull-request
creation, review requests, merge, workflow or runner actions, provider access,
Supabase mutation, deployment, production, or canonical-root mutation.
Publication requires a separate exact authority packet. The bridge preserves
the authority class, source role, and preparation contract and revalidates them
again when selecting a persisted standing packet.

The runtime bridge consumes an explicit standing-role binding snapshot plus
canonical Inbox JSON or JSONL envelopes. It verifies that each `onv1_` event ID
and `sha256:` digest matches the canonical payload bytes, deduplicates immutable
events, and upgrades the runtime work program to v2. The bridge never scrapes
task transcripts. `idle` and `notLoaded` bindings are resumable; `active`,
archived, missing, and unknown bindings are lane-local blockers and are never
steered.

The work-program file under `tmp/atlas/` is a derived atomic snapshot, not the
only durable copy of scheduler truth. If it is absent after restart, the bridge
recreates it only when both canonical Inbox envelopes and the current binding
snapshot are supplied. It admits nonterminal events first, reconstructs exact
reservations from deterministic packet identity plus recorded delivery results,
then consumes terminal receipts. A missing snapshot without those journals
still fails closed. This makes disposable `tmp` cleanup recoverable without
inventing packets, leases, deliveries, or completions.

## Lease behavior

An active lease persists its repository, mutating execution class, and normalized
resource claims in addition to its exact `writer_scope`. Missing isolation
identity is a recovery fault that blocks mutating dispatch instead of falling
back to a standing packet that may no longer exist. Multiple active leases for
one scope remain a collision and block that scope. Repository identities are
canonicalized case-insensitively before collision checks. A terminal correlated
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
Promoting a recovery-required delivery back to `delivered` requires explicit
`COMPLETE_TARGET_TASK_HISTORY` reconciliation, the exact event identity, and a
proof that observed effects match the admitted intent. A bare later
`DELIVERED` status or terminal receipt cannot clear recovery state. Successful reconciliation also
returns the correlated mutating lease to `active`; only the exact terminal
receipt may release that lease. Completion receipts retain the delivered task,
event, digest, reservation, and turn identities so replaying an append-only
delivery journal is idempotent while identity drift still fails closed.
When delivery and cancellation evidence arrive together, delivery settlement
runs first; a delivered intent cannot then be erased by cancellation.

Every release receipt must carry `terminal=true`, a successful terminal state,
the exact `packet_id`, `writer_scope`, reservation ID, and delivered turn ID. No
prose classification or uncorrelated terminal receipt releases capacity.

Obsolete packets are not deleted silently. `ATLAS MAIN` may emit a canonical
`SUPERSEDED` terminal disposition only while a packet remains `READY` or while
its exact delivery intent is `prepared` and has no returned turn. Prepared
cancellation requires the exact packet, writer scope, and reservation. A
delivered or recovery-required packet cannot be cancelled and still requires
complete target-task-history reconciliation.

`atlas.worker-lease.v2` now requires `writer_scope`; a lease without its
conflict-group identity is invalid and cannot reserve global capacity by
accident.

The default scope for a `repo_worktree` job is derived from its repository. A
`canonical_workspace` job always claims the ATLAS root. Explicit narrower
conflict groups remain responsible for complete, non-overlapping file,
worktree, port, browser, and external-writer claims.

An `external_mutation` job does not claim repository files or worktrees. It
must declare at least one exact `external_writers` resource, receives the same
durable mutating lease as source writers, and conflicts on writer scope or an
overlapping external writer. This lets PR lifecycle control continue beside a
held root validation scope without weakening same-repository source isolation.
Canonical envelope ingestion persists `protected_surface_authorized` exactly;
otherwise protected lifecycle wording remains blocked after handoff even when
the originating authority admitted that bounded surface.

Repository identities are canonicalized before scope derivation, persistence,
and collision checks. GitHub `owner/repo`, HTTPS, SSH, and `.git` aliases map to
one lowercase owner/repository key; unrecognized URL identities fail closed.
Structured `github` and `github-pr` claims plus GitHub pull-request URLs map to
one PR lifecycle writer key, so review, reply, resolution, ready, and merge
actions for one PR cannot run concurrently under alternate spellings.
Non-PR `github` and `git-branch` claims retain their case-sensitive suffixes.

A root validation hold owns only the checkout being validated. A source writer
for the same repository may continue from another worktree only when it declares
bounded file claims and an explicit non-wildcard worktree identity different
from the validated checkout. Missing, catch-all, wildcard-worktree, or
same-worktree claims fail closed; the ordinary wave conflict rule still
serializes overlapping repository writers.

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

The normal bridge invocation always includes `--delivery-results`; omitting the
delivery journal can recreate READY packets but cannot truthfully recover their
in-flight or completed delivery lifecycle.

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
  same-scope serialization, case-insensitive repository identity, and
  distinct-repository parallel waves.
- `tests/test_atlas_autonomous_lane_scheduler.py` proves canonical standing
  authority, binding-aware idle and notLoaded resumption, active-task
  suppression, dependency gating, atomic reservation, exact terminal release,
  zero-capacity preservation, bounded local-preparation admission and rejection,
  protected-term-safe read-only routing,
  active-lease isolation, and deterministic multi-scope wave selection.
  The suite also deletes the derived program snapshot and proves journal replay
  restores two disjoint owner reservations in one wave and releases an exactly
  delivered terminal packet without residue.
- `tests/test_atlas_workflow_recovery.py` and the generated workflow view prove
  that the durable manifest retains per-scope collision handling and standing
  continuation rules.
