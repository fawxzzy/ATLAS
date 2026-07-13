---
name: review-project-next-step
description: Review a software project or multi-repository system from user-provided examples, repository evidence, plans, boards, PRs, markers, receipts, logs, or status summaries; reconcile current truth, prioritize remaining work, and select the next safe execution packet. Use when the user asks what is done, what remains, what matters most, whether a new lane is justified, how to sequence work, how project notes map to current versus future work, or for a project health review, cleanup/resync review, launch-readiness review, roadmap reconciliation, or Codex execution prompt.
---

# Review Project and Choose the Next Step

Treat the review as a truth-reconciliation and routing task, not a brainstorming exercise.

## 1. Establish the evidence boundary

- State what sources are actually available: repository, branch/PR state, tests, plans, board cards, receipts, markers, deployments, screenshots, or user reports.
- Label facts, assumptions, and unknowns. Never convert a summary or percentage into proof.
- Prefer evidence in this order: live/runtime checks and deployment proof; tests and validation; diffs and commits; receipts and canonical plans; board state and summaries.
- Treat the owner repository as implementation truth. Treat coordination systems, boards, and ATLAS-like roots as routing and reconciliation surfaces unless their contract says otherwise.
- Preserve raw evidence. Add derived classifications rather than deleting or rewriting history.

## 2. Run the health check

Inspect only what the user authorized. Report:

- repository/branch/PR identity and cleanliness;
- divergence, stale worktrees, oversized PRs, or conflicting lanes;
- relevant validation results and what was not run;
- coordination drift between code, plans, cards, markers, and receipts;
- active blockers, protected/live seams, and missing human decisions.

If no repository context is available, say so and review only the supplied evidence.

## 3. Reconstruct the project state

Classify every material item into exactly one primary bucket:

1. **Proven complete** — implementation plus proportionate proof exists.
2. **Active gate** — already in progress or blocking the next milestone.
3. **Ready candidate** — bounded, dependency-satisfied, and safe to open.
4. **Future backlog** — valuable idea without current implementation admission.
5. **Blocked / decision required** — needs owner choice, credentials, live action, counsel, or external authority.
6. **Stale / duplicate / drift** — superseded, already covered, or inconsistent with canonical truth.

Keep feature ideas such as enemies, shops, items, or speculative systems in backlog unless evidence explicitly admits implementation. Do not inflate progress markers for ideation or card creation.

## 4. Rank work by constraint, not excitement

Apply this precedence:

1. Protect correctness, data, security, legal posture, and live systems.
2. Clear an existing merge/release stop point before opening fresh work.
3. Repair identity, generated truth, manifests, or coordination drift that makes later work unsafe.
4. Satisfy the nearest milestone gate with the smallest evidence-producing packet.
5. Remove recurring toil or ambiguity when it compounds across projects.
6. Polish and new capabilities only after upstream gates are honest.

Within a tier, prefer the item that:

- unlocks the most downstream work;
- has the clearest acceptance criteria and verification path;
- touches the fewest unrelated boundaries;
- preserves existing architecture and canonical ownership;
- creates reusable tests, automation, documentation, or governance.

Do not confuse urgency with importance or percent-complete with readiness.

## 5. Decide whether to open a packet

Open at most one primary execution packet per review unless the user explicitly asks for parallel lanes.

Admit a packet only when all are true:

- its owner and source of truth are known;
- upstream dependencies and current PR stop points are clear;
- allowed and unchanged paths can be stated;
- success and failure are observable;
- verification is available and proportionate;
- live/deploy/provider mutations are either excluded or explicitly authorized;
- the expected result changes project truth rather than merely producing another summary.

Otherwise choose a bounded read-only inventory, docs/contract freeze, reconciliation packet, or explicit stop.

Use this lifecycle when applicable:

`approval/readiness → execution → proof/reconciliation → marker or roadmap ratchet`

Ratchet progress only after the required receipt, tests, validation, and reconciliation exist. Hold at the gate when human, runtime, deploy, or external evidence is missing.

## 6. Produce the review

Lead with:

- **Done:** verified state or completed work.
- **Now:** the active gate or current review target.
- **Next:** the single recommended move.
- **Health check:** repo and evidence health, or an explicit statement that no repo context is loaded.

Then include only sections that add value:

- ranked remaining work;
- dependency or wave order;
- facts / assumptions / unknowns;
- risks and hard stops;
- reusable Rule, Pattern, Failure Mode, or Decision discoveries;
- marker update/table when markers are part of the supplied system.

Choose one recommendation and explain briefly why plausible alternatives lose.

## 7. Create an execution handoff when requested

Prefer a copy-paste-ready Codex prompt with:

- Objective
- Current verified state
- Scope and ownership boundary
- Plan
- Expected changed paths
- Expected unchanged paths
- Verification
- Documentation / receipts / board reconciliation
- Risks and hard stops
- Blocked / skipped reporting rules
- Acceptance criteria

For parallel work, split conflict-safe lanes into Wave 1 / Wave 2 and identify dependencies. Never add work to an oversized or already-integrating PR merely because it is open.

## Durable review rules

- **Rule — Proof before completion:** tests, diffs, deployments, receipts, and live checks outrank summaries.
- **Rule — Owner-repo truth:** coordination layers route work; owner repos own implementation truth.
- **Rule — Docs unlock code:** freeze contracts and handoffs before risky or cross-boundary implementation.
- **Rule — One honest next step:** select the smallest safe candidate that materially advances verified truth.
- **Pattern — Card to doctrine:** card → reviewed packet → diff → proof → completion review → roadmap update → reusable rule.
- **Pattern — Fast finish:** preflight → exact packet → implementation or reconciliation → validation → parity check → continue or stop.
- **Failure Mode — Summary-truth drift:** plans, boards, or markers claim more than code and evidence prove.
- **Failure Mode — Milestone flattening:** future ideas, active gates, and completed work are blended into one undifferentiated list.
- **Decision — Stop at the live seam:** do not cross deploy, provider, credential, legal, or production boundaries without explicit admission and evidence requirements.
