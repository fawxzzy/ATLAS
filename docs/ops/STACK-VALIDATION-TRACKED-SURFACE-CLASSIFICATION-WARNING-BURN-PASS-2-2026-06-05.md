# Stack Validation Tracked-Surface Classification Warning-Burn Pass 2

Date: 2026-06-05
Branch: `codex/root-path-discipline-warning-slice-1`

## Scope

Bounded root-side validator-classification slice only.

No owner-repo tracked source was edited.

Explicit non-scope:

- `repos/fawxzzy-fitness`
- `archive/`
- stack-lock refresh
- Vercel linkage mutation
- secret-surface deletion

## Why This Pass Was Admitted

After Pass 1, the remaining non-Fitness warning surface still mixed two different cases:

1. true local mutable residue such as ignored `.playbook`, `.lifeline`, `.vercel`, and untracked build outputs
2. fully tracked, clean surfaces that happened to live under mutable-name directories

The validator still warned on both classes equally, which overstated real residue.

## Changes

Changed `ops/validation/validate_stack.py`:

- added `mutable_surface_requires_warning(...)`
- mutable-path warnings now consult git state before emitting
- a mutable-path candidate still warns when git shows ignored, untracked, or modified local state
- a mutable-path candidate no longer warns when the entire surface is already fully tracked and clean

Expanded `tests/validation/test_validate_stack_mutable_state_rules.py`:

- tracked clean mutable surface does not warn
- ignored mutable surface still warns

## Verification

- `python -m unittest tests.validation.test_validate_stack_mutable_state_rules -v`
  - `4 tests OK`
- `python -m py_compile ops\validation\validate_stack.py tests\validation\test_validate_stack_mutable_state_rules.py`
  - passed
- `python .\ops\validation\validate_stack.py --ratchet`
  - `critical=0 error=16 warning=47 info=0`

## Result

Warning count moved from `56` to `47` without touching Fitness.

The warning surface now reflects real local residue much more closely.

Tracked clean surfaces that no longer warn include:

- `repos/playbook/.lifeline`
- `repos/foundation/.playbook`
- `repos/mazer/.playbook`
- `repos/trove/.lifeline`
- `repos/playbook-demo/playbook-demo/.playbook`
- `repos/playbook-demo/playbook-demo/dist`
- `repos/Nat1-Games/nat1-games/playwright-report`
- `repos/Nat1-Games/nat1-games/test-results`

The remaining non-Fitness warnings are now the smaller real local-state set:

- `_stack/.vercel`
- `playbook/.playbook`
- `lifeline/.playbook`
- `lifeline/.lifeline`
- `mazer/.vercel`
- `mazer/dist`
- `mazer/.env.local`
- `trove/.vercel`
- `Nat1-Games/nat1-games/.env`

The remaining `16` errors are unchanged stack-lock drift and remain outside this pass.

## Next Honest Move

Further warning reduction now requires one of:

1. deliberate owner-side cleanup of the remaining local mutable-state and secret surfaces
2. an explicit policy decision on retained `.vercel` linkage surfaces
3. a separate lock-refresh lane if the next goal is error reduction rather than warning reduction
