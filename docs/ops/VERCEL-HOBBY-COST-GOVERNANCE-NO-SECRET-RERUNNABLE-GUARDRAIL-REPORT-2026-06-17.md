# Vercel Hobby Cost Governance No-Secret Rerunnable Guardrail Report - 2026-06-17

- Date: `2026-06-17`
- Lane: `Vercel Hobby Cost Governance`
- Owner: `ATLAS/root`
- Mode: `root governance helper landing plus proof`
- Governing app: `Fawxzzy Fitness`
- Source surfaces:
  - `docs/memory/profiles/zachariah_workflow_profile.md`
  - `docs/atlas-book/01-current-state.md`
  - `docs/atlas-book/02-lanes-and-markers.md`
  - `docs/atlas-book/05-receipt-index.md`
  - `docs/atlas-book/12-restart-and-handoff-guide.md`
  - `docs/ops/VERCEL-HOBBY-COST-GOVERNANCE-CURRENT-USAGE-SNAPSHOT-AND-THRESHOLD-CHECKPOINT-2026-06-17.md`
  - `docs/ops/VERCEL-HOBBY-COST-GOVERNANCE-ROUTE-MIDDLEWARE-AND-FETCH-PRESSURE-INVENTORY-2026-06-17.md`
  - `ops/atlas/vercel_hobby_guardrail_report.py`
  - `tests/test_atlas_vercel_hobby_guardrail_report.py`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`
  - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.md`
- Control-plane checkpoint: `main@8a315797`

## Objective

Advance the lane from one durable route-pressure inventory to one rerunnable no-secret Hobby guardrail report that can be regenerated from local Fitness repo state without Vercel auth, billing access, or secrets.

## Helper Surface

New helper:

- `ops/atlas/vercel_hobby_guardrail_report.py`

Scope:

- reads `stack.yaml` repo registry
- resolves Fitness from repo id `fitness`
- reads local identity-only `.vercel/project.json`
- reads local `vercel.json`
- inventories `src/app/**/route.ts`
- inventories local fetch sites under `src/`
- inventories middleware posture from `src/middleware.ts`
- inventories public authless route exceptions from `src/lib/auth-session.ts`
- emits either JSON or markdown

Fail-closed boundaries:

- errors if the repo id is unknown
- errors if the local Vercel link file is missing or malformed
- errors if no route handlers are found

No-secret boundary:

- does not call Vercel
- does not read billing
- does not require `.env`
- does not require deploy authority

## Real Report Proof

JSON command:

- `python .\ops\atlas\vercel_hobby_guardrail_report.py --repo-id fitness --format json --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`

Markdown command:

- `python .\ops\atlas\vercel_hobby_guardrail_report.py --repo-id fitness --format markdown --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.md`

Current real report summary:

- total routes: `31`
- api routes: `22`
- auth routes: `5`
- dev routes: `4`
- force-dynamic routes: `29`
- explicit nodejs routes: `4`
- fetch sites: `34`
- internal fetch sites: `17`
- external-or-dynamic fetch sites: `17`
- deployment posture: `ok`
- route pressure posture: `watch`
- middleware pressure posture: `watch`
- integration pressure posture: `watch`
- hot route watch posture: `watch`

Current real middleware read:

- broad non-static matcher: `True`
- refresh-session call present: `True`
- public authless paths:
  - `/api/app-version`
  - `/api/discord/interactions`

Current explicit Node routes:

- `/api/discord/interactions`
- `/api/spotify/oauth/callback`
- `/api/spotify/oauth/start`
- `/api/vercel/deployment-webhook`

## Test Proof

Automated proof:

- `python -m unittest tests.test_atlas_vercel_hobby_guardrail_report -v`

Coverage:

- local fixture report builds and returns the expected summary counts
- JSON output write path works
- missing local `.vercel/project.json` fails closed

## Marker Movement

- `Vercel Hobby Cost Governance` moves from `55%` to `65%`

Why `65%` is honest:

- the lane now has one rerunnable guardrail report
- the report is no-secret and local-only
- the helper is test-backed and fail-closed on missing identity or route surfaces
- the output can be preserved in runtime receipts without requiring live connector access

Why the lane still stops here:

- no Fitness release or readiness flow consumes the report yet
- no preserved multi-snapshot trend proves stabilization or drift over time

## Exact Next Honest Moves

- `75%`: Fitness release or readiness flow includes a cost-governance checkpoint that consumes the guardrail report
- `85%`: at least two preserved usage or guardrail snapshots prove trend discipline

## Validation

- `python -m unittest tests.test_atlas_vercel_hobby_guardrail_report -v`
- `python .\ops\atlas\vercel_hobby_guardrail_report.py --repo-id fitness --format json --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`
- `python .\ops\atlas\vercel_hobby_guardrail_report.py --repo-id fitness --format markdown --output runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.md`

Result:

- tests passed
- JSON report emitted
- markdown report emitted
