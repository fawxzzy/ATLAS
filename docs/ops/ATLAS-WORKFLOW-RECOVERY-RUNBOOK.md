# ATLAS workflow recovery runbook

This runbook operates the contract in `docs/registry/ATLAS-WORKFLOW-MANIFEST.v1.json`. The generated architecture view is `docs/architecture/ATLAS-WORKFLOW-RECOVERY.md`. Stable logical role IDs are authoritative; runtime thread IDs are replaceable epochs.

## Safety invariant

Recovery is not archival authority. The default is dry-run and no-archive. A recovery run must never delete a partial runtime, archive a predecessor, steer an active task, or silently select between duplicates. ATLAS MAIN is the sole authority sink; the workflow architect owns specification and recovery proof only.

Before every filesystem or Git mutation, prove the exact checkout/worktree, branch, HEAD, status, upstream relation, applicable instructions, and writer lease. Stop on tracked or scratch drift, competing root writer, same-branch worktree collision, stale base, or inability to bind the workdir explicitly.

## Validate the durable contract

From the ATLAS root:

```powershell
python ops/atlas/workflow_recovery.py validate --json
python ops/atlas/workflow_recovery.py render --check
python -m unittest tests.test_atlas_workflow_recovery -v
```

Validation covers the manifest, runtime seed, answered-decision registry, preserved unbound runtime claims, prompt markers, topology endpoints, relative-path discipline, generated view, JSON schemas, canonical envelope payload digests, the complete desktop-observation fixture, and fixture recovery behavior.

Before routing an envelope, validate its source runtime identity and canonical payload digest:

```powershell
python ops/atlas/workflow_recovery.py validate-envelope path/to/envelope.json
```

An `answer_digest` is evidence about the operator's answer; it is not a substitute for the envelope `payload_digest`.

## Automatic GitHub validation

`.github/workflows/atlas-workflow-recovery.yml` is the dedicated source-validation workflow for this contract. It uses JSON form, a strict YAML subset, so the complete GitHub Actions object can be parsed and compared with the Python standard library without adding a CI-only YAML dependency. Relevant pull requests run it through an explicit recovery-surface path filter, including every schema consumed directly by repository validation and every repository-local `source_of_truth` reference reached transitively through the canonical manifest. The test suite derives that transitive denominator from the manifest and proves that deleting an input from the filter creates a validation failure. Local-automation references and separately owned `_stack` repository references remain outside this repository's trigger surface. Every push to `main` runs without a path filter, so each merged commit receives an exact-main result even when the merge does not change recovery files.

The workflow runs the canonical validation, generated-view check, focused unit suite, envelope fixture validation, and deterministic fixture-only recovery on Python 3.12 under both `ubuntu-latest` and `windows-latest`. The expected denominator is one workflow run with two `validate` jobs. It grants only `contents: read`, has no manual-dispatch trigger, reads no secrets, uploads no artifacts, calls no provider or deployment surface, and cannot reach live Codex tasks. Its semantic policy test compares the exact event map, filters, permissions, job, matrix, ordered steps, action identities, and commands; extra authority is rejected rather than ignored.

Executable actions are pinned to reviewed 40-character commit IDs, never mutable tags. The current pins are official, signature-verified `actions/checkout` v4 commit `11d5960a326750d5838078e36cf38b85af677262` and `actions/setup-python` v5 commit `a26af69be951a213d495a4c3e4e4022e16d87065`. To update either action, resolve the intended official major tag through GitHub ref metadata, verify the target commit, review the upstream change, and update the workflow and exact semantic-policy fixture together.

This CI contract is source proof, not recovery authority. Its fixture apply writes only ephemeral runner-local state under `runtime/atlas/workflow-recovery-ci`; it never authorizes `--adapter live`, standing-task mutation, archival, pin inference, or production/provider work. A failed or missing `main` run is a proof blocker: preserve the last accepted state and route exact run/job evidence through the release control plane. Do not dispatch or rerun a workflow without a separately admitted action. Branch-protection or ruleset enforcement is also a separate GitHub-settings decision.

## Supported desktop activity observation

The optional desktop observation is an externally produced, read-only status snapshot. Produce it through a supported Codex task/thread readback surface, then validate it before planning:

```powershell
python ops/atlas/workflow_recovery.py validate-desktop-observation runtime/atlas/workflow-recovery/desktop-observation.json --current runtime/atlas/workflow-recovery/current-desktop-observation.json
python ops/atlas/workflow_recovery.py recover --dry-run --adapter live --desktop-observation runtime/atlas/workflow-recovery/desktop-observation.json --desktop-observation-current runtime/atlas/workflow-recovery/current-desktop-observation.json
```

The v1 receipt is deliberately bound to the current `local` Codex host. It must cover the complete manifest role denominator and bind every role to its exact durable runtime ID, source host, canonical title, observation timestamp, supported activity value, and canonical payload digest. It expires after five minutes and permits only 30 seconds of future clock skew. Duplicate, partial, stale, future, malformed, mismatched, digest-invalid, unknown-role, or superseded evidence fails closed. A future remote-host topology requires a separately versioned host-binding contract; it is not inferred by v1.

Receipts are immutable. Supersession is therefore proven outside the candidate identity by the separately supplied trusted current receipt. A newer current receipt carries a cumulative, digest-bound `supersedes_observation_ids` list. The candidate is accepted only when its ID equals the trusted current head; if the head names the candidate, the candidate is rejected as superseded. If the two IDs differ without a cumulative supersession link, the chain is incomplete and also fails closed. The supported external observation ledger owns the current-head pointer; this repository neither creates nor mutates that ledger.

Allowed activity values are exactly `active`, `idle`, `notLoaded`, and `UNKNOWN`. Absence of evidence is `UNKNOWN`, never `idle`. Every entry must carry `pin_state: UNKNOWN` and `pin_capability: UNSUPPORTED`. The bridge never reads private desktop storage, SQLite catalogs, undocumented app state, or scraped UI state; it never infers pin state.

Observation can replace activity provenance only for a runtime already returned by primary discovery. Both the candidate and trusted current receipt are required. The CLI accepts them only with dry-run; combining observation with `--apply` is rejected. It cannot establish runtime existence, clear a discovery contradiction, create or repair a task, prove pin/archive state, authorize apply, or perform a lifecycle mutation. A reported active writer blocks recovery. Receipt/head identity, source host, and timestamps are visible but excluded from plan identity; the resulting activity state and decisions remain digest-bound.

## Cold start

1. Restore a clean ATLAS coordination repository and the registered `_stack` operator repository. Read root and nested instructions plus the canonical workflow profile.
2. Inspect Git identity and leases. Exactly one admitted ATLAS-root implementation writer is allowed. Operator coordination does not grant a second mutation lease.
3. Run the live dry-run, optionally with one fresh externally produced observation:

   ```powershell
   python ops/atlas/workflow_recovery.py recover --dry-run --adapter live
   python ops/atlas/workflow_recovery.py recover --dry-run --adapter live --desktop-observation runtime/atlas/workflow-recovery/desktop-observation.json --desktop-observation-current runtime/atlas/workflow-recovery/current-desktop-observation.json
   ```

4. Inspect `runtime/atlas/workflow-recovery/plan.json`, optional `post-apply-plan.json`, `creation-journal.json`, persistent `creation-journal.json.create.lock` and `creation-journal.json.lock`, `live-registry.json`, and `RECEIPT.json`. Live apply must use this canonical runtime directory; an alternate output directory or `--no-write-runtime` fails before discovery or mutation. `plan.json` remains the immutable accepted pre-mutation plan. Every `CREATE` transaction first acquires the bounded native create lock. While holding it, recovery reloads retained state under the separate journal transition lock, performs complete discovery, rebuilds that logical role's accepted decision, and durably commits a content-addressed `CREATE_INTENT` before the remote call. The intent binds the accepted plan, role, prior runtime, adapter, and provider-operation-key support. Recovery passes the deterministic operation key only where the supported adapter contract exposes it, keeps the create lock through remote creation, then durably replaces the intent with the returned runtime ID. A process death after the remote call therefore leaves either the runtime binding or the earlier intent. An unresolved intent never schedules another create. Exactly one discovered runtime carrying the same supported provider key can be proposed for separately accepted reconciliation; zero matches, multiple matches, claimant drift, or an adapter without supported key readback stays blocked. A timeout, new claimant, lease collision, decision drift, intent failure, create failure, or journal failure stops without a second create or automatic cleanup. Lock order is always create lock then journal lock; journal transitions never recursively acquire the create lock. Every journal intent, record, reconciliation, or confirmation update acquires the journal transition lock, reloads and validates the latest committed envelope, merges role-bound entries, rejects role/runtime/operation collisions, keeps the lock through durable replacement and committed readback, then releases it. Neither shared lock file is deleted. The temporary journal file is fsynced before replacement. POSIX systems then fsync the modified parent directory; Windows uses `MoveFileExW` with replace-existing and write-through flags. Unsupported primitives and lock acquisition, I/O, reload, merge, replacement, directory synchronization, or release failures stop later actions. After apply, `post-apply-plan.json` records the separate content-addressed readback plan used for terminal health and registry output. `RECEIPT.json` binds the accepted plan, post-apply plan, and journal event/digest. Runtime output is intentionally ignored by Git. Plan digests always exclude `generated_at`; when an observation is present they also exclude volatile receipt identity, source host, and timestamps. The validated activity effects, recovery decisions, cwd locator, and any resolved creation/bootstrap cwd remain digest-bound.
5. Reconcile every role as `HEALTHY`, `DEGRADED`, `MISSING`, `DUPLICATE`, `BLOCKED`, `HELD`, or `UNKNOWN`. Also inspect `unbound_runtime_claims`; they are preserved inventory and must never trigger create or lifecycle actions. Do not translate `notLoaded` into missing and do not translate an archived rollout file into an accepted supersession.
6. Read `docs/registry/ATLAS-WORKFLOW-DECISIONS.v1.json`. Repeat only `OPEN` questions; suppress `ANSWERED`, `EXPIRED`, and `SUPERSEDED` questions. Transport retention is not execution completion.
7. Recover ATLAS MAIN first. Do not initialize queues or owners until the root role is unique, readable, unarchived, pinned, and accepted.
8. Initialize ATLAS INBOX, MANUAL MESSAGES, FAWXZZY QUESTIONS, AI QUESTIONS, and FAWXZZY MESSAGES in parallel only after unique title/role bindings are proven.
9. Initialize the control plane, domain coordinator, and owners in parallel only across distinct writer scopes. A standing role being active is a hold, not an invitation to steer it.

### Scheduler and standing-task continuation

`ops/atlas/autonomous_lane_scheduler.py` is the one canonical control loop. Its persisted program identifies `atlas.main` as selector/supervisor, `atlas.release-control-plane` as a GitHub-lifecycle consumer, and `atlas.workflow-architect` as the design owner. Main admits new cross-lane scope, arbitrates collisions, and consumes the generated portfolio view; it is not the normal relay for owner, review, manual-decision, or DiscordOS traffic.

Normal routes are direct and owner-returning: owner -> Release -> owner, owner -> Manual -> owner, and owner -> DiscordOS -> owner. `atlas.inbox` receives an aggregation copy only. A failed or idle Inbox turn never blocks owner progress. Main receives material status and cross-lane decision copies, not every hop.

The scheduler selects by durable `writer_scope`, dependency, and closed resource claims. The safety invariant is one mutating lease per overlapping resource group, not one global owner writer. The canonical-root writer remains exclusive to its checkout. Disjoint owner repositories, isolated same-repository worktrees with non-overlapping file claims, and read-only scopes may advance concurrently within bounded global caps. Provider, production, secret, and manual-decision mutation surfaces remain singleton resources. Missing, scalar, stale, wildcard, or ambiguous claims fail closed; one legacy scalar worktree is normalized only when an exact top-level worktree field binds the same checkout.

Every material wake consumes all canonically authorized `READY` standing packets in dependency order and dispatches the largest conflict-free wave. A standardized packet is recognized through one normalized, duplicate-free policy set derived from either legacy `policy_id` or current `policy_ids`; the Workflow Standardization policy cannot be bypassed by using the plural form. It must carry two independently validated closed identities: `execution_target` names the current logical role, runtime epoch, and non-empty host that receives the work, while `owner_return` names the current source-owner callback. They may be different for owner -> Release -> owner, owner -> Manual -> owner, and owner -> DiscordOS -> owner routes. The scheduler binds both identities, the target role, source runtime, event, and payload into `transport_digest`; replaying the same event while changing a target epoch, callback epoch, or host is rejected. A standing execution target in `idle` or `notLoaded` state is resumed through that current binding. An active target is never steered: its packet remains queued until the target reaches a safe boundary, and the watchdog emits `BLOCKED_QUEUE` instead of interrupting it.

Before dispatch, snapshot canonical scheduler envelopes to `tmp/atlas/autonomous-inbox-events.jsonl`, current app-native role bindings to `tmp/atlas/standing-role-bindings.latest.json`, and native delivery observations to `tmp/atlas/delivery-results.latest.jsonl`. These are scheduler inputs; they are not evidence that the human-facing ATLAS INBOX task dispatched anything. Run the autonomous scheduler with all three. Send only jobs in its persisted `dispatch_plan`; before any app-native call the scheduler has transitioned the packet to `ACTIVE`, acquired its exact mutating lease, and written a durable delivery intent. Never hand-build a replacement standing-packet list.

`tmp/atlas/autonomous-work-program.json` is a derived snapshot. On a cold start,
invoke the scheduler with the canonical envelopes, bindings, and delivery
journal; it deterministically rebuilds packet, reservation, lease, intent, and
terminal state before selecting new work. Do not hand-create the missing file.
The bridge still fails closed when any required journal is absent or an exact
reservation cannot be reproduced.

For each app-native send, persist a delivery result containing the reservation, packet, execution-target role/runtime/host, writer scope, event, payload digest, transport digest, returned turn or failure, and native tool receipt. Cross-role routes have two correlated phases on the same durable reservation: `EXECUTION` proves the target turn, then `OWNER_RETURN` proves one distinct callback runtime, turn, native tool receipt, and admitted dedupe result. The second phase cannot arrive before the first, cannot replace the execution turn, and cannot bind two first-delivery proofs. Free-form `Next tracking thread` text, an Inbox copy, or a narrative acknowledgment cannot satisfy delivery validation. Duplicate native results are silent, idempotent evidence and cannot suppress or overwrite the first owner return.

If the owner host is unavailable, record `HOST_UNAVAILABLE` with a native failure receipt. Keep the exact intent and lease in recovery state; do not create a replacement packet or runtime. When the same logical role, epoch, and host reconnect, the scheduler changes the packet to `RECOVERY_READY` and reuses the exact reservation for one redelivery. A changed epoch, host mismatch, absent binding, or ambiguous send remains fail closed. For an otherwise ambiguous send, record `RECOVERY_REQUIRED`, inspect complete target history for the exact event ID, and do not retry until the original delivery is proven absent. Active work without a valid correlated lease becomes a scope hold.

A recovered delivery may be promoted only with explicit complete-target-history
evidence, the reconciled event ID, and proof that observed effects match the
admitted intent. Merely changing the status from `RECOVERY_REQUIRED` to
`DELIVERED` is rejected.

Every terminal packet resolves to exactly one closed successor: `NEXT_AUTONOMOUS_PACKET`, `MANUAL_REQUIRED`, `EXTERNAL_WAIT`, `TERMINAL_DOMAIN`, or `ERROR_RECOVERY`. Standardized terminal packets identified by singular or plural policy metadata must carry that explicit value; omission or a value outside the set is rejected. Legacy receipts may use only exact normalized closed states, never substring inference, so text such as `MANUALLY_VERIFIED_PASS`, `SUCCESS_NO_ERRORS`, or `UNKNOWN_ITEMS_ZERO` cannot accidentally select a blocking successor. A free-form tracking line cannot select a successor. A cross-role packet cannot disappear or release its lease until its direct owner-return phase is `DELIVERED` with the exact owner turn and immutable first-delivery proof. Each valid terminal receipt then releases only the exact correlated lease and immediately triggers selection of the next admitted conflict-free wave. `MANUAL_REQUIRED` names the stable question/answer event; `EXTERNAL_WAIT` names the external wake; `ERROR_RECOVERY` emits a content-addressed recovery packet. `BLOCKED`, `REVIEW_LATENCY`, `UNKNOWN`, or an active lease suppresses only that conflict group.

No packet may end in bare idle. `READY` without a lease must be selected exactly once or receive a `READY_IDLE` recovery packet. `ACTIVE` mutating work must have a current lease and heartbeat. Waiting work must name its manual, external, owner-boundary, host-reconnect, or recovery event. Watchdogs cover `READY_IDLE`, `OWNER_RETURN_UNKNOWN`, `STALE_ACTIVE_LEASE`, `MISSING_RUNTIME`, `HOST_UNAVAILABLE`, `BLOCKED_QUEUE`, and `ACTIVE_WITHOUT_LEASE`; they emit deterministic recovery packets rather than polling loops. Heartbeats remain interruption recovery and cannot select ordinary work.

The generated Main portfolio has exactly `DONE_RECENTLY`, `ACTIVE_NOW`, `READY_TO_START`, `WAITING_ON_ZAC`, `WAITING_EXTERNAL`, `BLOCKED_ERROR`, `NEXT_DISPATCHES`, and `HEALTH`. Every lane row identifies role, packet, resource claim, state, last receipt, next executable action, wake condition, owner-return proof/current tracker, and staleness. `HEALTH.scheduler` is `HEALTHY` only when there are zero actionable watchdogs, `BLOCKED` when `ACTIVE_WITHOUT_LEASE`, `MISSING_RUNTIME`, `OWNER_RETURN_UNKNOWN`, or `STALE_ACTIVE_LEASE` is present, and otherwise `DEGRADED`; the projection includes exact watchdog codes and counts. Status is derived from durable program state and does not require waking Main.

Fail closed when a standing packet lacks a canonical `onv1_` event ID and `sha256:` payload digest, a stable logical role, repository, writer scope, execution class, dependency proof, or a collision-free lease. These checks never widen GitHub, provider, deployment, production, Supabase, or data authority.

A terminal receipt releases capacity only when it explicitly carries `terminal=true` and exactly matches the active `packet_id`, `writer_scope`, reservation ID, and delivered turn ID. `BLOCKED`, `REVIEW_LATENCY`, `UNKNOWN`, malformed, or uncorrelated receipts retain the lease for that scope while unrelated scopes continue.

Retire stale or duplicate READY work through an auditable `SUPERSEDED` envelope. The bridge accepts that disposition only before delivery: a READY packet has no reservation, while a prepared packet must match its exact reservation and have no returned turn. Never use supersession to erase a delivered or ambiguous send.
10. Initialize the workflow architect and read embedded-service health last. DiscordOS, Foundation, Lifeline, Playbook Observer, Cortex, the service bus, ledgers, and heartbeats are components, not automatically required conversations.
11. Re-run dry-run. A healthy second run creates no role, sends no bootstrap message, and changes no registry binding.

## Accepted live apply

Live reconstruction is held until ATLAS MAIN or the operator independently accepts the exact plan. The acceptance file must contain:

```json
{
  "schema": "atlas.workflow.recovery-acceptance.v1",
  "event_id": "STABLE-ACCEPTANCE-EVENT-ID",
  "accepted_by_role_id": "atlas.main",
  "manifest_digest": "sha256:<exact manifest digest>",
  "plan_digest": "sha256:<exact plan digest>",
  "no_archive": true
}
```

Then run:

```powershell
python ops/atlas/workflow_recovery.py recover --apply --adapter live --acceptance runtime/atlas/workflow-recovery/ACCEPTANCE.json
```

Roles whose manifest locator is not `ATLAS_ROOT` require an explicit, absolute, admitted worktree binding on both the accepted planning run and the apply run. Repeat `--cwd-binding LOCATOR=ABSOLUTE_PATH` for each role that needs `CREATE` or `BOOTSTRAP`. The resolved path is included in the plan digest, and preflight rejects a missing, relative, duplicate, nonexistent, recovery-root, or changed binding before the first mutation. Local-only example:

```powershell
# Set this local-only variable to the absolute worktree approved in the acceptance packet.
python ops/atlas/workflow_recovery.py recover --apply --adapter live --cwd-binding "SOCIALS_OS_OWNER_PROJECT=$atlasSocialsWorktree" --acceptance runtime/atlas/workflow-recovery/ACCEPTANCE.json
```

Creation sends one canonical modern named profile (`:read-only`, `:workspace`, or `:danger-full-access`) through the app-server `permissions` field and omits legacy `sandbox`; unknown identifiers and legacy tokens such as `danger-full-access` fail closed. Bootstrap uses the same accepted cwd. The command preflights all required capabilities before the first mutation. Creation binds model, permissions, and cwd through `thread/start`; effort is supplied to the bootstrap `turn/start`. The current supported app-server thread protocol exposes neither a create-idempotency/operation-key parameter nor discoverable operation-key metadata. Recovery still records its deterministic intent key locally, but an ambiguous live crash outcome must remain blocked for exact accepted reconciliation rather than retrying `thread/start`. The supported app-server contract also exposes no mutation for repairing a missing policy on an existing runtime, so that repair fails preflight instead of being acknowledged as applied. The app-server does not expose task pin mutation or pin readback. Because every standing role requires a pin, creation or pin repair fails closed before mutation. `ATLAS-WORKFLOW-MAN-001` explicitly selected no manual fallback. The desktop observation bridge closes only supported activity provenance; it does not close the pin gate. Live recovery apply and archive-readiness remain unproven.

## Fixture-only creation and retry proof

Fixture apply cannot reach live tasks:

```powershell
python ops/atlas/workflow_recovery.py recover --apply --adapter fixture --fixture tests/fixtures/atlas-workflow-recovery/missing-task.json --acceptance tests/fixtures/atlas-workflow-recovery/fixture-acceptance.json --output-dir runtime/atlas/workflow-recovery-fixture --deterministic
```

The test lane covers healthy, missing, stale-ID, duplicate, active-writer, partial-create, process death after the remote call, exact provider-key reconciliation, fresh-process retry, concurrent independent journal instances, bounded lock contention, role/runtime/operation collisions, confirmed-state merge preservation, and unknown-state cases. Keep runtime output enabled when proving crash recovery; `--no-write-runtime` is fixture-only and intentionally cannot prove journal durability. Live apply rejects that flag. A successful create preserves the accepted plan unchanged, durably records its intent before the remote call, atomically retains the returned runtime ID, then carries the read-back binding into `post-apply-plan.json` and `live-registry.json`; a missing post-apply runtime fails closed. The terminal report uses the post-apply health rather than the pre-mutation status. A partial create is retained even if the immediately following action fails. After a process death, a fresh process either reuses a bound runtime, proposes one exact supported provider-key match for reconciliation, or blocks on the unresolved intent. It never creates a second runtime.

## Partial recovery

- Recover only roles whose dependencies and writer scopes are clear.
- Leave active roles untouched and queue bootstrap/repair events through ATLAS INBOX.
- A missing `create_if_missing` role may be planned for creation after acceptance.
- A missing `manual_gate` role stops for an exact decision.
- A missing `reuse_only` role stops until ATLAS MAIN resolves the accepted predecessor epoch.
- A stale runtime ID may be rebound only when complete discovery yields exactly one candidate and no unaccepted claimant.

## Task rollover

1. Persist the predecessor runtime ID, outstanding events/questions, writer scope, cwd/project, Git identity, prompt/manifest digest, and recovery checkpoint.
2. Create or resume one successor under an exact accepted packet. Bootstrap with a stable event ID and generated logical bindings.
3. Prove title, runtime policy, pin, prompt markers, routes, receipt delivery, and continuity reconstruction.
4. Record the predecessor as a related epoch and obtain ATLAS MAIN acceptance.
5. Mark the predecessor `ARCHIVE_ELIGIBLE` only after zero pending routes and successor readback. Archival itself is a separate lifecycle action and is never performed by the default recovery command.

## Crash or interruption recovery

Re-run the dry-run command. Do not rely on the last chat message. Read the runtime receipt and any partial-create IDs. If the prior process stopped after creating a runtime, the retry must bind that runtime by logical role and repair it. If discovery is unavailable, preserve every role as `UNKNOWN` and make no mutation.

Heartbeat automations are interruption recovery only. Rebind each heartbeat by logical role, prove a single active schedule, and suppress unchanged runs. They do not replace foreground coordination.

## Reconciliation and health audit

For each role, prove:

- one accepted runtime epoch and no unaccepted duplicate claimant;
- unarchived and pinned state;
- canonical title, prompt markers, model/effort floor, cwd/project/environment, and approval posture;
- writer-scope lease compatibility;
- upstream/downstream logical routes and a correlated readback receipt;
- no pending manual answer, notification, or inbound receipt stranded on a predecessor;
- continuity and source-of-truth references are readable.

For components, prove `_stack` operator commands, service-bus dedupe/retry, notification-ledger state, DiscordOS sole-writer routing, Foundation read-model reconstruction, Lifeline wake targets, Playbook Observer read-only behavior, Cortex activation hold, and exactly one heartbeat per declared automation.

## Failure handling and rollback

- Duplicate task or writer: stop, preserve all candidates, emit a collision receipt, and wait for exact disposition.
- Partial create: retain the created ID, emit `PARTIAL_CREATE`, and retry by role. Never delete as rollback.
- Title/runtime/pin/bootstrap failure: stop after the first failed mutation; do not continue to later roles.
- Active target: queue; do not steer, interrupt, archive, or replace.
- Unknown state: no mutation.
- Desktop observation failure: reject the complete snapshot. Require the trusted current immutable receipt, reject any older candidate named by its cumulative supersession list, and reject an incomplete head/candidate chain. Never apply a partial subset, infer idle from absence, or use observation to establish task existence.
- Missing source thread ID/host/title or bad event ID/digest: quarantine as a transport-contract failure; never acknowledge it as delivered. A corrected event must explicitly supersede the held event and carry a newly computed canonical payload digest.
- Apply drift: the acceptance is invalid if manifest or plan digest changes. Generate a new dry-run and obtain a new acceptance.

## Durable versus runtime placement

- Canonical contract, prompt fragments, schemas, answered-decision registry, live-mapping continuity seed, runbook, audit, and generated view: committed ATLAS paths.
- Mutable live registry, plans, receipts, and acceptance records: `runtime/atlas/workflow-recovery/`.
- Scratch app-server schemas/logs: `tmp/`.
- Durable fixtures: `tests/fixtures/atlas-workflow-recovery/`.
- Secrets: `secrets/` only; the recovery artifacts must remain secret-free.
