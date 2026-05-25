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
4. `docs/memory/profiles/zachariah_workflow_profile.md`
5. the relevant awareness slices
6. related initiative, proposal, and trust-posture refs
7. only then the target repo docs or code

The context-pack builder emits that order explicitly in `bootstrap_contract.ordered_reads`.

## Branch And Worktree Discipline

Every root-launched Codex lane must declare its execution surface before work starts.

Rules:

- no lane starts until the owner repo is explicit
- no lane starts until the target branch or worktree is explicit
- repo-specific lanes should use clean worktrees
- ATLAS root branches are for stack-root docs, projection, policy, audit, and coordination work only

Pattern:

1. identify whether the lane changes root projection truth or owner-repo truth
2. name the owner repo or root surface
3. name the target branch or worktree
4. open the minimum relevant context for that declared surface
5. start implementation only inside that declared surface

Failure Mode:

- starting multiple root-launched chats without an explicit owner repo and target worktree lets unrelated work inherit the active branch and creates mixed replay branches that are difficult to classify or normalize later

## Named Session Bootstrap Contract

Atlas may also expose named session modes for reusable Codex operating patterns.

Current active registry:

- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- schema: `schemas/atlas.session.mode.registry.v1.json`
- helper: `ops/atlas/list_session_modes.py`

Current active prompt doc:

- `docs/codex/FAST-ITERATION-LOOP.md`
- `docs/codex/CHECKPOINT-SWEEP.md`
- `docs/codex/STRUCTURAL-CHANGE-MODE.md`
- `docs/codex/DEEP-REVIEW-MODE.md`

Current active workflow doc:

- `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`

Rule:

- named session modes resolve through canonical docs and a registry-backed alias layer
- repo input resolves through `docs/registry/STACK-REPO-INVENTORY.json`
- the named mode sets default operating posture before repo-local code is opened

Current opener example:

- `Open the fast iteration loop for fawxzzy-fitness.`
- `Open checkpoint sweep mode for fawxzzy-fitness.`
- `Open structural change mode for fawxzzy-fitness.`
- `Open deep review mode for fawxzzy-fitness.`

That opener should resolve to:

- mode `fast-iteration-loop`
- repo `fitness` at `repos/fawxzzy-fitness`
- localhost assumption `running`
- validation mode `affected-screen`
- patch style `minimal`

Checkpoint opener should resolve to:

- mode `checkpoint-sweep`
- repo `fitness` at `repos/fawxzzy-fitness`
- localhost assumption `running`
- validation mode `related-flow`
- patch style `none-by-default`

Structural opener should resolve to:

- mode `structural-change-mode`
- repo `fitness` at `repos/fawxzzy-fitness`
- localhost assumption `running-if-useful`
- validation mode `scope-based`
- patch style `planned-bounded`

Review opener should resolve to:

- mode `deep-review-mode`
- repo `fitness` at `repos/fawxzzy-fitness`
- localhost assumption `optional`
- validation mode `risk-based`
- patch style `review-first`

Expected first response shape for this mode:

- repo recognized
- mode recognized
- localhost assumption
- validation mode
- patch style
- request for the first small change

Validation commands:

```powershell
python ops/atlas/list_session_modes.py
python ops/atlas/list_session_modes.py --mode-id fast-iteration-loop
python ops/atlas/validate_session_mode_registry.py
python ops/atlas/validate_session_mode_registry.py --mode-id fast-iteration-loop
python ops/atlas/validate_session_mode_registry.py --invocation "Open the fast iteration loop for fawxzzy-fitness." --repo fawxzzy-fitness
python ops/atlas/validate_session_mode_registry.py --mode-id checkpoint-sweep --invocation "Open checkpoint sweep mode for fawxzzy-fitness." --repo fawxzzy-fitness
python ops/atlas/validate_session_mode_registry.py --mode-id structural-change-mode --invocation "Open structural change mode for fawxzzy-fitness." --repo fawxzzy-fitness
python ops/atlas/validate_session_mode_registry.py --mode-id deep-review-mode --invocation "Open deep review mode for fawxzzy-fitness." --repo fawxzzy-fitness
```

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
- execution: `docs/registry/ATLAS-TOOL-REGISTRY.json`, `repos/fawxzzy-lifeline/docs/contracts/privileged-execution-contract.md`, `repos/fawxzzy-lifeline/docs/contracts/ui-proof-passed-receipt-contract.md`, `repos/fawxzzy-lifeline/docs/ops/lifeline-operator-surface.md`, `repos/fawxzzy-lifeline/docs/runbooks/hermetic-validation-operator-flow.md`
- orchestration: `docs/ops/ATLAS-SESSION-RUNBOOK.md`, `repos/_stack/docs/runbooks/STACK-WORKER-FLOW.md`, `repos/_stack/docs/dispatcher-protocol.md`
- doctrine/platform: `repos/fawxzzy-atlas/docs/ATLAS_PLATFORM_MODEL.md`, `repos/fawxzzy-atlas/docs/ATLAS_UAPI.md`, `repos/fawxzzy-atlas/docs/OWNERSHIP_BOUNDARIES.md`
- knowledge: `docs/knowledge/QUERY-CONTRACT.md`, `runtime/cortex/query/knowledge/bundle.json`
- topology/git: `docs/audits/STACK-REPO-INVENTORY.md`, `docs/audits/STACK-DEBT-LEDGER.md`, `runtime/receipts/validation/stack-validation.latest.json`
- operator/conversation: `docs/architecture/AWARENESS-FIRST-WORLD-MODEL.md`, `docs/ops/ATLAS-STATUS-RUNBOOK.md`, `runtime/cortex/catalog/memory/working-memory.latest.json`

Routing rule for execution context:

- prefer Lifeline contract and operator docs over root summaries when the task concerns capability profiles, approvals, execution receipts, proof-pass receipts, or worker-execution receipt lanes
- use Playbook verify docs for verification policy and verify output, not Lifeline execution docs
- use root docs only for routing, linkage, and read-model expectations

## Context-Pack Outputs

Builder:

- `python ops/atlas/build_codex_context.py --task-id <task-id> --objective "<objective>" --intent-class <intent>`

Outputs:

- `runtime/atlas/context-packs/<task-id>/context.json`
- `runtime/atlas/context-packs/<task-id>/context.md`

Prompt renderer:

- `python ops/atlas/prepare_codex_task.py --task-id <task-id>`

The renderer prints a copy-paste-ready Codex prompt from the saved context pack.

Named mode rendering:

- `python ops/atlas/prepare_codex_task.py --mode-id fast-iteration-loop --repo fawxzzy-fitness`
- `python ops/atlas/prepare_codex_task.py --mode-id checkpoint-sweep --repo fawxzzy-fitness`
- `python ops/atlas/prepare_codex_task.py --mode-id structural-change-mode --repo fawxzzy-fitness`
- `python ops/atlas/prepare_codex_task.py --mode-id deep-review-mode --repo fawxzzy-fitness`

Optional context-pack write while rendering a named mode:

- `python ops/atlas/prepare_codex_task.py --mode-id fast-iteration-loop --repo fawxzzy-fitness --write-context-pack`
- `python ops/atlas/prepare_codex_task.py --mode-id checkpoint-sweep --repo fawxzzy-fitness --write-context-pack`
- `python ops/atlas/prepare_codex_task.py --mode-id structural-change-mode --repo fawxzzy-fitness --write-context-pack`
- `python ops/atlas/prepare_codex_task.py --mode-id deep-review-mode --repo fawxzzy-fitness --write-context-pack`

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
