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
authority. A valid packet must originate from `fawxzzy.questions` under an
explicit current operator request, target an `owner.*` logical role, use `repo_worktree`, and
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

### Canonical-program schema compatibility

The v2 schema distinguishes current scheduler writes from immutable historical
records without migrating or rewriting the canonical program:

- an ordinary standing packet may persist `authority_class: null` and
  `source_preparation: null`; selecting
  `standing_local_source_preparation` still requires the existing closed
  source-preparation object;
- a current completion receipt remains limited to the five closed terminal
  successors; only a receipt carrying both `receipt_path` and
  `receipt_sha256` may use the bounded uppercase historical successor form;
- a current processed event retains the strict current routing and authority
  shape; only a record carrying `disposition` may use the strict historical
  shape, the audited legacy owner-return delivery orders, an optional
  `source_event_id`, or a bounded uppercase legacy decision ID ending in
  `:ANSWER`.

These discriminators are compatibility boundaries, not new writer authority.
Current scheduler writers do not emit `receipt_path`, `receipt_sha256`, or
`disposition`, so they cannot produce a historical variant accidentally.
Unknown authority classes, standing authority with null source preparation,
free-form current successors, unknown delivery orders, malformed dispositions,
legacy IDs without a historical discriminator, and extra historical fields all
remain invalid. Restart and replay preserve historical bytes; no compatibility
path rewrites the program or widens execution authority.

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
ambiguous result becomes `recovery-required`; the admitted recovery owner must
inspect complete target history for the exact event ID and must not retry
blindly. Active work without
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

Complete-history recovery has exactly two outcomes. If the target history
contains the matching turn, the bridge binds that returned turn and preserves
the existing reservation. If complete history contains no matching or active
turn and the original app call is independently proven terminally lost, a
`DELIVERY_RECOVERY_PROOF` may retire only that orphaned reservation. The proof
is a closed, canonically hashed `atlas.scheduler.delivery-recovery-evidence.v1`
projection containing the exact packet, writer scope, runtime, event, digest,
and reservation identities plus the canonical event ID and payload digest of
the supported target-history read receipt; `history_complete=true`; empty
matching and active turn sets; `original_call_state=TERMINALLY_LOST`; and
`effects_match_intent=false`. Missing, partial, extra, mismatched, or ambiguous
evidence leaves the intent and lease in `recovery-required`.

The absence transition also requires exactly one already-admitted successor
authority. That successor must name the retired packet in `replaces_packet_id`,
carry a distinct canonical event and packet identity, and preserve the logical
role, runtime binding, repository, writer scope, execution class, dependencies,
protected-surface authority, and complete resource claims. The scheduler
removes only the orphaned intent and correlated lease, records both proof and
successor identities in the completion receipt, then exposes the successor to
normal atomic reservation. Program locking and the distinct successor identity
permit exactly one fresh delivery. Replaying the old `RECOVERY_REQUIRED`
journal entry is silent; any later delivered-turn evidence contradicting the
absence proof fails closed.

Every release receipt must carry `terminal=true`, a successful terminal state,
the exact `packet_id`, `writer_scope`, reservation ID, and delivered turn ID. No
prose classification or uncorrelated terminal receipt releases capacity.

Obsolete packets are not deleted silently. `01 Ops` may consume a canonical
`SUPERSEDED` terminal disposition only while a packet remains `READY` or while
its exact delivery intent is `prepared` and has no returned turn. Prepared
cancellation requires the exact packet, writer scope, and reservation. A
delivered packet cannot be cancelled. A recovery-required packet can be
superseded only through the closed absence-proof transition above, issued by
the Workflow Architect recovery owner or MAIN under exact recovery authority;
ordinary owner/review/manual routing does not require MAIN as a relay.

`atlas.worker-lease.v2` now requires `writer_scope`; a lease without its
conflict-group identity is invalid and cannot reserve global capacity by
accident.

The default scope for a `repo_worktree` job is derived from its repository. A
`canonical_workspace` job always claims the ATLAS root. Explicit narrower
conflict groups remain responsible for complete, non-overlapping file,
worktree, port, browser, and external-writer claims.

An `external_mutation` job must declare at least one exact `external_writers`
resource, receives the same durable mutating lease as source writers, and
conflicts on writer scope or an overlapping external writer. It normally has no
repository file or worktree claim. A protected branch or pull-request writer
may retain exact source-file and isolated-worktree provenance; those additional
claims participate in the ordinary file and worktree conflict checks.
Canonical envelope ingestion persists `protected_surface_authorized` exactly;
otherwise protected lifecycle wording remains blocked after handoff even when
the originating authority admitted that bounded surface.

### Guarded external-attempt consumption

A mutating external-provider packet may carry one closed `external_attempt`
claim. The claim binds its attempt ID and limit, the expected persisted
consumption count, the authorizing event and payload digest, the exact writer
scope, the repository identity, and one normalized external-resource identity.
The resource must also appear in `resource_claims.external_writers`; the packet
must be `external_mutation` and must carry explicit protected-surface authority.
Missing, extra, malformed, mismatched, exhausted, or ineligible claim data fails
closed before reservation.

The first contract is deliberately one-shot: `limit` is exactly `1` and
`expected_consumed_count` is exactly `0` in both schema and candidate
admission. The claim's event and payload digest must also match exactly one
previously validated `OPERATOR_DECISION` or `OPERATOR_DECISION_ANSWER` from
`fawxzzy.authorization` in the canonical processed-event history. That decision
must carry a closed `external_attempt_authority` object whose attempt ID,
one-shot limit and expected count, writer scope, repository, and normalized
external-resource identity equal the claim exactly. The scheduler retains that
normalized scope with the processed decision and copies it into the immutable
consumption record. A missing scope, unrelated decision, or event-ID, digest,
role, kind, attempt, count, writer, repository, or resource mismatch is rejected
before a standing packet, attempt record, reservation, lease, or delivery intent
can change. The packet's separate `external_mutation`, protected-surface, exact
writer-scope, repository, and resource-claim checks remain the execution and
mutation-cap boundary.

Under the existing exclusive program lock, the scheduler compares the claim to
the immutable `external_attempts` ledger and prepares both the incremented
consumption record and deterministic reservation. It commits that record, the
`ACTIVE` packet, its lease, and its prepared delivery intent in the same atomic
program replacement. Claim-bearing reservation is also isolated in memory: any
validation, collision, or transition failure discards the working copy, leaving
no partial attempt, lease, or delivery state.

The ledger keeps one consumed record per attempt ID, including the originating
packet, idempotency key, and reservation. An exact restart therefore observes
the existing `ACTIVE` packet and correlated reservation without incrementing or
creating a second lease. Reuse by the same packet is already consumed; reuse by
a different packet or idempotency key is a cross-packet replay and fails closed.
Terminal settlement releases the lease but never removes consumed-attempt
history.

Operator recovery is evidence-driven: after an ambiguous restart, inspect the
canonical program under lock. If the ledger and correlated reservation are both
present, reconcile the existing delivery only. If neither is present, a fresh
authority may retry from the still-unconsumed count. If only one side is present,
or identities differ, hold for scheduler repair; never reconstruct, decrement,
or hand-edit the ledger and never issue the provider request.

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

A same-repository `external_mutation` may also continue beside the virtual root
validation hold, but only when its initial conflict set is exactly `files`, it
has explicit protected-surface authority, and it declares nonempty concrete
file, isolated-worktree, and external-writer claims. Every claimed worktree must
differ from the validation root. A missing or wildcard claim, a different
repository, the validation worktree itself, or any additional writer-scope,
worktree, external-writer, canonical-root, repository, port, or browser conflict
keeps the packet blocked. This exception removes only the validation candidate's
synthetic `**` file collision; normal execution-wave and active-lease collision
checks remain unchanged.

## Continuation behavior

`01 Ops` consumes only already-authorized READY packets, selects the largest deterministic
conflict-free wave within configured writer and read-only limits, and routes
each packet to its existing standing logical role. `IDLE` and `notLoaded` are
resumable binding states, not terminal states.

Root and cross-lane candidates must name an exact logical owner, repository,
writer scope, and execution class. Legacy selector or validation output without
that owner metadata is held as `root_owner_admission_required`; 01 Ops never
becomes a catch-all source or semantic authority.

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
