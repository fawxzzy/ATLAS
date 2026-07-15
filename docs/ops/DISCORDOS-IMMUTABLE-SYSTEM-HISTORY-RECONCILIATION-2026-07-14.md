# DiscordOS Immutable System History Reconciliation

## Decision

Accept the Unicode prevention and full live scan as closure of the superseded-text proof gap. Retain malformed Discord channel-name-change events on already-superseded archived threads as immutable platform history rather than actionable card drift.

This does not close the cross-project board-integrity marker. Seven required project-board classes remain blocked, and denominator-wide lifecycle, reaction, movement, formatting, and recurring-scan proof is still incomplete.

## Prevention merges

| Pull request | Merge | Outcome |
| --- | --- | --- |
| DiscordOS `#76` | `98846c2f5a855a30b5c129233a19339817f2c0a4` | Added fatal UTF-8 boundaries, NFC normalization, deterministic corruption classification, bounded diagnostic recovery, exact Unicode write/readback checks, and complete current/superseded history scanning. |
| DiscordOS `#77` | `fecdaabe56aa9fdf753b0732488e1a80d845ad31` | Separated non-deletable Discord system history from actionable board drift and prevented impossible cleanup retries. |

Both pull requests passed full DiscordOS verification. Their GitHub checks were green, they had no unresolved review threads, and their Vercel preview checks succeeded. No production deployment was requested or performed.

## Live scan

The post-policy registry scan covered all five enabled boards and every current or superseded record exposed by the registry:

| Metric | Result |
| --- | ---: |
| Registered boards | 12 |
| Enabled boards | 5 |
| Required blocked boards | 7 |
| Current cards | 288 |
| Superseded records | 49 |
| Healthy current cards | 136 |
| Structurally drifted current cards | 152 |
| Duplicate stable identities | 0 |
| Current text-integrity findings | 0 |
| Actionable text-integrity findings | 0 |
| Immutable system-history findings | 124 |
| Affected immutable messages | 74 |
| Affected superseded threads | 49 |

All 124 retained findings are journal-history spans on already-superseded records:

- Fitness active-board history: 100 spans;
- shared Completed-board history: 24 spans;
- validated Windows-1252/UTF-8 patterns: 99 spans;
- non-round-trippable historical fragments: 25 spans.

No current title, starter, or journal contains a classified text-integrity finding.

Primary evidence:

- `runtime/board-integrity/text-integrity-post-merge-2026-07-14-pr76/board-card-consistency.json`;
- `runtime/board-integrity/text-integrity-post-merge-2026-07-14-pr76/encoding-cleanup-dry-run.json`;
- `runtime/board-integrity/text-integrity-post-merge-2026-07-14-pr76/encoding-cleanup-apply.json`; and
- `runtime/board-integrity/text-integrity-post-merge-2026-07-14-pr76/board-card-consistency-post-policy.json`.

## Repair disposition

The exact dry run matched all 74 scanner-identified messages, with zero missing, extra, protected, or user-authored records. Every target was a Discord `CHANNEL_NAME_CHANGE` system event (`type 4`).

One guarded cleanup attempt changed zero messages. Discord documents `CHANNEL_NAME_CHANGE` messages as non-deletable and API error `50021` as `Cannot execute action on a system message`:

- <https://docs.discord.com/developers/resources/message>
- <https://docs.discord.com/developers/topics/opcodes-and-status-codes>

Deleting the 49 superseded threads would destroy retained provenance and break replacement links. That destructive workaround is rejected. The accepted disposition is:

1. preserve the clean replacement/current card;
2. keep the malformed system event only inside the archived superseded thread;
3. continue reporting exact immutable evidence;
4. exclude immutable platform history from actionable drift; and
5. keep the same finding actionable when it appears on a current thread.

## Reusable governance

**RULE - Platform Mutability Precedes Repair Admission**

Before admitting a cleanup action, classify the target resource against the platform's mutability contract. A bot-authored appearance does not prove a Discord system event is bot-mutable.

**PATTERN - Immutable Evidence With Actionable Projection**

Preserve immutable historical evidence, expose it in receipts, and project health from the mutable current surface instead of hiding evidence or blocking forever on an impossible action.

**FAILURE MODE - Bot-Owned Means Deletable**

Discord system events can carry the bot identity while remaining non-deletable. Treating author identity as deletion authority causes deterministic failed repair loops.

## Marker treatment

The superseded all-surface scan gap is closed, but unit 8 remains partial because seven required board classes have not been admitted and seeded. The fixed marker remains `0 / 10` (`0%`).
