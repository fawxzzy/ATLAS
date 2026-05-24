# Fitness Canonical Path Visibility Preflight

Date: 2026-05-24
Lane: Brand Asset Canonicalization
Mode: Read-only
Status: canonical Fitness path missing from active ATLAS root

## Goal

Explain why canonical restoration receipts say `repos/fawxzzy-fitness` was restored, while the active ATLAS root session cannot currently see that path.

## Direct Root Checks

### 1. Does `C:\ATLAS\repos\fawxzzy-fitness` exist?

- no

Observed result:

```text
Test-Path 'C:\ATLAS\repos\fawxzzy-fitness' -> False
```

### 2. Does `C:\ATLAS\repos` currently contain a Fitness child repo?

- no

Observed `repos/` children:

- `fawxzzy-lifeline`
- `fawxzzy-lifeline-operator-evidence`
- `fawxzzy-mazer`
- `fawxzzy-playbook`
- `fawxzzy-playbook-codex`
- `fawxzzy-stream`
- `fawxzzy-trove`
- `fawxzzy-trove-release-cutover`
- `Nat1-Games`
- `playbook-demo`
- `repo-backups`
- `Verta-Core`
- `ZachariahRedfield`
- `_stack`

## Stack Metadata Checks

### 3. Does `stack.yaml` still register Fitness?

- yes

Current registration:

```yaml
fitness:
  path: repos/fawxzzy-fitness
  role: application
  status: unmanaged
```

### 4. Does `stack.lock.yaml` still pin canonical Fitness?

- no

Observed state:

- no current canonical `fitness:` lock entry was found
- only older recovery or adjacent Fitness surfaces remain listed, such as:
  - `repos/fawxzzy-fitness-parity-recovery`
  - `repos/fawxzzy-fitness.reclone.20260502-195639`
  - `repos/fawxzzy-fitness-recovered`

Interpretation:

- the stack manifest still points to canonical Fitness
- the lock no longer records a live canonical Fitness child repo pin
- so the active metadata is already split even before any new Fitness brand work begins

## Receipt Consistency Checks

### 5. Does canonical restoration closeout still claim restoration complete?

- yes

[CANONICAL-REPO-RESTORATION-CLOSEOUT-2026-05-23.md](/C:/ATLAS/docs/ops/CANONICAL-REPO-RESTORATION-CLOSEOUT-2026-05-23.md) still states:

- canonical repo root exists at `repos/fawxzzy-fitness`
- canonical verification passed there
- `_stack` proved against that canonical path

### 6. When did the path disappear?

No direct filesystem deletion receipt was found in this pass.

The best bounded timeline from recorded evidence is:

1. canonical presence was asserted in the restoration closeout on 2026-05-23
2. active-root absence was already recorded later in [BRAND-FITNESS-PATH-VISIBILITY-2026-05-23.md](/C:/ATLAS/docs/ops/BRAND-FITNESS-PATH-VISIBILITY-2026-05-23.md)
3. the same absence is still present in [BRAND-FITNESS-PATH-VISIBILITY-RECHECK-2026-05-24.md](/C:/ATLAS/docs/ops/BRAND-FITNESS-PATH-VISIBILITY-RECHECK-2026-05-24.md)

Current conclusion:

- the disappearance happened before or during the 2026-05-23 brand-lane checks
- this preflight cannot name a precise deletion event or actor

## Worktree and Filesystem Checks

### 7. Are there active worktree conflicts?

- none were found for canonical Fitness

Observed `git worktree list` from ATLAS root shows only:

- `C:/ATLAS`
- several `tmp/` worktrees unrelated to canonical Fitness

No active worktree is occupying `repos/fawxzzy-fitness`.

### 8. Is canonical Fitness present somewhere else under `C:\ATLAS`?

- yes, but not in the canonical `repos/` child path

Observed alternate surfaces:

- retained reference:
  - `tmp/fawxzzy-fitness-main-prod-source-3d00eac7`
- recovery snapshots:
  - `recovery-snapshots/seq001a-effort-schedule-equivalence-20260521-083034/source-files/repos/fawxzzy-fitness`
  - `recovery-snapshots/seq001a-effort-schedule-equivalence-20260521-083048/source-files/repos/fawxzzy-fitness`

### 9. Is `tmp` still only retained reference, not active truth?

- yes

Observed retained reference state:

- `tmp/fawxzzy-fitness-main-prod-source-3d00eac7` exists
- branch: `main`
- remote: `https://github.com/fawxzzy/fawxzzy-fitness.git`
- HEAD: `7ceebde9d71564614df98e391b245a836d15c401`

This matches the prior tmp demotion receipts and remains:

- retained reference only
- not an authorized brand sync target
- not a replacement canonical child repo path

## Interpretation

This is not just a transient UI/session refresh problem.

The canonical Fitness repo is absent on disk from `repos/`, while:

- `stack.yaml` still points at it as canonical
- `stack.lock.yaml` no longer carries a live canonical Fitness pin
- retained reference and snapshot evidence still exist elsewhere under `C:\ATLAS`

That makes this a combined:

- filesystem visibility or disappearance problem
- stack metadata inconsistency problem

## Decision

- `needs reclone from GitHub`
- `needs stack metadata repair`

Secondary note:

- manual filesystem review is still useful if the team wants to identify how the canonical child repo disappeared, but it is not required to determine the safe next operational repair

## Safe Repair Direction

If this lane is resumed, the safe path is:

1. restore `repos/fawxzzy-fitness` as the canonical child repo from the GitHub remote
2. verify it is clean on `main`
3. repair the stack-facing metadata so canonical Fitness is again consistently represented
4. only then reconsider the Fitness brand sync package

## Prohibited Shortcuts

Do not:

- sync brand assets into `tmp/`
- treat recovery snapshots as canonical
- bypass canonical child repo restoration by writing into alternate Fitness checkouts

## Final Verdict

Fitness brand sync remains deferred.

The current blocker is not source-truth doctrine and not a reason to reintroduce `tmp`; it is the concrete absence of `repos/fawxzzy-fitness` from the active ATLAS root plus the fact that stack metadata no longer consistently reflects a live canonical Fitness child repo.
