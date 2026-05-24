# Stack Lock Decision - Fitness Computa Feedback Setup Alias Removal

Date: 2026-05-24
Status: accepted

## Decision
Accept Fitness commit `3e242a4d5bbf7a2dcf7eae160c07dfb2317b773c` into ATLAS root truth and repin `stack.lock.yaml`.

## Reason
- the deployed Fitness command surface removed the legacy `computa feedback setup` alias
- the live public and owner Computa cards were patched to match the deployed command contract
- this is a narrow Discord command-surface cleanup with no unrelated product-surface change

## Accepted Surface
- Fitness command parser
- Fitness Discord feedback docs
- Fitness Discord worker and route tests
- live Discord `Computa` and `Computa Owner` message bodies in `#main`

## Verification
- Fitness verification passed before acceptance:
  - `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions-route.test.ts`
  - `node --test scripts/discord-feedback-gateway-worker.test.mjs`
  - `npm run verify`
- ATLAS root validation rerun after repin

## Notes
- no deploy authority change
- no Discord permission model change
- no `tmp` fallback used
