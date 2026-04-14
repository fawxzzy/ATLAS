# Verta-Core Review

## Archive

- `archive_id`: `personal--verta-core`
- `source_name`: `personal`
- `import_dir`: `data/imports/knowledge/personal/verta-core`
- `reviewed_at`: `2026-04-13T20:27:30Z`
- `reviewer`: `Codex`

## Provenance

- original input: `repos/Verta-Core.zip`
- retained raw archive: `data/imports/knowledge/personal/verta-core/raw/Verta-Core.zip`
- exploratory full-repo candidate: `data/imports/knowledge/personal/verta-core-clean`
- sanitized candidate import: `data/imports/knowledge/personal/verta-core-sanitized`
- import manifest: `data/imports/knowledge/personal/verta-core/IMPORT-MANIFEST.json`
- evaluation: `data/imports/knowledge/personal/verta-core/EVALUATION.json`
- runtime catalog: `runtime/cortex/catalog/knowledge/personal--verta-core.json`
- owner or source context: imported through the ATLAS knowledge lane as quarantined private evidence; existing `repos/Verta-Core/` checkout remains untrusted and non-active until scrub and rotation complete
- provenance confidence: high

## Privacy And Risk

- `privacy_flag`: `private`
- `safe_for_indexing`: `no`
- `indexing_profile`: `metadata_only`
- `promotion_status`: `not_promoted`
- `promotion_allowed`: `false`
- `normalization_allowed`: `false`
- `quarantine_flags`: `credentials_secrets_risk`
- `quarantine_reason`: `Credential-like material was detected. Keep the archive quarantined to metadata-only handling until rotation and scrub are complete.`

## Evidence Notes

- The archive contains 1,826 files, including 589 Markdown files, 177 Python files, 323 log files, launcher scripts, eval data, and archived configuration artifacts.
- Secret-bearing documentation and config examples were detected in `.claude/launcher/launch_verta_core_with_auth.ps1`, `.claude/launcher/launch_verta_with_auth.ps1`, `.claude/launcher/README.md`, `CLAUDE_RUNS_FROM_HERE.md`, and `data/archive/config/teams_auth.example.json`.
- A curated sanitized candidate was exported from the scrubbed launcher/config/docs surface and re-imported as `personal--verta-core-sanitized`; it evaluates to `safe_for_indexing = restricted`, `indexing_profile = metadata_only`, and `promotion_status = not_promoted` with no `credentials_secrets_risk`.
- The broader exploratory candidate `personal--verta-core-clean` remained quarantined because the full historical tree still contains private, copyrighted, and executable surfaces outside the scrubbed lane.
- Copyright and courseware-style signals were also detected in multiple `docs/` and `data/evals/` artifacts.
- Executable content is present and remains subject to the no-execute rule.

## Decision

- keep the archive quarantined in `data/imports/knowledge/`
- retain only receipt-backed metadata in the runtime catalog
- do not create a promotion doc
- do not execute any archived scripts, launchers, or eval tooling
- do not treat `repos/Verta-Core/` as trusted or active repo truth until secret scrub and any required rotation are complete
- use the sanitized candidate only as a rebuildable metadata-only evidence path until policy allows promotion
- enforce the standing root trust gate in `docs/ops/VERTA-TRUST-GATE.md`

## Required Follow-Up

- scrub or remove token-bearing documentation and example secret material
- rotate any credentials that may have been exposed in docs, configs, or launcher guidance
- rerun evaluation after scrub before considering any promotion request
