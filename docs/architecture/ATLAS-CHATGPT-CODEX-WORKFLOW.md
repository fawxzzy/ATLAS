# The New Atlas Workflow Between You, ChatGPT, and Codex

## Executive summary

Your new workflow should be **native-first, Atlas-governed, and task-based**. In practice, that means you stop treating one giant chat as the execution engine, and you stop treating manual copy-paste as the handoff mechanism. Instead, you use ChatGPT as the command surface for strategy, decisions, scoping, and review; you use Codex as the execution surface for repository work, terminals, tests, worktrees, and parallel subagents; and you use Atlas as the governance layer that defines contracts, receipts, board state, marker truth, and cross-project rules.

The most important mental shift is this: **one project chat is not one long-running implementation thread**. Each distinct outcome should become its own Codex task, while durable guidance stays in `AGENTS.md` or checked-in documentation.

That means the future Atlas workflow is not "you write a huge prompt, paste it into Codex, wait, then paste the result back." It is closer to: **you choose the project and outcome, ChatGPT or an Atlas Control integration prepares the job, Codex runs it in the correct task/thread/worktree, and Atlas records the receipt and board consequences.**

The platform now provides real building blocks for that model: plugins and apps in ChatGPT and Codex, reusable skills, programmatic Codex thread start/read/list/resume, streamed turn events, integrated terminals, and subagents. What still does not exist as a single native primitive is a complete governed callback loop from an arbitrary chat into a chosen Codex thread and back into the exact originating conversation. That is why Atlas still needs a thin control-plane layer rather than only raw prompts.

## What changed in your operating model

Atlas is no longer just a cleanup project. It has evolved into the intended governance, truth, validation, routing, and receipt authority for the whole stack, while Playbook is the doctrine and evidence substrate, Contracts are the likely schema layer, and DiscordOS is the intended canonical board-and-card write surface.

So the old model looked like this:

```text
You think in ChatGPT
-> copy the prompt
-> paste into Codex
-> wait for Codex
-> copy the result back
-> manually interpret
-> manually update boards/docs/markers
```

The new model should look like this:

```text
You choose the project and outcome
-> ChatGPT scopes one bounded task
-> Atlas Control prepares a governed job
-> Codex runs the job in its own task/thread/worktree
-> tests, terminal output, and receipts are captured
-> Atlas records the result
-> board state and marker implications are handled through governed flows
```

That shift is consistent with the Atlas packet doctrine that chats are command surfaces, not durable truth, and that receipts, manifests, Git state, and validation outrank chat prose.

## Which surface does what

The cleanest way to think about the workflow is to separate **command**, **execution**, and **governance**.

Atlas remains the control plane. It decides how work is classified, what contracts or schemas apply, how results are receipted, what counts toward percent markers, and which project board events are legitimate.

ChatGPT project chats are the human-facing command surfaces. They are where you decide what to do next, translate product intent into bounded work, review results, and make acceptance decisions. They should not be treated as the durable system of record.

Codex is the execution environment. Each distinct outcome should get its own task; the task keeps its own transcript; and durable project instructions belong in `AGENTS.md` or checked-in documentation. In the desktop app, each task also has an integrated terminal scoped to its current project or worktree.

Plugins, apps, and skills are what remove the manual glue. They give you the right division of labor:

| Surface | What it is for |
| --- | --- |
| **ATLAS MAIN** | pinned anchor for cross-project architecture, governance, marker truth, receipts, routing policy |
| **Mazer chat** | product planning and bounded game/app tasks for Mazer |
| **Fitness chat** | product, launch, business, and bounded owner-lane tasks for Fitness |
| **Codex task** | actual code changes, tests, terminal work, subagents, diffs, commits |
| **Atlas Control plugin/app** | prepares governed jobs, launches or resumes Codex, records receipts, bridges board updates |
| **DiscordOS writer path** | applies board changes through one logical write path, not ad hoc multi-chat writes |

That final row matters because DiscordOS should stay a single logical writer rather than a multi-writer direct-edit surface.

### Standing Work conversations and launch trigger

The standing operator-facing command conversations are `ATLAS MAIN`, `Fitness`,
and `Mazer`. `ATLAS MAIN` is the pinned operational-preparation and stack
strategy anchor. `Fitness` is created with that exact display name after its
resume gates pass. The existing `Mazer` conversation is retained and receives
a current context-and-resume packet after its resume gates pass; it is not
replaced by a newly created conversation.

DiscordOS does not receive a standing Work conversation. It participates in
every governed workflow as the embedded board, card, publication, and readback
service.

The readiness closeout must prove the canonical Atlas writer and root truth,
the Work-to-Codex-to-`_stack` receipt loop, explicit runtime-policy receipts,
one governed DiscordOS board/publication canary, current project manifests and
Playbook profiles, a reconstructible Mazer live preview, healthy Fitness
validation, and removal of Fitness's direct Discord writer overlap.

Once `Fitness` exists and `Mazer` has been refreshed, their normal operating
loop is:

```text
inspect the current DiscordOS project board and cards
-> select, refine, create, or deduplicate the next card
-> launch one bounded Codex task through _stack
-> verify the implementation and produce a receipt
-> move, update, archive, remove, or create cards when evidence requires it
-> publish an event-specific Updates-channel message when policy says the
   result is externally meaningful
```

Card and update operations are part of task preflight and closeout, not a
separate DiscordOS chat handoff. Routine local commits and intermediate steps
remain durable execution events without automatically becoming public Update
posts.

The three standing conversations are persistent command surfaces. A bounded
Codex task is archived after its terminal result is accepted and its receipt is
durable. Active owner conversations are not archived. `ATLAS MAIN` may pause an
owner conversation for a serialized root-write window only through an explicit
checkpoint-and-resume contract that preserves all active work.

## What one real task now looks like

A task now starts in the relevant project chat, not in a generic global queue. You pick Atlas, Mazer, or Fitness depending on where the outcome lives. Atlas still handles root governance, cross-project architecture, and shared infrastructure. Mazer and Fitness handle owner-lane product work.

Once the outcome is identified, it becomes **one bounded task**. That matters because a card, packet, or deliverable can map to one execution thread instead of a mess of overlapping context.

Then Codex executes inside that task. Programmatic thread control is already available through thread start, resume, read, list, and turn-start primitives. Those are the exact building blocks Atlas needs to create a governed execution layer without pretending that visible chat windows are the system interface.

While the task runs, you can inspect it in the desktop app. The integrated terminal is task-scoped, and ChatGPT can read terminal output. If the work is decomposable, Codex and ChatGPT Work can run subagents in parallel and collect results into the main task. That is especially helpful for read-heavy exploration, test analysis, and review. Parallel write-heavy workflows still need non-overlapping ownership to avoid conflicts.

At the end, the outcome should not be "the last chat message." It should be a **receipt** that Atlas can trust: what task ran, what thread handled it, what files changed, what tests ran, what commit or PR exists, and what board or marker consequences follow.

## What is native now and what Atlas still has to own

OpenAI already gives you several native building blocks.

First, **task separation and shared project context** are native. Tasks stay separate, while durable instructions live in checked-in docs and `AGENTS.md`.

Second, **Codex thread lifecycle** is native. App Server and related thread controls can start new threads, resume stored ones, read stored ones without resuming them, list them with filters and pagination, and start turns against a target thread ID.

Third, **plugins, apps, and skills** are native. Plugins package reusable workflow capabilities. They can include apps and skills, and app-backed actions carry their own permissions and controls. Skills are reusable workflow units and can live in repositories under `.agents/skills` or be distributed via plugins.

Fourth, **permissions are native**. Codex now has built-in permission profiles such as `:read-only`, `:workspace`, and `:danger-full-access`. The permission-profile system also has a critical boundary: it should not be mixed with legacy sandbox configuration, because older sandbox settings can override the newer permission-profile model.

Fifth, **native task handoff is available in the desktop app**. A conversation
can be added to a local Codex task with its current context and project access.
The task is a separate transcript, not a continuously synchronized copy of the
strategy conversation. This removes the large prompt-copy step while receipts
remain the durable reverse handoff.

What is **not** fully native yet, at least not in one fully documented end-to-end surface, is the whole Atlas workflow by itself.

There is still no single documented primitive that says: "from any normal project chat, submit governed work to a specific long-lived Codex service thread, get a public run ID, and have the result automatically posted back into the exact source conversation."

That is why Atlas still needs a **thin ledger** and an **Atlas Control plugin/app**. The ledger does not need to be a second execution runtime. It needs to own governed identities and state that the native platform does not yet fully close for you, such as:

- card ID <-> job ID <-> Codex thread ID <-> turn ID
- lease ownership for conflicting operations like board writes
- receipt storage and marker evidence
- expected board version and idempotency state
- the human review decision that turns "Codex finished something" into "Atlas accepts this as proof"

This is also why the SQLite queue idea stays frozen as a proposal until native platform capabilities are fully accounted for. It may still become useful, but it should not be treated as the selected transport by default.

The model catalog exposed by the desktop app is not proof that the `_stack`
Codex executable supports the same model. Every governed launch must
capability-detect the execution host and record the requested and effective
model, reasoning, speed, permissions, and Codex version. Unsupported models
must fail before mutation or fall back only through an explicit, receipted
policy.

## What this means for Atlas, Mazer, Fitness, and DiscordOS

For **Atlas**, this means you stay in Atlas when the work is about architecture, contracts, Playbook, control-plane policy, shared validation, markers, or cross-project routing. Atlas decides the rules and records the receipts; it does not become the place where every product implementation conversation goes to die.

For **Mazer**, this means you work out of the Mazer chat for product work, feature planning, visual bugs, runtime issues, and parity work. When code execution is needed, the work becomes a bounded Codex task scoped to the Mazer repo or worktree. Atlas still governs the contracts and board expectations, but Mazer keeps product ownership.

For **Fitness**, the same rule applies. Fitness stays the place for launch decisions, product planning, business constraints, and owner-lane implementation work. Atlas governs shared standards, receipts, and marker truth, but Fitness owns Fitness decisions.

For **DiscordOS**, the most important nuance is that it should be treated as an embedded service path rather than a manual destination. You should not need to open a dedicated DiscordOS conversation every time you complete a task. Instead, Atlas Control or a governed board-mutation path should call the DiscordOS write surface on your behalf. That still preserves the requirement for one logical writer and for live sync and readback, while removing the need to operate DiscordOS as a separate day-to-day command surface.

For **GitHub**, local Git remains the immediate engineering truth while GitHub
is the first-class remote collaboration, backup, CI, review, release, and
delivery surface. Atlas must continuously reconcile repository inventory,
remote parity, branches, pull requests, Actions, releases, dependency and
security signals, and stale resources. `_stack` produces verified delivery
events; DiscordOS presents policy-selected updates and alerts.

For **canonical Atlas writes**, the Codex worker edits admitted files but never
stages or commits them. The parent `_stack` canonical writer owns exact staging,
verification, spec-to-diff, commit creation, and landing. Generated inventories
and locks must also state their snapshot semantics so their own commit does not
create endless self-referential drift.

## What you will actually do day to day

On a normal day, your workflow should feel much simpler than it does now.

You start in the right project chat. If you are making a cross-project decision, changing Atlas infrastructure, or defining contracts, you start in `ATLAS MAIN`. If you are building Mazer, you start in the existing Mazer conversation. If you are working on Fitness, you start in Fitness. The chat's job is to capture intent, break the work into one bounded outcome, and point at the right repo context.

If the task needs reusable workflow logic, ChatGPT should invoke an Atlas skill or plugin rather than expecting you to handcraft a giant prompt every time. That is the right home for something like an **Atlas Control** capability that can prepare jobs, invoke Codex, and coordinate app-backed systems.

Then Codex handles the actual implementation task. It runs in its own task/thread/worktree, uses the project's terminal, can delegate read-heavy subtasks to subagents when appropriate, and persists task history that can later be resumed or read programmatically.

When the task finishes, you do not treat the last assistant paragraph as the deliverable. You review the outcome, accept or reject it, and Atlas records the governed result. If the work affects cards or project state, a single logical board writer applies the update. If the work teaches Atlas something reusable, that rule or pattern is promoted into Playbook, Contracts, or checked-in instructions.

When the receipt is durable and the result is accepted, archive the bounded
task. Keep `ATLAS MAIN`, `Fitness`, and the existing `Mazer` conversation as the
long-lived operator surfaces.

So the practical answer is this:

**No, the target workflow is not continued manual copy-paste.**

But **also no**, the complete future state is not "one ordinary chat magically controls any Codex conversation with perfect native callback routing."

The actual near-term workflow is:

```text
You operate from project chats
-> Atlas or skills or plugins prepare governed work
-> Codex executes in bounded tasks
-> Atlas records receipts and truth
-> board updates happen through one governed write path
```

That is the model that fits both the official product surfaces now available and the governance rules already locked into Atlas.
