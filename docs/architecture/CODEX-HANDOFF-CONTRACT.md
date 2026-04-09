# Codex Handoff Contract

This document defines the ATLAS-owned handoff contract for structured Codex final output.

## Purpose

The contract exists so ATLAS can consume Codex task results without scraping chat transcripts, terminal output, or UI text.

Current design rules:

- ATLAS owns the contract shape and schema under `ops/codex/schemas/`.
- Handoff artifacts are explicit JSON files.
- Handoff artifacts are stored under `runtime/receipts/handoffs/`.
- The preferred capture mode is direct Codex final-output capture with schema-shaped JSON.
- Consumers derive commit and PR text from the handoff JSON, not from chat text.
- Adapters may change how Codex is launched, but they may not change the ATLAS handoff shape.

## Ownership Boundary

ATLAS owns:

- the schema file at `ops/codex/schemas/change_handoff.schema.json`
- the wrapper that assigns the output file path
- the validator that checks both the schema and the handoff payload
- the helper scripts that turn the handoff into commit and PR text

Codex owns:

- generating the final structured payload for the task
- populating the requested fields with task-specific content

Git hosting and repository policy still own:

- whether a commit is permitted in the current checkout
- whether a branch can be pushed
- whether a PR can be opened or merged

## Artifact Location

ATLAS stores each handoff under:

- `runtime/receipts/handoffs/<task>-<timestamp>.handoff.json`

Derived helper outputs may live beside the handoff, for example:

- `runtime/receipts/handoffs/<task>-<timestamp>.commit-message.txt`
- `runtime/receipts/handoffs/<task>-<timestamp>.pr.md`

These are runtime artifacts. They are intentionally outside repo roots and outside default exports.

## Capture Modes

### Preferred mode

Preferred mode is direct final-output capture into a JSON file while asking Codex to comply with the ATLAS schema.

Required properties of the launch flow:

- the wrapper chooses the handoff file path before Codex starts
- Codex writes the final result to that file directly
- the result is JSON, not markdown
- the result is validated against the ATLAS schema after the run

The exact CLI flag names can vary by Codex build. ATLAS does not standardize vendor flag names. It standardizes only the file contract and validation step.

### Acceptable fallback

If a Codex build cannot enforce the schema natively, the wrapper may still use direct final-output capture to a file, with the task instructions requiring JSON that matches the ATLAS schema.

This is still acceptable only when:

- the file is produced as Codex final output intentionally
- ATLAS reads only that final-output file
- ATLAS validates the JSON after capture

This fallback still does not permit transcript scraping.

## Contract Version

Current contract version:

- `atlas.codex.handoff.v1`

## Required Fields

The current schema requires these top-level fields:

| Field | Type | Notes |
| --- | --- | --- |
| `contract_version` | string | Must be `atlas.codex.handoff.v1` |
| `handoff_id` | string | Unique handoff identifier |
| `generated_at` | string | UTC ISO 8601 timestamp |
| `producer` | object | Capture metadata for the producing adapter |
| `task_name` | string | Human-readable task label |
| `workspace_root` | string | ATLAS-relative workspace root |
| `summary` | string | High-level change summary |
| `changed_files` | array | Structured changed-file list |
| `validation` | object | Validation status and commands |
| `commit_title` | string | Single-line git commit title |
| `commit_body` | string | Multi-line git commit body |
| `pr_title` | string | Single-line PR title |
| `pr_body` | string | Markdown PR body |

Optional top-level fields include:

- `scope_paths`
- `repo_ids`
- `mutation_mode`

## Structured Objects

### `producer`

Required fields:

- `kind`
- `name`
- `capture_mode`

Current `capture_mode` values:

- `schema_json`
- `explicit_json_file`

### `changed_files`

Each entry is an object with:

- `path`
- `summary`
- `status`

`path` should remain ATLAS-relative when the task was run from the ATLAS root.

### `validation`

Required fields:

- `status`
- `summary`
- `commands`

Each command entry records:

- `command`
- `status`

## Consumer Flow

ATLAS consumers should treat the handoff JSON as the single structured handoff surface.

Current consumers:

1. `ops/codex/commit_from_handoff.ps1`
2. `ops/codex/prepare_pr_from_handoff.ps1`

Consumer rules:

- validate first
- preview first
- execute git mutation only when explicitly requested
- keep derived text files outside repo roots unless a human deliberately moves them

## Manual Boundaries

The following steps can still require manual action:

- choosing the exact Codex CLI flags that map final output into the handoff file
- approving git access when `.git` operations are sandboxed by the environment
- reviewing staged content before commit
- pushing branches to remotes
- opening or submitting the PR in a protected repository

Protected branches, signed-commit requirements, token prompts, and hosted PR creation remain outside this contract.

## Minimal Example

```json
{
  "contract_version": "atlas.codex.handoff.v1",
  "handoff_id": "handoff-20260409T150000Z-example",
  "generated_at": "2026-04-09T15:00:00Z",
  "producer": {
    "kind": "codex",
    "name": "codex-final-output",
    "capture_mode": "schema_json"
  },
  "task_name": "atlas-codex-handoff",
  "workspace_root": ".",
  "scope_paths": [
    "docs/architecture",
    "docs/ops",
    "ops/codex"
  ],
  "repo_ids": [
    "stack"
  ],
  "mutation_mode": "stack_only",
  "summary": "Added an ATLAS-owned structured handoff flow for commit and PR preparation.",
  "changed_files": [
    {
      "path": "docs/architecture/CODEX-HANDOFF-CONTRACT.md",
      "summary": "Documented the handoff contract and ownership boundary.",
      "status": "added"
    },
    {
      "path": "ops/codex/commit_from_handoff.ps1",
      "summary": "Prepared preview-first commit message generation from handoff JSON.",
      "status": "added"
    }
  ],
  "validation": {
    "status": "passed",
    "summary": "Schema and synthetic handoff validation passed.",
    "commands": [
      {
        "command": "python .\\ops\\codex\\validate_handoff.py --schema-file .\\ops\\codex\\schemas\\change_handoff.schema.json",
        "status": "passed"
      },
      {
        "command": "python .\\ops\\codex\\validate_handoff.py --handoff-file .\\tmp\\scratch\\handoff.synthetic.json",
        "status": "passed"
      }
    ]
  },
  "commit_title": "ops: add Codex handoff contract",
  "commit_body": "Add an ATLAS-owned JSON handoff contract for Codex final output.\n\nInclude validation and helper scripts for preview-first commit and PR preparation.",
  "pr_title": "Add ATLAS Codex handoff flow",
  "pr_body": "## Summary\n- add an ATLAS-owned JSON handoff contract for Codex final output\n- add preview-first scripts for commit and PR preparation\n- validate the schema and a synthetic handoff example\n\n## Validation\n- python .\\ops\\codex\\validate_handoff.py --schema-file .\\ops\\codex\\schemas\\change_handoff.schema.json\n- python .\\ops\\codex\\validate_handoff.py --handoff-file .\\tmp\\scratch\\handoff.synthetic.json"
}
```

## Source Of Truth

The executable source of truth is:

- `ops/codex/schemas/change_handoff.schema.json`

This document is the human-readable contract.
