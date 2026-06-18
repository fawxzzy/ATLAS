# ATLAS QA Promotion Runbook

## Purpose

Operate the root-owned QA LLEL pipeline from scenario planning through promotion reporting.

## Inputs

The promotion lane reads:

- one scenario contract
- one repo adapter
- one run result
- one artifact manifest

## Commands

Plan or execute a scenario matrix:

```powershell
python ops/atlas/qa/run_matrix.py --scenario fitness.progression-pr-smoke --adapter fitness.web --dry-run
```

Collect artifacts for a run:

```powershell
python ops/atlas/qa/collect_artifacts.py --run <run-id>
```

Validate artifact authenticity:

```powershell
python ops/atlas/qa/validate_artifacts.py --run <run-id>
```

Create manual attestation templates for unresolved lanes:

```powershell
python ops/atlas/qa/manual_attestation.py scaffold --run <run-id>
```

Validate manual attestations:

```powershell
python ops/atlas/qa/manual_attestation.py validate --run <run-id>
```

Check whether a provider is live-smoke ready:

```powershell
python ops/atlas/qa/provider_readiness.py --provider ops/atlas/qa/providers/browserstack.playwright.v1.json --adapter fitness.web --scenario fitness.progression-pr-smoke
```

Evaluate a run:

```powershell
python ops/atlas/qa/evaluate_run.py --run <run-id>
```

Emit a promotion record:

```powershell
python ops/atlas/qa/promote_run.py --run <run-id> --scenario-file ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json --stack-validation-file runtime/receipts/validation/stack-validation.latest.json
```

Run the root CI gate entrypoint:

```powershell
python ops/atlas/qa/ci_gate.py --mode dry-run --scenario fitness.progression-pr-smoke --adapter fitness.web
python ops/atlas/qa/ci_gate.py --mode evidence --scenario fitness.progression-pr-smoke --adapter fitness.web
python ops/atlas/qa/ci_gate.py --mode promotion --scenario fitness.progression-pr-smoke --adapter fitness.web
```

Run an operator-only BrowserStack-backed smoke when protected credentials are available:

```powershell
$env:BROWSERSTACK_USERNAME="<github-actions-secret>"
$env:BROWSERSTACK_ACCESS_KEY="<github-actions-secret>"
python ops/atlas/qa/ci_gate.py --mode evidence --scenario fitness.progression-pr-smoke --adapter fitness.web --provider browserstack.playwright.v1
```

Report contract compatibility before repo rollout:

```powershell
python ops/atlas/qa/compatibility_report.py --scenario fitness.progression-pr-smoke --adapter fitness.web
```

Collect root-readable repo-native test evidence:

```powershell
python ops/atlas/qa/test_evidence.py --run <run-id>
```

Render an operator-facing evidence report:

```powershell
python ops/atlas/qa/report_run.py --run <run-id>
python ops/atlas/qa/evidence_index.py
python ops/atlas/qa/release_readiness.py
python ops/atlas/qa/adoption_drift.py
python ops/atlas/qa/release_rehearsal.py
python ops/atlas/qa/release_snapshot.py --repo fitness --run <run-id>
python ops/atlas/qa/waiver_monitor.py
python ops/validation/compile_python_tools.py --path ops/atlas/qa --path ops/validation
```

Propose and bless governed visual baselines from an evidence run:

```powershell
python ops/atlas/qa/baselines.py propose --run <run-id>
python ops/atlas/qa/baselines.py bless --run <run-id> --lens desktop.chromium.emulated --approved-by <operator>
```

## Operating Rules

- Rule: executable failures block promotion.
- Rule: missing required artifacts block promotion unless the scenario policy explicitly allows manual certification.
- Rule: required real-device proof for high-risk scenarios must resolve to `satisfied`, `manual_required`, or `missing`; never silently pass.
- Rule: dry-run evidence may validate wiring, but may never satisfy promotion.
- Rule: a missing required visual lens blocks promotion unless the scenario policy explicitly allows a manual certification lane.
- Rule: promotion-grade QA requires both valid evidence and clean root governance unless a formal waiver contract exists.
- Rule: a lane waiver may mark a real-device lane as waived, but it must never mark that lane as passed.
- Rule: expired, wrong-run, or wrong-scenario waivers must fail release readiness when the receipt is reevaluated.
- Rule: `waived_promoted` remains release debt; monitor expiry and replace it with real proof when the blocking lane becomes available.
- Rule: browser-backed screenshots from emulated desktop, Android, and iPhone lenses are evidence-grade artifacts, but they are not physical-device proof.
- Rule: promotion records must state the highest satisfied evidence tier.
- Rule: repo-native unit and integration evidence must be collected through a versioned test-evidence receipt when a scenario marks it required for promotion.
- Rule: manual device evidence may resolve manual review, but it must be labeled as manual attestation rather than automated physical proof.
- Rule: `promoted_physical` and `promoted_physical_manual` must remain distinct.
- Rule: baselines should be promoted artifacts, not generated from dry-run screenshots.
- Rule: provider credentials are runtime-only and must never appear in adapters, scenarios, receipts, reports, baselines, or logs.
- Rule: repo lint failures are repo-owned blockers; root QA must surface them instead of bypassing them.
- Rule: promotion wording should match the evidence profile that actually passed.
- Rule: manual attestation may satisfy physical/manual review, but it must never be labeled as automated provider proof.
- Rule: release gates must be repo-tier aware. A physical-device gap in one repo must not block unrelated package, docs, or standard web repos.
- Rule: Fitness must remain non-release-ready until real manual or provider-backed physical evidence exists.
- Rule: no-credential provider readiness must never produce a false physical pass.
- Rule: release readiness must match the target SHA or stack lock pin, not just a recent receipt.
- Rule: release readiness may also require a trusted receipt origin when the release profile enables it.
- Rule: trusted-origin receipts must come from protected CI or protected manual execution; do not relabel local receipts as trusted.
- Rule: Windows `__pycache__` rewrite failures are cache hygiene issues, not source-truth failures; use the compile helper before treating them as validation regressions.

## Decision Meanings

- `promote`
  Executable truth is clean, required artifacts are complete, and required certification is satisfied.
- `manual_review`
  Executable truth may be clean, but artifacts or real-device proof still need human certification.
- `hold`
  Executable truth failed or required evidence is missing.
- `dry_run`
  Pipeline wiring was validated, but no promotion claim may be made from the receipt.

Promotion status tiers:

- `promoted_emulated`
  Promotion passed on executable truth plus governed emulated-browser evidence.
- `promoted_physical`
  Promotion passed on executable truth plus automated physical-device evidence.
- `promoted_physical_manual`
  Promotion passed on executable truth plus valid manual attestation for physical-device lanes.
- `manual_review`
  Evidence is partially satisfied, but one or more physical-device lanes still require manual completion.
- `waived_promoted`
  Promotion is release-ready only through a visible scoped waiver; the waived lane remains unsatisfied proof.

Profile-aware display labels:

- `promoted_contract`
  Human-facing label for `promoted_emulated` when the evidence profile is `package_contract`.
- `promoted_docs_governance`
  Human-facing label for `promoted_emulated` when the evidence profile is `docs_governance`.
- `promoted_web_visual`
  Human-facing label for `promoted_emulated` when the evidence profile is `web_visual`.

Visual status meanings:

- `not_configured`
  No governed visual diff assertions exist for the scenario.
- `passed`
  Configured visual assertions stayed within threshold.
- `baseline_required`
  Visual assertions exist, but one or more promoted baselines are still missing.
- `failed`
  A configured visual assertion exceeded threshold or the baseline or candidate artifact was invalid.

Test evidence status meanings:

- `not_configured`
  The scenario does not require repo-native test receipts.
- `planned`
  The scenario declared test evidence, but the run was only dry-run planning.
- `clean`
  Required repo-native test receipts passed.
- `failed`
  One or more required repo-native test receipts failed.
- `missing`
  The scenario declared required test evidence, but the receipt or command mapping was missing.

## Review Checklist

Before accepting a `promote` record, confirm:

1. the scenario contract matches the intended release surface
2. the adapter points at the canonical repo commands
3. the artifact manifest links the expected lenses and artifact kinds
4. executable truth is `clean`
5. real-device proof status is appropriate for the scenario criticality
6. stack validation is not blocking the root promotion gate

## CI Orchestration

Root workflow orchestration is permitted under `.github/workflows/**` only when the workflow delegates behavior to root-owned scripts.

- Use `ops/atlas/qa/ci_gate.py` as the single QA gate entrypoint.
- Keep workflow YAML thin: checkout, runtime setup, script invocation, artifact upload.
- Do not duplicate adapter logic, artifact validation, or promotion logic in workflow steps.
- Keep provider choice behind root provider manifests and adapter refs rather than workflow-specific vendor logic.
- BrowserStack live smoke should run only from protected manual dispatch with secrets present; missing credentials must resolve to `provider_unavailable`, not a false pass.

## Warning Budget

Stack validation warnings are governance debt, not promotion blockers by default.

- Use `runtime/receipts/validation/stack-warning-budget.latest.json` and `.md` as the current budget receipt.
- The budget is report-only for now: baseline the current warning count, prevent large increases, and track reductions over time.
- Review `warning_delta_from_baseline`, `top_5_warning_categories`, `top_5_warning_repos`, `recommended_next_fix`, and `budget_status` before deciding whether a warning increase needs explanation.
- When the warning count drops below baseline, the lower count becomes the new baseline for future runs.

## Protected Dispatch

Use GitHub Actions `workflow_dispatch` to generate trusted release receipts. Current required inputs are:

- `dispatch_scope`
- `mode`
- `scenario`
- `adapter`
- `provider`
- `enforce_release_readiness`
- `release_repo`
- `target_sha`
- `max_receipt_age_hours`
- `waiver_spec`

Use `dispatch_scope=single` for the existing one-scenario QA gate.
Use `dispatch_scope=release_refresh` to refresh protected receipts for either one release repo or the default release set from `ops/atlas/qa/release_policy.v1.json`.

Protected dispatch should upload:

- `bootstrap-release-repos.latest.json` and `.md`
- `protected-release-refresh.latest.json` and `.md` when `dispatch_scope=release_refresh`
- `release-readiness.latest.json` and `.md`
- `release-rehearsal.latest.json` and `.md`
- `evidence-index.latest.json` and `.md`
- `waiver-monitor.latest.json` and `.md`
- `adoption-drift.latest.json` and `.md`
- `stack-validation.latest.json` and `.md`
- `stack-warning-budget.latest.json` and `.md`
- Do not silently promote warnings to errors until the categories are understood and owned.

## Adoption Receipt

Adoption is not complete because config exists. Adoption means:

1. child-owned adapter and scenario manifests exist in the repo
2. ATLAS root can execute and validate those manifests
3. the evidence index records the repo's current promotion state and evidence profile
- `.github/workflows/atlas-qa-llel.yml` must keep pull requests on provider-free `dry-run`; provider-backed runs are `workflow_dispatch` only.
- Stack validation uses declared root scan surfaces instead of recursive root scanning, but it must still fail if a required governance surface such as `README-STACK.md`, `AGENTS.md`, `.github/workflows/`, `docs/`, or `ops/` falls out of coverage.

## Release Readiness

Use `ops/atlas/qa/release_readiness.py` to map adopted repos onto their release gate profile.

- `fitness` is governed as `release_critical_web`.
- `trove` is governed as `web_visual`.
- `playbook` is governed as `docs_governance`.
- `lifeline` and `foundation` are governed as `package_contract`.

Fitness also carries one release-mode governance checkpoint:

- `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`

That guardrail report must stay fresh, match contract version `atlas.vercel_hobby_guardrail.v1`, and remain readable from root release-readiness before Fitness release enforcement can pass.

The release-readiness report should mark a repo release-ready only when its latest meaningful receipt satisfies the repo's release profile.

Use `python ops/atlas/qa/release_readiness.py --repo <repo-id> --mode release --enforce` to fail a release path when a target repo is not release-ready.
Use `--target-sha <sha>` to enforce against an explicit release target when the stack lock or repo HEAD is not the intended source of truth.
Use `--max-receipt-age-hours <hours>` to tighten freshness during rehearsals or cutovers.

The root workflow auto-enforces release readiness on:

- `workflow_dispatch` when `enforce_release_readiness=true`
- `push` to `release/<repo-id>/...`
- `push` tags matching `<repo-id>-v...`

If a release path does not use one of those naming patterns, pass the repo id explicitly through the manual dispatch input.

Release readiness now records provenance fields:

- `target_sha`
- `receipt_sha`
- `sha_match`
- `stack_lock_pin`
- `readiness_source_run_id`
- `receipt_origin_type`
- `trusted_origin_required`
- `trusted_origin_match`
- `trusted_origin_status`
- `origin_enforcement_stage`
- `selection_reason`

Fresh receipts for the wrong SHA must fail enforcement.
When a release profile enables trusted origins, correct-SHA receipts from untrusted execution paths must fail enforcement too.

Trusted receipt origins are:

- `local_dev`
- `ci_pr`
- `ci_release`
- `protected_manual`
- `provider`

Protected manual dispatch can be used to produce a trusted non-PR receipt without putting provider secrets or operator identities into source files.

Before `dispatch_scope=release_refresh`, bootstrap the requested child repos from `stack.lock.yaml`:

```powershell
python ops/atlas/qa/bootstrap_release_repos.py --repo playbook
```

Rules for protected bootstrap:

- clone the repo from the locked `remote`
- checkout the exact locked `commit`
- fail if `remote` is missing
- fail if `commit` is missing
- fail if the requested release repo is still marked `dirty: true` in `stack.lock.yaml`
- fail if the checked-out `HEAD` does not match the locked commit
- fail if the checked-out worktree is dirty after bootstrap

Protected release proof must run against a clean, pushed, exact-SHA child repo checkout. Local dirty child repo state cannot become trusted release evidence.

When a protected manual refresh must preserve a scoped waiver, pass `waiver_spec` as JSON.
The spec is reissued for the new protected run, so the new receipt stays visibly `waived_promoted` instead of silently degrading to `manual_review`.
Required fields are:

- `repo_id`
- `scenario_id`
- `waived_lane`
- `reason`
- `expires_at`
- `evidence_present`
- `limitation`

Origin enforcement stages:

- `observe`
  Report origin trust but never block on it.
- `warn`
  Keep the repo release-ready if everything else passes, but surface that the receipt should be refreshed through CI or protected manual flow.
- `enforce`
  Block release readiness when the receipt origin is outside the trusted release origins for the profile.

## Adoption Drift

Use `ops/atlas/qa/adoption_drift.py` to check that child repos still own real QA intent and have fresh root-readable receipts.

- The drift scanner must verify child-owned `qa/adapters/*.json`, `qa/scenarios/*.json`, and `docs/qa.md`.
- The drift scanner should flag stale receipts, missing manifests, invalid contract versions, and release-policy mismatches.
- Adoption means child-owned intent plus root-readable receipts, not root-side prototypes.
- Prototype-only root configs such as `stream` must stay labeled as `prototype_only_root_config` until they are adopted or retired.

## Release Rehearsal

Use `ops/atlas/qa/release_rehearsal.py` before relying on the gate operationally.

- Rehearsal must exercise both passing repos and intentionally blocked repos.
- The current expected blocked case is `fitness`, with the physical/manual-proof blocker only.
- Rehearsal should not mutate repo state.
- CI/manual dispatch can now regenerate `release-readiness.latest.*`, `release-rehearsal.latest.*`, and adoption-drift artifacts from the workflow path as well as local scripts.

## Protected Manual BrowserStack Usage

- Use BrowserStack only from protected manual flows. The root workflow exposes it as the `provider` input on `ATLAS QA LLEL`.
- Leave `provider` set to `none` for normal PR validation and for any manual run that does not need provider-backed real-device evidence.
- Select `browserstack.playwright.v1` only for operator-triggered `evidence` or `promotion` runs that are explicitly exercising the provider lane.
- Store `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY` in GitHub Actions secrets. Do not place them in committed files, workflow inputs, logs, issue comments, or ad hoc command history.
- If the provider is requested without credentials, the expected result is `provider_unavailable`. That status should preserve the normal QA/manual-review semantics instead of converting BrowserStack absence into a default developer blocker.
- Provider errors must redact credential values before surfacing stderr or stdout back to the operator.

## Retention

Store generated QA runtime records under `runtime/atlas/qa/`.

- `matrix.result.json`
- `artifacts.manifest.json`
- `artifact.validation.json`
- `evaluated.result.json`
- `promotion.record.json`
- `test-evidence.json`
- `report.summary.json`
- `evidence-index.latest.json`

These runtime files are generated evidence, not committed source artifacts.

## Provider Notes

- Keep the provider contract behind `ops/atlas/qa/providers/**`.
- BrowserStack support is credential-gated through provider manifests and environment variables; do not commit provider secrets.
- BrowserStack readiness is an operator lane, not a default PR requirement.
- Provider choice stays replaceable. ATLAS owns the evidence contract, not the vendor.
