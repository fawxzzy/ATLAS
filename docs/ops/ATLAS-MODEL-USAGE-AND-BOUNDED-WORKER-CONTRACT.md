# ATLAS model usage and bounded-worker contract

Status: local source candidate; publication and runtime adoption are separately
gated.

Contract version: `atlas.execution-profiles.v1`

## Purpose

ATLAS uses provider-neutral logical execution profiles while keeping the active
provider mapping explicit and versioned. A bounded packet selects a profile.
A standing role declares its default and minimum profile through an exact
versioned role-policy map. The resolver verifies the requested and effective
identities; it never dispatches work, silently changes a model, or acts as a
second scheduler.

This contract supersedes only the earlier all-Sol profile mapping. It preserves
the read-only baseline, role/runtime fail-closed behavior, requested/effective
UNKNOWN behavior, five canary classes, and every external-provider hold.

## Official evidence

Evidence was fetched on 2026-07-27 from:

- [GPT-5.6 model guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6)
- [GPT-5.6 migration guide](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol.md)
- [GPT-5.6 prompting guide](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md)
- [Codex pricing and usage](https://learn.chatgpt.com/docs/pricing#what-are-the-usage-limits-for-my-plan)

The model guide identifies Sol as the flagship tier, Terra as the balanced
lower-price tier, and Luna as the efficient high-volume tier. The migration
guide explicitly requires tier-aware family mappings for routers. The prompting
guide recommends the lowest reasoning effort that passes representative evals
and reserves `max` for the hardest quality-first work. Codex usage varies with
model, context, reasoning, tools, retrieval, and caching; prompt length alone is
not a reliable budget.

These sources do not turn documented usage ranges into hard task budgets.
Exact token and cost observations remain nullable when the runtime does not
expose them.

## Canonical mapping

| Profile | Current mapping | Default effort | Allowed effort | Intended work |
| --- | --- | --- | --- | --- |
| FAST | `gpt-5.6-luna` | `low` | `low`, `medium` | extraction, classification, transformation, structured summaries, status projections, dedupe rendering |
| STANDARD | `gpt-5.6-terra` | `medium` | `medium`, `high` | routine bounded implementation, non-critical review, everyday tool work |
| DEEP | `gpt-5.6-sol` | `high` | `high`, `xhigh` | complex analysis, scheduler recovery, migration planning, security review, architecture |
| CRITICAL | `gpt-5.6-sol` | `xhigh` | `xhigh`, `max` | highest-risk quality-first work |

Rules:

1. The bounded packet selects the profile; the thread title does not.
2. A role floor cannot be silently clamped. A below-floor packet is rejected
   and must be explicitly reissued.
3. Failed acceptance evidence may escalate a packet upward.
4. High-risk or CRITICAL work never downgrades for cost alone.
5. `max` requires an explicit benchmark exception identifier.
6. `ultra` is not part of this mapping.
7. Unproven effective model, reasoning, provider, adapter, runtime identity, or
   scheduler-admitted turn blocks execution.
8. Fallback is never silent.

Fitness and Mazer retain a `high` reasoning floor. Valid examples include
STANDARD/Terra `high`, DEEP/Sol `high` or `xhigh`, and CRITICAL/Sol `xhigh`.
FAST/Luna and STANDARD/Terra `medium` fail closed for those roles.

## Requested and effective observation

Every requested execution records:

- profile ID and version;
- model and reasoning effort;
- selection reason and workload class;
- context, token, turn, and retry budgets;
- evidence tier;
- fallback and escalation policies;
- the target logical role, host, runtime thread, and runtime epoch;
- an optional benchmark exception when `max` is requested.

Every effective observation records:

- model and reasoning effort;
- provider;
- adapter ID and version;
- runtime version and readback source;
- the effective logical role, host, runtime thread, runtime epoch, and turn;
- fallback reason, which is null for an exact execution.

UNKNOWN is an honest observation, not an execution identity. If the selected
profile requires proven effective identity, UNKNOWN blocks before work begins.
Requested and effective model and reasoning must match exactly. A provider or
adapter mismatch also blocks. The requested role, host, runtime thread, and
runtime epoch must match the scheduler-admitted binding. The effective binding
must additionally match the exact scheduler-admitted turn. Every binding value
must be current, non-empty, and non-UNKNOWN. The observation retains all three
bindings as durable proof. A runtime restart or new execution turn requires new
scheduler-admitted evidence; neither is silently reconciled.

The resolver validates every registry input and its complete output against the
closed registry and observation schemas before it may return `ADMITTED`.
Missing required fields and unknown properties therefore block even when the
hand-written semantic checks would otherwise pass. The CLI uses the same closed
registry-schema boundary.

## Budgets and usage

Context budgets cap the input bundle and repeated-evidence bytes. Turn budgets
set a maximum and escalation checkpoint. Retry budgets name retryable and
terminal classes. Token budgets may be observation-only when the host does not
expose enforceable token ceilings.

Enforceable limits are inclusive: equality passes and one unit over blocks.
Input-bundle and repeated-evidence bytes must remain under their context caps,
the required immutable-reference count must be met, turns and retry attempts
must not exceed their maxima, and a reached escalation checkpoint requires an
explicit checkpoint observation. When token enforcement is `HARD_LIMIT`, the
relevant exact token observations must be present and within the output and
total ceilings. Nullable token observations are valid only for limits that are
not being enforced, including `OBSERVE_ONLY`.

Exact usage fields are nullable:

- input tokens;
- cached input tokens;
- output tokens;
- reasoning tokens;
- provider cost, which must be a finite non-negative number when present.

The following proxies are always recorded:

- input bundle bytes;
- repeated evidence bytes;
- unique evidence references;
- files read;
- turns;
- tool calls;
- child workers;
- retry attempts;
- correction loops;
- whether the escalation checkpoint was observed;
- elapsed milliseconds to material state.

## Bounded-worker boundary

- `ATLAS MAIN` is the only canonical scheduler.
- The resolver is pure, deterministic, and non-dispatching.
- An adapter applies the requested profile and reports effective observations.
- A worker executes only the bound packet and returns a receipt; it does not
  route work.
- Codex is the first canary adapter.
- Claude and LiteLLM remain uninstalled and separately gated.

Destination routing, owner return, leases, and lifecycle transitions remain in
the existing workflow scheduler. This source packet adds no live dispatcher,
provider call, runtime activation, or global configuration.

## Canary contract

The immutable baseline is
`onv1_f2c164eb892f46fa66ea834c6bba96206a3109a9e6817b765d1546690e900502`.

| Canary | Starting profile | Required evidence |
| --- | --- | --- |
| STATUS_PROJECTION | FAST | E1 |
| ROUTINE_SOURCE_CORRECTION | STANDARD | E2 |
| INDEPENDENT_REVIEW | STANDARD or DEEP | E3 |
| SCHEDULER_RECOVERY | DEEP | E3 |
| MIGRATION_PLANNING | DEEP | E3 |

The completed-canary set must contain these five unique identities exactly.
Every accepted campaign result binds the baseline event and byte count, reports
all six comparison dimensions with baseline/candidate/pass evidence, and
includes a reproducible reduction calculation. Repeated evidence must not
exceed 2,480 bytes, a minimum 30 percent reduction from the 3,543-byte baseline
proxy. Savings count only when no acceptance criterion or required evidence
reference is dropped and quality, completeness, and tool correctness do not
regress.

Rule: a versioned profile mapping is immutable. Model, allowed and default
reasoning, elevation rule, workload classes, and the complete standing-role
default/floor/minimum-reasoning map all require a new reviewed profile version
when changed.

Failure Mode: validating individual fields without validating the complete
closed registry and observation permits schema-invalid work to appear admitted.
The resolver and CLI must schema-check their inputs and emitted object before
admission. A non-finite cost is invalid JSON evidence and is normalized to null
only after a blocking diagnostic is retained.

## Migration

1. Publish the registry, schemas, resolver, fixture, tests, and this document as
   one reviewed contract.
2. Keep existing manifest model/effort fields readable.
3. Add new profile observations without rewriting historical receipts.
4. Extend the current Codex adapter only in a separately reviewed packet.
5. Run one canary class at a time.
6. Activate runtime enforcement only after cold-start reconstruction and exact
   readback prove requested/effective identity.
7. Keep external adapters absent until separately authorized.

## Rollback

Disable new-profile admission and restore the prior registry pointer. Continue
reading immutable new observations without rewriting history. Preserve queues,
reservations, owner returns, and UNKNOWN values. A rollback never authorizes a
silent model substitution.

## Stop conditions

Stop and retain the packet when:

- the registry version or official mapping drifts without a new reviewed
  version;
- a requested/effective identity cannot be proven;
- a role/runtime/host/epoch/turn binding is ambiguous;
- a silent model, reasoning, provider, or adapter downgrade appears;
- a canary reduces context by dropping acceptance criteria or evidence;
- a new provider installation, authentication, or call becomes necessary;
- an eighth source path or overlap with the frozen PR #149 or owner-result
  packet is required.

## Verification

`tests/test_atlas_model_governance_contract.py` validates the four-profile
matrix, exact role floors, Fitness high-floor behavior, requested/effective
identity, host/runtime/epoch/turn drift, UNKNOWN and downgrade rejection, closed
registry inputs and emitted observations, finite cost evidence, exact profile
mappings, hard and observation-only budgets, escalation checkpoints, complete
five-canary campaigns, provider-neutral boundaries, canonical JSON, and
portable paths.
