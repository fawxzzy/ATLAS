# Vercel Hobby Cost Governance Marker Admission Pass 1 - 2026-06-13

- Date: `2026-06-13`
- Lane: `Vercel cost governance`
- Owner: `ATLAS/root`
- Mode: `root governance and marker admission`
- Governing app: `Fawxzzy Fitness`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `ops/atlas/marker_knockout_selector.py`
  - `tests/test_atlas_marker_knockout_selector.py`
  - `runtime/receipts/validation/stack-validation.latest.md`
  - `runtime/receipts/validation/stack-validation.latest.json`
  - [Vercel Hobby plan docs](https://vercel.com/docs/plans/hobby)
  - [Vercel pricing](https://vercel.com/pricing)
  - [Observability Plus docs](https://vercel.com/docs/observability/observability-plus)
- Control-plane checkpoint: `main@2d4a6b1e`

## Objective

Admit one supporting open marker so Fitness cheap-by-design Vercel posture stays durable before any Pro upgrade or observability add-on dependency is allowed to creep in by panic, drift, or undocumented habit.

## Scope

- Fawxzzy Fitness cost governance on Vercel Hobby
- cheap-by-design pre-Pro operating discipline
- no deploy, billing-setting, or project-setting mutation

## Marker Admission

Admit exactly one new supporting open marker:

- `Vercel Hobby Cost Governance: 35%`

Placement:

- supporting open marker only
- not front-page
- grouped with release/publication/surface-adjacent supporting markers rather than automation markers

## Current Verified Platform Facts

As of `2026-06-13`, the official Vercel docs show:

- Hobby is the intended free baseline, while Pro starts at `$20/month` plus additional usage; those figures are date-sensitive and should be rechecked before any upgrade decision
- Hobby currently includes `4 CPU-hrs`, `360 GB-hrs` provisioned memory, `1,000,000` function invocations, `10,000` Speed Insights events, and `50,000` Web Analytics events
- the pricing page currently shows `1M / month` included for Edge Requests on Hobby
- Observability Plus is currently available on Pro and Enterprise plans, and the Observability Plus docs describe it as an optional upgrade rather than a normal Hobby feature

These facts are governance inputs, not a standing guarantee. Future receipts must re-check the official docs before using exact thresholds operationally.

## What The Marker Tracks

- active CPU / compute growth
- function invocation growth
- edge request and middleware pressure
- route fetch pressure
- image optimization, analytics, and Speed Insights pressure when relevant
- runtime-log and observability retention limits
- Observability Plus / Pro gating
- explicit upgrade thresholds instead of defaulting to paid-plan drift

## Explicit Upgrade Threshold Model

- `Green`: current production traffic fits Hobby with margin and no Pro-only observability dependency exists
- `Yellow`: sustained usage approaches documented Hobby included usage, or route, middleware, or fetch pressure is trending upward enough that the margin is shrinking
- `Red`: repeated Hobby exhaustion risk appears, a Pro-only observability dependency becomes required, or production reliability needs exceed what the cheap-by-design Hobby posture can honestly support
- any upgrade decision must be backed by a separate receipt with current usage evidence, growth reason, and rollback or cost-control posture

## Non-Goals

- no immediate Pro upgrade
- no `.vercel` mutation
- no secret or billing config changes
- no deployment
- no Fitness code mutation
- no claim that Hobby will always be sufficient
- no claim that Pro is needed now

## Why The Initial Value Is 35%

- the cost-governance concern is now identified clearly enough to deserve durable marker space
- Fitness already has cheap-by-design intent rather than a blank slate
- but repeatable usage snapshots, route-pressure inventory, and durable threshold proof are not yet preserved in the root truth model

That is enough for admission, but not enough for a higher starting percentage.

## Marker Movement Rules

- `45%`: first root receipt lands with current Vercel usage snapshot categories and the threshold model
- `55%`: route, middleware, and fetch pressure inventory exists
- `65%`: a Hobby guardrail report can be rerun without secrets
- `75%`: Fitness release or readiness flow includes a cost-governance check
- `85%`: two or more usage snapshots prove trend discipline
- `95%`: the Pro-upgrade gate is durable and exercised against realistic growth cases
- `100%`: cheap-by-design governance is repeatable, preserved through release workflow, and the Pro path is explicit without being accidentally triggered

## Marker Movement

- `Vercel Hobby Cost Governance`: new marker admitted at `35%`
- no existing marker percentage moved in this pass

## Root Validation And Safety

- this pass is root governance only
- no Fitness repo mutation was needed
- no Vercel project settings were changed
- no deploy ran
- no secret-bearing surface was read or exposed

Validator preflight required one cleanup and one lock refresh before the marker could land:

- removed generated `repos/DiscordOS/.vercel`
- removed generated `repos/DiscordOS/node_modules`
- refreshed `stack.lock.yaml` to the current pinned working set after DiscordOS advanced on local `main`

## Validation

- `git status -sb`
- `git fetch origin main`
- `git rev-list --left-right --count origin/main...HEAD`
  - result: `0	0`
- `git log -1 --oneline --decorate`
  - result: `2d4a6b1e (HEAD -> main, origin/main) docs: reconcile broader execution behavior frontier`
- `python ops/validation/validate_stack.py --ratchet`
  - final result after cleanup and lock refresh: `critical=0 error=0 warning=0 info=0`
- `python ops/atlas/marker_knockout_selector.py --format json`
  - expected result after admission: parse succeeds and first admissible marker remains `AI Repetition-to-Automation Pipeline`
- `python ops/atlas/marker_knockout_selector.py --format markdown`
  - expected result after admission: render succeeds

## Protected Surfaces Not Touched

- `repos/fawxzzy-fitness/**`
- secrets and billing settings
- deployment settings and deploy actions
- `archive/` contents beyond existing local residue

## Rule

Keep Fitness on a cheap-by-design Hobby posture by default; any move toward Pro or Pro-only observability must be threshold-backed, explicit, and separately receipted.
