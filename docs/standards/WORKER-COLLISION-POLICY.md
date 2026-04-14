# Worker Collision Policy

This standard defines the deterministic conflict rules for worker overlap detection.

## Rule Order

Apply rules in this order:

1. forbidden scope violation
2. drift conflict
3. overlap conflict
4. no conflict

## Forbidden Scope

- if a worker touches a forbidden glob, the worker hard fails
- the assignment is invalid for that action scope
- no merge request is emitted for a pure forbidden-scope violation unless it also overlaps other workers

## Drift Conflict

- if two workers touch the same path and the `file_digest_before` values differ, treat it as a drift conflict
- pause both workers
- emit a merge request
- require a merger worker to reconcile from the paused handoff artifacts

## Overlap Conflict

- if two workers touch the same path, the same `file_digest_before`, and overlapping line ranges, treat it as a conflict
- pause both workers
- emit a merge request
- merge resolution must be performed off the paused handoff artifacts

## No Conflict

- if line ranges do not overlap and the file is merge-safe, continue
- merge-safe status is an explicit policy input, not an inference from transcripts

## Observer Model

- supervisors observe status artifacts only
- touched ranges are the authoritative collision surface
- transcripts are not part of the collision contract

## Merge Handoff

- paused workers hand off their paused context artifacts
- merger workers receive a merge request plus the paused handoff refs
- resume only after the merge worker emits the reconciliation handoff
