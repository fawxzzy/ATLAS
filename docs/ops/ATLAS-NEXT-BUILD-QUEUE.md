# ATLAS Next Build Queue

This queue is grounded against the live ATLAS workspace on `2026-04-18`.

It replaces the older pre-adoption sequencing that assumed Playbook export, root consumption, and the first vertical repo slices were still pending.

## Current Workspace Posture

- the ATLAS root worktree currently has convergence and continuity changes in flight rather than a clean posture snapshot
- the thin cockpit is already live as a root-only, read-only operator surface
- Playbook owner-truth export is already landed and root-side consumption is already wired
- the continuity lane is real: manifest, loader, handoff, and historical query coverage are visible from root
- reviewed Verta derivative notes are landed without changing Verta's visible-untrusted metadata-only posture
- `fitness` has repo-owned targeted verification truth and should project as the first bounded `verified` repo
- `mazer` now has repo-owned targeted verification truth and should project as the second bounded `verified` repo
- root-side reporting now projects both bounded verified repos and must stay aligned with the owner evidence

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
  - `repos/fawxzzy-mazer/exports/mazer.playbook.verification.report.v1.json`
  - `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-ADOPTION.md`
  - `repos/fawxzzy-mazer/docs/ops/MAZER-PLAYBOOK-VERIFICATION.md`
  - `repos/fawxzzy-mazer/tests/playbook-adoption-evidence.test.mjs`
  - `repos/fawxzzy-mazer/tests/playbook-verification-report.test.mjs`

## Next Execution Order

### 1. Stack-wide source-verified synergy registry across repos/**

Mazer is no longer the blocking frontier. The next strong lane is stack-wide synergy discovery, but only as source-verified discovery with owner repos still holding truth.

Projection artifact:

- `docs/registry/STACK-SYNERGY-REGISTRY.json`

Target outcomes:

- inventory cross-repo surfaces that already behave like shared assets but still lack a clear owner, contract, or package
- keep root as the projection layer and treat owner repos as the source of truth
- avoid reopening generic root or cockpit invention work

### 2. First-wave owner-surface discovery

Target outcomes:

- `lifeline`: approvals, receipts, capability nouns, and reusable contracts
- `playbook`: governance, verification workflow-pack reuse, and explicit owner-truth checks
- `_stack`: orchestration, merge, resume, and worker contracts
- rank the first-wave outputs by duplication, active initiative pressure, and contract absence before widening further

### 3. Atlas/Fitness telemetry-first tranche

Target outcomes:

- build the first concrete shared glossary and shared event-contract inventory across Atlas and Fitness
- treat Atlas/Fitness as tranche 1 of the stack-wide registry, not as the whole program
- keep the emphasis on telemetry and event contracts before any shared implementation

### 4. Canonical noun glossary and top shared event contracts

Target outcomes:

- freeze the canonical nouns that the shared registry depends on, starting from the candidate set published in `docs/registry/STACK-SYNERGY-REGISTRY.json`
- publish the first shared event-contract and telemetry inventory before any implementation sharing
- keep the gate explicit: share contracts before sharing implementations

### 5. Atlas instrumentation against the frozen contracts

Target outcomes:

- instrument Atlas against the agreed event and telemetry contracts
- keep risky integration work in shadow mode until the contract lane proves stable

### 6. Fitness instrumentation against the frozen contracts

Target outcomes:

- instrument Fitness against the same contracts without inventing a second contract dialect
- verify the shared inventory from owner-repo evidence rather than stack-root restatement

### 7. Second-wave repo ranking and reusable checks after contract freeze

Target outcomes:

- rank second-wave repos by duplication, shared nouns, active initiative pressure, and contract absence
- extract reusable workflow, CI or CD, and warehouse checks only after the registry and contract lane are real
- keep this as a reuse lane, not a shortcut around contract ownership

### 8. Only later: auth, shared UI, cross-sell, and ML

Target outcomes:

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
- do not jump to auth, shared UI, cross-sell, or ML before the stack-wide registry and contract lane are source-verified
