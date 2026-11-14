# ATLAS Release Policy Classes

- Status: **POLICY CLASSES RECORDED; per-repo row acceptance PENDING**
- Date: 2026-11-14
- Decision: Zac chose "3 classes + 10-repo table PR" (2026-11-14).
- Scope: classification and evidence only. This document grants no release,
  deploy, publish or production authority.
- Authorization model: PR #214 "Automate fully proven clean releases" and PR #215
  "Harden verified release production authorization" (both merged 2026-08-27)
  define `VERIFIED_RELEASE_PRODUCTION_CONTINUATION` in
  `docs/registry/ATLAS-AUTHORIZATION-POLICY.v1.json` and
  `ops/atlas/authorization_policy.py` (single production deployment, rollback
  target retained, automatic rollback). That is the authorization model. This
  document defines per-repo readiness classes, which the model does not.
  Their wording predates the Claude-only execution model.

## Classes

| Class | Release event | Required before release | Hard stops |
| --- | --- | --- | --- |
| deploy-surface | The Vercel production deployment (FawxzzyWeb, Mazer, Fitness). GitHub releases = 0 is not a defect for this class. | CI green on the exact head; the repo profile's verify commands pass; rollback target recorded before deploy; deploy goes through the shared Vercel deploy pacer. | Database changes, credentials, DNS/domains, billing. |
| library-publish | Git tag plus GitHub release, produced through the repo's own release-prep. | The repo's own release-prep and hosted checks pass on the exact head. | Release-prep and package publish remain hard stops. |
| no-release | None. A recorded reason replaces readiness. | Keep CI/verify delta at zero where a gate exists. | Reason must be re-stated if the repo gains a deploy surface or package. |

## Ten-repo table

Facts read 2026-11-14: `gh release list`, tags, latest `gh run list --branch main`
(one latest run is not a full CI verdict; "in progress" means no conclusion at
read time), and `stack.yaml` `repo_overrides` on origin/main. Branch protection was
not re-read in this pass.

| Repo | GH releases / tags | Last main run | `release_eligible` | Class | Gap or reason |
| --- | --- | --- | --- | --- | --- |
| ATLAS | 0 / 0 | Atlas Stack Generator: success | not in lock (root) | no-release | Stack root; gate is `validate_stack` with a zero-delta rule. |
| FawxzzyWeb (`trove`) | 0 / 0 | CI: in progress (previous runs success) | true | deploy-surface | Profile `web` defines checks, aliases and rollback. |
| mazer | 0 / 0 | Verify: in progress (previous run success) | source-pin, no flag | deploy-surface | Profile `mazer` defines checks, alias and rollback. |
| fawxzzy-fitness | 0 / 35 tags | fitness-event-contracts: success | source-pin, no flag | deploy-surface | Profile `fitness`; meaning of the tags is unverified. |
| playbook | 2 / 2 (latest v0.54.1) | ci / Playbook CI: in progress (demo-refresh success) | true | library-publish | Only repo with real GitHub releases. |
| fawxzzy-platform | 0 / 0 | contracts: success (2026-11-11) | not in lock | undecided | Needs a profile or a recorded no-release reason. |
| socials-os | 0 / 0 | verify: success (2026-10-15) | not in lock | undecided | Stale run; no profile. |
| _stack | 0 / 0 | `_stack verify`: success (2026-08-21) | false | no-release | Frozen; run is stale. |
| lifeline | 0 / 0 | Dependabot Updates: success (2026-09-01, not a CI verdict) | true | no-release while frozen | Flag contradicts freeze; no CI verdict read. |
| foundation | 0 / 0 | Foundation CI: success (2026-07-15) | true | no-release while frozen | Flag contradicts freeze; run is four months old. |

Owner acceptance of each row is **PENDING**. Fitness, Mazer, FawxzzyWeb and
Playbook sessions own their own rows; this table is a proposal until they accept.

## `release_eligible` reconciliation

`stack.yaml` marks four repos `release_eligible: true`:

- `playbook`: consistent with library-publish.
- `trove` (FawxzzyWeb): consistent with deploy-surface.
- `lifeline` and `foundation`: **discrepancy.** Both are frozen and have no
  releases or profile. Under this policy they are no-release while frozen.

The flags are **not changed here.** They feed `stack.lock.yaml` and the QA
release-readiness checks (`ops/atlas/qa/release_readiness.py`), so a flag change
needs its own PR with lockfile regeneration and the related tests. Until then,
automation must not treat Lifeline or Foundation as shippable on the strength of
`release_eligible: true`; the class above takes precedence.

## Not verified

Branch protection on all ten repos; whether any non-latest main workflow is
failing; the meaning of the Fitness tags; the full text of the authorization
policy beyond gate and class names.
