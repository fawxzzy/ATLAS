# Playbook Adoption Matrix

This matrix is the root-owned visibility surface for cross-repo Playbook convergence.

Current statuses are evidence-based working assessments from the stack-root read models, the live repo inventory at `docs/registry/STACK-REPO-INVENTORY.json`, and the Playbook owner export. They do not become repo-owned truth until the named verification artifact exists in the owning repo or stack surface.

## Status Legend

- `adopted`: repo-local owner-truth adoption evidence exists and targeted proof is green, but repo-owned verification truth is not yet landed or not yet strong enough to project `verified`
- `verified`: repo-local adoption evidence and repo-owned verification truth are both reproducible, root-visible, and scoped explicitly so the status does not overclaim broader certification
- `partial`: current artifacts show meaningful alignment, but explicit contract adoption is not yet proven
- `missing`: no explicit contract adoption artifact is visible from the stack root yet
- `n/a`: the surface is intentionally out of the current adoption gate

## Matrix

| Surface | Scope | Current Status | Evidence Now | Verification Needed | First Slice |
| --- | --- | --- | --- | --- | --- |
| `stack` | stack coordination root | `partial` | `README-STACK.md`, `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`, `docs/ops/ATLAS-PLAYBOOK-CONVERGENCE.md` | root-visible adoption and continuity report | publish and maintain the stack-level report surface |
| `playbook` | repo-local governance owner | `partial` | `repos/fawxzzy-playbook/exports/playbook.contract.example.v1.json`, `repos/fawxzzy-playbook/exports/playbook.contract.schema.v1.json`, `repos/fawxzzy-playbook/docs/contracts/PLAYBOOK-CONTRACT.md` | owner-repo verification beyond the export slice | keep the export canonical and versioned |
| `atlas` | doctrine and context-routing owner | `partial` | awareness-first and conversation docs already enforce grounded, explicit files | context or verify output tied to the shared Playbook contract | route contract refs and continuity refs by intent |
| `lifeline` | approvals and execution owner | `partial` | current stack doctrine already routes execution and approvals here | repo-local artifact that names the implemented contract version | align approvals, receipts, and execution surfaces |
| `_stack` | orchestration and resume owner | `partial` | current stack doctrine already routes worker flow here | repo-local artifact that names the implemented contract version | align merge and resume patterns |
| `knowledge lane` | stack-owned import, catalog, and promotion lane | `partial` | `docs/knowledge/IMPORT-RUNBOOK.md`, `docs/knowledge/QUERY-CONTRACT.md`, `docs/knowledge/PROMOTION-RUNBOOK.md` | explicit continuity promotion flow from handoff or archive into queryable outputs | wire conversation continuity into the import and promotion lane |
| `fitness` | application repo | `verified` | `repos/fawxzzy-fitness/exports/fitness.playbook.adoption.evidence.v1.json`, `repos/fawxzzy-fitness/exports/fitness.playbook.verification.report.v1.json`, `repos/fawxzzy-fitness/docs/ops/FITNESS-PLAYBOOK-ADOPTION.md`, `repos/fawxzzy-fitness/docs/ops/FITNESS-PLAYBOOK-VERIFICATION.md`, `repos/fawxzzy-fitness/tests/playbook-adoption-evidence.test.mjs`, `repos/fawxzzy-fitness/tests/playbook-verification-report.test.mjs` | keep the targeted verification report and reproducible green path honest; broader product verification remains explicitly out of scope | maintain the repo-owned targeted verification lane and let root consume it read-only |
| `mazer` | application repo | `adopted` | `repos/fawxzzy-mazer/exports/mazer.playbook.adoption.evidence.v1.json`, `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-ADOPTION.md`, `repos/fawxzzy-mazer/tests/playbook-adoption-evidence.test.mjs` | repo-owned verification truth or an honest blocked or missing report if the verification path still fails | complete the Mazer verification slice without forcing `verified` |
| `stream` | incubating application repo | `missing` | visible in `stack.yaml` and inventory only | repo-local adoption note or explicit incubating defer decision | decide whether it joins the first rollout |
| `nat1-games` | incubating application repo | `missing` | visible in `stack.yaml` and inventory only | repo-local adoption note or explicit incubating defer decision | decide whether it joins the first rollout |
| `playbook-demo` | demo surface | `n/a` | demo repo exists in `stack.yaml` and inventory | explicit demo-role decision if reused for contract demos | keep out of the critical path unless intentionally used as a mirror |

## Verification Rule

A status should move only when the owning surface has a concrete artifact such as:

- a repo-local spec
- a machine-readable contract file
- a repo-local verify output that names the contract version
- a stack-visible report or receipt that proves the rollout

`verified` specifically requires a repo-owned verification artifact with declared scope in addition to the adoption evidence.

`adopted` to `verified` requires all of the following:

- the owner-repo verification run passes
- the repo-owned verification artifact or report is published in the expected shape
- root consumes that artifact without reinterpretation
- the root projection updates cleanly
- continuity captures the recovery narrative separately from live posture

Until then, the matrix is an honest working assessment, not proof.

## Root Projection Note

ATLAS now projects these statuses into the awareness and cockpit read models, but those projections stay negative-safe:

- local-only repos remain visible without being marked verified
- missing or malformed owner exports render non-green
- continuity coverage is reported separately from adoption
- `fitness` should project as `verified` for its targeted convergence slice without implying broader product-wide certification
- `mazer` should remain `adopted` until its verification slice lands or reports an honest blocked state
