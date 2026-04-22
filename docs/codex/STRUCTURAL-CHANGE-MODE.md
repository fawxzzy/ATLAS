# Structural Change Mode Bootstrap Prompt

This document is the Codex-facing bootstrap contract for the named Atlas session mode `structural-change-mode`.

Use it together with:

- `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- `docs/registry/STACK-REPO-INVENTORY.json`

## Purpose

Translate the rapid-loop escalation boundary into a named session opener that future AIs can execute consistently when the work stops being micro-change sized.

This document is the execution bootstrap layer for structural, cross-cutting, schema-related, or routing-heavy work.

## Named mode

- mode name: `structural-change-mode`
- primary opener: `Open structural change mode for <repo>.`

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

- operator text: `Open structural change mode for fawxzzy-fitness.`
- resolved repo id: `fitness`
- resolved repo path: `repos/fawxzzy-fitness`

If repo resolution is ambiguous, ask for clarification before starting the mode.

## Bootstrap reads

Before starting structural work, read these Atlas surfaces in order:

1. `stack.yaml`
2. `stack.lock.yaml`
3. `docs/registry/STACK-REPO-INVENTORY.json`
4. `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
5. `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
6. this prompt doc
7. only then the target repo docs or code

## Startup operating instructions

When `structural-change-mode` is active for a repo, Codex should:

- stop treating the task as a rapid-loop change
- identify the structural seam before editing
- clarify the likely blast radius across routes, components, schemas, shared chrome, or data contracts
- prefer a bounded implementation plan before patching
- choose validation based on the breadth of the change rather than affected-screen defaults
- call out when checkpoint or full-app sweeps are now justified
- preserve architecture unless the operator explicitly asks for a larger redesign

Do not:

- keep using minimal-patch assumptions when the work is plainly cross-cutting
- present affected-screen validation as sufficient when shared contracts are changing
- hide scope growth just to stay in a faster loop
- turn structural work into an unbounded rewrite without naming the impacted surfaces

## Default mode contract

| Field | Value |
| --- | --- |
| `localhost_assumption` | `running-if-useful` |
| `validation_mode` | `scope-based` |
| `patch_style` | `planned-bounded` |
| `sweep_posture` | `checkpoint-or-broader-as-needed` |
| `escalation_trigger` | `shared contracts`, `routing`, `schema`, or `cross-cutting UI behavior` |

## Expected first response shape

When the opener is recognized and repo resolution succeeds, the first response should report:

- repo recognized
- mode recognized
- why rapid-loop assumptions no longer fit
- suspected scope
- validation posture
- request for the first structural target or constraint

Preferred shape:

```text
repo recognized: <logical_id> -> <local_path>
mode recognized: structural-change-mode
rapid-loop status: exited
suspected scope: <shared surface or contract area>
validation posture: scope-based
request: tell me the structural target or the constraint to preserve
```

## Expected structural response shape

After each implementation step in this mode, report:

- files changed
- shared surfaces or contracts affected
- what to verify
- whether checkpoint or broader sweep coverage is now warranted
- whether the task should stay structural or split again

Preferred shape:

```text
files changed: <path list>
shared surfaces: <surface or contract list>
verify: <specific checks>
sweep posture: <checkpoint | broader> <reason>
mode follow-up: <stay structural | split into rapid-loop sized slices>
```

## Invocation examples

- `Open structural change mode for fawxzzy-fitness.`
- `Open structural change mode for fitness.`
- `Structural change mode for repos/fawxzzy-fitness.`
- `This is cross-cutting now. Open structural change mode for fawxzzy-fitness.`

## Rule

Named AI session modes must resolve to canonical Atlas docs, not ad hoc interpretation.

## Pattern

Separate knowledge docs from execution bootstrap prompts, then bind both through a lightweight alias registry.

## Failure Mode

A workflow doc with no named invocation contract is hard to reuse consistently across sessions and repos.
