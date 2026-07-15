# DiscordOS Text Integrity Reconnaissance

## Decision

Admit a DiscordOS code repair for deterministic Unicode integrity scanning and
write prevention. Do not admit a live text-repair batch yet.

The current evidence distinguishes live Discord text from locally corrupted
display or serialization. Node-parsed UTF-8 evidence retains valid `U+2014`
em dashes, while a Windows PowerShell read/write hop can display or persist the
same bytes as `U+00E2 U+20AC U+201D` (`â€”`). A console-rendered string is not
sufficient evidence that the live Discord title is corrupt.

## Quantified state

The read-only audit covered `334` enabled-board records:

| Board | Total rows | Current | Superseded |
| --- | ---: | ---: | ---: |
| Shared legacy intake | 1 | 1 | 0 |
| Fitness | 61 | 36 | 25 |
| Mazer | 65 | 65 | 0 |
| Music Sesh | 151 | 151 | 0 |
| Shared Completed | 56 | 32 | 24 |
| **Total** | **334** | **285** | **49** |

For all `285` current cards, the audit found zero instances in titles,
starters, or paginated journals of:

- single-pass UTF-8/Windows-1252 corruption;
- known double-pass corruption;
- `U+FFFD` replacement characters; or
- C1 control characters associated with incorrect code-page decoding.

Four live titles contain intentional valid `U+2014` em dashes. They must be
preserved. The `49` superseded records remain a proof gap because the current
registry returns before inspecting their complete starter and history text.

## Root causes

1. Windows PowerShell default text decoding can corrupt otherwise valid UTF-8
   evidence. File reads and writes must declare UTF-8 explicitly and validate
   it fatally.
2. DiscordOS `repairMojibakeText` uses lossy punctuation substitution and can
   convert valid em or en dashes into ASCII ` - `.
3. Hard-coded pattern replacement is not a safe general decoder and can
   misclassify legitimate non-ASCII text.
4. Superseded records exit the consistency scan before title, starter, and
   paginated-history text integrity is measured.
5. Existing cleanup utilities inspect only the first 100 messages and rely on
   deletion or replacement-thread behavior that is outside the accepted
   update-in-place policy.

## Canonical policy

- Normalize Unicode text to NFC and encode source, JSON, hashing, and Discord
  boundaries as UTF-8.
- Preserve valid typography and non-English names.
- Use ASCII only where a protocol contract explicitly requires it.
- Repair only when Windows-1252 byte reconstruction produces valid UTF-8,
  round-trips exactly, and strictly reduces a deterministic corruption score.
- Permit at most two validated recovery passes.
- Fail closed on ambiguous text, `U+FFFD`, unpaired surrogates, invalid UTF-8,
  or non-round-trippable input.
- Never repeatedly replace punctuation as a substitute for validated decoding.

## Admitted code packet

The smallest safe DiscordOS pull request should:

1. Add `scripts/discordos-board-text-integrity.js` for fatal UTF-8 input, NFC
   normalization, corruption classification, validated single/double recovery,
   spans, and code-point evidence.
2. Update `scripts/discordos-board-card-journal.js` to preserve valid Unicode
   and reject corrupt rendered starter or journal output.
3. Update `scripts/discordos-board-card-consistency.js` to inspect superseded
   rows and emit exact counts by board, surface, pattern, thread ID, and message
   ID across complete pagination.
4. Update `scripts/discordos-board-card-contract.js` to block corrupt proposed
   writes and verify exact Unicode readback.
5. Update `scripts/discordos-board-card-migration-plan.js` to validate owner
   exports and live titles without lossy transliteration.

Tests must cover valid em/en dashes, accented names, single and double
corruption, ambiguous recovery rejection, invalid UTF-8, every event field,
PR `#70` long-body compaction compatibility, all three readback surfaces,
superseded records, histories beyond 100 messages, and exact code-point
readback.

## Live-repair gate

After the code pull request is merged, run one serialized, read-only scan over
all `334` records and complete histories. A live update-in-place repair is
admitted only for exact message or thread IDs with:

- raw before hashes and code points;
- deterministic proposed text and hashes;
- bot-owned mutable messages;
- current-hash preconditions;
- batches of at most ten thread IDs; and
- exact post-write text, NFC, hash, identity, and unchanged-surface readback.

Do not delete, recreate, clone, archive, or replace threads. User-authored or
immutable system messages require explicit operator disposition.

## Marker treatment

Unit 8 of `DiscordOS Cross-Project Board Integrity & Lifecycle Repair` remains
incomplete. Closing proof requires the merged prevention code, all-surface
coverage for the `49` superseded records, complete pagination, exact counts,
valid typography preservation, and exact before/after evidence for any
non-empty live repair set.
