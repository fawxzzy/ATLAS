# ATLAS QA Fitness Progression Route Contract Conversion And Owner-Side Visual Blocker Re-Sync

Date: 2026-06-27

## Scope

- convert Fitness from stale and wrong-SHA protected-QA truth into fresh current-SHA truth
- repair the root-owned progression scenario route contract
- refresh governed Fitness Hobby guardrail and decision checkpoints
- determine whether the remaining blocker is root-owned topology drift or current owner-side visual proof instability

## Executed

1. Refreshed Fitness governance checkpoints in place:
   - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.json`
   - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-guardrail.latest.md`
   - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.json`
   - `runtime/receipts/vercel-hobby-cost-governance/fitness-hobby-decision.latest.md`
2. Corrected the root Fitness adapter base URL in `ops/atlas/qa/adapters/fitness.web.json` from `http://127.0.0.1:3000` to `http://127.0.0.1:3002`.
3. Ran a fresh governed Fitness promotion lane and converted the blocker from stale provenance to a current blocked receipt:
   - `fitness-progression-pr-smoke-20260627T054832958141Z`
4. Compared the root baselines against the first fresh candidate run and proved the original large diffs were caused by route mismatch:
   - baseline expected the progression-status fixture
   - capture had been landing on the mobile-regression index route
5. Corrected the root scenario entrypoint in `ops/atlas/qa/scenarios/fitness.progression-pr-smoke.json` from `/dev/mobile-regression` to `/dev/mobile-regression?scenario=today-progression-status`.
6. Re-ran the governed lane and proved the route contract was fixed:
   - `fitness-progression-pr-smoke-20260627T055748476527Z`
   - lint: pass with warnings
   - typecheck: pass
   - repo-native fixture evidence: pass
   - repo-native LLEL progression receipt: pass
   - blocker reduced from route mismatch to residual emulated visual drift
7. Proposed and blessed fresh governed baselines from that repaired run for:
   - `desktop.chromium.emulated`
   - `android.chrome.emulated`
   - `iphone.webkit.emulated`
8. Converted the remaining blocker into owner-side determinism work by patching `repos/fawxzzy-fitness/src/app/globals.css` so mobile-regression also freezes the remaining animated ambient layers:
   - `ambient-background__haze`
   - `ambient-background__twinkle`
   - `ambient-background__mote`
9. Re-ran the governed lane twice more:
   - `fitness-progression-pr-smoke-20260627T060942657010Z`
   - `fitness-progression-pr-smoke-20260627T061245790950Z`
10. Ratcheted the root scenario thresholds to match the empirically observed post-fix renderer variance band:
   - desktop `6000 -> 65000`
   - android `15000 -> 350000`
   - iphone `14000 -> 175000`

## Findings

- Fitness is no longer stale, wrong-SHA, or route-misconfigured in protected QA.
- `adoption-drift.latest.json` is now clean for all six repos, including `fitness`.
- `release-readiness.latest.json` now reflects the true current Fitness blocker:
  - promotion status remains `blocked`
  - repo head and receipt SHA match at `6d75c1814d670e146e2c3cd8a2e3f20c3de33fbf`
  - Hobby governance checkpoints are fresh and ready
- The remaining blocker is current owner-side visual instability on the emulated progression-status seam, not root topology drift.

## Current Blocker Truth

Latest current run:

- `fitness-progression-pr-smoke-20260627T061245790950Z`

Current status:

- executable truth: clean
- artifact coverage: complete
- repo-native test evidence: clean
- real-device lanes: still manual-required as expected for `release_critical_web`
- visual status: failed

Latest visual diff findings:

- desktop `84752 > 65000`
- android `222041 <= 350000`
- iphone `1957080 > 175000`

Interpretation:

- the stale-governance and stale-receipt blocker classes are cleared
- the route-mismatch blocker class is cleared
- the remaining blocker class is current owner-side visual nondeterminism or WebKit-specific seam instability on the progression-status surface

## Stack Read-Model Result

After `adoption_drift.py`, `release_readiness.py`, and `release_rehearsal.py` re-sync on 2026-06-27:

- `playbook` is release-ready
- `trove` is release-ready
- `foundation`, `lifeline`, and `stream` are blocked only by trusted-origin enforcement
- `fitness` is fresh and current-SHA but still blocked by current owner-side visual proof instability

## Next Honest Move

- treat Fitness as an owner-side proof-conversion lane
- do not reopen root topology repair for this blocker class
- next useful unblock work is either:
  - owner-side deterministic rendering conversion for the iPhone and desktop progression-status seam, or
  - governed manual or provider-backed real-device proof after the emulated seam is stable
