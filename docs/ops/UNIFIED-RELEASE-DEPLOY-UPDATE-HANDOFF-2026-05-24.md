# Unified Release / Deploy / Update Handoff

Date: 2026-05-24
Lane: Unified Workflow Convergence
Mode: docs-only handoff map
Status: handoff baseline recorded

## Goal

Define one canonical cross-stack handoff from repo-local release preparation to `_stack` deploy authority, release-ledger evidence, Discord `#updates` publishing, feedback/completion review, and ATLAS root receipt packaging.

This pass does not deploy, mutate Vercel, mutate Supabase, post to Discord, or change repo implementation behavior.

## Governing Rules

- Repo-local commands may prepare, verify, and build; they do not become deploy authority by implication.
- `_stack` is the only approved preview and production deploy authority for governed Vercel app lanes.
- No manual deploy is the default.
- No Discord post may publish before proof exists.
- ATLAS root records cross-repo governance and lock truth; it does not duplicate repo-owned product or bot truth.
- Playbook extracts reusable rules, patterns, and failure modes from governed evidence after the workflow completes.

## Canonical Handoff Chain

1. Repo-local release prep
2. `_stack` deploy authority
3. Release-ledger evidence
4. Discord `#updates` publish boundary
5. Feedback and completion review boundary
6. ATLAS root receipt packaging
7. Playbook doctrine extraction and promotion

## Boundary Map

| Stage | Canonical entrypoint | Owner | Required proof before handoff | Output |
| --- | --- | --- | --- | --- |
| Repo-local release prep | repo-local commands and docs | owner repo | local verify/build/release-prep evidence | release-ready candidate |
| Deploy authority | `_stack` preview/prod wrapper | `_stack` | repo-local readiness plus `_stack` preflight success | governed deployment attempt |
| Release-ledger evidence | repo-owned release ledger | owner repo | successful deploy evidence and release metadata | durable shipped-evidence row |
| Discord publish boundary | repo-owned bot/admin publish surface | owner repo + Discord surface | deploy proof plus curated user-facing summary | public update post |
| Feedback/completion review | feedback exports, review docs, completion checkpoints | owner repo + planning/governance surfaces | shipped change linked to reviewed work | closed-loop review evidence |
| Root receipt packaging | `docs/ops/**`, `stack.lock.yaml`, root validation | ATLAS root | cross-repo impact or lock truth change | stack-level receipt/checkpoint |
| Doctrine extraction | Playbook notes/contracts | Playbook owner surface | stable repeated pattern or failure mode | promoted rule/pattern/failure-mode candidate |

## 1. Repo-Local Release Prep Boundary

Repo-local release prep is where app owners verify, version, build, and prepare release artifacts.

Current governed example:

- Fitness repo-local `release:*` commands prepare release version and metadata.
- Fitness repo-local verify and build commands prove the repo is ready.
- Trove and Mazer repo-local surfaces provide repo verification and product-specific readiness.

Repo-local release prep may:

- verify local product behavior
- build artifacts
- prepare version metadata
- prepare release notes inputs
- refresh repo-owned ledgers or draft artifacts where documented

Repo-local release prep may not:

- become deploy authority by naming
- imply production promotion
- bypass `_stack` deploy preflights

Rule:

- release preparation is not deploy authorization

Failure mode:

- operators treat release or build commands as approval to ship production directly

## 2. `_stack` Deploy Authority Boundary

`_stack` is the approved operator entrypoint for preview and production deploys for Fitness, Trove, and Mazer.

Current governed state:

- Fitness preview/prod deploy authority runs through `_stack` `fitness:deploy:*`
- Trove deploy wrappers fail closed if local `.vercel/project.json` identity drifts from pinned Trove identity
- Mazer deploy wrappers fail closed if author identity or pinned local Vercel identity drifts

`_stack` deploy authority is where:

- deploy-intent becomes explicit
- fail-closed identity preflights run
- approved preview/prod wrappers reach Vercel
- exceptional recovery paths stay separate from the default operator path

No-manual-deploy default:

- direct repo-local `vercel` or `vercel --prod` is recovery-only or exceptional
- direct deploy commands are not the canonical workflow
- deploys should not begin outside `_stack` unless an incident/recovery lane explicitly authorizes it

Rule:

- mutation follows trust, not curiosity

Pattern:

- repo-local prep -> `_stack` preflight -> deploy wrapper -> proof

Failure mode:

- deploy wrappers exist, but operators still improvise manual Vercel commands because the boundary is undocumented

## 3. Release-Ledger Evidence Boundary

Release ledgers are repo-owned evidence surfaces, not deploy authority.

Current strong example:

- Fitness production deploys are expected to produce a release ledger entry in `docs/releases/RELEASE_LEDGER.jsonl`

The release-ledger boundary exists to capture:

- deployed commit
- environment
- deployment URL and production URL
- user-facing change summary
- internal change summary
- verification set
- artifacts and known gaps

Rule:

- a production deploy is not fully governed until shipped evidence is recorded

Pattern:

- deploy proof -> ledger evidence -> downstream publish or review

Failure mode:

- a deploy happens, but the only trace is CLI output or memory instead of durable evidence

## 4. Discord `#updates` Publishing Boundary

Discord updates are downstream publication, not deploy authority and not task truth.

Current governed Fitness pattern:

1. production deployment event is observed
2. bounded update draft is created
3. admin reviews with `/update-latest`
4. admin publishes with `/update-publish`
5. Discord receives curated user-facing copy

No-Discord-post-before-proof rule:

- no public update post before deploy evidence exists
- no feedback-card mutation stream into `#updates`
- no raw commit log, migration name, stack trace, or infra-only noise in release posts

Discord publish may:

- announce shipped user-facing changes
- summarize why the change matters
- point users to the correct live surface

Discord publish may not:

- act as deploy proof
- replace the release ledger
- replace feedback-thread audit comments
- publish ahead of governed evidence

Rule:

- deployment metadata is input, not user-facing release copy

Failure mode:

- a deploy or feedback-card mutation causes premature public posting before proof or curation exists

## 5. Feedback Card / Completion Review Boundary

Feedback review and completion proof sit between shipped work and durable governance learning.

Canonical intent:

- feedback forum thread history remains inside the forum or audit-comment surface
- reviewed exports become planning inputs
- completion review links shipped change back to the reviewed work
- one shipped item produces one appropriate public update format

This boundary is where the stack checks:

- whether the work actually answered the reviewed request
- whether a card-specific update format should replace a broad release summary
- whether any known gaps or follow-ups stay open

Rule:

- public release narration and feedback-card history must stay distinct

Failure mode:

- teams duplicate raw feedback-card state into ATLAS, GitHub, and Discord, creating multiple competing truths

## 6. ATLAS Root Receipt Packaging Boundary

ATLAS root packages the stack-level truth that crosses repo boundaries.

ATLAS root should package:

- stack-lock repins and decision receipts
- convergence inventories and handoff maps
- cross-repo governance checkpoints
- pause/resume lane receipts
- root validation results

ATLAS root should not duplicate:

- repo-owned release ledger rows
- repo-owned deploy docs as owner truth
- Discord bot draft/publish runtime state
- repo-local product verification as if root owned it

Pattern:

- repo owner truth stays local; ATLAS root records the cross-repo consequence

Failure mode:

- root becomes a second implementation ledger instead of a coordination and governance layer

## 7. Playbook Extraction Boundary

Playbook should become mandatory once a workflow yields stable reusable doctrine instead of one-off local facts.

Playbook extraction points in this handoff:

- release-prep versus deploy-authority separation
- fail-closed identity preflight patterns
- release-ledger evidence requirements
- no-public-post-before-proof doctrine
- feedback-history versus release-announcement boundary
- cross-repo receipt packaging rules

What Playbook should extract:

- reusable rules
- patterns
- failure modes
- contract candidates
- promotion candidates for workflow doctrine

What Playbook should not do here:

- become the live deploy wrapper
- replace repo-owned release ledgers
- replace ATLAS root continuity or receipt packaging

Rule:

- extracted knowledge is evidence first and reusable doctrine second

## 8. Fallback / Recovery Path

Recovery is explicit and exceptional.

If the canonical handoff cannot proceed:

1. classify the failure
2. keep the default path blocked
3. authorize a bounded recovery lane only if needed
4. record the recovery action and route back to canonical flow

Acceptable fallback classes:

- `_stack` preflight blocked by identity drift
- deploy provider ingestion failure or Git/Vercel linkage issue
- release-ledger evidence missing after otherwise successful deploy
- Discord publish blocked while deploy proof remains valid

Recovery rules:

- direct repo-local `vercel --prod` remains recovery-only, not default
- recovery must not silently rewrite the canonical process
- any recovery deploy must still produce evidence, review, and root receipt packaging
- after recovery, the system should return to repo-local prep -> `_stack` deploy authority -> evidence -> publish

## Recommended Canonical Operator Story

The stack should present one simple operator story:

1. prepare and verify inside the owner repo
2. deploy only through `_stack`
3. record shipped evidence in the owner repo
4. publish curated Discord updates only after proof
5. package cross-repo consequences in ATLAS root
6. extract reusable doctrine through Playbook after closure

This is the first convergence contract for release, deploy, and updates.

## Remaining Gaps

- Trove Git auto-deploy state is still not documented in governed surfaces.
- Mazer Git auto-deploy state is still not documented in governed surfaces.
- `_stack` still has no remote, so operator-truth commits remain local-only and require root lock acceptance.
- Discord update and release-ledger automation is still strongest in Fitness, not yet generalized as a cross-stack contract.
- Remote preview/unfurl verification remains a separate deploy-backed lane and is intentionally not opened here.

## Validation

Validation command:

- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos`

Expected interpretation for this package:

- docs-only convergence mapping
- no deploy
- no Discord publish
- no Vercel or Supabase mutation
