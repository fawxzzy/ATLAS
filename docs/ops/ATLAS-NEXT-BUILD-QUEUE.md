# ATLAS Next Build Queue

This queue is grounded against the live ATLAS workspace on `2026-04-17`.

It replaces the older pre-adoption sequencing that assumed Playbook export, root consumption, and the first vertical repo slices were still pending.

## Current Workspace Posture

- the ATLAS root worktree currently has convergence and continuity changes in flight rather than a clean posture snapshot
- the thin cockpit is already live as a root-only, read-only operator surface
- Playbook owner-truth export is already landed and root-side consumption is already wired
- the continuity lane is real: manifest, loader, handoff, and historical query coverage are visible from root
- reviewed Verta derivative notes are landed without changing Verta's visible-untrusted metadata-only posture
- `fitness` has repo-owned targeted verification truth and should project as the first bounded `verified` repo
- `mazer` has repo-local adoption evidence and targeted proof, but remains `adopted` until the verification slice lands or reports an honest block
- root-side reporting was lagging those repo-local adoption slices and must stay aligned with the owner evidence

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
| `mazer` | present at `repos/fawxzzy-mazer` | `origin` visible | repo-local adoption is landed and targeted proof is green; broader verify still needs explicit handling before `verified` |
| `stream` | present at `repos/fawxzzy-stream` | no remote visible in this workspace | incubating and still outside the first adopted tranche |
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
  - `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-ADOPTION.md`
  - `repos/fawxzzy-mazer/tests/playbook-adoption-evidence.test.mjs`

## Next Execution Order

### 1. Mazer verification slice

This is the highest-leverage next slice because the root posture, cockpit, Playbook export, and continuity lane are already landed.

Target outcomes:

- add repo-owned verification truth for `mazer`
- project that verification read-only into root reporting
- if the existing timeout or broader path still blocks verification, report that honestly as blocked or missing instead of forcing `verified`
- keep the verification scope explicit so the status does not overclaim broader product certification

### 2. Additional repo-local waves only where leverage is clear

After the Mazer slice, only widen the rollout where there is clear leverage.

Target outcomes:

- prioritize `lifeline`, `_stack`, or `atlas` only when the next operator constraint actually depends on them
- keep application rollout selective rather than mechanical
- avoid widening ATLAS root into a second truth store

### 3. Historical reviewed-note promotion only where coverage is partial or missing

This is no longer the primary program gap. Keep doing it only where it buys real historical coverage.

Target outcomes:

- fill partial or missing historical answers with reviewed derivative notes
- keep raw Verta sources visible-untrusted and metadata-only
- avoid turning reviewed-note promotion into a general documentation binge

### Deferred after the current frontier: cross-app synergy lane

The Atlas and Fitness cross-app synergy report is now retained as a reviewed strategy note, not as a live posture update.

Target outcomes after the current frontier:

- start with a synergy registry for assets that already behave shared but have no clear owner, contract, or package
- land shared event contracts and telemetry alignment before auth, shared UI, cross-sell, or data work
- treat reusable CI or CD and Playbook workflow rules as the second implementation lane
- keep unified auth, shared UI, cross-sell, and shared data or ML explicitly deferred behind the earlier contract and identity prerequisites

## Not Yet Verified Here

- a repo-owned verification report for `mazer` is not landed yet
- `_stack`, `atlas`, and `stream` still present as local-only identities from the current workspace view
- voice is still intentionally below the current priority line and not certified

## Do Not Do In This Wave

- do not copy Playbook owner truth into ATLAS root
- do not widen cockpit or awareness into execution controls
- do not widen root into a second truth store
- do not treat imported planning material or transcripts as doctrine just because it is searchable
- do not force `verified` when the evidence still says blocked or missing
- do not use cross-app synergy research to skip the current Mazer verification and root-consumption frontier
