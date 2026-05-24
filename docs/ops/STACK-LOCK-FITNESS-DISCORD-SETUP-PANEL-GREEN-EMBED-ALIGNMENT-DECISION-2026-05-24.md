## Stack Lock Decision - Fitness Discord Setup Panel Green Embed Alignment

Date: 2026-05-24
Status: accepted

### Decision

Accept Fitness commit `072fb3c04db1d84717ca1635895fed27ea7373da` into ATLAS root truth and repin `stack.lock.yaml`.

### Scope Accepted

- Feedback setup launcher now uses the governed green embed color
- Music Sesh setup panel now uses the governed green embed color even when the room is closed
- tests cover both public setup surfaces
- production deploy and live Discord panel cleanup are recorded

### Why This Is Accepted

- it fixes visible Discord OS format drift on canonical setup surfaces
- it preserves existing command and button behavior
- it aligns setup posts with the established governed green embed contract already used by updates and command cards

### Verification

Repo-local:

- `node --import ./scripts/register-test-aliases.mjs --test src/lib/discord/interactions.test.ts`
- `npm run verify`

Stack-level:

- root validation after repin

### Stack Lock Update

- `stack.lock.yaml`
  - `fitness.commit = 072fb3c04db1d84717ca1635895fed27ea7373da`
