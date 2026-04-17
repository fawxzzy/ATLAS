# Playbook Adoption Matrix

This matrix is the root-owned visibility surface for cross-repo Playbook convergence.

Current statuses are evidence-based working assessments from stack-root artifacts. They do not become repo-owned truth until the named verification artifact exists in the owning repo or stack surface.

## Status Legend

- `partial`: current artifacts show meaningful alignment, but explicit contract adoption is not yet proven
- `missing`: no explicit contract adoption artifact is visible from the stack root yet
- `n/a`: the surface is intentionally out of the current adoption gate

## Matrix

| Surface | Scope | Current Status | Evidence Now | Verification Needed | First Slice |
| --- | --- | --- | --- | --- | --- |
| `stack` | stack coordination root | `partial` | `README-STACK.md`, `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`, `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` | root-visible adoption and continuity report | publish and maintain the stack-level report surface |
| `playbook` | repo-local governance owner | `partial` | `README-STACK.md` routes governance, policy, and verification to Playbook | human-readable spec plus machine-readable contract export | export the canonical contract |
| `atlas` | doctrine and context-routing owner | `partial` | awareness-first and conversation docs already enforce grounded, explicit files | context or verify output tied to the shared Playbook contract | route contract refs and continuity refs by intent |
| `lifeline` | approvals and execution owner | `partial` | current stack doctrine already routes execution and approvals here | repo-local artifact that names the implemented contract version | align approvals, receipts, and execution surfaces |
| `_stack` | orchestration and resume owner | `partial` | current stack doctrine already routes worker flow here | repo-local artifact that names the implemented contract version | align merge and resume patterns |
| `knowledge lane` | stack-owned import, catalog, and promotion lane | `partial` | `docs/knowledge/IMPORT-RUNBOOK.md`, `docs/knowledge/QUERY-CONTRACT.md`, `docs/knowledge/PROMOTION-RUNBOOK.md` | explicit continuity promotion flow from handoff or archive into queryable outputs | wire conversation continuity into the import and promotion lane |
| `fitness` | application repo | `missing` | visible in `stack.yaml` and inventory only | repo-local adoption note, verify output, or explicit defer decision | decide current scope and adoption target |
| `mazer` | application repo | `missing` | visible in `stack.yaml`, inventory, and initiative refs only | repo-local adoption note, verify output, or explicit defer decision | decide current scope and adoption target |
| `stream` | incubating application repo | `missing` | visible in `stack.yaml` and inventory only | repo-local adoption note or explicit incubating defer decision | decide whether it joins the first rollout |
| `nat1-games` | incubating application repo | `missing` | visible in `stack.yaml` and inventory only | repo-local adoption note or explicit incubating defer decision | decide whether it joins the first rollout |
| `playbook-demo` | demo surface | `n/a` | demo repo exists in `stack.yaml` and inventory | explicit demo-role decision if reused for contract demos | keep out of the critical path unless intentionally used as a mirror |

## Verification Rule

A status should move only when the owning surface has a concrete artifact such as:

- a repo-local spec
- a machine-readable contract file
- a repo-local verify output that names the contract version
- a stack-visible report or receipt that proves the rollout

Until then, the matrix is an honest working assessment, not proof.
