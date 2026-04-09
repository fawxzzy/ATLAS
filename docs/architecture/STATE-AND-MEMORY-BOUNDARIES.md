# State and Memory Boundaries

This document defines where mutable state may live and how future memory systems must interact with the stack.

## Core Rule

Code, doctrine, mutable state, and exports are separate classes. They must not collapse into one path.

## Path Ownership By State Class

| State class | Paths | Notes |
| --- | --- | --- |
| code | `repos/**`, `ops/**` | committed executable logic |
| doctrine | `docs/**`, repo-local doctrine docs | committed human-readable truth |
| retained mutable state | `runtime/**` | non-secret state that must survive a session |
| disposable mutable state | `tmp/**` | safe to delete |
| export state | `packages/**` | bundles, patches, snapshots, releases |
| durable non-secret data | `data/**` | imports, fixtures, export-like data |
| secrets | `secrets/**` | never part of default exports |

## What Must Not Happen

- repo roots must not become the default storage for mutable state
- exports must not be mixed into source trees
- secret material must not be mixed into doctrine or exports
- session memory must not exist only in a model context window

## Current Mutable State Contract

Today, retained state should land in:

- `runtime/codex`
- `runtime/devservers`
- `runtime/lifeline`
- `runtime/playbook`
- `runtime/receipts`
- `runtime/state`

Disposable state should land in:

- `tmp/logs`
- `tmp/captures`
- `tmp/previews`
- `tmp/scratch`

## Playbook Memory Boundary

Playbook may own repo-local memory and knowledge artifacts inside the repo that it governs.

That is acceptable when:

- the repo is the right scope for the memory
- the files are explicit
- the files are versioned or otherwise inspectable

Playbook should not silently become the stack-wide memory authority for all repos.

## Future CORTEX Memory Boundary

CORTEX may eventually own cross-repo memory and orchestration state, but only under these rules:

1. cross-repo state must live outside repo roots
2. the storage path must be explicit
3. the format must be inspectable
4. recommendations must be reconstructible from stored inputs
5. memory must support human review and reset

The likely future home is under `runtime/state/` and `runtime/receipts/`, not inside random repo folders.

## Codex Session Memory Boundary

Codex should treat memory as one of three things:

1. immediate conversational context
2. explicit file artifacts created during the task
3. repo-local or stack-level configuration already on disk

Only the second and third are durable. If something matters after the session ends, write it to the correct stack path.

## Safe Memory Handoff Pattern

Safe handoff uses artifacts such as:

- validation json reports
- audits
- architecture decisions
- export manifests
- repo audits
- structured migration notes

Unsafe handoff depends on:

- remembering implicit chat context only
- undocumented manual conventions
- hidden local caches that are required to reproduce decisions

## Manual Boundaries For Now

Keep these manual until the memory model is mature:

- deciding which stack receipts become durable knowledge
- promoting CORTEX observations into operational policy
- automatic replay of prior session intent across repos
- any automatic write-back from a memory engine into active repos

## Recommended Direction

Near term:

- keep stack truth in docs and manifests
- keep runtime truth in explicit runtime receipts
- keep repo truth in repo-local docs and config
- keep orchestration recommendations advisory

Later:

- let CORTEX read explicit receipts
- let CORTEX propose next tasks
- keep Codex as the executor that performs reviewed changes
