# Stack Lock Decision - Fitness Music Sesh Setup Repost Fix

Date: 2026-05-24
Status: accepted

## Decision
Accept Fitness commit `626bba9ec7ed50897942d5a9bb2ece7b732c7117` into ATLAS root truth and repin `stack.lock.yaml`.

## Reason
- fixes a live Discord operator-surface bug in the Music Sesh setup command
- keeps setup behavior aligned with the existing feedback launcher repost pattern
- does not widen runtime scope beyond the narrow setup path

## Accepted Surface
- Music Sesh Discord setup route
- Music Sesh main-channel message-command setup path
- focused route tests covering slash and message-command repost behavior
- governed production deploy on the canonical Fitness project

## Verification
- repo verification passed before acceptance
- governed `_stack` production deploy completed successfully
- ATLAS root validation rerun after repin

## Notes
- no Vercel identity change
- no Supabase schema change
- no Discord permission change
- unrelated preexisting Fitness asset/build dirt remained untouched
