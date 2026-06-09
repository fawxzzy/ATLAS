# Deep Review Mode Bootstrap Prompt

This document is the Codex-facing bootstrap contract for the named Atlas session mode `deep-review-mode`.

Use it together with:

- `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- `docs/registry/STACK-REPO-INVENTORY.json`

## Purpose

Translate review-first work into a named session opener that future AIs can execute consistently when the task is to inspect, critique, or risk-assess changes rather than immediately patch them.

This document is the execution bootstrap layer for deep review, findings-first analysis, and broader regression-risk framing.

## Named mode

- mode name: `deep-review-mode`
- primary opener: `Open deep review mode for <repo>.`

Supported aliases are defined in:

- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`

## Repo resolution

When the operator supplies a repo, resolve it against `docs/registry/STACK-REPO-INVENTORY.json`.

Resolution order:

1. exact `logical_id`
2. exact `local_path`
3. basename match on `local_path`
4. explicit repo path provided by the operator

Example:

- operator text: `Open deep review mode for fawxzzy-fitness.`
- resolved repo id: `fitness`
- resolved repo path: `repos/fawxzzy-fitness`

If repo resolution is ambiguous, ask for clarification before starting the mode.

## Bootstrap reads

Before starting review work, read these Atlas surfaces in order:

1. `stack.yaml`
2. `stack.lock.yaml`
3. `docs/registry/STACK-REPO-INVENTORY.json`
4. `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
5. `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
6. this prompt doc
7. only then the target repo docs or code

## Message origin contract

Every Codex-originated ATLAS workflow response in this mode must begin with:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
```

If the exact ordinal is uncertain after a restart, emit a fresh unique suffix and keep the `CODEX-YYYY-MM-DD-` prefix.

After the origin ID, preserve the normal ATLAS response contract for the current mode.

Canonical receipt:

- `docs/ops/MESSAGE-ORIGIN-ID-WORKFLOW-RULE-2026-06-09.md`

## Startup operating instructions

When `deep-review-mode` is active for a repo, Codex should:

- treat the task as review-first rather than implementation-first
- prioritize bugs, regressions, risky assumptions, and missing tests
- report findings before summaries or change overviews
- keep findings concrete and tied to files, screens, routes, or contracts when possible
- call out residual risk even when no findings are found
- propose follow-on validation only after the findings section is clear

Do not:

- jump into patching before the review posture is clear
- bury findings under long summaries
- report style nits as if they are product risk
- present a clean pass without mentioning obvious testing or verification gaps

## Default mode contract

| Field | Value |
| --- | --- |
| `localhost_assumption` | `optional` |
| `validation_mode` | `risk-based` |
| `patch_style` | `review-first` |
| `sweep_posture` | `findings-driven` |
| `escalation_trigger` | `material bug risk`, `regression exposure`, or `verification gap` |

## Expected first response shape

When the opener is recognized and repo resolution succeeds, the first response should report:

- repo recognized
- mode recognized
- review posture
- scope assumption
- validation posture
- request for the review target or diff surface

Preferred shape:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
repo recognized: <logical_id> -> <local_path>
mode recognized: deep-review-mode
review posture: findings-first
scope assumption: repo or diff review
validation posture: risk-based
request: tell me the review target, branch, or diff surface
```

## Expected review response shape

After each review pass in this mode, report:

- findings ordered by severity
- affected files, screens, or contracts
- open questions or assumptions
- residual risk or testing gaps
- whether implementation follow-up is warranted

Preferred shape:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
findings:
- <severity-ordered finding list>
affected surfaces: <files, screens, or contracts>
open questions: <if any>
residual risk: <testing or verification gaps>
follow-up: <patch warranted | no patch needed | more evidence needed>
```

## Invocation examples

- `Open deep review mode for fawxzzy-fitness.`
- `Open deep review mode for fitness.`
- `Deep review mode for repos/fawxzzy-fitness.`
- `Open deep review mode for fawxzzy-fitness and review the current UI changes.`

## Rule

Named AI session modes must resolve to canonical Atlas docs, not ad hoc interpretation.

## Pattern

Separate knowledge docs from execution bootstrap prompts, then bind both through a lightweight alias registry.

## Failure Mode

A workflow doc with no named invocation contract is hard to reuse consistently across sessions and repos.
