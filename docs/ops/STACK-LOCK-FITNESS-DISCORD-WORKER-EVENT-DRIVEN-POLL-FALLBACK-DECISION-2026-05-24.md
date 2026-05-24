## Stack Lock Decision - Fitness Discord Worker Event-Driven Poll Fallback

Date: 2026-05-24
Status: accepted

### Decision

Accept Fitness commit `cd1eb19cea15156697d4564364c10c91ba7f965d` into ATLAS root truth and repin `stack.lock.yaml`.

### Scope Accepted

- Discord Gateway worker fallback polling is no longer steady-state while the gateway is healthy
- fallback polling is slower by default and only activates when the gateway never becomes ready or disconnects
- worker lifecycle tests cover the new startup, ready, and disconnect behavior
- Fitness Discord worker runtime docs now match the event-driven contract

### Why This Is Accepted

- it directly addresses a measured operator/runtime cost issue
- it preserves the existing command surface and authority boundaries
- it reduces Vercel load without requiring a deploy or new platform mutation
- local runtime was normalized by stopping stale workers and relaunching a single clean worker

### Verification

Repo-local:

- `node --test scripts/discord-feedback-gateway-worker.test.mjs`
- `npm run verify`

Stack-level:

- local worker idle log stays quiet after gateway health is established
- root validation run after repin

### Stack Lock Update

- `stack.lock.yaml`
  - `fitness.commit = cd1eb19cea15156697d4564364c10c91ba7f965d`
