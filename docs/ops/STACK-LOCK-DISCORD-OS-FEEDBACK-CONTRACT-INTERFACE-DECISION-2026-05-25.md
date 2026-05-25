# Stack Lock Decision - DiscordOS Feedback Contract Interface - 2026-05-25

## Decision

- `stack.lock.yaml` was refreshed during this package.

## Reason

- `discordos` is already tracked in the governed stack lock
- the new DiscordOS commit for the feedback contract interface package changed `repos/DiscordOS` HEAD
- root validation reported a blocking lock mismatch until the lockfile was regenerated

## Refresh Command

```text
python .\ops\stack\generate_lockfile.py
```

## What Changed

- `stack.lock.yaml#discordos` now points at the current DiscordOS interface-scaffold commit at refresh time
- the stack component entry was also refreshed by the canonical generator during the same pass because the ATLAS worktree was dirty while the receipt lane was still open

## Package Reference

- `docs/ops/DISCORD-OS-FEEDBACK-CONTRACT-INTERFACE-PACKAGE-1-2026-05-25.md`

## Validation Result

After the lock refresh:

- `critical=0`
- `error=0`
- `warning=289`
