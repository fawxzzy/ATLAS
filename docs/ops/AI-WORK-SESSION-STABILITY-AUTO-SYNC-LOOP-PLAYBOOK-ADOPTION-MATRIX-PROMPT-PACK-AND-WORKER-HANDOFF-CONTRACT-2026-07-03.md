# AI Work Session Stability Auto-Sync Loop Playbook Adoption Matrix Prompt-Pack And Worker Handoff Contract

- CODEX-MSG-ID: `CODEX-2026-07-03-AI-WORK-SESSION-STABILITY-PLAYBOOK-ADOPTION-MATRIX-PROMPT-PACK`
- Date: `2026-07-03`
- Mode: `docs-only prompt-pack and worker handoff contract`
- Scope: `freeze the future read-only Playbook adoption matrix worker contract without implementing it`
- Control-plane checkpoint: `main@29e56525`
- Worker implementation: `not included`
- Owner-repo mutation: `none`
- Platform mutation: `none`
- Protected-surface mutation: `none`
- Marker movement: `none`

## Objective

Freeze the implementation handoff for one future read-only Playbook adoption matrix worker that answers:

`Is Playbook actually surfaced, consumed, referenced, or enforced by ATLAS/Codex workflows and active owner-repo governance surfaces, or is it merely documented?`

Expected future files:

- `ops/atlas/playbook_adoption_matrix.py`
- `tests/test_atlas_playbook_adoption_matrix.py`

Naming decision: use `playbook_adoption_matrix.py` rather than an `ai_work_session_*` prefix because the worker's subject is the stack-wide Playbook adoption matrix. The AI Work Session lane owns this control-plane handoff, but the future helper should stay reusable by Cortex, Playbook, and root-governance readers.

## Required CLI Flags

The future worker must support:

- `--json`
- `--scope root|owner|platform|research`
- `--owner <name>` as read-only owner-lane classification input only
- `--strict`
- `--output <root-relative-path>`

Default behavior:

- read-only inspection
- no writes unless `--output` is provided
- deterministic stdout summary plus JSON when `--json` is supplied
- fail closed when required local truth cannot be read
- no network or platform calls by default

## Source Surfaces

The future worker must inspect Playbook source surfaces, including:

- `docs/PLAYBOOK_NOTES.md`
- Playbook-related docs under `docs/`
- Playbook continuity manifests under `docs/memory/initiatives/`
- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/standards/WORKER-ORCHESTRATION.md`
- current AI Work Session receipts, manifests, and Book mirrors
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`

It must also inspect consumer or adoption surfaces, including:

- Codex prompt and packet patterns in receipts
- ATLAS Book current-state and restart surfaces
- marker selector and routing surfaces
- continuity manifests
- QA/release workflows only when they reference Playbook doctrine
- owner-repo adoption references from stack inventory metadata, read-only only

## Adoption Signal Model

The future worker must distinguish:

- `documented_doctrine`: Playbook exists as doctrine or notes only
- `referenced_doctrine`: Playbook is cited by a receipt, prompt, policy, or Book surface
- `consumed_doctrine`: a workflow reads or projects Playbook truth into a decision
- `enforced_doctrine`: a test, validator, selector, or command gates behavior on Playbook truth
- `stale_doctrine`: cited Playbook truth contradicts current source or routing truth
- `missing_adoption`: a relevant surface has no Playbook adoption signal
- `owner_lane_advisory_adoption`: owner repo evidence exists but remains read-only/advisory to root
- `cortex_substrate_candidate`: a reusable rule, pattern, failure mode, prompt-governance contract, handoff example, or curated-data boundary is fit for future Cortex consumption

The worker must not promote `documented_doctrine` to `consumed_doctrine` merely because the same string appears in ATLAS docs.

## JSON Output Fields

The future worker must emit one object with these top-level fields in deterministic order:

- `schema_version`
- `status`
- `root`
- `branch`
- `head`
- `parity`
- `playbook_sources`
- `adoption_surfaces`
- `consumer_matrix`
- `non_consumers`
- `doctrine_signals`
- `pattern_signals`
- `failure_mode_signals`
- `cortex_substrate_candidates`
- `owner_lane_adoption`
- `gaps`
- `blockers`
- `warnings`
- `required_followups`
- `safe_to_continue`

The schema version is `atlas.playbook_adoption_matrix.v1`.

## Status Classes

- `ok`: Playbook adoption can be classified from available read-only surfaces and no blocking contradiction exists.
- `advisory_gap`: adoption is incomplete, source-only, stale, or missing, but root can continue safely.
- `blocker`: authoritative truth is unavailable, contradictory, unsafe to classify, or would require mutation.
- `internal_error`: unexpected runtime failure.

## Exit-Code Policy

Default mode:

- `0` for `ok`
- `0` for `advisory_gap`
- `2` for `blocker`
- `3` for `internal_error`

Strict mode:

- `0` for `ok`
- `1` for `advisory_gap`
- `2` for `blocker`
- `3` for `internal_error`

## Allowed Read-Only Checks

The future worker may read:

- root branch, HEAD, upstream parity, staged names, unstaged names, and untracked names
- Playbook source surfaces under `docs/`
- `docs/ops/PLAYBOOK-ADOPTION-MATRIX.md`
- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/atlas-book/01-current-state.md`
- `docs/atlas-book/02-lanes-and-markers.md`
- `docs/atlas-book/05-receipt-index.md`
- `docs/atlas-book/11-system-map-graph.md`
- `docs/atlas-book/12-restart-and-handoff-guide.md`
- `docs/atlas-book/13-vision-and-endgames.md`
- continuity manifests under `docs/memory/initiatives/`
- latest stack validation receipt under `runtime/receipts/validation/`
- marker selector output
- continuity health output
- owner repo branch/status/HEAD and selected exported adoption files only when explicitly requested as read-only status

## Forbidden Mutation Behavior

The future worker may not:

- mutate files by default
- edit Playbook doctrine
- edit ATLAS Book, receipts, manifests, selector, tests, or code
- mutate owner repos
- mutate Supabase, Vercel, BrowserStack, GitHub secrets, or deployment surfaces
- stage, commit, push, fetch, merge, or change branches
- edit PR bodies
- deploy or publish
- generate receipts
- move markers
- write runtime latest outputs by default
- clean residue
- touch `archive/`, `.playwright-mcp/`, `.vercel/`, `secrets/`, `.env`, or `.env*`
- treat owner-lane evidence as root-owned proof
- treat documentation-only doctrine as enforced adoption

## Protected Output-Path Policy

`--output` may write only to a root-relative, non-protected path. Absolute paths, paths escaping the root, and paths under protected prefixes must return `blocker` without writing.

Protected prefixes:

- `archive/`
- `.playwright-mcp/`
- `.vercel/`
- `secrets/`
- `.env`
- `.env*`

## Stop Conditions

The future worker must return `blocker` when:

- root branch, HEAD, or parity cannot be read
- Playbook source surfaces cannot be classified safely
- marker selector output cannot be read
- continuity health cannot be read
- stack validation has `critical` or `error` for a readiness claim
- source truth and consumer truth contradict in a way that would change adoption classification
- owner-lane evidence is required but was not explicitly requested read-only
- owner or platform mutation would be required to answer honestly
- protected proof, PR mutation, deploy, or publication would be required
- the requested output path is absolute, outside the root, or protected

## Proof Matrix

The future worker packet must later prove:

1. clean root Playbook source scan returns `ok`
2. source-only doctrine is classified as `documented_doctrine`, not consumed or enforced
3. receipt reference is classified as referenced or consumed according to context
4. selector or manifest reference is classified as operational adoption
5. missing adoption is classified as `advisory_gap`
6. strict mode returns nonzero on `advisory_gap`
7. blocker state returns nonzero
8. protected output path is rejected
9. absolute output path is rejected
10. deterministic JSON field ordering holds
11. owner scope remains read-only and advisory
12. Cortex substrate candidate extraction classifies reusable rules, patterns, failure modes, prompt-governance surfaces, handoff examples, and curated-data boundaries without mutating them

## Marker Decision

No marker moves from this prompt-pack.

`AI Work Session Stability & Auto-Sync Loop` remains `55%`.

Movement to `70%` requires:

- Playbook adoption matrix implementation
- direct tests
- clean validation
- preserved read-only contract
- reconciliation receipt proving the adoption-matrix threshold
- restart surfaces updated

## Exact Next Package

`AI Work Session Stability & Auto-Sync Loop Playbook adoption matrix implementation-readiness closeout and worker-routing`

Why:

- the worker objective is now frozen
- the future file paths are now frozen
- the CLI contract, JSON contract, status classes, exit-code policy, read-only/no-mutation guard, Playbook source and consumer surfaces, adoption signal model, Cortex-substrate relevance model, protected output-path policy, proof matrix, and stop conditions are now frozen
- the next honest docs-only step is to decide whether implementation may be routed to the exact future files without widening into mutation or marker movement

## Rule

`Adoption Matrix Before Adoption Claims`

Do not claim Playbook is consumed or enforced merely because it is documented. Consumption and enforcement require a concrete workflow, selector, validator, test, or owner-visible adoption surface.

## Pattern

admission -> prompt-pack and worker handoff contract -> implementation-readiness closeout and worker-routing -> bounded read-only worker landing -> reconciliation receipt and marker decision

## Failure Mode

`Doctrine Echo Inflation`

The lane fails if repeated documentation references are counted as operational adoption. The future worker must separate source doctrine, references, consumers, enforcement, stale doctrine, missing adoption, owner-lane advisory adoption, and Cortex-substrate candidates.
