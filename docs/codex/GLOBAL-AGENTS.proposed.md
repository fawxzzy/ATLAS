# Proposed `~/.codex/AGENTS.md` For ATLAS-Style Stacks

This is a proposed user-level AGENTS file for future use. It is not active automatically.

## Purpose

Provide default behavior for Codex sessions that work across stack roots like ATLAS without hardcoding one machine path.

## Proposed Contents

```md
# Global Codex Rules

Scope
- Applies when no nearer `AGENTS.md` overrides it.
- Prefer the nearest project or stack `AGENTS.md` when present.

Discovery
- If the current working directory contains `stack.yaml`, treat it as a stack root.
- If the current working directory is inside a git repo that contains `AGENTS.md`, use the repo-local rules.

Path Discipline
- Prefer relative paths in committed docs, config, and scripts.
- Do not commit machine-specific absolute paths unless explicitly required and labeled local-only.

State Discipline
- Keep runtime state out of repo roots when the stack exposes `runtime/`.
- Keep disposable logs and captures under `tmp/` when the stack exposes `tmp/`.
- Keep secrets out of exports and out of documentation examples.

Routing
- Root stack sessions should focus on stack-wide files, standards, manifests, and cross-repo coordination.
- Single-repo implementation work should happen inside the target repo root.

Exports
- Default source exports should exclude `secrets/`, `runtime/`, `tmp/`, `.env*`, build outputs, and dependency folders.
```

## Adoption Notes

- Keep this global file generic.
- Put stack-specific rules in the stack root `AGENTS.md`.
- Put repo-specific rules in repo-local `AGENTS.md`.

## Prompt Framing Update

If this proposal is reused as prompt scaffolding for an ATLAS-style stack, do not describe the global index or awareness layer as missing.

Use this framing instead:

- `Global Index Layer is partially implemented as registry + descriptors + observations + snapshot + attention + working memory + Awareness API. The missing layer is initiative management, durable extension lifecycle, and governed action progression.`
- `Awareness -> attention -> initiative -> governed action -> memory refinement.`
- `Not everything knows everything. Nothing meaningful stays dark.`
