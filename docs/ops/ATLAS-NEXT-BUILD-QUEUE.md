# ATLAS Next Build Queue

This queue is grounded against the live ATLAS workspace on `2026-04-19`.

It replaces the older pre-adoption sequencing that assumed Playbook export, root consumption, and the first vertical repo slices were still pending.

## Current Workspace Posture

- the ATLAS root worktree currently has convergence and continuity changes in flight rather than a clean posture snapshot
- the thin cockpit is already live as a root-only, read-only operator surface
- Playbook owner-truth export is already landed and root-side consumption is already wired
- Playbook now owns the reusable event-contract workflow surface plus publish and rollback guidance for downstream callers
- the continuity lane is real: manifest, loader, handoff, and historical query coverage are visible from root
- reviewed Verta derivative notes are landed without changing Verta's visible-untrusted metadata-only posture
- `atlas` and `fitness` now both carry owner-repo caller workflows pinned to an immutable Playbook workflow ref instead of tracking `@main`
- `fitness` has repo-owned targeted verification truth and should project as the first bounded `verified` repo
- `mazer` now has repo-owned targeted verification truth and should project as the second bounded `verified` repo
- root-side reporting now projects both bounded verified repos and must stay aligned with the owner evidence
- Fitness owner truth now also carries the frozen Wave 2 metrics pack, the first funnel/dashboard consumer pack, the first growth pack, and the pilot-readiness threshold pack under `truth-pack/fitness/event-contract/`
- one shadow-only Fitness placement now has measured proof in owner truth, and the current pilot-readiness gate evaluates to `stay_shadow`, so the rollout remains shadow-only rather than pilot-live

## Repo And Git Visibility

### Core repos

| Repo | Local visibility | Git remote visibility | Notes |
| --- | --- | --- | --- |
| `playbook` | present at `repos/fawxzzy-playbook` | `origin` visible | owner contract export and tests are already landed |
| `lifeline` | present at `repos/fawxzzy-lifeline` | `origin` visible | still needs its own repo-local adoption tranche |
| `_stack` | present at `repos/_stack` | no remote visible in this workspace | local-only visibility is still acceptable for repo-local adoption work |
| `atlas` | present at `repos/fawxzzy-atlas` | no remote visible in this workspace | doctrine repo remains visible but not remotely proven here |

### Application and demo repos

| Repo | Local visibility | Git remote visibility | Notes |
| --- | --- | --- | --- |
| `fitness` | present at `repos/fawxzzy-fitness` | `origin` visible | repo-local adoption and targeted verification report are landed |
| `mazer` | present at `repos/fawxzzy-mazer` | `origin` visible | repo-local adoption and targeted verification report are landed |
| `stream` | present at `repos/stream` | no remote visible in this workspace | incubating and still outside the first adopted tranche |
| `playbook-demo` | nested repo present at `repos/playbook-demo/playbook-demo` | `origin` visible | keep out of the critical path unless intentionally used as a contract demo surface |
| `nat1-games` | nested repo present at `repos/Nat1-Games/nat1-games` | `origin` visible | still incubating from the convergence-program perspective |

## Verified Landings

The following items are concretely visible in this workspace now:

- Playbook owner export:
  - `repos/fawxzzy-playbook/exports/playbook.contract.example.v1.json`
  - `repos/fawxzzy-playbook/exports/playbook.contract.schema.v1.json`
  - `repos/fawxzzy-playbook/docs/contracts/PLAYBOOK-CONTRACT.md`
- root read-only consumption:
  - `ops/atlas/playbook_contract.py`
  - `ops/atlas/awareness.py`
  - `ops/atlas/cockpit.py`
- continuity lane:
  - `ops/atlas/continuity.py`
  - `data/imports/knowledge/continuity/harvest-manifest.json`
  - `docs/knowledge/promotions/atlas--historical-planning-harvest-20260417.md`
  - `runtime/receipts/handoffs/playbook-convergence-historical-planning-harvest-20260417t161500z.handoff.json`
- reviewed Verta derivative lane:
  - `docs/knowledge/promotions/atlas--historical-planning-harvest-20260417.md`
  - `docs/ops/VERTA-TRUST-GATE.md`
- repo-local adoption tranches:
  - `repos/fawxzzy-fitness/exports/fitness.playbook.adoption.evidence.v1.json`
  - `repos/fawxzzy-fitness/exports/fitness.playbook.verification.report.v1.json`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-PLAYBOOK-ADOPTION.md`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-PLAYBOOK-VERIFICATION.md`
  - `repos/fawxzzy-fitness/tests/playbook-adoption-evidence.test.mjs`
  - `repos/fawxzzy-fitness/tests/playbook-verification-report.test.mjs`
  - `repos/fawxzzy-mazer/exports/mazer.playbook.adoption.evidence.v1.json`
  - `repos/fawxzzy-mazer/exports/mazer.playbook.verification.report.v1.json`
  - `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-ADOPTION.md`
  - `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-VERIFICATION.md`
  - `repos/fawxzzy-mazer/tests/playbook-adoption-evidence.test.mjs`
  - `repos/fawxzzy-mazer/tests/playbook-verification-report.test.mjs`
- wave-1 event-contract enforcement lane:
  - `repos/fawxzzy-playbook/.github/workflows/event-contract-pack.yml`
  - `repos/fawxzzy-playbook/docs/contracts/EVENT_CONTRACT_WORKFLOW_CONSUMERS.md`
  - `repos/fawxzzy-playbook/docs/RELEASING.md`
  - `repos/fawxzzy-atlas/.github/workflows/event-contracts.yml`
  - `repos/fawxzzy-fitness/.github/workflows/event-contracts.yml`
  - `repos/fawxzzy-fitness/src/lib/ecosystem/fitness-shadow-warehouse.test.ts`
- Fitness Wave 2 owner packs:
  - `repos/fawxzzy-fitness/truth-pack/fitness/event-contract/atlas-fitness-wave-2-metrics-pack.v1.json`
  - `repos/fawxzzy-fitness/truth-pack/fitness/event-contract/atlas-fitness-funnel-dashboard-pack.v1.json`
  - `repos/fawxzzy-fitness/truth-pack/fitness/event-contract/atlas-fitness-growth-pack.v1.json`
  - `repos/fawxzzy-fitness/truth-pack/fitness/event-contract/README.md`

## Next Execution Order

Wave 1 owner-repo implementation is landed enough to treat as release-stable now that the shared workflow consumers are pinned to an immutable Playbook ref. Wave 2 metrics, funnel, growth, and pilot-readiness owner packs now exist in Fitness owner truth. Root should project that state once and then stop; the next contract-defining move belongs in the Fitness repo.

Projection artifact:

- `docs/registry/STACK-SYNERGY-REGISTRY.json`

### 1. Root sync once from owner evidence

Target outcomes:

- update `docs/registry/STACK-SYNERGY-REGISTRY.json`, `README-STACK.md`, and this queue from the landed Playbook, Atlas, and Fitness owner evidence
- record that the reusable workflow consumers are pinned to immutable Playbook ref `9ce397e893e4007afbe93366770867ed64f66500`
- project only that the first Fitness growth pack exists in owner truth, the pilot-readiness pack exists in owner truth, the current gate result is `stay_shadow`, no pilot-live rollout is authorized yet, and the next owner-repo work is evidence-surface completion in Fitness
- keep the root as a pointer and projection surface rather than a second truth store
- stop after the sync; do not restate owner truth at root

### 2. Fitness pilot evidence surface completion

Target outcomes:

- build the missing repo-owned evidence surface inside `repos/fawxzzy-fitness` so the pilot-readiness evaluator can measure the frozen thresholds from runtime receipts
- keep rollout posture shadow-only until the owner threshold gate turns green
- keep root out of evidence-surface and gate implementation beyond projecting the owner-repo result

### 3. Keep later work parked

Target outcomes:

- do not widen one measured shadow-only placement into pilot-live at root
- keep unified auth behind telemetry hygiene, support tooling, and account-model stabilization
- keep shared UI behind explicit token, package, and publishing ownership
- keep cross-sell behind identity and attribution
- keep shared data or ML last

## Not Yet Verified Here

- `_stack`, `atlas`, and `stream` still present as local-only identities from the current workspace view
- voice is still intentionally below the current priority line and not certified

## Do Not Do In This Wave

- do not copy Playbook owner truth into ATLAS root
- do not widen cockpit or awareness into execution controls
- do not widen root into a second truth store
- do not treat imported planning material or transcripts as doctrine just because it is searchable
- do not force `verified` when the evidence still says blocked or missing
- do not reopen event-contract freezing or workflow-pack proving work unless new owner evidence says the current owner lane regressed
- do not treat floating workflow refs as a stable consumer contract
- do not treat shadow-only measured proof as pilot-live promotion
- do not jump to auth, shared UI, cross-sell, or ML before the Fitness pilot-readiness gate is green in owner truth
- do not blur the decision gate: root work changes projection truth; owner-repo work changes owner truth
