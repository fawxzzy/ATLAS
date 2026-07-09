# Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory implementation-readiness closeout and worker routing

- Date: `2026-07-09`
- Lane: `Cortex Dual-Mode Replacement Readiness`
- Mode: `ATLAS-root docs-only implementation-readiness closeout`
- Marker movement: none

## Objective

Close the remaining root-only design questions for the ChatGPT/Codex role-inventory helper and route one bounded implementation worker without widening authority beyond admitted root doctrine.

## Source Chain

The readiness decision rests on this durable chain:

- `docs/ops/CORTEX-DUAL-MODE-AND-SIMULATION-SUBSTRATE-MARKER-ADMISSION-2026-07-09.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-OPERATING-MODE-CONTRACT-FREEZE-2026-07-09.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-FIRST-IMPLEMENTATION-ADMISSION-2026-07-09.md`
- `docs/ops/CORTEX-DUAL-MODE-REPLACEMENT-READINESS-CHATGPT-CODEX-ROLE-INVENTORY-PROMPT-PACK-AND-WORKER-HANDOFF-CONTRACT-2026-07-09.md`
- `docs/memory/profiles/zachariah_workflow_profile.md`
- `docs/architecture/ATLAS-CORTEX-PLAYBOOK-CODEX.md`
- `docs/PLAYBOOK_NOTES.md`

## Readiness Decision

The ChatGPT/Codex role-inventory helper is `implementation_ready`.

Why:

- the operating model, admission, and prompt-pack are durable
- the worker objective is explicit
- the CLI contract is explicit
- the JSON contract is explicit
- the role schema is explicit enough for one bounded first implementation
- read-only and no-mutation guardrails are explicit
- authority denials are explicit
- allowed source surfaces are explicit
- forbidden surfaces are explicit
- output-path guards are explicit
- proof obligations are explicit
- no remaining root-only ambiguity blocks one bounded worker

## Question Closeout

1. Operating model, admission, and prompt-pack durable:
   - yes; all three are landed and indexed doctrine receipts on `main`
2. Worker objective explicit:
   - yes; classify current ChatGPT/Codex and adjacent operator interfaces into the dual-mode replacement model
3. CLI contract explicit:
   - yes; `python ops/cortex/chatgpt_codex_role_inventory.py [--json] [--source <root-relative-path>]... [--output <tmp/**.json>] [--strict]`
4. JSON output contract explicit:
   - yes; deterministic advisory JSON with source refs, role inventory, target buckets, denials, warnings, blockers, and safety status
5. Role-inventory schema explicit:
   - yes; role records are constrained to admitted role classes, target classes, and authority notes
6. Read-only and no-mutation guard explicit:
   - yes; no repo mutation, no marker movement, no owner-truth authority, no receipt authority, no workflow dispatch
7. Authority denials explicit:
   - yes; execution, approval, owner-truth, final-receipt, deploy, secret, transcript, workflow, `_stack`, repo, platform, owner-repo, protected-surface, and marker authority all stay denied
8. Allowed source surfaces explicit:
   - yes; only the admitted root-owned doctrine refs listed in the prompt-pack and readiness chain
9. Forbidden surfaces explicit:
   - yes; owner repos, hidden transcripts, secrets, `.env*`, deploy/platform surfaces, workflow surfaces, runtime-latest writeback, and protected roots remain forbidden
10. Output-path guards explicit:
    - yes; write output only to explicit root-relative `tmp/**.json`
11. Proof obligations explicit:
    - yes; focused helper tests, JSON smoke, safe tmp-output smoke, and root validation are all frozen
12. Remaining root-side ambiguity:
    - none that blocks a first bounded worker
13. Exact worker packet routed:
    - `Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory first-implementation worker packet 1`
14. Exact worker touch files:
    - `ops/cortex/chatgpt_codex_role_inventory.py`
    - `tests/test_cortex_chatgpt_codex_role_inventory.py`
15. Exact forbidden surfaces still in force:
    - owner repos
    - hidden transcript/chat/session state
    - secrets and `.env*`
    - Vercel, Supabase, deploy, workflow, and platform mutation surfaces
    - marker, receipt, Book, manifest, or selector writeback by the helper
16. Exact post-worker package:
    - `Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory first-implementation worker cluster reconciliation`
17. Marker movement:
    - none in this readiness receipt; `Cortex Dual-Mode Replacement Readiness` remains `0%`

## Exact Worker Objective

Implement one bounded, read-only helper that consumes only admitted root-owned doctrine surfaces, deterministically classifies current ChatGPT/Codex plus adjacent ATLAS/Playbook/Cortex role responsibilities, maps them into the future dual-mode replacement model, and preserves all authority denials.

## Exact Allowed Touch Surfaces

The worker may touch only:

- `ops/cortex/chatgpt_codex_role_inventory.py`
- `tests/test_cortex_chatgpt_codex_role_inventory.py`

Runtime proof may create temporary files only under:

- `tmp/cortex/`

## Exact Forbidden Authority

The worker must not:

- read hidden transcripts or session state
- read or print secrets
- read `.env*`
- touch owner repos
- touch deploy, workflow, Vercel, Supabase, or platform mutation surfaces
- stage, commit, or push
- emit final receipts
- move markers
- widen into simulation-role mapping

## Exact Post-Worker Package

If the worker lands cleanly, the exact next package is:

```text
Cortex Dual-Mode Replacement Readiness ChatGPT/Codex role inventory first-implementation worker cluster reconciliation
```

That reconciliation may add one bounded receipt plus receipt-index and selector mirror updates only after focused proof and validation succeed.

## Marker Decision

No marker moves.

`Cortex Dual-Mode Replacement Readiness` remains `0%`.
