# DiscordOS Project Board Admission Reconnaissance

## Decision

Classify all seven `project_forum_not_discovered` registry entries as
`needs-board-creation`. None maps safely to an existing forum, none currently
has an accepted owner card export, and none should be silently changed to not
applicable.

This is read-only admission evidence. It does not create forums, seed cards,
change retention, or move the active marker.

## Live inventory

Live Discord readback found `21` channels, `6` forums, and `336` unique active
or archived threads. The expected parent for governed project boards is
`Project Feedback Boards` with channel ID `1508057063874629684`.

| Project | Existing project forum | Canonical owner | Required source decision | Proposed forum |
|---|---|---|---|---|
| Atlas | None | Atlas root `stack` operator layer | Root-owned Atlas card export or explicit direct-Discord authority | `atlas` |
| DiscordOS | None | `repos/DiscordOS` board and Discord writer | Project-specific export separate from writer-role operations | `discordos` |
| Foundation | None | `repos/foundation` shared contract foundation | Foundation owner export/config | `foundation` |
| Lifeline | None | `repos/lifeline` local operator | Lifeline owner export/config | `lifeline` |
| Cortex | None | Root-owned `runtime/cortex` subsystem | Atlas-root export; unresolved remote Cortex is not authority | `cortex` |
| `_stack` | None | `repos/_stack` workflow operator | `_stack` owner export; keep distinct from Atlas | `stack` |
| Playbook | None | `repos/playbook` governance runtime | Playbook board-card export distinct from product/schema exports | `playbook` |

Each admission requires a serialized owner packet followed by one DiscordOS
single-writer creation/admission cluster. The cluster must:

1. create and read back the type-15 forum under the stable parent;
2. record its stable channel ID;
3. replace `unadmitted-v1` with the accepted owner source adapter;
4. enable the registry entry;
5. run paginated exact readback;
6. seed cards only through separately admitted owner records.

Forum creation and card seeding are different mutation classes. Creating an
empty admitted forum does not authorize inventing or copying cards.

## Rejected aliases

- Atlas-named cards currently on Fitness or Mazer remain owner-board cards;
  their titles do not create an Atlas board.
- `discordos-testing` is a Testing text channel, not a project forum.
- The archived `Discord Os` story-game thread is under the shared legacy
  feedback forum, not a DiscordOS project board.
- `mazer: multiplayer foundation` is a Mazer card, not the Foundation project.
- Playbook-named Mazer cards remain Mazer cards.
- `_stack` remains a separate project identity from Atlas.

## Additional mismatches

- `music-sesh` exists both as a governed project forum and as a text channel in
  the Music Sesh category. The type distinction is real, but the duplicate
  display name needs explicit operator documentation to prevent misrouting.
- The shared Completed forum is healthy for card consistency, but its live
  topic still says `Completed Fitness feedback cards`. The topic must be
  normalized to shared cross-project terminal storage through DiscordOS and
  read back exactly.
- `feedback-testing` is correctly excluded. `feedback-submission` is a text
  channel and must not be admitted as a board.
- No channel or category mojibake was observed. The archived `Discord Os`
  thread has casing/spacing drift but valid Unicode.

## Packet order

1. Complete the four-card Mazer normalization recovery.
2. Resolve the single Fitness owner-identity card.
3. Define Atlas and Cortex root-owned board exports.
4. Define `_stack`, Playbook, Foundation, Lifeline, and DiscordOS owner exports.
5. Create and admit the seven forums through one DiscordOS writer.
6. Normalize the shared Completed topic and document the Music Sesh channel
   type distinction.
7. Run the complete registry scan and ratchet only denominator-wide proof.

No repository, Git, Discord, Vercel, Supabase, or card state was mutated by
this reconnaissance.
