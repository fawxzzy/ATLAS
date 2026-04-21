# Stack Repo Inventory

This inventory is the stack-level visibility surface for child repos under `repos/**`.

ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.

Operational rule:

- `stack.yaml` declares topology
- `stack.lock.yaml` pins the working set
- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces
- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree

## Summary

- Repo count: `10`
- Dirty repo count: `4`
- Release-eligible repo count: `4`
- Excluded surface count: `2`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:0743964c70146b238d2586cee5ba90530fd2721930d5dcbdc628e13c8924a6d0`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | main | a91bfbddbb2a7e0f83983c52cac9f7027e18cc4c | a91bfbddbb2a7e0f83983c52cac9f7027e18cc4c | True | trusted | False | - |
| fitness | repos/fawxzzy-fitness | - | - | - | - | adjacent | False | - |
| lifeline | repos/fawxzzy-lifeline | main | 632075b1bb65aed59839cb1f9e205b826e41995d | 632075b1bb65aed59839cb1f9e205b826e41995d | False | trusted | True | - |
| mazer | repos/fawxzzy-mazer | main | 3f90b9d5b476642a565a91ea8619561356c52382 | 3f90b9d5b476642a565a91ea8619561356c52382 | False | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | main | ce9643465d69f76a46d92d0db6ed855d117e1bbd | ce9643465d69f76a46d92d0db6ed855d117e1bbd | True | trusted | False | - |
| playbook | repos/fawxzzy-playbook | main | 96acb49a67fcf650f0cd331f0c98b0966bac237d | 96acb49a67fcf650f0cd331f0c98b0966bac237d | True | trusted | True | - |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | cf2d9bf45ed7be820c85d45c124596e4479a8701 | cf2d9bf45ed7be820c85d45c124596e4479a8701 | True | trusted | False | - |
| stream | repos/fawxzzy-stream | codex/fstrm-wave3-surface-base | 2a03ef229bcb599855dcec31498cf8acfb6ee824 | 2a03ef229bcb599855dcec31498cf8acfb6ee824 | False | trusted | False | - |
| trove | repos/fawxzzy-trove | codex/trove-one-page-cleanup | 9387e0b44d12df89eba0a2f36187648ceb1aa829 | 9387e0b44d12df89eba0a2f36187648ceb1aa829 | False | trusted | True | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| verta_core_archive | repos/Verta-Core.zip | True | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | True | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
