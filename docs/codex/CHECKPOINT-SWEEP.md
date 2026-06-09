# Checkpoint Sweep Bootstrap Prompt

This document is the Codex-facing bootstrap contract for the named Atlas session mode `checkpoint-sweep`.

Use it together with:

- `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- `docs/registry/STACK-REPO-INVENTORY.json`

## Purpose

Translate checkpoint-mode validation from the rapid-localhost workflow into a named session opener that future AIs can execute consistently.

This document is the execution bootstrap layer for a broader validation pass after one or more rapid-loop edits.

## Named mode

- mode name: `checkpoint-sweep`
- primary opener: `Open checkpoint sweep mode for <repo>.`

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

- operator text: `Open checkpoint sweep mode for fawxzzy-fitness.`
- resolved repo id: `fitness`
- resolved repo path: `repos/fawxzzy-fitness`

If repo resolution is ambiguous, ask for clarification before starting the mode.

## Bootstrap reads

Before starting the sweep, read these Atlas surfaces in order:

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

When `checkpoint-sweep` is active for a repo, Codex should:

- assume `localhost` or the emulator is still available unless the operator says otherwise
- treat the task as a checkpoint validation pass rather than a micro-change loop
- start from the smallest sweep that answers the checkpoint question
- prefer Level 2 related-flow sweep first
- use Level 3 full-app sweep only when the checkpoint or operator request warrants it
- avoid opportunistic product edits while validating
- report what was checked, what still needs eyes, and whether the checkpoint is satisfied

Do not:

- fall back into one-change-at-a-time patch mode unless the operator redirects
- run a full-app sweep by reflex when a related-flow sweep is enough
- make new UI edits just because a sweep exposed optional polish ideas
- blur validation work with structural refactor work

## Default mode contract

| Field | Value |
| --- | --- |
| `localhost_assumption` | `running` |
| `validation_mode` | `related-flow` |
| `patch_style` | `none-by-default` |
| `sweep_posture` | `checkpoint` |
| `escalation_trigger` | `full-app impact is plausible`, `operator asks for broader confidence`, or `related-flow sweep is insufficient` |

## Expected first response shape

When the opener is recognized and repo resolution succeeds, the first response should report:

- repo recognized
- mode recognized
- localhost assumption
- validation mode
- sweep posture
- request for the checkpoint target or changed area

Preferred shape:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
repo recognized: <logical_id> -> <local_path>
mode recognized: checkpoint-sweep
localhost assumption: active
validation mode: related-flow
sweep posture: checkpoint
request: tell me the changed area or the checkpoint you want covered
```

## Expected checkpoint response shape

After each checkpoint pass in this mode, report:

- screens or flows checked
- sweep level used
- what to visually verify
- whether the checkpoint is satisfied
- whether a wider sweep is warranted

Preferred shape:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
screens checked: <screen or flow list>
sweep level: <Level 2 | Level 3>
visual verify: <specific checks>
checkpoint status: <satisfied | follow-up needed>
wider sweep: <not needed | recommended> <reason>
```

## Invocation examples

- `Open checkpoint sweep mode for fawxzzy-fitness.`
- `Open checkpoint sweep mode for fitness.`
- `Checkpoint sweep for repos/fawxzzy-fitness.`
- `Start checkpoint sweep for fawxzzy-fitness after the current UI batch.`

## Rule

Named AI session modes must resolve to canonical Atlas docs, not ad hoc interpretation.

## Pattern

Separate knowledge docs from execution bootstrap prompts, then bind both through a lightweight alias registry.

## Failure Mode

A workflow doc with no named invocation contract is hard to reuse consistently across sessions and repos.
