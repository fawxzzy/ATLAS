# Atlas thread naming, Authorization, and context standard

## Visible standing titles

Atlas is assumed for governed stack tasks, so visible titles do not repeat the
word `ATLAS`.

| Logical role | Canonical visible title | Compatibility aliases |
| --- | --- | --- |
| `fawxzzy.questions` | `Questions` | `FAWXZZY QUESTIONS` |
| `manual.messages` | `Authorization` | `MANUAL MESSAGES` |
| `atlas.main` | `00 Main` | `ATLAS MAIN` |
| `atlas.release-control-plane` | `01 Release` | `ATLAS PR, CI & Release Control Plane`, `01 ATLAS RELEASE` |
| `atlas.workflow-architect` | `01 Architect` | `ATLAS WORKFLOW ARCHITECT`, `01 ATLAS ARCHITECT` |
| `atlas.workflow-operations` | `01 Ops` | `01 ATLAS OPS` |
| `atlas.inbox` | `Inbox` | `ATLAS INBOX` |

Logical role IDs and historical receipts do not change. Old titles remain
read-only aliases so recovery can recognize prior epochs without recreating
them.

`Questions` is the general-purpose operator conversation. Status and question
turns are read-only by default. An explicit bounded user request may authorize
work, but Questions does not silently absorb Main, Release, Authorization,
owner, provider, or production authority.

## Inter-thread transport labels

Every cross-thread message ends with:

```text
HANDOFF: YES|NO
RESPONSE_EXPECTED: YES|NO
RETURN_TO: <logical-role>/<stable-thread-id>|NONE
WAKE_CONDITION: <specific event>|NONE
```

Status and audit copies use `HANDOFF: NO` and `RESPONSE_EXPECTED: NO`. A true
handoff names the exact owner-return role and stable thread ID and receives one
correlated response. These labels describe transport intent; they do not grant
authority.

## Authorization learning

`Authorization` is the human authority surface. It should not repeatedly ask
Zac for materially identical low-risk decisions.

The canonical policy is
`docs/registry/ATLAS-AUTHORIZATION-POLICY.v1.json`.

A reusable learned authorization becomes active after two distinct matching
explicit approvals when:

- the action class is allowlisted;
- scope and constraints are materially identical;
- evidence and identities are fresh;
- the action is bounded, reversible, collision-free, and fully proven;
- no later denial or modification exists.

Every reuse emits an exact owner-first `AUTO_AUTHORIZED` decision receipt. It
does not broaden the action and does not execute it.

Two exact operator-granted rules are active immediately:

- one clean draft-to-ready transition from
  `OPEN_DRAFT_CLEAN_MERGEABLE_UNMERGED` after every declared identity, CI,
  review, graph, parity, worktree, mergeability, and policy gate passes;
- retirement of one exact accidental statusless GitHub deployment metadata
  record after proof of zero workflow, provider, Vercel, or production
  execution, using only its inactive remediation status, exact deletion, and
  absence readback.

The ready rule does not authorize merge. The metadata rule does not authorize
provider execution, deployment, production, source mutation, or deletion of
any other record.

Production, provider mutation, Supabase apply, Auth or live-data mutation,
secret or credential access, DNS, billing, purchase, destructive work, security
bypass, source retirement, and ownership or retention changes never become
learned automatic authority.

## Durable thread context

Every governed substantive turn must persist a compact context checkpoint to:

`runtime/atlas/thread-context/<thread-id>/`

The checkpoint records:

- stable thread and logical-role identity;
- visible title and lifecycle state;
- concise Done, Now, Next, decision, blocker, receipt, and source-reference
  lists;
- a canonical payload digest and immutable checkpoint ID.

It intentionally does not copy raw transcripts, secrets, tokens, private keys,
cookies, or environment values. Raw provider conversation history remains
source evidence; Atlas stores the durable operational context required to
rehydrate and continue correctly.

Checkpoint triggers:

1. after a substantive operator turn;
2. before a handoff or owner-return;
3. when a blocker or wake condition changes;
4. before terminal closeout or archival;
5. after restart recovery changes the active state.

An exact retry is idempotent. A changed checkpoint is append-only. The per-thread
`latest.json` and global `index.json` are derived read models. If persistence
fails, the task must report `CONTEXT_PERSISTENCE_BLOCKED` and must not claim a
terminal handoff or archive-safe state.

Use:

```text
python -m ops.atlas.persist_thread_context --thread-id <id> --role-id <role> --title <title> --state <state> --summary <summary> [section options]
```

## Failure modes

- Renaming a thread without updating recovery aliases causes a future title
  repair to revert it.
- Treating repeated approval as blanket autonomy can mutate production or
  sensitive external state without current intent.
- Saving only chat prose makes restart continuity dependent on one provider.
- Saving raw transcripts into Atlas can persist secrets or irrelevant personal
  data.

The standard therefore separates visible naming, exact learned authority, and
compact source-linked context persistence.
