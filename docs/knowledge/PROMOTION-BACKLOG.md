# Promotion Backlog

This backlog ranks current knowledge archives for safe `derived_only` promotion.

Ranking signals:

- `promotion_allowed`
- `safe_for_indexing`
- secrets risk
- privacy posture
- user relevance to ATLAS stack topics

Current policy:

- raw evidence stays in `data/imports/knowledge/`
- promotion docs are the durable truth for derived knowledge
- `metadata_only` archives stay metadata-only
- `derived_only` promotions must stay policy-safe and human-authored
- Verta remains quarantined and unpromoted
- reviewed derivative notes may summarize selected Verta historical sources without changing archive trust posture or archive promotion status

## Current Ranking

1. `personal--atlas-stack-git-versioning-openai-integration-research`
2. `personal--atlas-universal-extensible-ai-powered-os-ecosystem-inspired-by-linux-and-git`
3. `personal--atlas-storage-system-rule-based-compression-deduplication-graph`
4. `personal--atlas-universal-interoperable-technology-stack`
5. `personal--college-fullstack-ai-archive`
6. `personal--desktop-lrpython-linear-regression`
7. `personal--verta-core`

## Decisions

- Promoted now: `personal--atlas-stack-git-versioning-openai-integration-research`
- Promoted now: `personal--atlas-storage-system-rule-based-compression-deduplication-graph`
- Promoted now: `personal--atlas-universal-extensible-ai-powered-os-ecosystem-inspired-by-linux-and-git`
- Already promoted: `personal--atlas-universal-interoperable-technology-stack`
- Held back: `personal--college-fullstack-ai-archive` because it is private courseware with executable content and a narrower metadata-only posture
- Held back: `personal--desktop-lrpython-linear-regression` because it remains metadata-only and is not the next safe derived-only promotion
- Held back: `personal--verta-core` because it has credential-like material, copyright signals, and executable content
- Allowed separately: ATLAS-authored reviewed derivative notes for selected Verta historical docs where provenance, claim labeling, and trust boundaries stay explicit

## Promotion Notes

- `personal--atlas-stack-git-versioning-openai-integration-research` is a high-level research note about stack coordination, Git versioning, and OpenAI integration boundaries. It is safe to retain as derived knowledge because the promotion omits raw text and only records policy-safe synthesis.
- `personal--atlas-storage-system-rule-based-compression-deduplication-graph` is a design note about storage policy, compression, deduplication, and graph-shaped organization. It is safe to retain as derived knowledge because the promotion stays at the architectural level.
- `personal--atlas-universal-extensible-ai-powered-os-ecosystem-inspired-by-linux-and-git` is an architecture note about an extensible ATLAS ecosystem. It is safe to retain as derived knowledge because the promotion summarizes the system shape rather than copying source material.

## Hold Policy

- Do not promote archives with secrets risk.
- Do not promote Verta until scrub and rotation complete.
- Do not promote archives where copyrighted or executable material would widen policy exposure beyond metadata-only handling.
- Reviewed derivative notes about Verta history must not flip `personal--verta-core*` from metadata-only or untrusted status.
