# Atlas Post-Merge Review Follow-ups

## Decision

Preserve two actionable post-merge review findings discovered during the
2026-07-14 Playbook CI and `_stack` Atlas Contracts v2 reconciliation. The
merged delivery evidence remains valid; these are bounded follow-up defects,
not reasons to reopen or repeat the completed execution clusters.

Both repairs remain owner-repository work. Atlas records and routes them but
does not patch either repository from the root writer.

## Follow-up registry

| ID | Owner | Severity | Status | Finding |
| --- | --- | --- | --- | --- |
| `PB-DEMO-ALLOWLIST-001` | Playbook | P2 | Ready when the Playbook writer slot is available | The demo managed-docs compatibility helper may write paths that the demo refresh allowlist rejects. |
| `STACK-RUNTIME-REQUEST-001` | `_stack` | P2 | Ready when the `_stack` writer slot is available | Contracts v2 can report a non-default requested approval policy as `never`. |

## PB-DEMO-ALLOWLIST-001

### Evidence

- `repos/playbook/scripts/demo-managed-docs-compat.mjs` always writes
  `docs/commands/README.md` and may update
  `docs/PLAYBOOK_PRODUCT_ROADMAP.md`.
- `repos/playbook/scripts/demo-refresh.mjs` omits both paths from
  `REQUIRED_ALLOWED_PATHS`.
- Playbook pull request `#23` merged as
  `374aed60a62ff43cdf4293ee2875de9b8eb52a1c`.
- The manually dispatched post-merge `demo-integration` workflow run
  `29376621748` succeeded. This confirms current fixture health but does not
  eliminate the conditional allowlist defect.

### Required outcome

1. Make every path the compatibility helper can intentionally mutate an
   explicit, deterministic member of the demo refresh mutation contract.
2. Add a regression fixture in which the commands README differs and the
   roadmap lacks one managed revision layer.
3. Prove the intended files are accepted while an unrelated file still fails
   closed.
4. Run the complete Playbook verification and the demo integration workflow.
5. Return a receipt that links the repair commit, pull request, workflow run,
   and final remote parity.

## STACK-RUNTIME-REQUEST-001

### Evidence

- `repos/_stack/ops/codex/CodexRunner.Common.ps1` stores `approval` only under
  the resolved runtime-policy layer.
- `repos/_stack/ops/codex/AtlasContractsV2Producer.ps1` serializes both the
  requested and resolved layers through the same converter and defaults a
  missing layer-local approval value to `never`.
- `_stack` pull request `#5` merged as
  `554aae99196abc31910ea250e269cc307c48b042` and the full `_stack`
  verification passed.

### Required outcome

1. Preserve the explicitly requested approval policy in the requested runtime
   layer or provide a request-aware conversion path with equivalent truth.
2. Keep the resolved approval policy separately receipted.
3. Add a non-default approval fixture that proves requested and resolved values
   cannot be silently conflated.
4. Run the complete `_stack` verification and Contracts v2 producer tests.
5. Return a receipt that links the repair commit, pull request, checks, and
   final remote parity.

## Routing constraints

- Do not combine these defects into one cross-repository task or pull request.
- Do not launch either repair while its owner repository already has a writer.
- Use GPT-5.6 Sol with high reasoning or above, full local access, network
  access, live web search, and no approval prompts.
- Push and pull-request authority is granted only inside the admitted owner
  packet. Production deployment and Discord mutation are not implied.
- After each repair, reconcile the owner board card, work journal, GitHub
  checks, remote parity, and post-work receipt through their authoritative
  owners.

## Marker treatment

These findings do not advance the DiscordOS Cross-Project Board Integrity and
Lifecycle Repair marker and do not alter the fixed denominator of that marker.
They are durable owner-side reliability work discovered during reconciliation.
