# Git Topology And Stack Registry Audit

Audit date: `2026-04-13`

Scope:

- stack registry entries in `stack.yaml`
- pinned components in `stack.lock.yaml`
- repo-like and excluded surfaces under `repos/`

## Summary

The lockfile pins the stack control repo plus eight child-repo components. The managed pinned set is now explicit, while known non-release surfaces are called out separately instead of being left to convention.

Two important topology facts remain true:

- Cortex is a root-owned subsystem under `runtime/cortex/**`, not a managed child repo
- Verta remains present under `repos/` as an untrusted excluded surface and must stay out of release sets

## Pinned Components

These components are intentionally pinned in `stack.lock.yaml`:

| Repo id | Path | Trust class | Release eligible |
| --- | --- | --- | --- |
| `stack` | `.` | `trusted` | `false` |
| `atlas` | `repos/fawxzzy-atlas` | `trusted` | `true` |
| `playbook` | `repos/fawxzzy-playbook` | `trusted` | `true` |
| `lifeline` | `repos/fawxzzy-lifeline` | `trusted` | `true` |
| `fitness` | `repos/fawxzzy-fitness` | `trusted` | `true` |
| `mazer` | `repos/fawxzzy-mazer` | `trusted` | `true` |
| `nat1-games` | `repos/Nat1-Games/nat1-games` | `trusted` | `false` |
| `playbook-demo` | `repos/playbook-demo/playbook-demo` | `trusted` | `false` |

## Registry Entries Not Pinned

These registry entries are intentionally not part of the pinned child-repo set:

| Repo id | Path | Reason |
| --- | --- | --- |
| `playbook-v1` | `repos/playbook-old/playbookv1` | Registry path is missing; legacy surface remains unresolved. |
| `mazer-unreal` | `repos/mazer-legacy-unreal/Mazer` | Registry path is missing; legacy surface remains unresolved. |

## Root-Owned Subsystems

These surfaces are owned at the stack root and are intentionally not modeled as child repos:

| Subsystem id | Path | Owner | Notes |
| --- | --- | --- | --- |
| `cortex` | `runtime/cortex` | `stack` | Active read-only coordination/runtime subsystem for catalogs, query state, and supervisor artifacts. |

## Adjacent Context Surfaces

These paths may exist as historical or adjacent context but are not active managed repo surfaces:

| Path | Current interpretation |
| --- | --- |
| `repos/cortex` | Historical framework snapshot adjacent to the active root-owned Cortex subsystem. |

## Excluded Untrusted Surfaces

These surfaces are explicit exclusions, not managed release candidates:

| Surface id | Path | Trust class | Release eligible | Reason |
| --- | --- | --- | --- | --- |
| `verta_core_checkout` | `repos/Verta-Core` | `untrusted` | `false` | Token-bearing checkout remains quarantined until scrub and rotation complete. |
| `verta_core_archive` | `repos/Verta-Core.zip` | `untrusted` | `false` | Token-bearing archive remains quarantined private evidence. |

## Unregistered Git Roots Under `repos/`

The following independent git roots exist under `repos/` but are not tracked by the current stack registry or lockfile:

| Path | Current interpretation |
| --- | --- |
| `repos/_stack` | Historical operator/workflow repo; still useful context, but not part of the pinned managed release set. |
| `repos/ZachariahRedfield` | Additional standalone git root; not part of the current managed stack contract. |

## Wrapper And Parent Surfaces

These top-level folders are wrappers or parents, not the actual pinned git roots:

| Parent path | Pinned child root |
| --- | --- |
| `repos/Nat1-Games` | `repos/Nat1-Games/nat1-games` |
| `repos/playbook-demo` | `repos/playbook-demo/playbook-demo` |

## Release Eligibility Rules

- only `trusted` pinned components may enter a release-eligible set
- excluded or `untrusted` surfaces must stay out of release sets
- adjacent surfaces such as `repos/cortex` may be audited, but they are not implied release members

## Follow-Up

- keep `stack.lock.yaml` refreshed when the pinned working set changes
- keep Cortex modeled as a root-owned subsystem unless it becomes a real independent child repo with a clean registry entry
- resolve or retire missing legacy registry entries
- keep Verta excluded until scrub and rotation are complete
- decide whether `repos/_stack` and `repos/ZachariahRedfield` should stay unregistered or be formally classified later
