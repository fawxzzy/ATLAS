# DiscordOS Mazer Board Correction

Date: 2026-07-09

## Mistakes Found

- The Mazer board was modeled as `mazer-feedback` / `Mazer Feedback` instead of the operator-requested `mazer`.
- The live-sync path defaulted to creating or discovering a standalone forum instead of targeting the existing project feedback forum.
- Card bodies were thin summaries and did not match the richer feature-card style used elsewhere.
- Incomplete cards were not required to carry the failure reaction metadata that marks work as not done.
- Tests encoded the incorrect board name and thin card format, so verification passed while the result was wrong.

## Guardrails Added

- Mazer board identity must be `mazer`.
- Mazer board placement must declare `project-feedback` with the canonical project feedback forum ID.
- Every card must include summary, acceptance criteria, proof plan, reference, next command, and reaction metadata.
- Every incomplete card must use the failure reaction.
- The live-sync path updates existing card starter messages and applies the configured reaction instead of only creating new threads.

## Verification Requirement

Future DiscordOS board work must verify:

- board identity and channel family
- card shape and detail richness
- reaction state for completed and incomplete cards
- live-sync target selection
- exact screenshot or live-readback target when a visual Discord surface is claimed
