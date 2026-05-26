# ATLAS Root Self-Lock Policy Decision - 2026-05-25

- Date: `2026-05-25`
- Lane: `ATLAS Root Self-Lock Policy Decision Pass`
- Mode: `docs and stack-policy decision`

## Scope

Decide the correct durable workflow for ATLAS root docs and receipt commits when the ATLAS root itself is included in `stack_lock.include_repo_ids`.

This pass does not:

- delete `archive/`
- touch `tmp/`
- mutate Supabase
- mutate Vercel
- touch Discord runtime
- start product work

## Inputs

- `docs/ops/QUEUED-WORK-REVIEW-PACKET-2026-05-25.md`
- `stack.yaml`
- `stack.lock.yaml`
- `ops/stack/generate_lockfile.py`
- `ops/validation/validate_stack.py`
- latest validation receipts
- `docs/ops/FULL-STACK-RESYNC-CLEAN-CLOSEOUT-BASELINE-PASS-2-2026-05-25.md`

## Decision Questions

### 1. Is root `stack` intentionally self-lock-tracked

Yes.

Evidence:

- `stack.yaml` explicitly listed `stack` inside `stack_lock.include_repo_ids`
- `stack.lock.yaml` therefore carried a `components.stack` entry pinned to the ATLAS root `HEAD`

### 2. Should every root-doc commit be followed by a lock refresh commit

No.

Reason:

- the lock refresh commit itself changes root `HEAD`
- that immediately makes the just-written root `stack` pin stale again
- the pattern does not converge to a stable committed state

### 3. Should root docs/checkpoints use a two-commit pattern: commit docs, refresh stack lock

No.

Reason:

- with root `stack` self-lock-tracked, a two-commit pattern is mathematically unstable
- commit A changes root `HEAD`
- lock refresh before commit B can only pin commit A
- commit B then changes `HEAD` again and re-stales the root pin immediately

### 4. Should specific receipt-only docs be excluded from self-lock churn

Yes, by policy at the root lock layer rather than by trying to special-case specific receipt files.

Approved policy:

- keep `stack` in `repo_registry`
- remove `stack` from `stack_lock.include_repo_ids`
- continue to lock-track managed child repos and excluded surfaces
- treat ATLAS root docs/receipt commits as governance surfaces validated by normal stack validation, not by self-pinning the root repo commit inside `stack.lock.yaml`

### 5. What is the approved closeout sequence for docs-only root commits

Approved sequence:

1. make the ATLAS root docs/receipt changes
2. if stack policy or non-root tracked repo truth changed, regenerate:
   - `stack.lock.yaml`
   - `docs/registry/STACK-REPO-INVENTORY.json`
   - `docs/audits/STACK-REPO-INVENTORY.md`
3. run normal validation:
   - `python .\ops\validation\validate_stack.py`
4. commit the docs/receipt/policy package as one bounded root commit
5. push `main`

Important rule:

- do not try to re-pin root `stack` to its own post-commit `HEAD`
- normal validation is the durable correctness gate for root docs packages

### 6. Can the queued review packet be committed safely using that sequence

Yes.

Once `stack` is removed from `stack_lock.include_repo_ids`, the queued closeout receipts, ATLAS Book refresh, and review packet can be committed without immediately re-staling the root lock truth again.

## Policy Change Applied

This pass applies the policy directly:

- removed `stack` from `stack.yaml` `stack_lock.include_repo_ids`
- removed the now-unused `stack` entry from `stack_lock.repo_overrides`

The root remains:

- in `repo_registry`
- validated by normal stack validation
- visible in stack governance

But it is no longer self-lock-tracked in `stack.lock.yaml`.

## Regeneration Commands

```powershell
python .\ops\stack\generate_lockfile.py
python .\ops\stack\export_repo_inventory.py
```

## Files Changed In This Pass

- `stack.yaml`
- `stack.lock.yaml`
- `docs/registry/STACK-REPO-INVENTORY.json`
- `docs/audits/STACK-REPO-INVENTORY.md`
- `docs/ops/ATLAS-ROOT-SELF-LOCK-POLICY-DECISION-2026-05-25.md`

Plus the queued closeout receipts and ATLAS Book refresh surfaces made durable under this policy.

## Validation Expectation

Expected durable state after regeneration:

- normal validation remains green
- `--allow-missing-locked-repos` remains unnecessary
- queued review packet and closeout receipts become commit-safe

## Remaining Blockers After This Decision

This decision removes the root commitability blocker.

Remaining non-policy blockers are now operational:

- retained `tmp/` worktrees and evidence
- helper Vercel retain-temporary surfaces
- Fitness residue
- Lifeline residue
- Playbook residue
- still-gated Supabase and DiscordOS runtime/data mutation lanes

## Next Package

- `Playbook And Lifeline Retained Worktree / Residue Disposal Planning Pass`

Or, if choosing a Fitness-local cleanup lane first:

- `Fitness Brand Preview Residue Pass`
