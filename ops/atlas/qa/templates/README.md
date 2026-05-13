# ATLAS QA Adapter Rollout Templates

These templates are root-owned adoption bundles for child repos. They are intentionally limited to manifest examples, discovery guidance, and validation commands. They do not copy any root QA pipeline logic.

Ownership split:
- Root owns schemas, runners, artifact validation, lens registry, promotion logic, and CI gate behavior.
- Child repos own adapter config, scenario config, and repo-specific selectors, routes, commands, and assertions.

Template bundles:
- `ops/atlas/qa/templates/web/` for browser-facing web repos.
- `ops/atlas/qa/templates/api-package/` for API, service, library, or package repos.
- `ops/atlas/qa/templates/docs-only/` for docs-first repos with no required visual evidence lane.

Important constraint:
- The current `atlas.qa.scenario.v1` contract requires at least one declared `proof.pr_lens`.
- Because of that, nonvisual repos still need a minimal declared lens, even when required artifacts are only `executable_report`, `api_report`, or `manual_note`.
- The docs-only and API/package templates model that constraint explicitly instead of pretending the schema is lensless.

Root-relative refs:
- Default visual lens registry: `ops/atlas/qa/lenses/atlas-default-web.v1.json`
- Web example adapter: `ops/atlas/qa/templates/web/template.web.json`
- Web example scenario: `ops/atlas/qa/templates/web/template.web.smoke.json`
- API/package example adapter: `ops/atlas/qa/templates/api-package/template.api-package.json`
- API/package example scenario: `ops/atlas/qa/templates/api-package/template.api-package.contract.json`
- Docs-only example adapter: `ops/atlas/qa/templates/docs-only/template.docs-only.json`
- Docs-only example scenario: `ops/atlas/qa/templates/docs-only/template.docs-only.verify.json`

Validation commands:

```bash
python ops/atlas/qa/validate_adapter.py --adapter-file ops/atlas/qa/templates/web/template.web.json
python ops/atlas/qa/validate_scenario.py --scenario-file ops/atlas/qa/templates/web/template.web.smoke.json
python ops/atlas/qa/run_matrix.py --adapter-dir ops/atlas/qa/templates/web --scenario-file ops/atlas/qa/templates/web/template.web.smoke.json --dry-run
```

```bash
python ops/atlas/qa/validate_adapter.py --adapter-file ops/atlas/qa/templates/api-package/template.api-package.json
python ops/atlas/qa/validate_scenario.py --scenario-file ops/atlas/qa/templates/api-package/template.api-package.contract.json
python ops/atlas/qa/run_matrix.py --adapter-dir ops/atlas/qa/templates/api-package --scenario-file ops/atlas/qa/templates/api-package/template.api-package.contract.json --dry-run
```

```bash
python ops/atlas/qa/validate_adapter.py --adapter-file ops/atlas/qa/templates/docs-only/template.docs-only.json
python ops/atlas/qa/validate_scenario.py --scenario-file ops/atlas/qa/templates/docs-only/template.docs-only.verify.json
python ops/atlas/qa/run_matrix.py --adapter-dir ops/atlas/qa/templates/docs-only --scenario-file ops/atlas/qa/templates/docs-only/template.docs-only.verify.json --dry-run
```

Adoption flow:
1. Copy the closest template bundle into the target repo-owned location.
2. Replace the example `repo_id`, `repo_path`, `adapter_id`, commands, and routes with repo-local values.
3. Add or adjust an optional `prepare` command when CI evidence lanes need dependency or browser setup before capture.
4. Keep root-relative refs for root-owned assets such as the shared lens registry unless the root standard adds a repo-local override.
5. Validate the adapter and scenario before wiring the repo into the root CI gate.

Discovery checklist:
- See `ops/atlas/qa/templates/discovery-checklist.md`.
