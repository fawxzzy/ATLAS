# GitHub Control-Plane Live DiscordOS Projection Ratchet - 2026-07-14

## Decision

The `discordos_projection` unit is complete. GitHub Control-Plane Integration moves from `7 / 8 = 87.5%` to `8 / 8 = 100%`.

This is an implementation-readiness ratchet, not a claim that volatile GitHub state is permanently healthy. The daily read-only GitHub watch remains active, and all cleanup candidates remain held behind separate mutation authority.

## Live Proof

One short-lived `atlas.approval-record.v2` authorized exactly one external mutation:

- target: `discordos:updates`
- scope: `publish_projection:ghp_add3230d0a45ab8462308dd3d6dfe62402f4ba905a7a81f731a1986987075a02`
- constraints: `single-writer`, `exact-readback`, `no-mentions`
- automatic retry: disabled

The application preserved the complete identity chain:

| Identity | Value |
|---|---|
| GitHub event | `ghr_395799bd49db4eaba279f3120f0d884afe8f30f6d635d6e23c321e34009fbafd` |
| Atlas admission | `gha_40a043521f2dd2a7dbd5e91790e28eb787227c1c61bb0bd2fad0e80bfd7f7a97` |
| Atlas projection | `ghp_add3230d0a45ab8462308dd3d6dfe62402f4ba905a7a81f731a1986987075a02` |
| DiscordOS application | `dga_c9586fb6a138383f23cd7eb5d26814d74a36ba7bdd2cdb24f076992550f682e1` |
| Application receipt | `dpa_2f61e2415f62bc0eb5f5023b64a579cf` |
| Discord message | `1526435158406856787` |

The terminal application receipt reports:

- `status=sent_verified`
- `ok=true`
- `sends_messages=true`
- `readback.ok=true`
- `readback.exactMatch=true`
- identical requested and observed message identifiers
- identical requested and observed body digest `a5aa3dee3458d7131b2f447a011b0f54d009151a34b6787d1e32bb73c7727a47`
- no mention parsing
- `writes_board=false`
- `writes_storage=false`
- `replay.state=none`

The local machine-readable evidence is retained under `tmp/github-projection-canary-2026-07-13/`, including the no-send readiness receipt and the terminal live application receipt. It is runtime evidence and is not promoted as a committed secret-bearing artifact. The committed receipt records only non-secret identities, digests, and outcomes.

## Authority Boundaries

- DiscordOS remained the single logical Discord writer.
- `_stack` and Atlas supplied facts, admission, and projection identities; they did not format or send the Discord message directly.
- The canary wrote no board state and no storage state.
- No deployment, GitHub mutation, Supabase mutation, or owner-repository mutation occurred.
- The approval expired after the bounded live action and does not authorize replay.
- No branch or worktree cleanup authority changed.

## Marker Basis

The accepted denominator remains eight binary units:

1. `repository_inventory`
2. `parity_projection`
3. `actions_projection`
4. `open_work_hygiene`
5. `release_security_projection`
6. `cleanup_governance`
7. `stack_event_correlation`
8. `discordos_projection`

All eight now have accepted evidence. `Atlas Full-System Re-evaluation` remains `50%`; this ratchet does not satisfy its separate closing-audit gate.

## Ongoing Operations

The desktop automation `Atlas GitHub Control-Plane Watch` remains the read-only freshness monitor. Future parity, workflow, release, security, PR, issue, or endpoint-state changes are health deltas, not reasons to rewrite the completed implementation denominator unless the control-plane contract itself regresses.
