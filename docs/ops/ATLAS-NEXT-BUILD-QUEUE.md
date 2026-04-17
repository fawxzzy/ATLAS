# ATLAS Next Build Queue

This queue is grounded against the live ATLAS workspace on `2026-04-17`.

It replaces the older pre-adoption sequencing that assumed Playbook export, root consumption, and the first vertical repo slices were still pending.

## Current Workspace Posture

- the ATLAS root worktree currently has convergence and continuity changes in flight rather than a clean posture snapshot
- the thin cockpit is already live as a root-only, read-only operator surface
- Playbook owner-truth export is already landed and root-side consumption is already wired
- the continuity lane is real: manifest, loader, handoff, and first historical harvest artifacts are visible from root
- `fitness` and `mazer` both already have repo-local Playbook adoption exports, docs, and targeted adoption tests
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
| `fitness` | present at `repos/fawxzzy-fitness` | `origin` visible | repo-local adoption is landed and targeted proof is green |
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
- repo-local adoption tranches:
  - `repos/fawxzzy-fitness/exports/fitness.playbook.adoption.evidence.v1.json`
  - `repos/fawxzzy-fitness/docs/ops/FITNESS-PLAYBOOK-ADOPTION.md`
  - `repos/fawxzzy-fitness/tests/playbook-adoption-evidence.test.mjs`
  - `repos/fawxzzy-mazer/exports/mazer.playbook.adoption.evidence.v1.json`
  - `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-ADOPTION.md`
  - `repos/fawxzzy-mazer/tests/playbook-adoption-evidence.test.mjs`

## Next Execution Order

### 1. Historical planning query coverage

This is the highest-leverage next slice because the continuity lane already has enough structure that answer quality is now the main gap.

Target outcomes:

- source-family clustering for historical planning lanes
- explicit coverage for the historical planning questions that matter to current work
- structured handoffs and promotions grouped by planning family instead of tiny per-file fragments
- tests that prove ATLAS can answer the historical continuity and prioritization questions from retained evidence

### 2. Explicit adopted-to-verified gate

After historical query coverage, add the root-visible gate that decides when a repo can move from `adopted` to `verified`.

Target outcomes:

- one explicit gate model for `G1` through `G5`
- one root-visible verification report
- honest current evaluation for `fitness` and `mazer`
- bounded handling for unrelated broader verification debt

### 3. Additional repo-local adoption waves

After the first two slices above:

1. `lifeline`
2. `_stack`
3. `atlas`
4. `stream`
5. `nat1-games`

Use repo-local adoption only where the repo actually needs it; do not widen the rollout mechanically.

## Not Yet Verified Here

- a root-visible adopted-to-verified report is not landed yet
- historical planning query coverage tests are not landed yet
- `fitness` and `mazer` targeted adoption tests are green, but broader `verified` promotion proof is still incomplete
- `_stack`, `atlas`, and `stream` still present as local-only identities from the current workspace view

## Do Not Do In This Wave

- do not copy Playbook owner truth into ATLAS root
- do not widen cockpit or awareness into execution controls
- do not treat imported planning material or transcripts as doctrine just because it is searchable
- do not auto-promote `verified` from targeted repo-local tests alone
