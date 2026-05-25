# Stack Lock Decision - DiscordOS Feedback Adapter Stub - 2026-05-25

## Decision

- `stack.lock.yaml` was refreshed during this package.

## Reason

- `discordos` is already tracked in the governed stack lock
- the new DiscordOS commit for the feedback adapter stub package changed `repos/DiscordOS` HEAD
- the lockfile needed to be regenerated so validation could reflect the current governed repo state

## Refresh Command

```text
python .\ops\stack\generate_lockfile.py
```

## What Changed

- `stack.lock.yaml#discordos` now points at the current DiscordOS adapter-stub commit at refresh time
- the canonical generator also refreshed the ATLAS component entry because the root worktree was dirty while the receipt lane was still open

## Package Reference

- `docs/ops/DISCORD-OS-FEEDBACK-ADAPTER-STUB-PACKAGE-1-2026-05-25.md`

## Validation Result

After the lock refresh:

- `critical=0`
- `error=0`
- `warning=289`
