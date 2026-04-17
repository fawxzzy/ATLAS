# ATLAS Codex Context Runbook

This runbook defines the root-owned context-pack flow for root-launched Codex work.

ATLAS root selects context. Child repos remain owners of their own truth.

## Rule

Pattern: Intent-Routed Context

Root selects the minimum relevant ATLAS surfaces for a task. Intelligence compounds by routing to the right existing owner, not by re-indexing or copying everything.

Freeze this rule:

- federate, do not duplicate
- raw evidence stays where it lives
- promoted truth is tracked deliberately
- runtime and query artifacts are rebuildable
- clients select the right slice instead of dumping the whole stack into every task

Do not install Playbook into ATLAS root as a second truth source. Reference Playbook through root-owned inventory and context routing instead.

## Bootstrap Contract

Every root-launched Codex task should bootstrap in this order:

1. `stack.yaml`
2. `stack.lock.yaml`
3. `docs/registry/STACK-REPO-INVENTORY.json`
4. the relevant awareness slices
5. related initiative, proposal, and trust-posture refs
6. only then the target repo docs or code

The context-pack builder emits that order explicitly in `bootstrap_contract.ordered_reads`.

## Intent Routing

Use these owner lanes:

- `governance` -> Playbook
- `execution` -> Lifeline
- `orchestration` -> `_stack`
- `doctrine/platform` -> Atlas repo
- `knowledge` -> knowledge lane
- `topology/git` -> repo inventory + lock + debt ledger
- `operator/conversation` -> awareness + status + working memory

Current route surfaces:

- governance: `repos/fawxzzy-playbook/docs/commands/verify.md`, `repos/fawxzzy-playbook/docs/rules/verify-rules.md`, `repos/fawxzzy-playbook/docs/contracts/verify-output.md`
- execution: `docs/registry/ATLAS-TOOL-REGISTRY.json`, `repos/fawxzzy-lifeline/docs/privileged-execution.md`, `repos/fawxzzy-lifeline/examples/privileged-execution/*.json`
- orchestration: `docs/ops/ATLAS-SESSION-RUNBOOK.md`, `repos/_stack/docs/runbooks/STACK-WORKER-FLOW.md`, `repos/_stack/docs/dispatcher-protocol.md`
- doctrine/platform: `repos/fawxzzy-atlas/docs/ATLAS_PLATFORM_MODEL.md`, `repos/fawxzzy-atlas/docs/ATLAS_UAPI.md`, `repos/fawxzzy-atlas/docs/OWNERSHIP_BOUNDARIES.md`
- knowledge: `docs/knowledge/QUERY-CONTRACT.md`, `runtime/cortex/query/knowledge/bundle.json`
- topology/git: `docs/audits/STACK-REPO-INVENTORY.md`, `docs/audits/STACK-DEBT-LEDGER.md`, `runtime/receipts/validation/stack-validation.latest.json`
- operator/conversation: `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`, `docs/ops/ATLAS-STATUS-RUNBOOK.md`, `runtime/cortex/catalog/memory/working-memory.latest.json`

## Context-Pack Outputs

Builder:

- `python ops/atlas/build_codex_context.py --task-id <task-id> --objective "<objective>" --intent-class <intent>`

Outputs:

- `runtime/atlas/context-packs/<task-id>/context.json`
- `runtime/atlas/context-packs/<task-id>/context.md`

Prompt renderer:

- `python ops/atlas/prepare_codex_task.py --task-id <task-id>`

The renderer prints a copy-paste-ready Codex prompt from the saved context pack.

## Size Discipline

Context packs must stay selective.

- include only the route surfaces needed for the declared intent
- include only the target repo inventory entries
- include only related initiatives, proposals, attention items, and working-memory items
- keep trust posture visible
- keep Verta metadata-only and untrusted

Do not include:

- raw repo dumps
- whole transcript history
- irrelevant repos
- copied child-repo truth

Repo-owned evidence refs may appear as deferred refs. They are references to open later, not hydrated copies.

## Determinism

Given the same:

- task id
- objective
- intent class
- target repo ids or paths
- root source surfaces

the builder must emit the same selected refs and `context_digest`.

No wall-clock timestamps belong in the context payload.

## Verification

Expected checks for this slice:

- identical task inputs produce the same selected refs and `context_digest`
- a Mazer task pulls the Mazer initiative, its proposed soak session, the Mazer repo inventory entry, and current trust/attention surfaces
- a Playbook task pulls verify rules and bindings, not unrelated repo content
- a Lifeline task pulls tool registry plus capability and approval examples
- Verta stays visible but metadata-only and untrusted
- `python ops/validation/validate_stack.py --ratchet` stays green
