# Stack Lock Decision - Fitness Discord Feedback Submit Picker

Date:
- 2026-05-24

Decision:
- accept Fitness commit `d7040be8ebbddb2c9d340b0fe990c1ccf903a9c1` into ATLAS stack truth

Reason:
- the feedback launcher contract changed in a user-facing way
- the public submit flow is now picker-first instead of modal-first
- bug and feature cards now preserve explicit section overrides through the bounded feedback pipeline
- ATLAS lock truth should point at the Fitness commit that contains the new launcher, modal, and forum-section behavior

Accepted component update:
- `fitness.commit`: `626bba9ed158e228ae5224187be8323901c50320` -> `d7040be8ebbddb2c9d340b0fe990c1ccf903a9c1`

Verification:
- `npm run verify` in `repos/fawxzzy-fitness`
- `python .\ops\validation\validate_stack.py --allow-missing-locked-repos` in the ATLAS root (`.`)
