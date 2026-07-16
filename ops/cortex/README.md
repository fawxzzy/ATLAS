# Cortex Shadow-Agent Surface

This directory remains a root-owned Cortex consumer surface.

Contract-first philosophy:

- ATLAS and Playbook govern repetition-family truth, proof expectations, fallbacks, owner boundaries, and non-claim boundaries.
- Cortex consumes exported contracts from those truth surfaces.
- Cortex must not invent its own readiness model or absorb governance, receipt, product, or enforcement truth.
- Cortex remains inspection-oriented here; scaffold presence does not imply workflow authority or production readiness.

Local scaffold doctrine:

- Rule: No Agent Without Boundary
- Pattern: Shadow Before Authority
- Failure Mode: Scaffold Masquerading as Readiness

Shadow-agent distinction:

- `shadow-only`: the agent may load a governed contract and produce a local, inspectable summary or draft without authority.
- `blocked`: the family is explicitly non-runnable because it depends on human judgment, approval gates, or unresolved external/session defects.

Current files:

- `ops/cortex/shadow_agent_registry.py`: typed contract loader, admissibility gate, and summary surface for the shadow-agent registry.
- `ops/cortex/operator_surface.py`: existing Cortex operator surface that now projects both the shadow-agent registry and the current shadow-consumption artifacts.
- `ops/cortex/shadow_validation_summary.py`: bounded consumer for the `validation-summary-shadow` contract that emits a local no-authority proof artifact.
- `ops/cortex/shadow_marker_checkpoint.py`: bounded consumer for the `marker-checkpoint-shadow` contract that emits a local no-ratchet proof artifact.
- `ops/cortex/shadow_receipt_doctrine_draft.py`: bounded consumer for the `receipt-doctrine-draft-shadow` contract that emits a local draft-only no-admission proof artifact.
- `runtime/cortex/shadow-agent-registry.seed.v1.json`: governed seed registry derived from ATLAS receipts and doctrine.
- `schemas/atlas.cortex.shadow-agent-registry.v1.json`: shape contract for the seed registry.

Source-of-truth boundary:

- canonical admission truth lives in `docs/ops/AI-REPETITION-TO-AUTOMATION-PIPELINE-AUTOMATION-CANDIDATE-THRESHOLD-PASS-1-2026-06-01.md`
- canonical Cortex-consumption truth lives in `docs/ops/PLAYBOOK-EVERYWHERE-CORTEX-INTERFACE-CONTRACT-FIRST-AGENT-SHADOWING-PASS-1-2026-06-01.md`

No agent without boundary:

- an agent must not run unless its trigger family, stable inputs, proof artifact, fallback, and owner boundary are explicit
- new agents should shadow before authority
- prompt-shaped agent behavior is drift, not a contract
- blocked or non-shadow admissibility states must fail at the registry gate rather than being inferred downstream

Creation OS advisory read model:

- `creation_os_advisory_read_model.py` reads the pinned Atlas and Playbook inputs as exact Git blobs and builds only the dedicated Creation OS catalog, query projection, and execution receipt.
- The projection contains exactly six Playbook review candidates and one separately deferred Atlas product Decision. It never projects promoted knowledge or Decision-as-candidate data.
- Missing evidence is `unknown`, a changed pinned revision is `stale`, and duplicate, hash, kind, destination, disposition, Decision-admission, or doctrine drift is `conflict`. Any such state blocks before writes.
- Cortex authority is limited to read and advisory synthesis, routing, and retrieval. Policy, doctrine, scheduling, execution, deployment, approval, board, repository mutation, promotion, and automatic selection remain false.
- Write and byte-stability check:

  ```text
  python ops/cortex/creation_os_advisory_read_model.py --write --atlas-repo <atlas-worktree> --playbook-repo <playbook-repo>
  python ops/cortex/creation_os_advisory_read_model.py --check --atlas-repo <atlas-worktree> --playbook-repo <playbook-repo>
  ```
