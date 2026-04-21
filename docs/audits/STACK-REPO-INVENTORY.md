# Stack Repo Inventory

This inventory is the stack-level visibility surface for child repos under `repos/**`.

ATLAS root remains the control repo and coordination layer. Child repos remain independent git roots and are not vendored, mirrored, or installed into the root as a second source of truth.

Operational rule:

- `stack.yaml` declares topology
- `stack.lock.yaml` pins the working set
- this inventory publishes the visible topology for root status, chat, search, and future cockpit surfaces
- `repos/**` stays untracked by the root repo except for explicit stack-owned docs and audits outside that tree

## Summary

- Repo count: `11`
- Dirty repo count: `3`
- Release-eligible repo count: `6`
- Excluded surface count: `2`
- Stack manifest: `stack.yaml`
- Stack lock: `stack.lock.yaml`
- Inventory digest: `sha256:3fd220026373b19afc9739a002ebe46dfff80f26ce569c7c3db0ecba96e07110`

## Managed Repos

| Repo id | Path | Branch | Pinned commit | Current commit | Dirty | Trust | Release | Related initiatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _stack | repos/_stack | main | a91bfbddbb2a7e0f83983c52cac9f7027e18cc4c | a91bfbddbb2a7e0f83983c52cac9f7027e18cc4c | False | trusted | False | - |
| atlas | repos/fawxzzy-atlas | main | bd34580de7610d1ee00cdfc4593b69d05c84c0b0 | bd34580de7610d1ee00cdfc4593b69d05c84c0b0 | False | trusted | True | - |
| fitness | repos/fawxzzy-fitness | main | 911c4a936a17560d6843c661474b86ac4abcf11a | 911c4a936a17560d6843c661474b86ac4abcf11a | False | trusted | True | - |
| lifeline | repos/fawxzzy-lifeline | main | 327da3765b047698fbb7b551a6cb117412da83dc | 327da3765b047698fbb7b551a6cb117412da83dc | False | trusted | True | - |
| mazer | repos/fawxzzy-mazer | main | 847b3c61a51dc9fada74731304483b0ffab3e62a | 847b3c61a51dc9fada74731304483b0ffab3e62a | True | trusted | True | initiative:initiative-mazer-d2-learning-scorer |
| nat1-games | repos/Nat1-Games/nat1-games | main | ce9643465d69f76a46d92d0db6ed855d117e1bbd | ce9643465d69f76a46d92d0db6ed855d117e1bbd | True | trusted | False | - |
| playbook | repos/fawxzzy-playbook | main | 96acb49a67fcf650f0cd331f0c98b0966bac237d | 96acb49a67fcf650f0cd331f0c98b0966bac237d | False | trusted | True | - |
| playbook-demo | repos/playbook-demo/playbook-demo | main | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | 4d0444bcb14c3470fe0913a21c8739f0791a1827 | False | trusted | False | - |
| stack | . | main | a963848c9d60acc38e262d31dfe4916057f61351 | a963848c9d60acc38e262d31dfe4916057f61351 | True | trusted | False | - |
| stream | repos/fawxzzy-stream | codex/fstrm-wave3-surface-base | 2a03ef229bcb599855dcec31498cf8acfb6ee824 | 2a03ef229bcb599855dcec31498cf8acfb6ee824 | False | trusted | False | - |
| trove | repos/fawxzzy-trove | main | cec9c6ac2df8e23737a0c68a2d94c2090aa200e2 | cec9c6ac2df8e23737a0c68a2d94c2090aa200e2 | False | trusted | True | - |

## Excluded Surfaces

| Surface id | Path | Present | Trust | Release | Visibility | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| verta_core_archive | repos/Verta-Core.zip | True | untrusted | False | metadata_only | Token-bearing Verta archive remains quarantined private evidence and must stay out of release sets. |
| verta_core_checkout | repos/Verta-Core | True | untrusted | False | metadata_only | Token-bearing Verta checkout remains quarantined and untrusted until scrub and rotation are complete. |
