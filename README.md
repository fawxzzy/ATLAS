# ATLAS

ATLAS is the portable stack root: the filesystem contract above the stack's repos, not an application repo. The full stack description lives in [README-STACK.md](README-STACK.md); agent rules live in [AGENTS.md](AGENTS.md); the documentation map is [docs/index.md](docs/index.md).

## Playbook bootstrap ladder

When orienting in this repo with the Playbook CLI, use the canonical bootstrap ladder, in order:

1. `ai-context`
2. `ai-contract`
3. `context`

Then use `verify`, `plan`, `apply`, `verify` for the remediation loop. Command truth for this repo is recorded in [docs/contracts/command-truth.json](docs/contracts/command-truth.json); the command guide is [docs/commands/README.md](docs/commands/README.md).
