# Playbook commands used from ATLAS

ATLAS does not define its own CLI. This page lists how the Playbook CLI is used against this repo. Command lifecycle, role, and discoverability classification is owned by the Playbook product repo (`fawxzzy/playbook`); the machine-readable record for this repo is [../contracts/command-truth.json](../contracts/command-truth.json).

The Playbook runtime used for ATLAS checks is the read-only mirror at `runtime/playbook-cli` (untracked; `runtime/**` is ignored by `.gitignore`).

| Command | Use here |
|---|---|
| `ai-context` | Bootstrap ladder step 1 |
| `ai-contract` | Bootstrap ladder step 2 |
| `context` | Bootstrap ladder step 3 |
| `index` | Build the repository intelligence index |
| `verify` | Policy and rule verification |
| `doctor` | Repo health and documentation audit |
| `plan` / `apply` | Remediation loop (`verify`, `plan`, `apply`, `verify`) |

Playbook output is source proof only. It does not grant execution authority or prove deployment, adoption, or acceptance.
