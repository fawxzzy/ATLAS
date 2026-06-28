# ATLAS Root Published Checkpoint Semantics Hardening And Restart Truth Re-Sync

## Scope

- harden the canonical restart interpretation for committed ATLAS-root inventory and Book checkpoint surfaces
- stop treating the published root checkpoint inside committed root-owned artifacts as a guarantee that live `HEAD` still matches after the publication commit itself lands
- keep marker posture flat while rewording the restart spine around the already-published clean checkpoint

## Why

The previous root resync pass correctly refreshed the published clean checkpoint to ATLAS `main` commit `26ceaaa4e50ec67122c65a7a26f29e0e7344e722`, but the next committed Book-only resync advanced live root `HEAD` again to `d046de0646be3d901f17a405403fb43d65e9aed8`.

That exposed a self-referential truth problem:

- the committed inventory and Book mirrors live inside the same root repo they describe
- a root-only publication commit can advance live `HEAD` without changing the last published clean checkpoint those artifacts intentionally capture
- if the restart spine keeps narrating that checkpoint as the always-live root `HEAD`, root can loop forever on paperwork-only re-sync passes

This pass fixes the interpretation, not the underlying protected-QA blocker posture.

## Executed Proof

### Live root-vs-published-checkpoint read

- `git rev-parse HEAD`
- `rg -n -e "26ceaaa4e50ec67122c65a7a26f29e0e7344e722" -e "d046de0646be3d901f17a405403fb43d65e9aed8" docs/atlas-book docs/memory/initiatives docs/registry docs/audits`

Result:

- live ATLAS root `HEAD` had advanced to `d046de0646be3d901f17a405403fb43d65e9aed8`
- the published inventory and canonical Book mirrors still referenced clean checkpoint `26ceaaa4e50ec67122c65a7a26f29e0e7344e722`

### Continuity and validation recheck

- `python ops/stack/generate_lockfile.py`
- `python ops/atlas/continuity_manifest_health.py`
- `python ops/atlas/continuity_open_marker_restart_index.py`
- `python ops/validation/validate_stack.py`

Result:

- `stack.lock.yaml` was refreshed to the current managed working set after validation exposed stale `stack.lock.yaml#mazer` branch and dirty-state drift
- initiative manifest health: `19 ok / 0 warning / 0 error`
- eligible open-marker restart index: `7 / 7 restart-ready`
- stack validation: `critical=0 error=0 warning=2 info=0`
- the remaining warnings are retained non-blocking `mazer` generated-state residue at `repos/mazer/node_modules` and `repos/mazer/dist`

## Current Truth

- the published inventory still truthfully captures the last published clean ATLAS root checkpoint at `26ceaaa4e50ec67122c65a7a26f29e0e7344e722`
- later root-only publication commits may advance live `HEAD` beyond that checkpoint without invalidating the checkpoint itself
- the live stack lock now also pins current `mazer` branch `codex/mazer-pass-2-recovery-tightening` with active dirty state so root validation stays aligned to the real managed working set instead of an older clean-only assumption
- `fitness` still remains clean on `codex/fitness-main-progression-summary-reapply` at `b5f29793eb87dc7538a15160180f159688acd1b4`
- the protected-QA blocker posture is unchanged:
  - `fitness` remains `manual_review`
  - remaining physical/manual lanes are still `android.chrome.real` and `iphone.webkit.real`
  - ATLAS GitHub Actions still lacks `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`

## Consequences

- the canonical restart spine now treats the committed root checkpoint as a published clean checkpoint rather than as an always-live root `HEAD` claim
- no marker ratchet is justified from this pass alone because no broader restart substrate, owner truth, or blocker class changed
- `Inventory & Truth Map` remains `93%`
- `Truth Map & ATLAS Book` remains `99%`

## Next Honest Moves

1. Keep the current inventory-facing and Book-facing lanes held flat after this semantics hardening pass.
2. Reopen only with one real blocker conversion, broader continuity automation, or new projection drift beyond this self-referential root checkpoint class.
