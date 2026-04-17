# ATLAS Continuity Harvest Backlog

This backlog turns saved roadmap drafts, PDFs, handoffs, and historic planning material into reusable continuity inputs without reopening discovery every session.

It is a root-side continuity slice. It is not permission to merge owner-repo truth into ATLAS root.

## Guardrails

- raw source artifacts stay raw evidence first
- do not promote everything automatically
- do not treat transcript residue as canonical memory
- do not duplicate child-repo truth in root
- promote only validated, durable decisions, tasks, principles, and evidence

## Outcome Target

For each saved planning artifact, ATLAS should be able to answer:

- what it is
- where it came from
- whether it is raw evidence or promoted truth
- what durable decisions or tasks it contributed
- what initiative, plan, knowledge, or receipt it maps to now

## Intake Pipeline

### Stage 1. Inventory

Build a manifest of saved planning artifacts grouped by type:

- roadmap drafts
- planning docs
- PDFs
- handoff notes
- old chat exports
- session artifacts
- proposal and review artifacts

Default output target:

- `data/imports/knowledge/continuity/harvest-manifest.json`

Minimum metadata per source:

- source path
- artifact type
- created or modified date when available
- related repo, initiative, or topic
- promotion status
- trust posture

### Stage 2. Evidence Capture

For each source, retain:

- raw file reference
- checksum when useful
- short source summary
- obvious relationship to existing initiatives or plans

### Stage 3. Structured Extraction

Extract only durable items such as:

- decisions
- open questions
- milestones
- named initiatives
- acceptance criteria
- policy or principle statements
- known traps and non-goals

### Stage 4. Promotion

Promote validated outputs into the correct lane:

- initiative json
- plan json
- knowledge docs
- receipts or reviews
- adoption matrix updates when appropriate

### Stage 5. Linkage

Each promoted item should link back to:

- source artifact refs
- related initiative refs
- related repo refs
- whether human review happened

## First Practical Slices

1. Create the continuity harvest manifest for saved planning artifacts already visible from ATLAS root.
2. Add a source classification rubric with `raw`, `structured`, and `promoted`.
3. Select the top ten highest-value saved artifacts for extraction.
4. Extract durable decisions and tasks from those ten artifacts.
5. Promote validated outputs into initiative, plan, knowledge, and receipt lanes.
6. Record unresolved questions in one tracked queue instead of leaving them in transcript residue.

## Acceptance Criteria

- old planning work is reusable without transcript-diving
- raw evidence remains distinguishable from promoted truth
- no duplicate owner-repo truth is created in root
- original ideas remain attributable and linked to current initiatives
- future sessions can bootstrap from structured artifacts instead of memory guesswork

## Good First Questions

- Is this artifact evidence, doctrine, plan, or residue?
- Does it belong in root memory, root knowledge, or an owner repo?
- Is there already a newer promoted version?
- Should this remain historical context only?
