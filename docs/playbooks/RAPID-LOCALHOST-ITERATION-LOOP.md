# Rapid Localhost Iteration Loop

This workflow defines a reusable Atlas loop for fast UI iteration against a running local app.

It is stack-agnostic first:

- keep the local runtime alive
- take one small request at a time
- make the minimal patch
- rely on live reload, HMR, or Fast Refresh for immediate preview
- validate the affected screen first
- reserve broader screenshot sweeps and visual regression passes for checkpoints

Use this as the default Codex loop when a developer is already holding `localhost` or an emulator open and wants rapid iteration rather than a full end-to-end verification cycle after every micro-change.

Related Atlas entries:

- Local development and operator flow:
  - `docs/ops/ATLAS-SESSION-RUNBOOK.md`
  - `docs/ops/ATLAS-CODEX-CONTEXT-RUNBOOK.md`
- UI contracts and observation:
  - `docs/ops/ATLAS-UI-OBSERVATION.md`
  - `docs/ops/ATLAS-UI-DRIFT-VALIDATION.md`
  - `docs/ops/ATLAS-UI-VISUAL-PROOF.md`
- Automation policy:
  - `docs/ops/AUTOMATION-LEVELS.md`
- Named session bootstrap:
  - `docs/codex/FAST-ITERATION-LOOP.md`
  - `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`

## Name

Rapid Localhost Iteration Loop

## Intent

Document the fastest safe operator loop for small UI changes when the developer already has the local runtime running and can review each patch immediately.

The goal is to keep the live-preview loop instant tonight:

- patch only what the request requires
- preview the result through live reload instead of restarting the app
- use screenshot validation in affected-screen mode by default
- defer broader consistency sweeps until explicit checkpoint moments

## Named session bootstrap

Atlas binds this workflow to the named session mode:

- mode: `fast-iteration-loop`
- prompt doc: `docs/codex/FAST-ITERATION-LOOP.md`
- alias registry: `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`

Atlas also binds checkpoint validation to:

- mode: `checkpoint-sweep`
- prompt doc: `docs/codex/CHECKPOINT-SWEEP.md`
- alias registry: `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`

Atlas binds rapid-loop escalation to:

- mode: `structural-change-mode`
- prompt doc: `docs/codex/STRUCTURAL-CHANGE-MODE.md`
- alias registry: `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`

Atlas binds review-first work to:

- mode: `deep-review-mode`
- prompt doc: `docs/codex/DEEP-REVIEW-MODE.md`
- alias registry: `docs/registry/ATLAS-SESSION-MODE-REGISTRY.json`

This means the opener:

- `Open the fast iteration loop for fawxzzy-fitness.`

should resolve to:

- the target repo from `docs/registry/STACK-REPO-INVENTORY.json`
- this workflow doc
- the Codex bootstrap prompt
- the default localhost assumption
- the default affected-screen validation posture
- the expected first-response shape

And the opener:

- `Open checkpoint sweep mode for fawxzzy-fitness.`

should resolve to:

- the same workflow doc
- the checkpoint-sweep prompt doc
- the default related-flow checkpoint posture
- the expected checkpoint-first response shape

And the opener:

- `Open structural change mode for fawxzzy-fitness.`

should resolve to:

- the same workflow doc
- the structural-change-mode prompt doc
- a scope-based validation posture instead of affected-screen defaults
- an explicit response that rapid-loop assumptions no longer fit

And the opener:

- `Open deep review mode for fawxzzy-fitness.`

should resolve to:

- the same workflow doc
- the deep-review-mode prompt doc
- a findings-first review posture
- an explicit first response asking for the review target, branch, or diff surface

## When to use

- the developer already has `localhost`, a simulator, or a device session running
- the request is small, scoped, and screen-oriented
- HMR, Fast Refresh, or another live-reload path is already available
- the expected result can be checked on one current or affected screen
- the repo already has lightweight screenshots, visual checks, or manual preview habits that can be reused

## When not to use

- the change becomes structural, cross-cutting, schema-related, or routing-heavy
- the change requires coordinated edits across many screens, flows, or packages
- the current runtime is unstable enough that repeated restarts are the real bottleneck
- the work needs broad contract verification before any visual preview is trustworthy
- the screen or navigation state is not reproducible enough for a quick affected-screen check

## Prerequisites

- a persistent local runtime is already running
- the target route or screen is known
- the expected auth state and seed or mock state are known
- the repo's existing live-reload path is functioning
- the operator knows the lightest available validation method for the touched surface

If stack-root artifacts are captured during the loop, keep them disposable and path-safe:

- screenshots or captures -> `tmp/captures/`
- preview notes or scratch output -> `tmp/previews/`

## Resource posture

Rapid iteration should stay fast without leaving unnecessary browser or runtime load behind.

Default workstation posture:

- keep one maintained local runtime per active repo lane
- keep one maintained browser surface per active repo lane
- keep one active app tab for the target route when preview is needed
- do not accumulate duplicate localhost tabs, duplicate dev servers, or idle browser automation surfaces for the same repo

Idle posture:

- if the operator is reasoning, writing docs, or doing non-visual work, park the browser to `about:blank` or another neutral low-overhead surface
- reopen the app route only when visual verification, browser automation, or live interaction is actually needed
- if a second browser or server instance is temporarily needed for comparison, call that out explicitly and close or park it as soon as the comparison ends

Rule:

- before opening a new browser tab or starting a new local server for the same repo, first check whether the existing one is already healthy and reusable

## Core loop

1. Assume the developer keeps `localhost` or the emulator running unless the runtime is actually broken.
2. Take one small request at a time and restate the affected screen or flow.
3. Make the minimal patch that satisfies the request without widening scope.
4. Let HMR, Fast Refresh, or live reload update the preview in place.
5. Run the lightest appropriate validation for the changed surface.
6. Report exactly which screen or screens changed, what to verify visually, and whether the next step should stay in affected-screen mode or move to a checkpoint sweep.
7. Stay in rapid-loop mode until the request stops being a micro-change.

## Fast mode vs checkpoint mode

| Mode | Use when | Default validation | What to avoid |
| --- | --- | --- | --- |
| Fast mode | One small UI request, one current screen, one bounded patch | Level 0 or Level 1 | restarting the app, widening scope, running a full screenshot sweep |
| Checkpoint mode | a batch of micro-changes is done, a handoff is coming, or confidence needs a broader pass | Level 2 or Level 3 | pretending the app is fully checked after only one screen refresh |

Fast mode is the default.

Checkpoint mode is for moments such as:

- before handoff
- before commit or PR packaging
- after a cluster of related UI edits
- before asking another operator to continue
- when a screen-local change may have leaked into shared chrome or an adjacent flow

## Guardrails

- do not restart the dev server unless necessary
- do not keep animated app routes open when no live preview is being used
- do not open duplicate browser tabs or duplicate localhost servers for the same repo lane unless the comparison need is explicit
- do not widen scope during a rapid loop
- do not run full sweeps after every tiny change
- do not turn a local preview pass into a full automation project during Wave 1
- stop using rapid-loop mode when the change becomes structural, cross-cutting, schema-related, or routing-heavy

## Screen inventory

The screen inventory is the source of truth for screenshot sweeps and should stay repo-local when a project already owns one.

Atlas defines the reusable fields, not a forced implementation:

| Field | Purpose |
| --- | --- |
| `route_or_screen_name` | Stable route or screen name used in chat, docs, and screenshot tags |
| `path_or_navigation_entry_point` | URL path, deep link, or navigation sequence that opens the screen |
| `required_auth_state` | Required auth posture such as anonymous, signed-in, admin, or seeded account |
| `seed_or_mock_state` | Required mock, fixture, or seeded domain state |
| `canonical_viewport_or_device` | Canonical browser viewport, simulator, or device profile |
| `screenshot_tag_or_category` | Stable screenshot tag or category used for affected-screen checks and sweeps |

Inventory rule:

- every screen that participates in screenshot sweeps should have one stable inventory record
- the record should describe how to reach the screen, not just what the screen looks like
- checkpoint sweeps should iterate the inventory instead of relying on operator memory

## Validation ladder

### Level 0: current-screen visual spot check

Use when:

- the change is visibly isolated
- the developer already has the right screen open
- a quick human inspection is enough for the current patch

Expected output:

- confirm what changed
- list the two or three visual details to inspect

### Level 1: affected-screen screenshot refresh

Use when:

- the changed screen should be refreshed or recaptured
- a lightweight screenshot proof is helpful
- the change is still local enough that a broader sweep would be low-signal

Default posture:

- this is the default screenshot mode for rapid iteration

### Level 2: related-flow sweep

Use when:

- the edit touches shared chrome, reusable components, or adjacent states
- one screen is not enough, but the whole app still does not need a pass

Examples:

- entry screen plus success state
- tab surface plus one sibling state
- list view plus detail or composer state

### Level 3: full-app sweep at checkpoint

Use when:

- a checkpoint is reached
- a cluster of changes needs broader consistency confidence
- packaging, handoff, or a wider review is about to happen

Default posture:

- checkpoint only, not every iteration

## Stack adapters

### Web

Default loop:

- keep `localhost` running
- rely on HMR or live reload after each patch
- use the affected route as the first validation target
- use Playwright screenshots when the repo already has Playwright or when an ad hoc screenshot is the lightest available proof

Web adapter guidance:

- prefer route-scoped screenshot checks over full browser-suite runs during rapid iteration
- reserve full visual regression or multi-route sweeps for checkpoint mode
- if the repo already has deterministic screenshot tags or capture ids, reuse them instead of inventing a second naming system

### Mobile / Expo / React Native

Default loop:

- keep the simulator or device session running
- rely on Fast Refresh after each patch
- return the exact screen or navigation path the developer should inspect
- use existing screenshot, capture, or device-recording tooling before adding anything heavier

Mobile adapter guidance:

- prefer one stable emulator or device profile per swept screen
- use lightweight screen capture guidance in Wave 1 when no stronger harness already exists
- only move toward a wider screenshot harness in Wave 2 or when the repo already owns it

## Rule

Keep a persistent local runtime alive and optimize for minimal patches plus immediate preview.

## Pattern

Use two-speed validation plus one-browser runtime hygiene. Check the affected screen every iteration, run broader screenshot sweeps only at checkpoints, and park idle browser surfaces when preview is not active.

## Failure Mode

Running a full screenshot pass after every micro-change destroys iteration speed and creates low-signal work. Leaving duplicate animated localhost tabs and duplicate dev servers alive creates the same kind of waste at the workstation level.

## Example operator prompts

1. "Assume localhost/emulator is already running. Make the smallest possible change for this request, preserve architecture, and rely on live reload / Fast Refresh for preview."
2. "After the patch, tell me exactly which screen(s) changed, what I should visually verify, and whether affected-screen validation or a checkpoint sweep is appropriate."
3. "Use screenshot validation in affected-screen mode unless I explicitly ask for a broader sweep."
4. "If the request becomes structural or cross-cutting, stop treating it as a rapid-loop change and say so."

## Notes for future AIs

- treat this as a reusable Codex loop, not a one-project trick
- prefer project-native tooling over new dependencies
- keep Wave 1 validation manual or lightweight unless stronger automation already exists
- treat screenshot sweeps as inventory-driven checkpoint work, not default per-patch behavior
