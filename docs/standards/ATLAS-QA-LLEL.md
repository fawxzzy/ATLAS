# ATLAS QA LLEL Standard

## Purpose

ATLAS owns the QA LLEL as the stack-level evaluation and promotion layer.

- Rule: executable repo checks remain the source of truth.
- Rule: the QA LLEL grades coverage, artifact completeness, certification status, and promotion readiness above repo-native tests.
- Rule: dry-run evidence may validate pipeline wiring, but may never satisfy promotion.
- Rule: ATLAS promotion requires evidence-grade QA receipts, not merely successful test execution.
- Failure Mode: treating screenshot judgment as a replacement for executable assertions creates unverifiable release signals.

This standard applies to cross-repo QA governance at the ATLAS root. Repo-local test runners, fixtures, and browser harnesses stay inside the target repo.

## Definition

QA LLEL is the ATLAS-local name for the evaluation layer that:

1. reads a root-owned scenario contract
2. dispatches repo-native verification commands through a repo adapter
3. ingests proof artifacts into a normalized manifest
4. evaluates executable truth, artifact coverage, and certification gaps
5. emits a transparent promotion decision

The QA LLEL is not a new shared runtime package. It is a root-owned contract, schema, orchestration, and reporting layer.

ATLAS QA LLEL defines quality evidence, not just tests.

- A repo may pass unit tests and still fail QA LLEL promotion if it cannot produce valid evidence.
- Dry-run evidence proves pipeline wiring only.
- Evidence-grade QA requires real artifacts.
- Promotion-grade QA requires real artifacts plus validated evaluation plus a root promotion receipt.

## Contract Versioning

ATLAS QA LLEL is now frozen as a root-owned v1 contract set.

- Rule: QA LLEL contracts are versioned. Root may reject unknown or incompatible child-repo QA contracts.
- Rule: adapters, scenarios, capture receipts, artifact manifests, test evidence receipts, manual attestations, visual baselines, promotion records, and evidence indexes must declare a supported contract version.
- Pattern: run `python ops/atlas/qa/compatibility_report.py --scenario <scenario-id> --adapter <adapter-id>` before broad repo adoption.

## Architecture

ATLAS QA is split into five layers.

1. Scenario contract
   Root-owned manifests define route intent, auth or seed expectations, device lenses, required artifacts, and promotion policy.
2. Repo adapter
   Each repo declares its canonical start strategy, verification commands, supported scenarios, and device-lens execution modes.
3. Execution
   Repos continue running their own deterministic unit, API, contract, browser, or visual checks with their preferred tooling.
4. Artifact bundle
   Each scenario run emits a governed manifest that links screenshots, traces, logs, videos, and executable reports under one run id.
5. Evaluation and promotion
   ATLAS grades the run, marks gaps explicitly, and emits a release-facing decision record.

Repo-native unit and integration tests feed QA LLEL as evidence.

- Pattern: unit tests remain repo-native; QA LLEL makes their results root-readable and promotion-aware.
- Rule: failed required test evidence blocks promotion the same way failed executable truth does.

- Pattern: standardize contracts, adapters, artifacts, CLI verbs, and reports before standardizing repo runtime code.
- Failure Mode: shared runtime before shared boundary increases cross-repo coupling without increasing trust.

## Proof Levels

ATLAS uses two proof levels.

### Fast proof

Fast proof runs on pull requests.

- desktop web emulation
- Android-class browser emulation
- iPhone-class browser emulation
- targeted visual comparisons
- trace retention on failure or retry

- Rule: browser-backed emulated screenshots are valid evidence-grade artifacts, but they are emulated lens evidence, not physical-device proof.

## Evidence Tiers

ATLAS promotion must report the highest evidence tier satisfied.

Supported tiers:

- `dry_run`
- `emulated_browser`
- `physical_device`
- `manual_attestation`

Rules:

- Emulated browser evidence and physical-device evidence are both real artifacts, but they are not the same proof tier.
- Promotion status describes the outcome; evidence profile describes the kind of proof that satisfied the repo.
- Manual attestation may resolve a physical-device review lane, but it must never be labeled as automated physical-device proof.
- A promotion record without tier identity is invalid.
- Rule: physical-device evidence should be required by scenario criticality, not globally across every repo or scenario.

## Evidence Profiles

ATLAS uses evidence profiles to distinguish browser-oriented proof from non-visual contract proof without changing the v1 promotion outcome vocabulary.

Supported profiles:

- `web_visual`
- `package_contract`
- `docs_governance`

Rules:

- Web repos should report `web_visual` when browser-backed capture is part of the satisfied evidence.
- Package repos should report `package_contract` when deterministic command, test, or contract evidence satisfied promotion.
- Docs and governance repos should report `docs_governance` when managed-doc and contract checks satisfied promotion.

## Release Gate Policy

ATLAS release readiness is repo-tier specific. Physical-device proof is required only where the repo and scenario tier demand it.

Default release gate profiles live in `ops/atlas/qa/release_policy.v1.json`.

Default profile mapping:

- `package_contract`
  Release requires governed command, unit, or contract evidence.
- `docs_governance`
  Release requires docs audit, lint, and governance contract evidence.
- `web_visual`
  Release requires governed emulated browser evidence plus executable truth.
- `release_critical_web`
  Release requires physical-device evidence or valid manual attestation in addition to emulated browser evidence.

Mode expectations:

- `pr`
  Optimize for fast confidence. Use repo-native checks plus emulated browser evidence for web repos.
- `main`
  Require root-readable evidence for the repo profile.
- `release`
  Require the release gate for the repo profile to be satisfied.
- `manual_promotion`
  Follow the release gate and preserve any manual or provider lineage explicitly.

- Pattern: release readiness is repo-tier specific; physical-device proof belongs to release-critical web flows, not every repo.
- Failure Mode: once release readiness exists, stale receipts can create false confidence unless adoption freshness is checked.
- Failure Mode: fresh receipts for the wrong commit can create false release confidence unless provenance is checked against the release target SHA or stack pin.
- Failure Mode: correct-SHA receipts can still be weak if they were produced outside the trusted release path and the release profile requires trusted origins.
- Pattern: trusted-origin enforcement should be staged by release profile; do not globally flip every adopted repo to enforced in one move.
- Pattern: release receipt selection should prefer the strongest valid target-matching evidence, not merely the newest receipt.

### Real proof

Real proof runs on merge, release, or nightly lanes for high-risk scenarios.

- one real desktop browser session
- one real Android browser session
- one real iPhone Safari session
- preview URL first, local or staging tunnel fallback when a hosted preview is unavailable

- Rule: emulate broad, certify narrow.
- Failure Mode: calling emulation "real-device proof" hides production risk instead of reducing it.

## Lens Standard

Every visual QA scenario must declare its required lens profiles through the root lens manifest.

Default required visual lens profiles:

- `desktop.chromium`
- `android.chrome`
- `iphone.webkit`

- Pattern: one QA scenario should fan out across multiple user lenses instead of creating separate scenario files for every device archetype.
- Rule: a missing required lens is a promotion failure unless the scenario policy explicitly allows a manual certification lane.
- Rule: each adapter lens must declare `evidence_kind`, `required_for`, `promotion_tier`, and `fallback_behavior`.

## Scenario Bundle

One scenario run must stay correlated across all lenses.

Required bundle keys:

- `scenario_id`
- `run_id`
- `repo_id`
- `git_sha`
- `step_id`
- `lens_id`
- `proof_kind`

Required artifact kinds:

- `screenshot`
- `trace`
- `console_log`
- `network_log`
- `executable_report`

Optional artifact kinds:

- `video`
- `api_report`
- `manual_note`

Every screenshot artifact is valid only when it includes:

- `scenario_id`
- `adapter_id`
- `run_id`
- `repo_id`
- `git_sha`
- `lens_id`
- `viewport`
- `browser_engine`
- `captured_at`
- `source_url`
- `artifact_sha256`

- Pattern: one scenario, three lenses.
- Failure Mode: unrelated screenshots with no shared manifest produce evidence without lineage.

## Evidence Rules

Screenshots must be browser or device-backed artifacts.

- Rule: a screenshot artifact must be a real file, non-empty, decodable, hashed, and bound to the active run id.
- Rule: dry-run or synthetic evidence may not satisfy promotion.
- Rule: emulated browser capture may satisfy evidence-grade QA for fast proof, but it does not satisfy a scenario that explicitly requires physical-device proof.
- Rule: physical-device artifacts must record provider or attestation lineage, device identity, capture method, and artifact hash.
- Failure Mode: visual QA without browser-backed screenshots gives false confidence and must not be promotable.

## Visual Diffs

Visual baselines are governed evidence, not convenience snapshots.

- Rule: screenshots prove render existence; visual diffs prove render stability.
- Rule: baselines must live under `data/atlas/qa/baselines/`.
- Rule: dry-run screenshots may never become blessed baselines.
- Rule: governed baselines must move through `proposed`, `blessed`, `superseded`, or `rejected` state; unmanaged screenshots do not count as promotion baselines.
- Rule: failed visual diffs block promotion.
- Pattern: use per-lens thresholds and ignored regions where mobile/browser variance is known but bounded.

## Reports

Each run should emit an operator-facing evidence report alongside machine-readable receipts.

- Pattern: QA receipts are machine-verifiable; QA reports are operator-verifiable.
- Expected outputs:
  - `report.md`
  - `report.html`
  - `report.summary.json`
- Reports must show promotion tier, missing evidence tiers, per-lens artifacts, and visual diff results when configured.
- Pattern: one run produces receipts; the evidence index shows QA health over time.

## Governance Rules

### Executable truth first

Executable pass or fail comes from deterministic assertions, API checks, contract checks, and explicit visual diffs. The QA LLEL may summarize or rank risk, but it must not overrule a failed executable check.

### Artifact-first review

Promotion records must remain explainable from scenario contracts, executable reports, and artifact manifests. A green summary without linked evidence is not certification.

### Governance drift stays visible

Promotion records must surface unrelated root governance blockers such as stack validation drift separately from repo QA failures.

- Failure Mode: new QA infrastructure can appear healthy while promotion is still blocked by unrelated root governance drift.

### Real-device proof is selective

Require real-device proof for user-visible, high-value, or release-critical flows:

- install and acquisition
- auth and recovery
- navigation shell and layout anchors
- conversion or purchase flows
- design-system anchor screens

### Manual gaps stay visible

When a repo or provider cannot supply a real-device lane yet, mark the gap as `manual_required` or `missing`. Do not treat absence as pass.

Scoped waivers may unblock release-critical flows temporarily, but the evidence chain must stay honest.

- Rule: a waiver may waive a lane; it may not relabel that lane as passed physical proof.
- Rule: waivers must be run-scoped, scenario-scoped, time-bound, and visible in promotion, readiness, and evidence-index receipts.
- Rule: a waiver may keep release readiness green while manual attestation remains invalid, but only when the missing lane is explicitly waived and all other required evidence is already clean.
- Failure Mode: using a waiver to masquerade as satisfied physical proof breaks the release evidence contract.

### Tiered promotion statuses

Use explicit statuses instead of generic `promoted`.

- `dry_run`
- `blocked`
- `manual_review`
- `promoted_emulated`
- `promoted_physical`
- `promoted_physical_manual`
- `waived_promoted`

### Display labels

ATLAS v1 keeps the wire-level promotion status vocabulary stable, but operator reports should render profile-aware display labels.

- `promoted_emulated` + `package_contract` => `promoted_contract`
- `promoted_emulated` + `docs_governance` => `promoted_docs_governance`
- `promoted_emulated` + `web_visual` => `promoted_web_visual`

- Rule: promotion wording must match the evidence profile that actually passed.

## Adoption Drift

ATLAS must continuously distinguish real child-repo adoption from root-side prototypes.

- Rule: adoption means child-owned QA intent plus root-readable receipts, not root-side prototype manifests.
- Rule: adopted repos must keep fresh meaningful receipts; dry-run-only or stale receipts do not count as steady-state adoption truth.
- Pattern: use an adoption drift scanner to validate child manifests, receipt freshness, and release-policy alignment over time.
- Pattern: prototype QA configs must be explicitly labeled as prototype, adopted, or retired.

### Portable paths only

Contracts, manifests, reports, and prompts must use ATLAS-root-relative refs. Machine-local absolute paths are not part of the contract.

### Root CI workflows stay thin

Root GitHub Actions workflows may orchestrate QA LLEL only through root-owned scripts and contracts.

- Rule: `.github/workflows/**` at the ATLAS root is an orchestration surface, not a second implementation surface.
- Failure Mode: embedding repo-specific QA behavior in workflow YAML duplicates the pipeline and makes promotion harder to trust.

## Adapter Rules

Repo adapters are root-owned manifests that point at repo-local commands. They must declare:

- `repo_id`
- `repo_path`
- canonical start strategy
- canonical verification commands
- supported scenarios
- device lenses and execution modes

Adapters may point at existing repo commands such as `qa:ui-pass`, `qa:matrix`, `qa:llel:progression`, or repo-native Playwright suites. They should wrap existing healthy surfaces before inventing new ones.

- Pattern: wrap existing QA commands before inventing new ones.
- Failure Mode: replacing healthy repo-local tooling with a generic abstraction for standardization theater.
- Pattern: root owns QA machinery; repos own QA intent.

## Real-Device Strategy

ATLAS uses preview-first real-device certification.

1. Prefer repo preview URLs when the repo has a governed preview flow.
2. Fall back to local or staging tunnel mode when preview hosting is unavailable or unsuitable.
3. Keep provider selection outside the schema contract.

Supported provider models:

- hosted real-browser grids
- hosted or self-hosted mobile-device clouds
- Appium-compatible manual or automated device farms

The root contract records proof expectations and outputs. Repo adapters or CI lanes choose the concrete provider through a replaceable provider adapter.

- Pattern: provider-agnostic physical capture keeps ATLAS from coupling governance to one vendor.

## CI Shape

### Pull request

- lint
- typecheck
- repo-native deterministic verify
- emulated smoke matrix
- targeted visual assertions
- artifact bundling
- evaluation report

### Merge

- expanded smoke matrix
- artifact review for intentional visual changes
- certification gap review

### Release or nightly

- real-device triad for high-risk scenarios
- full artifact bundle upload
- promotion report

## Files

Root-owned contracts and reports live in:

- `schemas/atlas.qa.scenario.v1.json`
- `schemas/atlas.qa.artifact.v1.json`
- `schemas/atlas.qa.result.v1.json`
- `schemas/atlas.qa.promotion.v1.json`
- `schemas/atlas.qa.lens.v1.json`
- `ops/atlas/qa/**`
- `runtime/atlas/qa/**`
- `.github/workflows/**` for orchestration only

Repo-local execution stays in the target repo.

## Rollout

Roll out in four waves.

1. Wave 1 root-only governance
2. Wave 2 repo adapters in parallel, one repo per worker
3. Wave 3 screenshot and observability lanes in parallel per repo
4. Wave 4 certification and promotion at root

Parallel ownership should follow the existing ATLAS collision policy.
