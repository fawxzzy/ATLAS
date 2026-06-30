# Fast Iteration Loop Bootstrap Prompt

This document is the Codex-facing bootstrap contract for the named Atlas session mode `fast-iteration-loop`.

Use it together with:

- `docs/playbooks/RAPID-LOCALHOST-ITERATION-LOOP.md`
- `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`
- `docs/registry/STACK-REPO-INVENTORY.json`

## Purpose

Translate the reusable rapid-localhost workflow into a named session opener that future AIs can execute consistently.

This document is the execution bootstrap layer.

The workflow doc explains the system.

This prompt doc explains what Codex should do when the mode is invoked.

## Named mode

- mode name: `fast-iteration-loop`
- primary opener: `Open the fast iteration loop for <repo>.`

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

- operator text: `Open the fast iteration loop for fawxzzy-fitness.`
- resolved repo id: `fitness`
- resolved repo path: `repos/fawxzzy-fitness`

If repo resolution is ambiguous, ask for clarification before starting the mode.

## Bootstrap reads

Before acting on the first UI request, read these Atlas surfaces in order:

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

When `fast-iteration-loop` is active for a repo, Codex should:

- assume `localhost` or the emulator is already running unless the operator says otherwise
- reuse one maintained browser surface and one maintained local runtime for that repo lane unless the operator explicitly opens a comparison need
- accept one small, scoped change at a time
- make the minimal patch needed for the request
- preserve repo architecture and naming
- prefer affected-screen validation by default
- park the browser to `about:blank` or another neutral low-overhead surface when live preview is not actively needed
- reserve broader screenshot sweeps for checkpoints
- escalate when the request stops being rapid-loop sized

Do not:

- restart the dev server unless necessary
- open duplicate localhost tabs or duplicate servers for the same repo lane unless the comparison need is explicit
- widen scope because the local runtime makes bigger edits convenient
- run a full sweep after every micro-change
- pretend structural work is still a rapid-loop task

## Default mode contract

| Field | Value |
| --- | --- |
| `localhost_assumption` | `running` |
| `browser_surface_policy` | `one-maintained-surface` |
| `idle_browser_posture` | `park-to-blank` |
| `local_runtime_policy` | `reuse-single-healthy-instance` |
| `validation_mode` | `affected-screen` |
| `patch_style` | `minimal` |
| `sweep_posture` | `checkpoint-only` |
| `escalation_trigger` | `structural`, `cross-cutting`, `schema-related`, or `routing-heavy` change |

## Expected first response shape

When the opener is recognized and repo resolution succeeds, the first response should report:

- repo recognized
- mode recognized
- localhost assumption
- validation mode
- patch style
- prompt for the first small request

Preferred shape:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
repo recognized: <logical_id> -> <local_path>
mode recognized: fast-iteration-loop
localhost assumption: active
validation mode: affected-screen
patch style: minimal
request: send the first small change
```

## Expected per-patch response shape

After each patch in this mode, report:

- files changed
- screens affected
- what to visually verify
- whether a checkpoint sweep is warranted

Preferred shape:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
files changed: <path list>
screens affected: <screen list>
visual verify: <specific checks>
checkpoint sweep: <not needed | recommended> <reason>
```

## Invocation examples

- `Open the fast iteration loop for fawxzzy-fitness.`
- `Open the fast iteration loop for fitness.`
- `Start fast iteration loop for repos/fawxzzy-fitness.`
- `Rapid ui loop for fawxzzy-fitness. Assume localhost is already running.`

## Rule

Named AI session modes must resolve to canonical Atlas docs, not ad hoc interpretation.

## Pattern

Separate knowledge docs from execution bootstrap prompts, then bind both through a lightweight alias registry.

## Failure Mode

A workflow doc with no named invocation contract is hard to reuse consistently across sessions and repos.
