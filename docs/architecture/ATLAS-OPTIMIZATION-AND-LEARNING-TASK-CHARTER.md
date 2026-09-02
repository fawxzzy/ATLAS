# 02 ATLAS Optimization & Learning task charter

Status: accepted  
Logical role: `atlas.workflow-optimization`  
Canonical visible title: `02 ATLAS Optimization & Learning`

## Mission

This is the single standing task for improving how work moves through ATLAS,
the local Windows host, Codex, ChatGPT, imported or otherwise authorized Claude
evidence, and the durable receipts emitted by software in the governed stack.
It owns cross-system discovery, workflow measurement, compute and context
efficiency, historical learning, repetition-to-automation discovery, and
admitted improvements to ATLAS-root workflow governance.

The task is a coordination and learning owner, not an omniscient context store
or a catch-all execution owner. "All available context" means evidence that is
currently retrievable through an authorized filesystem root, supported task or
history readback, explicit import, connector, tool, receipt, or operator-provided
artifact. Unavailable context remains `UNKNOWN`.

## Unified task lineage

This task is the only active standing owner for the three conversations that
Zac explicitly merged. Their useful contracts are components here; their old
conversation surfaces are not alternate queues or fallback runners.

| Conversation | Durable task identity | Disposition | Component retained here |
| --- | --- | --- | --- |
| `02 ATLAS Optimization & Learning` | `01a03746-df21-7770-bf72-41adb70052b4` | canonical active task | priority loop, measurement, governance, instructions, real-workflow adoption, and unified reporting |
| `02 Compute Cleanup & ATLAS Optimization` | `01a034f8-0701-7ac2-b2ca-af9ee21978b2` | absorbed and archived | `component.host-compute-and-storage`: Windows compute, process, cache, disk, restart, and bounded cleanup work |
| `02 Repair and Learn` | `01a02fc6-07b8-70e1-9798-25dabc4e07e0` | absorbed and archived | `component.repair-and-learn-corpus`: exact-cursor historical review, deduplication, Engineering Memory candidates, and automation discovery |

The one recurring heartbeat targets the canonical active task. It selects the
highest-value non-conflicting cluster across the components, uses one compact
checkpoint, and never wakes or writes to either archived predecessor. Its
stable automation ID may remain `repair-and-learn` for migration continuity;
the ID is not a second role or a second program.

## Atlas-first execution contract

This task must use Atlas while improving Atlas. Atlas is the operating substrate
for every cluster, not merely the subject of periodic documentation work.

Before mutation, the task must answer `Have we already solved this problem?`
from Engineering Memory and current durable evidence, then either reuse the
precedent or record why it does not apply. It must read the smallest current
slice of the workflow manifest, latest task checkpoint, exact selector or
admitted packet, binding and writer-lease state, and relevant receipts.

Execution and closeout use the existing canonical seams:

- `atlas.job-envelope.v2` for dispatched executable work;
- `atlas.execution-receipt.v2` for the bounded result and observable latency,
  retry, history-read, token/cache/cost, verification-reuse, and quality data;
- exact resource claims, correlations, owner-first routing, and wake conditions;
- the shared task-context checkpoint for deterministic continuation; and
- Engineering Memory precedent search, mutation gate, evidence bundle, and
  candidate promotion rather than a parallel learning system.

When a cluster exposes a real Atlas gap, this owner may make an admitted root
contract, prompt, recovery, measurement, or automation correction and must test
it through at least one representative inheriting workflow. It must not create
a second scheduler, protocol, queue, receipt type, memory system, or supervisor
task. Atlas setup work counts as progress only when it removes a measured
bottleneck, enables a real workflow, or strengthens proof at an existing risk
boundary.

### Anti-churn admission gate

One observed, non-product-blocking failure is retained as one canonical
observation. It does not fan out to additional analysis workers, Engineering
Memory promotion, or implementation until matching content-addressed evidence
recurs, the issue blocks product work, or bounded diagnostics identify a cause.
This suppresses receipt multiplication without discarding the original evidence.

Task-corpus coverage keeps two identity denominators. Standing and user-visible
task identities are material coverage. Ephemeral reviewers and bounded helpers
are auxiliary coverage: they remain countable for cost and lifecycle analysis,
but an ephemeral-only change cannot trigger a material handoff merely because
the optimization program created it. Both gates use existing job, receipt,
checkpoint, and Engineering Memory seams; they create no new protocol.

### Common release-safety controls

`ACCEPT_BOUNDED_COMMON_CONTROL_R001` installs two root-owned reusable gates.
PC-024 performs strict same-origin Workbox URL canonicalization before exact
coverage, byte-count, and SHA-256 comparison. It rejects foreign origins,
unsafe decoded paths, traversal, duplicate canonical keys, and unadmitted query
or fragment changes; it never reduces identity to a basename. PC-025 performs a
read-only immutable Vercel workspace, project, organization or team, binding
hash, reparse-path, and supported command-profile preflight before any CLI
invocation. Missing, generated, mismatched, ambiguous, wrong-team, or
unclassified linkage surfaces fail closed.

These common controls are governance and validation primitives only. Product
verifier adoption remains owner work. Vercel invocation, `.vercel` mutation,
provider cleanup, deployment, production, credentials, and deletion remain
separately governed effects. The canonical implementation is
`ops/atlas/release_safety_controls.py`; its accepted Rule and Failure Mode
provenance is retained in
`docs/memory/decisions/decision-atlas-common-release-safety-controls-r001.json`.

Completed standing-task consolidation uses the installed
`atlas-thread-capability-retirement` skill. The optimization owner measures and
improves that conversion workflow, verifies that reusable responsibilities are
wired into skills or a genuinely stateful successor agent, and tracks archival
latency and failures. It must preserve checkpoints, receipts, historical
provenance, active writer/lease safety, and task-service readback; it may not
declare a task archived merely because routing was updated or an archive request
was submitted.

## Context domains

| Domain | Evidence this task may gather | Default work | Hard boundary |
| --- | --- | --- | --- |
| ATLAS | Root governance, registries, receipts, runtime state, stack docs, named repositories, task continuity, and provider readback when separately authorized | Index, reconcile, benchmark, learn, propose or make admitted root-governance improvements | Does not absorb repository writers, Release, provider, production, Supabase, live-data, secret, billing, or destructive authority |
| Windows host | Explicitly accessible files, configuration, installed tools, processes, services, storage, logs, and performance evidence | Diagnose latency, compute, storage, process, cache, toolchain, and restart-related bottlenecks; prepare bounded cleanup | No ambient screen/history claim; no secrets extraction; no deletion or retention change until exact targets and retention class are proven |
| Codex | Current task context, projects, attached folders, local task/session evidence, `AGENTS.md`, memories, skills, plugins, MCP configuration, automations, terminal/browser/app evidence, and supported readbacks | Reduce context amplification, tool exposure, retries, task fragmentation, model overuse, and verification duplication; improve durable instructions and recovery | A task title, goal, plugin, broad filesystem access, or remembered fact does not create external or protected effect authority |
| ChatGPT | Every task or chat retrievable through supported app readback, explicit export, project attachment, or operator-provided artifact, with exact task identity and cursor | Review bounded historical pages, reconcile decisions and failure patterns, deduplicate against current governance, and advance content-addressed cursors | ChatGPT private/cloud history is not ambiently visible; unreadable or unexported tasks remain inventoried `UNKNOWN`, and conversation prose never outranks current source or validated receipts |
| Claude | Explicitly imported Claude Code or Claude Cowork instructions, settings, projects, project memories, skills/plugins, recent chats, MCP, hooks, commands, subagents, and authorized local/exported artifacts | Reconcile useful patterns with ATLAS and Codex, deduplicate conflicting instructions, preserve source provenance, and route candidates through Engineering Memory | Claude cloud/private context is not ambiently visible; nothing is treated as current until imported, exported, connected, or read back through a supported authorized surface |
| Software receipts | Every retrievable durable receipt or receipt-like lifecycle artifact from ATLAS, repositories, CI, Git/provider tooling, deployments, databases, browsers, terminals, desktop applications, and other explicitly scoped software | Inventory by producer/schema/identity, correlate with the originating task and effect boundary, deduplicate, measure retries and lifecycle gaps, and learn reusable failure or verification patterns | Receipt access is read-only evidence intake; it does not grant provider, production, live-data, secret, billing, destructive, merge, deployment, or owner-repository authority, and secrets or raw tool outputs are never copied into the learning corpus |
| Cross-system synthesis | Content-addressed summaries, source references, accepted decisions, measurements, and candidates from the domains above | Build one coherent operating model, identify repetition, measure bottlenecks, and ratchet reusable improvements | Never paste raw histories into the active task, silently merge conflicting authorities, or treat inference as verified state |
| Operator | Direct requirements, approvals, corrections, reported symptoms, and acceptance decisions from Zac | Preserve intent, surface meaningful decisions in this task, and record reusable approved rules in their canonical owner | Silence is not approval; current-task authorization cannot be generalized to protected effects or unrelated owners |

Codex projects and imports are acquisition mechanisms, not new truth classes.
Durable ATLAS artifacts, immutable source identity, validated receipts, and fresh
supported readback continue to outrank remembered or conversational prose.

## Named work domains

1. **Workflow performance** — wall clock, time to useful output, prompt size,
   history reads, tool calls, retries, model/reasoning routing, service tier,
   commentary churn, and verification reuse.
2. **Compute and host health** — Windows process, service, storage, cache,
   runtime, dependency, and restart diagnostics; bounded cleanup only after
   retention and effect authority are proven.
3. **Context engineering** — source indexing, retrieval-on-demand, instruction
   layering, task/project structure, compact checkpoints, cursor reuse, and
   prompt/tool-surface minimization.
4. **Codex configuration** — `AGENTS.md`, projects, memories, skills, plugins,
   MCP, automations, model policy, task lifecycle, and supported local history
   or application controls.
5. **Claude integration** — explicit import or export intake, instruction and
   project reconciliation, provenance preservation, conflict detection, and
   migration of accepted reusable patterns into canonical ATLAS seams.
6. **Historical learning** — cursor-driven review of every retrievable,
   authorized Codex, ChatGPT, and Claude task corpus plus content-addressed
   software receipts, precedent search, candidate deduplication, rejection of
   solved patterns, and Engineering Memory promotion through existing gates.
7. **Automation discovery** — identify repeated deterministic work, define the
   smallest existing seam that can own it, and require exact owner admission
   before implementation or activation.
8. **Governance and instructions** — maintain the inherited optimization
   contract, truth hierarchy, authority separation, writer discipline,
   lifecycle labels, checkpoints, receipts, and rollback rules.
9. **Adoption and verification** — route architecture changes to Architect,
   already-admitted mechanical adoption to Ops, owner-local fixes to the exact
   source owner, and verify that improvements affect real workflows.

Across historical sources, select the most recently updated authorized source
and its newest unread content first, then work backward through exact durable
cursors. This recency preference exists because newer decisions and code often
supersede older material. It never skips an older dependency needed for current
identity, provenance, authority, security, privacy, migration, rollback, or
contradiction resolution.

The ATLAS Book is a dual human and AI system map. Human chapters explain the
system; `docs/atlas-book/AI-SYSTEM-MAP.v1.json` provides a compact pointer map
that every generated Codex context inherits. Neither surface replaces current
owner truth, receipts, bindings, provider readback, or runtime checkpoints.

## Continuous operating loop

1. **Rehydrate through Atlas** from the workflow manifest, latest shared task
   checkpoint, exact selector or packet, binding and writer state, and valid
   content-addressed receipts. Do not reconstruct state from chat prose.
2. **Search precedent** before mutation and record reuse or explicit rejection.
3. **Discover** only the source slice needed for the current cluster. Prefer
   exact paths, cursors, manifests, and supported imports over broad history
   scans.
4. **Classify** every important claim as current fact, accepted durable fact,
   assumption, candidate, stale evidence, `UNKNOWN`, or separately governed
   authority.
5. **Measure** the current bottleneck and record the preimage. Missing token,
   cache, cost, or timing telemetry stays `UNKNOWN`.
6. **Choose** the smallest coherent ratchet with a quality floor and rollback
   boundary. Reuse solved precedent before inventing a new mechanism.
7. **Execute through canonical Atlas seams** only within the admitted writer and
   effect scope. Use the existing v2 job and receipt contracts where work is
   dispatched; never introduce a parallel orchestration surface.
   Keep discovery, source edits, external effects, and destructive work as
   separate authority boundaries.
8. **Verify** the touched contract and one representative workflow surface.
   Fewer turns or a cheaper model alone is not proof of improvement.
9. **Learn** by deduplicating the result against Engineering Memory and routing
   any retained candidate to its exact owner.
10. **Persist and continue** with a compact task checkpoint containing Done,
   Now, Next, decisions, blockers, receipts, authority qualifiers, source refs,
   and the next cursor or wake condition.

## Task structure and routing

Keep one main standing task because these work domains share the same
cross-system measurement, learning, and governance objective. Use bounded
components, corpus batches, or owner-routed packets rather than creating a new
standing conversation for each source domain.

Separate independent product outcomes into their owner tasks. This task may
inspect and optimize the workflow around those outcomes, but it must not become
their implementation, release, provider, production, or destructive owner.

The former `atlas.repair-and-learn` task is an absorbed predecessor implemented
as `component.repair-and-learn-corpus`. Its raw history is not the active task
context. Resume it from durable cursors and content-addressed review batches.

## Completion and ratchet rule

This standing task is never "complete" merely because a policy file exists.
A ratchet is accepted only when:

- the preimage and postimage are identified;
- the representative quality floor passes;
- the workflow that should inherit the change is verified;
- the authority and rollback boundaries remain intact;
- the result and remaining bottleneck are persisted; and
- the next highest-value non-conflicting cluster is selected or a precise wake
  condition is recorded.

The portfolio target remains greater-than-two-times effective speed, measured
across representative work clusters rather than inferred from a single model,
task, or shorter conversation.

## Supported Codex context references

- Projects and chats: <https://learn.chatgpt.com/docs/projects>
- Long-running work: <https://learn.chatgpt.com/docs/long-running-work>
- `AGENTS.md` discovery: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- Memories: <https://learn.chatgpt.com/docs/customization/memories>
- Import from Claude and other agents: <https://learn.chatgpt.com/docs/import>

Required rules stay in versioned ATLAS instructions and contracts. Memories
remain a recall layer, and imports remain provenance-bearing inputs that must be
reviewed before their permissions, MCP servers, hooks, or commands are trusted.
