# Stack Lock And Inventory Mazer Mechanics/Mobile Proof Resync

Date: 2026-07-03
Branch: `main`

## Scope

Refresh ATLAS root inventory after Mazer PRs `#22` and `#23` merged the generated-menu AI proof and generated-play traversal proof.

## Owner Repo Truth

- repo: `repos/mazer`
- branch: `main`
- head: `3e460aa7e47d0effa9278f4ed1a1c0285c1c3e25`
- PRs:
  - `https://github.com/fawxzzy/mazer/pull/22`
  - `https://github.com/fawxzzy/mazer/pull/23`
- active mechanics/mobile marker: `81%`
- owner-repo validation:
  - `npm exec vitest -- run tests\ai\demo-walker.test.ts tests\reset\legacy-marker.test.ts --reporter=dot`
  - `npm exec vitest -- run tests\reset\legacy-play-step.test.ts tests\reset\legacy-marker.test.ts --reporter=dot`
  - `npm run verify`

## Root Updates

- regenerated `docs/registry/STACK-REPO-INVENTORY.json`
- regenerated `docs/audits/STACK-REPO-INVENTORY.md`
- `stack.lock.yaml` had no committed content change from this resync

## Root Proof

- `python ops\stack\generate_lockfile.py`
  - lock digest: `sha256:1fc5b5078ba80d0f9defce9cbbf96a4b3aaddeb86296ed2e94885eba272578e6`
- `python ops\stack\export_repo_inventory.py`
  - dirty repo count: `0`
  - inventory digest: `sha256:d5f9ed84e97c71dbb430730086d1912d32c02a9b9443fa9c8ef5baa71c4d4136`
- `python ops\validation\validate_stack.py --ratchet`
  - `critical=0 error=0 warning=4 info=0`

## Closeout

The published inventory now records clean Mazer main at `3e460aa7e47d0effa9278f4ed1a1c0285c1c3e25` after the active mechanics/mobile marker reached `81%`.
