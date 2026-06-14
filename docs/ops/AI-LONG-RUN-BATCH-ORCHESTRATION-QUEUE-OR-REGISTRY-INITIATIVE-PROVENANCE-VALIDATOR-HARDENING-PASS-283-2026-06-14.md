# AI Long-Run Batch Orchestration Queue-Or-Registry Initiative Provenance Validator Hardening Pass 283 - 2026-06-14

- Date: `2026-06-14`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned validator hardening`
- Source surfaces:
  - `ops/validation/validate_stack.py`
  - `tests/validation/test_validate_stack_initiative_provenance.py`
  - `stack.lock.yaml`

## Objective

Close the remaining silent-reopen seam after the earlier initiative/proposal sync-path hardening by making stale initiative attention provenance fail validation explicitly instead of being detectable only after downstream drift symptoms.

## Executed Changes

- updated `ops/validation/validate_stack.py`
  - extracted shared `load_known_attention_refs(root)` helper for current world-model attention ids
  - added `validate_initiative_provenance(stack_file)` to validate `docs/memory/initiatives/*.json`
  - initiative provenance now fails closed when:
    - `related_attention_refs` is not an array
    - an entry is not a non-empty string
    - an `attention:*` ref no longer resolves against the current attention artifact
    - a non-attention file ref no longer resolves on disk
  - wired the new validator into the main stack validation flow ahead of proposed-session validation
- added `tests/validation/test_validate_stack_initiative_provenance.py`
  - proves stale initiative attention refs are reported
  - proves current attention refs plus file-backed refs remain clean
- refreshed `stack.lock.yaml`
  - kept the pinned working set aligned after the root validator change

## Test Proof

- `python -m unittest tests.validation.test_validate_stack_initiative_provenance tests.test_atlas_run_initiative_loop tests.validation.test_validate_stack_execution_receipt_repairs tests.validation.test_validate_stack_resume_contract tests.validation.test_validate_stack_mutable_state_rules`
  - `Ran 16 tests`
  - `OK`
- `python .\ops\validation\validate_stack.py --ratchet`
  - final result: `critical=0 error=0 warning=0 info=0`

## Result

- initiative stale-attention drift is now a first-class validator failure instead of a later inferred symptom
- queue-or-registry provenance discipline now has both:
  - a live sync-path repair surface
  - an explicit validator guard if a future writer bypasses that path

## Marker Read

- `AI Long-Run Batch Orchestration -> 48%`
- reason:
  - one more real restart-safe doctrine seam is now explicit and machine-enforced
  - the lane still remains below broader operator adoption or execution-home widening because this pass hardens validator truth rather than adding new orchestration capability

## Next Best Move

- expose this initiative/proposal provenance status directly in a compact root-facing status surface so drift is visible before a full validator run
