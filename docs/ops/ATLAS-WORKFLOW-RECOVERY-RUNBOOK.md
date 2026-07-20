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

4. Inspect `runtime/atlas/workflow-recovery/plan.json`, `live-registry.json`, and `RECEIPT.json`. Runtime output is intentionally ignored by Git. The plan digest always excludes `generated_at`; when an observation is present it also excludes volatile receipt identity, source host, and timestamps. The validated activity effects, recovery decisions, cwd locator, and any resolved creation/bootstrap cwd remain digest-bound.
5. Reconcile every role as `HEALTHY`, `DEGRADED`, `MISSING`, `DUPLICATE`, `BLOCKED`, `HELD`, or `UNKNOWN`. Also inspect `unbound_runtime_claims`; they are preserved inventory and must never trigger create or lifecycle actions. Do not translate `notLoaded` into missing and do not translate an archived rollout file into an accepted supersession.
6. Read `docs/registry/ATLAS-WORKFLOW-DECISIONS.v1.json`. Repeat only `OPEN` questions; suppress `ANSWERED`, `EXPIRED`, and `SUPERSEDED` questions. Transport retention is not execution completion.
7. Recover ATLAS MAIN first. Do not initialize queues or owners until the root role is unique, readable, unarchived, pinned, and accepted.
8. Initialize ATLAS INBOX, MANUAL MESSAGES, FAWXZZY QUESTIONS, AI QUESTIONS, and FAWXZZY MESSAGES in parallel only after unique title/role bindings are proven.
9. Initialize the control plane, domain coordinator, and owners in parallel only across distinct writer scopes. A standing role being active is a hold, not an invitation to steer it.
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

Creation sends one canonical modern named profile (`:read-only`, `:workspace`, or `:danger-full-access`) through the app-server `permissions` field and omits legacy `sandbox`; unknown identifiers and legacy tokens such as `danger-full-access` fail closed. Bootstrap uses the same accepted cwd. The command preflights all required capabilities before the first mutation. The current Codex app-server supports list/read/start/resume/unarchive/title/model/effort/cwd/bootstrap operations, but does not expose task pin mutation or pin readback. Because every standing role requires a pin, creation or pin repair fails closed before mutation. `ATLAS-WORKFLOW-MAN-001` explicitly selected no manual fallback. The desktop observation bridge closes only supported activity provenance; it does not close the pin gate. Live recovery apply and archive-readiness remain unproven.

## Fixture-only creation and retry proof

Fixture apply cannot reach live tasks:

```powershell
python ops/atlas/workflow_recovery.py recover --apply --adapter fixture --fixture tests/fixtures/atlas-workflow-recovery/missing-task.json --acceptance tests/fixtures/atlas-workflow-recovery/fixture-acceptance.json --no-write-runtime --deterministic
```

The test lane covers healthy, missing, stale-ID, duplicate, active-writer, partial-create, retry, and unknown-state cases. A partial create is retained. The next run discovers it through the stable role marker, repairs it, and never creates a second runtime.

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
