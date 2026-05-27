# Local Data Gateway First Implementation Selection - 2026-05-27

- Date: `2026-05-27`
- Lane: `Local Data Gateway first implementation package selection checkpoint`
- Mode: `docs-only implementation selection checkpoint`
- Source receipts:
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-IMPLEMENTATION-PLANNING-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-STACK-HELPER-CONTRACT-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-PROOF-PACKET-EXEMPLARS-2026-05-27.md`
  - `docs/ops/LOCAL-DATA-GATEWAY-DOCTRINE-CHECKPOINT-2026-05-27.md`
- Control-plane checkpoint: `main@c4afd47`

## Objective

Select the first real implementation slice for the Local Data Gateway helper and record why the other plausible options stay deferred.

This pass does not:

- implement `_stack` helper code
- emit packet artifacts
- send any packet downstream
- widen into lane-specific automation
- mutate runtime, schema, or app code
- touch `archive/`

## Root State

- branch: `main`
- HEAD: `c4afd47`
- status: clean except intentional untracked `archive/`

## Validation Posture

Executed:

- `python .\ops\validation\validate_stack.py`

Result:

- `critical=0 error=0 warning=307`

## Candidate Comparison

The smallest real first-slice choices were:

1. `packet field validator`
2. `dry-run packet emitter`
3. `manifest/schema linter`
4. `lane proof packager`

## Selection

Select exactly one first implementation slice:

- `packet field validator`

## Why `packet field validator` Wins

This is the smallest reusable helper slice because it proves the packet contract can be enforced without yet claiming:

- artifact emission
- lane-specific planning logic
- proof packaging
- quasi-export behavior disguised as dry-run output

What it proves cleanly:

- required fields can be checked consistently
- schema/version can fail closed
- exclusion-summary and proof-reference requirements can be enforced
- later emit/manifest lanes can depend on one shared contract gate

Why this is smaller than the manifest generator from the prior planning packet:

- validator logic is reusable across every later helper mode
- it avoids early coupling to artifact-path shape
- it avoids mixing field enforcement with planning-output generation
- it avoids building a half-emitter under the name of planning

## Deferred Alternatives

### `dry-run packet emitter`

Deferred because:

- too close to final packet emission
- risks producing de facto export artifacts before validator behavior is proven
- too easy to smuggle in hidden transformations under "preview" semantics

Reopen condition:

- only after the validator slice exists and proves contract-fail behavior on real exemplars

### `manifest/schema linter`

Deferred because:

- narrower than the validator in the wrong way
- checks shape quality, but not necessarily packet-contract semantics across required fields
- too likely to become a formatting or path linter instead of a contract gate

Reopen condition:

- only if later helper implementation proves a separate manifest-specific lint layer is still useful after validator coverage exists

### `lane proof packager`

Deferred because:

- too workflow-shaped for a first slice
- blends contract enforcement with receipt/output packaging
- risks lane-specific hardcoding and proof-template behavior before the core packet gate is stable

Reopen condition:

- only after validator plus a first local emit/prototype lane exist

## Smallest Safe Boundary

The first implementation package should therefore do only this:

- accept a local packet or candidate packet description
- enforce required Local Data Gateway contract fields
- return pass/fail plus missing/invalid field results
- stop before any manifest generation, packet write, or proof packaging

It must not:

- generate downstream-ready artifacts
- discover remote input sources
- send anything
- infer secrets
- construct prompts
- package lane-specific proof output

## Marker Recommendation

Keep `Local Data Gateway` flat at `10%` in this pass.

Why:

- this is a sharper implementation choice, not implementation proof
- no helper code exists yet
- no validator proof receipt exists yet

## Exact Next Package

`Local Data Gateway _stack packet field validator package 1`

Why:

- it is now the smallest reusable implementation boundary
- every later manifest, emit, and proof flow depends on it
- it avoids turning the first helper into a half-automation runner

## Rule

First implementation selection must prefer smallest reusable boundary over ambitious workflow coverage.

## Pattern

Doctrine -> contract -> exemplar proof -> helper boundary -> first implementation selection -> validator proof -> later emit/proof layers

## Failure Mode

Choosing an implementation that is already half-helper, half-automation runner.
