# Manual Deploy Exception Inventory

Date: 2026-05-24
Lane: Manual Deploy Exception Burn-Down
Mode: docs-only inventory
Status: inventory complete

## Goal

Find every documented or active deploy path in the current stack surfaces and classify whether production deploy authority is already governed by `_stack` or still depends on manual or ad hoc operator behavior.

This pass does not deploy, pull env, mutate Vercel, mutate Supabase, or change scripts.

## Current Doctrine

The intended stack rule is already clear:

- production-capable deploys should flow through `_stack`
- canonical repo identity must be verified before deploy
- Git-triggered auto-deploys must not silently replace the governed path
- release notes and Discord updates derive from deployment truth, but deployment metadata is not user-facing copy

The lane is not fully closed yet because some app deploy families are more strongly governed than others, and some historical manual habits are still documented or implied in repo-local release rituals.

## Evidence Surfaces

Primary evidence used in this inventory:

- `repos/_stack/package.json`
- `repos/_stack/config/release-targets.json`
- `repos/_stack/README.md`
- `repos/_stack/docs/fitness-verify.md`
- `repos/_stack/docs/ops/fitness-vercel-deploy-recovery.md`
- `repos/_stack/ops/Test-FitnessDeployLink.ps1`
- `repos/_stack/ops/Test-FitnessDoctor.ps1`
- `repos/_stack/ops/Invoke-MazerDeploy.ps1`
- `repos/_stack/config/fitness-deploy.identity.json`
- `repos/fawxzzy-fitness/package.json`
- `repos/fawxzzy-fitness/docs/COMMANDS.md`
- `repos/fawxzzy-fitness/docs/LOCAL-PROD-DATA-SYNC.md`
- `repos/fawxzzy-fitness/docs/ops/FITNESS-DISCORD-UPDATES.md`
- `repos/fawxzzy-fitness/docs/releases/RELEASE_LEDGER.jsonl`
- `docs/ops/TMP-DEPENDENCY-DEMOTION-RECEIPT-2026-05-23.md`
- `docs/ops/FITNESS-CANONICAL-PATH-RESTORATION-REPAIR-2026-05-24.md`

## Deploy Path Inventory

| Command or path | Owner repo | Target project | Production-capable | Current status | Required verification or gate | Discord `#updates` / feedback closeout tie-in | Replacement governed path or follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pnpm run fitness:deploy:preflight` | `_stack` | Fitness Vercel project `prj_rtlFVOMFAWCRoJ3SQjHloi89881K` | no | allowed and canonical preflight gate | `_stack` preflight must pass; canonical repo must exist; `.vercel/project.json` must match immutable team/project IDs; Git auto-deploy must remain `disabled` | indirect only; production publish should never happen without this gate first | keep as canonical guard; use before every preview or prod Fitness deploy |
| `pnpm run fitness:deploy:preview`, `fitness:deploy:preview:logs`, `fitness:deploy:prebuilt` | `_stack` | Fitness Vercel preview path for `fawxzzy-fitness` | no | allowed and governed | `fitness:deploy:preflight`; `fitness:verify:clean` or `fitness:build:vercel` depending on path | no public `#updates` publish expected; preview deploys are ignored by the update bot | keep as canonical preview path; no repo-local direct Vercel deploy |
| `pnpm run fitness:deploy:prod`, `fitness:deploy:prebuilt:prod` | `_stack` | Fitness production deploy for `fawxzzy-fitness` | yes | allowed and canonical | `fitness:deploy:preflight`; `fitness:verify:clean` or `fitness:build:vercel`; typed confirmation via launcher for prod target | yes; only Fitness production deployments should create update drafts; publish remains curated via `/update-latest` and `/update-publish` | keep as the only approved Fitness production path |
| `pnpm run fitness:git:autodeploy:disable` | `_stack` | Fitness Vercel Git integration state | indirectly | allowed maintenance guard | run when preflight finds `createDeployments` drift | protects update-bot trust by preventing hidden production deploy creation outside the governed lane | keep; use to burn down Git-triggered deploy regressions |
| Direct `vercel` or `vercel --prod` from `repos/fawxzzy-fitness` | Fitness | Fitness Vercel project | yes | discouraged and treated as a recovery-only exception | if ever used historically, current production SHA must first be recovered into Git; canonical repo only; do not treat dirty local deploys as normal release source | production deploy events still feed update drafts, but this path weakens trust and should not be normal release authority | replace with `_stack` `fitness:deploy:*`; document any future direct use as recovery incident, not standard workflow |
| `npm run release:patch`, `release:minor`, `release:major` | Fitness | Fitness repo release metadata and versioning | indirectly | allowed as repo-local release ritual, not deploy authority | local verify and release readiness expectations still apply, but these commands do not replace `_stack` deploy authority | can support release-note preparation, but public `#updates` still depend on actual production deployment plus manual publish | keep as repo-local semver and release-prep helpers only; pair with `_stack` deploy path for production |
| `npm run release:preflight`, `release:fitness:prepare`, `release:fitness:record`, `release:fitness:diff`, `release:fitness:ready` | Fitness | Fitness release readiness and ledger | no | allowed support lane, not deploy authority | repo-local verify, release-readiness, and ledger validation | yes; supports curated release copy and ledger evidence, but does not itself publish or deploy | keep as release support only; do not mistake for deploy entrypoint |
| `pnpm run trove:deploy:preview`, `trove:deploy:prebuilt` | `_stack` | Trove Vercel preview path behind `fawxzzy-trove.vercel.app` | no | allowed and governed, but identity proof is lighter than Fitness | repo-local `npm --prefix ../fawxzzy-trove run verify`; optional prebuilt isolation | no documented `#updates` or Discord closeout lane in this pass | keep as canonical Trove preview path, but add stronger project-identity guard later if Trove becomes production-critical |
| `pnpm run trove:deploy:prod`, `trove:deploy:prebuilt:prod` | `_stack` | Trove production path behind `fawxzzy-trove.vercel.app` | yes | allowed, but less hardened than Fitness | repo-local verify before Vercel; typed confirmation in launcher for prod target | no documented Discord release bot tie-in | keep as current governed path; future burn-down should add immutable project-identity proof comparable to Fitness |
| Direct `vercel` deploy from `repos/fawxzzy-trove` | Trove | Trove Vercel project | yes | discouraged by governance pattern even though `_stack` wraps the same CLI | if ever needed for debugging, it should be treated as bypass of the approved operator surface | no documented closeout path | replace with `_stack` `trove:deploy:*` commands |
| `pnpm run mazer:deploy:preflight` | `_stack` | Mazer deploy identity gate | no | allowed and canonical preflight gate | checks required Git owner identity and latest commit author before any deploy | none documented | keep as canonical preflight |
| `pnpm run mazer:deploy:preview`, `mazer:deploy-preview` | `_stack` | Mazer Vercel preview deploy | no | allowed and governed | owner-author preflight plus local `mazer:verify` | none documented | keep as canonical preview path |
| `pnpm run mazer:deploy:prod`, `mazer:deploy-prod` | `_stack` | Mazer production deploy | yes | allowed, but governance is identity-focused rather than project-ID-focused | owner-author preflight plus local `mazer:verify` | none documented | keep as current governed path; future burn-down should record immutable Vercel project identity similar to Fitness |

## Classification Summary

### Strongly governed now

These deploy paths already fit the intended operator model:

- Fitness preview and production deploys through `_stack`
- Fitness preflight and Git auto-deploy disable guard
- Mazer preview and prod deploys through `_stack`
- Trove preview and prod deploys through `_stack`

Shared properties:

- explicit operator command
- repo-local verification before deploy
- no Git-push auto-deploy authority
- launch-surface exposure through `_stack` release targets instead of ad hoc shell memory

### Governed, but still weaker than Fitness

Trove and Mazer still have weaker deploy governance than Fitness in one key way:

- Fitness has explicit immutable Vercel identity proof in `_stack` config plus dedicated preflight and doctor scripts
- Trove currently relies on `_stack` wrapping the right repo path and deployed host expectations, but this pass did not find a matching immutable project-ID guard
- Mazer has a strong Git-author ownership preflight, but this pass did not find an equivalent immutable Vercel project-ID contract

These are not broken paths. They are burn-down candidates because the governance is less explicit than the Fitness lane.

### Manual or ad hoc exceptions still worth burning down

The remaining exception class is concentrated in Fitness history and repo-local habits:

- direct repo-local `vercel` or `vercel --prod` deployment remains a documented recovery hazard in Fitness docs
- repo-local release bump commands can look like deploy authority even though they are only release preparation and recording surfaces
- production Discord update publication is still intentionally manual after deploy, which is correct, but means the closeout lane is split across deploy truth plus admin publish action

## Fitness-Specific Deploy Truth

Fitness is currently the cleanest governed production lane.

Canonical deploy identity:

- team id: `team_CMJn7MvzFZZBnhNnjVUZF2RD`
- scope: `fawxzzy`
- project id: `prj_rtlFVOMFAWCRoJ3SQjHloi89881K`
- project name: `fawxzzy-fitness`
- Git auto-deploy creation: `disabled`

Current production doctrine:

- deploy from canonical `repos/fawxzzy-fitness`
- do not deploy from `tmp`
- do not treat dirty local Vercel CLI deploys as normal release authority
- do not bypass `_stack` preflight

Discord closeout tie-in:

- only Fitness production deployments should create update drafts
- preview deployments should not create update drafts
- deployment metadata is bounded input, not public release copy
- public publish still requires manual curated review

## Burn-Down Targets

This inventory suggests the next manual-deploy exception work should focus on four gaps:

1. codify Trove Vercel project identity with a preflight path comparable to Fitness
2. codify Mazer Vercel project identity in addition to the existing owner-author guard
3. mark repo-local Fitness release scripts more explicitly as release-prep only, not deploy authority
4. audit any remaining docs that still imply direct `vercel --prod` is normal instead of recovery-only

## No-Deploy Confirmation

This pass did not:

- deploy any app
- mutate Vercel settings
- mutate Supabase
- pull env
- change repo scripts
- post to Discord

## Lane Interpretation

Manual Deploy Exception Burn-Down is no longer about discovering whether `_stack` owns any deploy path at all.

It is now about:

- removing the remaining documented ambiguity around direct repo-local deploy behavior
- hardening non-Fitness deploy lanes to the same identity-proof standard as Fitness
- ensuring deployment truth and Discord release closeout remain explicit and governed
