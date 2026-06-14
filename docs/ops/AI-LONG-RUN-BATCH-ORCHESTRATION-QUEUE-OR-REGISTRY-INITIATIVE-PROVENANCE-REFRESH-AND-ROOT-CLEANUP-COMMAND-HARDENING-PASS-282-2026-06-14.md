# AI Long-Run Batch Orchestration Queue-Or-Registry Initiative Provenance Refresh And Root Cleanup Command Hardening Pass 282 - 2026-06-14

- Date: `2026-06-14`
- Lane: `AI Long-Run Batch Orchestration`
- Mode: `root-owned process hardening and warning-class elimination`
- Source surfaces:
  - `ops/atlas/run_initiative_loop.py`
  - `ops/atlas/run_session.py`
  - `tests/test_atlas_run_initiative_loop.py`
  - `stack.yaml`
  - `stack.lock.yaml`

## Objective

Stop two repeating root-side failure classes from reopening after otherwise valid queue-or-registry work:

1. stale initiative and proposed-session attention provenance after session or world-model refresh
2. recurring Fitness generated-state cleanup warnings caused by the validator invoking cleanup through `npm run` on Windows

## Executed Changes

- updated `ops/atlas/run_initiative_loop.py`
  - extracted callable `run_initiative_loop(...)` for reuse from root session sync paths
  - added `resolved_related_attention_refs(...)` so stale `attention:*` refs are pruned against the current attention model
  - made initiative related-attention output deterministic instead of leaking set iteration order
  - kept proposal regeneration bound to current actionable attention refs
- updated `ops/atlas/run_session.py`
  - `sync_session_outputs(...)` now runs `run_initiative_loop(root=ROOT, dry_run=False, refresh_inputs=False)` before rendering status snapshots
  - session and world-model refresh now also refresh initiative/proposal provenance instead of waiting for later validator reopen
- added `tests/test_atlas_run_initiative_loop.py`
  - proves stale initiative attention refs are removed
  - proves proposed-session `triggering_attention_refs` are regenerated from current attention only
- updated `stack.yaml`
  - root validation now invokes the Fitness cleanup script directly with `node scripts/cleanup-repo.mjs ... --report-path ...`
  - bypasses the `npm run` wrapper that was recreating or retaining `node_modules` after the script itself succeeded
- refreshed `stack.lock.yaml`
  - repinned the current root working set after the stack cleanup command contract changed

## Live Proof

- `npm run cleanup:repo:validation`
  - proved the hardened Fitness cleanup script can relocate a real leftover `node_modules` tree without warninging out
- `node scripts/cleanup-repo.mjs --include-build-cache --include-node-modules --include-playbook-state --relocate-to-tmp`
  - proved the direct-script invocation removes `node_modules` cleanly without the `npm run` wrapper residue problem
- `npm install`
  - succeeded from a clean Fitness repo after the residue path was cleared
- `npm run verify`
  - passed in `repos/fawxzzy-fitness`

## Test Proof

- `python -m unittest tests.test_atlas_run_initiative_loop tests.test_atlas_resume_session tests.validation.test_validate_stack_execution_receipt_repairs tests.validation.test_validate_stack_resume_contract tests.validation.test_validate_stack_mutable_state_rules`
  - `Ran 16 tests`
  - `OK`
- `python .\ops\validation\validate_stack.py --ratchet`
  - final result: `critical=0 error=0 warning=0 info=0`

## Result

- initiative and proposed-session provenance now refreshes inside the normal session sync process instead of reopening later as stale-attention validation debt
- the repeating Fitness cleanup warning class is removed at the process layer by using the direct cleanup command that actually clears residue on Windows
- the stack returns to clean ratcheted validation after both fixes land together

## Marker Read

- `AI Long-Run Batch Orchestration -> 47%`
- reason:
  - one real restart-safety gap in queue-or-registry initiative/proposal provenance is now closed in the live sync path
  - one repeating warning-producing cleanup seam is now hardened at the process layer instead of being manually re-cleared after each pass
  - the lane stays low because this is still infrastructure hardening around the queue-or-registry family, not broader operator adoption or new execution-home behavior

## Next Best Move

- tighten queue-or-registry status rendering or validator doctrine around proposed-session and initiative residue classes that can still reopen if future runtime writers bypass the canonical sync path
