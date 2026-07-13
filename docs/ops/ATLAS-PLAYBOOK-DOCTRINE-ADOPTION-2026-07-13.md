# ATLAS Playbook Doctrine Adoption

- Date: `2026-07-13`
- Scope: Atlas root doctrine adoption by stable source reference only
- Playbook source PR: `fawxzzy/playbook#22`
- Accepted owner ref: `main`
- Accepted owner commit: `952b63aa6457d871024a224a089c4088490d69c5`

## Source Truth

Playbook source truth was verified from the local Git object database at the accepted owner commit with `git show <commit>:<path>` reads, not from the active Playbook working tree.

- Registry: `docs/doctrine/atlas-engineering-doctrine-registry.v1.json`
  - SHA-256: `4a013540d2f613c4cec583b071d9dc5986730faee772573fcc79750a5730dcf3`
- Schema: `docs/doctrine/atlas-engineering-doctrine-registry.schema.v1.json`
  - SHA-256: `84f081b2b04b72db455609b086aa2295fcb487de9c51f8e24a230d1161483162`
- Governed skill: `.agents/skills/review-project-next-step/SKILL.md`
  - SHA-256: `ba8fee476d665ef4a0d4190ac278bfaf6b8ba21b4a7e7f799d6733bd72a2ca63`

## Adoption Boundary

Playbook owns doctrine and Atlas owns adoption/conformance evidence.

Atlas root now records:

- the accepted Playbook source repository, ref, commit, and artifact paths
- the source artifact digests
- the stable adopted record IDs grouped by lifecycle
- the governed skill identity and path
- the read-only validator, test coverage, and this receipt

Atlas root does not republish doctrine statements, rationale text, or any second canonical doctrine registry.

## Validation Evidence

- Preflight contract status: validated
  - `C:\ATLAS\.codex\logs\20260713T124310042Z-atlas-playbook-doctrine-adoption\atlas.component-manifest.v2.json`
  - `C:\ATLAS\.codex\logs\20260713T124310042Z-atlas-playbook-doctrine-adoption\atlas.job-envelope.v2.json`
  - both validation sidecars report `ok: true`
- `python -m unittest tests.test_atlas_playbook_doctrine_adoption -v`
  - `10` tests passed
  - failure coverage includes `source_commit_missing`, `source_path_missing`, `source_digest_mismatch`, `adopted_record_unknown`, `lifecycle_mismatch`, `copied_doctrine_rejected`, duplicate adopted IDs, and malformed skill identity
- `python ops/atlas/playbook_doctrine_adoption.py --json`
  - status: `verified`
  - registry id: `atlas-engineering-doctrine-registry`
  - schema version: `atlas-engineering-doctrine-registry.v1`
  - schema id: `atlas-engineering-doctrine-registry.schema.v1.json`
  - all recorded digests matched observed Git-object digests
  - all source record IDs were adopted exactly once under the correct lifecycle group
  - no copied doctrine statement field or doctrine body was present in the Atlas adoption record
- `python ops/validation/validate_stack.py`
  - result: `critical=0 error=5 warning=9 info=0`
  - the five errors remain the pre-existing `working-memory-catalog-drift` and `_stack` lockfile drift classes already present in the root validation receipt
  - this packet changed none of those surfaces and did not widen that blocker class
- `git diff --check`
  - no whitespace or merge-marker failures

## Active Local Checkout Distinction

The canonical local Playbook checkout remains intentionally different from the accepted owner-main source:

- Active local branch: `codex/path-discipline-warning-slice-playbook`
- Active local head: `10b8f0ac044a7f9c66b4aa8dd08f6abd2d1c5269`
- Accepted source commit used for doctrine verification: `952b63aa6457d871024a224a089c4088490d69c5`

That divergence was reported as a warning only. The validator still accepted the adoption because it read the accepted source artifacts from Git objects at the accepted commit rather than from the active working tree.

## Remaining Work

This packet completes:

- Playbook doctrine registry publication as the accepted owner source for Atlas doctrine consumption
- Atlas root adoption/conformance evidence for that registry

This packet does not complete:

- universal component adoption across the twelve declared components
- owner-side proof for `_stack`, DiscordOS, Lifeline, Playbook, Mazer, Fitness, Foundation, Trove, Stream, Nat1, and Playbook Demo
- broader governed skill rollout beyond the Atlas root adoption unit
