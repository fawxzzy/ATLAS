# ATLAS Retention And Memory Policy

This policy defines how ATLAS compacts stack context without treating chat state as durable truth and without treating the ATLAS root as a git repo.

## Goals

- reduce manual re-reading of stack doctrine and audit notes
- keep derived memory inspectable, source-backed, and resettable
- keep previews, receipts, and temp artifacts from growing without bound
- never let retention delete repo source, raw imports, or source-of-record docs

## Memory Sources

ATLAS may extract normalized memory only from explicit source files:

- `docs/**/*.md`
- `docs/knowledge/**/*.md`
- `docs/playbooks/**/*.md`
- repo-local audit docs under registered repo roots, such as `docs/repo-audit.md` and markdown files with `audit` in the filename

ATLAS memory extraction must not read chat transcripts as source-of-record truth.

## Memory Artifact Rules

Normalized memory artifacts live under:

- `runtime/cortex/catalog/memory/`

Each artifact must:

- record the ATLAS-relative source path
- record the source kind and repo id when applicable
- include an overview derived from the source text
- include normalized key points with source line numbers
- keep provenance back to the source file

ATLAS memory is extractive by default. It may normalize formatting and whitespace, but it must not invent facts that are not present in the source document.

## Retention Classes

### Canonical material

These are source-of-record paths and are never auto-deleted by memory compaction:

- `docs/**`
- repo source under `repos/**`
- durable imports under `data/imports/**`
- release artifacts under `packages/**`
- handoff receipts under `runtime/receipts/handoffs/**`

### Durable derived memory

These artifacts are derived, but they are still retained because they reduce repeated manual reading:

- latest memory artifacts in `runtime/cortex/catalog/memory/*.json`
- `runtime/cortex/catalog/memory/memory-catalog.latest.json`

ATLAS may archive duplicate or orphaned memory artifacts when a newer artifact or the source file already covers the same need.

### Operational receipts

ATLAS keeps live operational receipts under `runtime/receipts/**`.

Current compaction rule:

- timestamped event receipts may be archived once `latest.json` exists in the same receipt lane and the timestamped file is older than the live retention window

### Disposable artifacts

These paths are expected to be ephemeral:

- `tmp/previews/**`
- `tmp/scratch/**`

Current compaction rule:

- stale preview artifacts may be deleted after the preview retention window
- expired scratch files may be deleted after the temp retention window

## Current Windows-Friendly Retention Windows

- previews: 7 days live in `tmp/previews/`
- scratch temp files: 3 days live in `tmp/scratch/`
- timestamped event receipts with a sibling `latest.json`: 14 days live before archive

These windows are stack policy, not git policy.

## What ATLAS May Auto-Delete

- stale files under `tmp/previews/`
- expired files under `tmp/scratch/`

## What ATLAS May Archive

- timestamped event receipts when `latest.json` already preserves the current operational state
- duplicate memory artifacts for the same source doc
- orphaned memory artifacts whose source doc no longer exists

## What ATLAS Must Never Auto-Delete

- stack doctrine under `docs/**`
- repo source under `repos/**`
- raw imports under `data/imports/**`
- release and packaging outputs under `packages/**`
- handoff JSON under `runtime/receipts/handoffs/**`
- any file under `secrets/**`

## Inspectability Rules

Every compaction run must emit a retention report that shows:

- what was kept
- what was compacted
- what was archived
- what was skipped

Every memory extraction run must emit stable JSON artifacts so a human can trace a claim back to the source file.

## Repo Boundary Rule

Memory and retention are stack-owned, but commit and PR actions are repo-owned.

ATLAS may prepare commit and PR artifacts from a handoff, but the target repo must be the actual registered repo root that owns the changed files. ATLAS must never assume the ATLAS root is the git target.
