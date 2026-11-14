# Playbook consumer integration contract (ATLAS side)

ATLAS consumes Playbook; it does not own it.

- Owner: the Playbook product repo `fawxzzy/playbook` (child repo under `repos/playbook`, an independent git root).
- Runtime: the read-only mirror `runtime/playbook-cli`, ignored by this repo's `.gitignore`. Nothing in it is vendored into ATLAS.
- Commands: bootstrap ladder `ai-context`, `ai-contract`, `context`; remediation loop `verify`, `plan`, `apply`, `verify`. See [commands/README.md](commands/README.md) and [contracts/command-truth.json](contracts/command-truth.json).
- Authority: a Playbook result is source proof only. It does not authorize execution, and it does not prove deployment, adoption, or acceptance.
- Learning and promotion (`improve`, `memory`, `patterns promote`) are propose-only; human review precedes any promotion.
- Rule: federate repo truth, do not duplicate it. Playbook command semantics stay in `fawxzzy/playbook`; relationship notes live in [architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md](architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md).
