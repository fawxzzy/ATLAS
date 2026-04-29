# Fawxzzy Fitness Live UI Handoff

Date:
- 2026-04-26

Workspace:
- `repos/fawxzzy-fitness`

Scope:
- live mobile UI refinement
- history exercises
- history sessions
- history session detail
- add exercise
- exercise info
- auth screens
- account/settings

Working rules carried through this thread:
- do not close the user's personal browser windows
- live browser work is allowed only in isolated browser sessions launched by Codex
- do not create divergent cardio vs strength layouts if a shared component should own it
- inspect divergent branches before token or class tweaking
- keep edits scoped
- prefer real signed-in local app screenshots over mocks or mirror screens

Current runtime state:
- single healthy app runtime on `http://127.0.0.1:3000`
- current dev launcher: `repos/fawxzzy-fitness/scripts/dev.mjs`
- current server logs:
  - `runtime/fitness/app-3000.out.log`
  - `runtime/fitness/app-3000.err.log`
- the stale-chunk failure that kept recurring on this repo is:
  - `Cannot find module './1682.js'` from `.next/server/webpack-runtime.js`
- when that happens, the successful recovery path in this thread was:
  1. stop only the process listening on `127.0.0.1:3000`
  2. delete `repos/fawxzzy-fitness/.next`
  3. relaunch only one server with `node scripts/dev.mjs --hostname 127.0.0.1 --port 3000`

Useful auth/session artifacts:
- current real-user session file:
  - `runtime/fitness/live-user-auth-current-project.json`
- current live session detail id used at the end of this thread:
  - `0513ce97-1dd7-40a6-ba64-41a77ddae450`

Most relevant screenshots from the end of this thread:
- history session detail baseline:
  - `tmp/screens/live-refine-20260426/history-session-detail-live-current-v19-baseline.png`
- history session detail expanded:
  - `tmp/screens/live-refine-20260426/history-session-detail-live-current-v20-expanded.png`
- earlier valid current route screenshot before the last detail pass:
  - `tmp/screens/live-refine-20260426/history-session-detail-live-current-v8-3000.png`

What was changed on the history session detail screen:
- header now uses the shared detailed-session title logic and drops the date
- summary card now reuses the detailed sessions-card display logic instead of the old one-off summary header
- extra spacing was added between the bar/title area and the stats blocks
- zero-set exercises are hidden
- exercise row summary label changed from `Latest` to `Best`
- `Logged exercises` title and subtitle were removed
- detail exercise chevron layout now uses the shared overlay/meta pattern so the right rail stops stealing width

Primary files changed in the last stretch:
- `repos/fawxzzy-fitness/src/app/history/[sessionId]/LogAuditClient.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistorySessionCard.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistoryDetailExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/app/dev/history-session-detail-live/page.tsx`

Important preview-route fixes that matter if the next thread continues screenshot work:
- `src/app/dev/history-session-detail-live/page.tsx`
  - stopped using `getExerciseNameMap()` because that path redirected through `requireUser()`
  - replaced it with direct exercise-name loading from the same Supabase client used for the rest of the preview route
  - wrapped capture mode in `BottomActionsProvider` so `HistoryLogPageClient -> LogAuditClient` stops crashing on `useBottomActions must be used within BottomActionsProvider`

Useful exact commands from this thread:
- lint the final detail-screen files:
  - `node scripts/next-cli.mjs lint --file src/app/history/[sessionId]/LogAuditClient.tsx --file src/components/history/HistorySessionCard.tsx --file src/components/history/HistoryDetailExerciseCard.tsx --file src/app/dev/history-session-detail-live/page.tsx`
- direct live-data preview route used for the final detail screenshots:
  - `/dev/history-session-detail-live?capture=1&sessionId=0513ce97-1dd7-40a6-ba64-41a77ddae450&userId=af46ac5a-f12b-4d69-874f-22c9c56d29dc`

Known caveat at handoff time:
- the screen code is in better shape than the screenshot pipeline
- the detail screenshots that finally worked came from the live-data preview route, not the direct signed-in browser route
- the real route and the preview route both depend on the `:3000` runtime staying free of the stale `.next` chunk issue
- the repo worktree contains many unrelated modifications from the broader thread; do not revert unrelated changes

Best next step:
- continue refining the history session detail screen from the baseline and expanded screenshots above
- if live capture breaks again, fix the single `:3000` runtime first instead of starting additional servers or killing broad browser processes

## Thread lessons added on 2026-04-28

### Preferred live screenshot workflow now

1. keep one healthy local runtime only:
   - `http://127.0.0.1:3000`
2. refresh and reuse the real signed-in auth artifact:
   - `runtime/fitness/live-user-auth-current-project.json`
3. prefer the real signed-in route over a preview route when the real route is stable
4. use the repo runner first for standard captures:
   - `node scripts/qa/cdp-edge.mjs <capture-config.json>`
5. if the UI state is hard to reach or the runner keeps clicking the wrong thing, switch to a direct Playwright script that:
   - calls `ensureFreshSessionArtifactFile()`
   - builds cookies with `buildCookiesFromArtifactSession()`
   - strips `path` when `url` exists before `addCookies()`
   - drives the exact state and writes the screenshot directly

### Capture paths that proved reliable

- active proof shots during the thread:
  - `repos/fawxzzy-fitness/.codex/qa/captures/`
- handoff-grade thread references:
  - `tmp/screens/live-refine-20260426/`

### Why direct Playwright mattered

- `cdp-edge.mjs` is good for:
  - route loads
  - auth bootstrap
  - deterministic one- or two-click captures
- direct Playwright was needed when:
  - repeated button labels made text selectors ambiguous
  - the screen auto-entered a deeper state than expected
  - we needed to inspect the live DOM to see the real click order

### Logged-session screen behavior that affected capture order

- on the final edit flow for the logged-session screen:
  - tapping `Edit` entered the edit surface
  - tapping an exercise card could move directly into the set-focused state depending on the current structure
- because of that, never assume the old click order still works; inspect the live buttons if a capture lands in the wrong state

### Production deploy lessons from this thread

- the final successful deploy command was:
  - `vercel deploy --prod --yes`
- two unrelated build blockers had to be fixed before the UI changes could ship:
  - `src/components/ExercisePicker.tsx`
    - shared goal-validation branch needed a real `GoalValidationResult` type so Vercel stopped inferring `requiredFields` as plain `string[]`
  - `src/app/dev/stretch-session-preview/page.tsx`
    - needed `BottomActionsProvider` because that preview tree used bottom actions and broke production build during prerender
- takeaway:
  - when prod deploy fails, inspect the actual build log first
  - do not assume the current screen patch is the deploy blocker

### Stable commands worth reusing

- lint the main logged-session edit/detail files:
  - `node scripts/next-cli.mjs lint --file src/app/history/[sessionId]/LogAuditClient.tsx --file src/components/ui/workout-entry/LoggedSetSummaryRow.tsx --file src/components/session/SessionExerciseBlock.tsx`
- standard runner capture:
  - `node scripts/qa/cdp-edge.mjs tmp/captures/<capture-config>.json`
- direct signed-in Playwright fallback:
  - run an inline Node script from `repos/fawxzzy-fitness` that imports:
    - `./scripts/qa/fitness-auth-artifact.mjs`
    - `playwright`
  - bootstrap cookies from the auth artifact and shoot the exact target state

### Guardrails that should stay true in future live UI threads

- do not close the user’s personal browser windows
- use isolated browser sessions only
- prefer shared component reuse over one-off visual forks
- if a route or preview uses bottom actions, verify it is inside `BottomActionsProvider`
- if the screenshot pipeline lies, prove the state with direct DOM inspection before changing UI code again

## 2026-04-28 additions

Scope expanded in the later thread:
- live history sessions screen
- compact session-card layout
- Today-screen header parity
- stale-browser and stale-screenshot debugging

### Working model for live UI edits

- Prefer the real local dev app on `http://127.0.0.1:3000`.
- Prefer live-data preview routes over fixture-only screens when the user is asking about the current signed-in experience.
- Keep one runtime on `:3000`; do not stack multiple dev servers while debugging screenshot mismatches.
- Use isolated automation or capture sessions. Do not touch the user's personal browser windows just to gather proof.
- When layout parity is the goal, inspect the sibling screen that already has the desired pattern before changing card logic. In this thread, the History compact-row metadata had to follow the Today header order instead of inventing a new sequence.

### Canonical live history sessions route

Use the live-data history sessions route instead of fixture boards when validating compact rows:

- `/dev/history-sessions-live?userId=<target-user-id>`

Useful variants:

- full live route with normal shell:
  - `/dev/history-sessions-live?userId=<target-user-id>`
- capture-focused route:
  - `/dev/history-sessions-live?userId=<target-user-id>&capture=1`

Rules:

- resolve the target `userId` locally at run time; do not commit a personal email or hardcode a fresh user id into new stack docs unless there is a clear operational reason
- use the real user data path when the bug depends on truncation, wrapping, date tags, or session counts
- use fixture routes only when deterministic owner-side regression is the goal rather than live-user debugging

### Screenshot capture workflow that actually worked

The reliable local flow for live screenshots was:

1. verify the runtime is the one you expect through `/api/app-version`
2. open the live-data preview route, not a mock or fixture route
3. capture at mobile width with an explicit JSON spec passed to `scripts/qa/cdp-edge.mjs`
4. write the screenshot to a unique filename every time
5. if the image will be shown in chat, never reuse the previous image path

Recommended capture spec shape:

```json
{
  "url": "http://127.0.0.1:3000/dev/history-sessions-live?userId=<target-user-id>&cb=<timestamp>",
  "width": 390,
  "height": 844,
  "mobile": true,
  "deviceScaleFactor": 1,
  "initialWaitMs": 1800,
  "navigationTimeoutMs": 30000,
  "networkIdleTimeoutMs": 30000,
  "actions": [
    {
      "type": "waitForSelector",
      "selector": "[data-history-card='session']",
      "timeoutMs": 30000
    }
  ],
  "finalWaitMs": 1500,
  "outPath": "tmp/captures/history-real-account-capture-<timestamp>.png"
}
```

Command:

```powershell
node scripts/qa/cdp-edge.mjs tmp/captures/history-real-account-capture-<timestamp>.json
```

Artifact placement rule:

- preferred screenshot lane: `tmp/captures/**`
- preferred temporary JSON spec lane: `tmp/captures/**`
- do not commit generated screenshots or capture specs

### Failure modes we hit and how to avoid them

#### 1. Stale client bundle made the user see old UI

What happened:

- source edits were correct
- the running app was current
- the user's browser still rendered older history code

What fixed it in local dev:

- unregister service workers in dev
- clear CacheStorage in dev
- reload once per build id in dev

The repo-side fix landed in:

- `repos/fawxzzy-fitness/src/components/ServiceWorkerBootstrap.tsx`

Operational rule:

- if the user says the screen still looks old after a confirmed rebuild, suspect stale client state before assuming the last screenshot is authoritative

#### 2. Reusing the same screenshot path made chat appear stale

What happened:

- a newly captured image was written over the old filename
- the chat surface continued showing the old bitmap

Rule:

- always emit a new screenshot filename for each recapture shown to the user
- add a cache-busting query value to the captured URL when needed

#### 3. Fixture routes hid the real truncation and spacing bug

What happened:

- fixture or synthetic rows did not reflect the real account's title lengths and wrapping behavior
- the UI looked different once the live account route was captured

Rule:

- if the bug is about line wrapping, right-rail anchoring, row height, search counts, or header counts, capture the live-data preview route first

#### 4. Freehand layout rewrites drifted away from the product pattern

What happened:

- the compact history row was changed without first matching the Today pattern that already existed elsewhere in the app

Rule:

- when a screen should "look like" another screen, inspect and reuse the shared order, separators, and component patterns before changing layout logic

### Current high-signal checks for history-session UI work

- title above the search bar is absent on the history sessions route
- compact session rows stay on one line unless they truly run out of width
- metadata order matches Today: routine, weekday, then day name
- the date tag and chevron live on a stable right rail
- the screenshot shown to the user comes from a fresh path, not a reused image filename

## Later thread outcomes added on 2026-04-28

### Logged-session detail screen patterns that are now intentional

- non-edit and edit mode share one structural model instead of diverging:
  - header and sticky top controls
  - lower-half viewport shell
  - pinned focused card at the top of that shell
  - scrolling middle content only
  - bottom content docked close to the bottom action bar

## Account/settings screen state at thread close

Primary files:
- `repos/fawxzzy-fitness/src/app/settings/page.tsx`
- `repos/fawxzzy-fitness/src/components/settings/SettingsAccordionClient.tsx`
- `repos/fawxzzy-fitness/src/components/settings/SettingsHeaderIdentity.tsx`
- `repos/fawxzzy-fitness/src/components/settings/AccountSettingsForm.tsx`
- `repos/fawxzzy-fitness/src/components/settings/GlassEffectsSettings.tsx`
- `repos/fawxzzy-fitness/src/components/settings/LegacyMigrationSettings.tsx`

Current intended mobile model:
- one shared outer settings card
- one expanded section at a time
- three disclosure sections in this order:
  1. `Data & Account`
  2. `Preferences`
  3. `Import Legacy Data`
- when one section expands, the others leave the visible stack so the open section owns the screen

Current header behavior:
- top header no longer shows a `Signed in` tag
- header identity is centered
- it should render:
  - `username | email` when available
  - `email` only otherwise
- current fallback chain:
  1. auth metadata username/display_name
  2. remembered login display name
  3. email local-part fallback

Current settings-section behavior:
- collapsed cards:
  - centered titles
  - bottom-right chevrons
  - no helper subtitle text
- expanded cards:
  - no extra inner border shell
  - keep only the outer card border
  - inner controls sit directly on the shared screen surface

Current legacy import behavior:
- no `Available` tag in the collapsed card
- no raw snapshot JSON in the normal mobile flow
- one button runs export -> import -> parity once the required credentials are present
- button is centered and not forced full width

Current save-button rules:
- `Save account` and `Save preferences` stay greyed out until there is a real unsaved change
- after a successful save, the baseline resets so the button greys out again

Known capture behavior after the accordion refactor:
- the page currently opens with `Data & Account` focused by default
- to capture the fully collapsed view, click `Data & Account` once after load
- to capture other expanded states reliably, start from a fresh page load, collapse the default section if needed, then open the target section

Useful final screenshots:
- collapsed:
  - `repos/fawxzzy-fitness/.codex/qa/captures/settings-live-390-v24-collapsed-header-username-email.png`
- account expanded:
  - `repos/fawxzzy-fitness/.codex/qa/captures/settings-live-390-v18-account-expanded-tight.png`
- preferences expanded:
  - `repos/fawxzzy-fitness/.codex/qa/captures/settings-live-390-v20-preferences-expanded-tight.png`
- legacy expanded:
  - `repos/fawxzzy-fitness/.codex/qa/captures/settings-live-390-v22-legacy-button-centered-actual.png`
- final header fallback proof:
  - `repos/fawxzzy-fitness/.codex/qa/captures/settings-live-390-v26-header-final-fallback.png`
- when an exercise is focused:
  - the focused exercise becomes the pinned top card of the lower viewport shell
  - only the set list or set-edit content should scroll
- when a set is focused in edit mode:
  - the set card becomes the pinned top card
  - the horizontal measurement rail becomes the active middle content
  - notes are displaced by set-edit controls instead of competing for height

### Logged-session truth rules that changed in code

- the top stats summary now derives exercise and set counts from the logged exercises visible on the screen, not from the original routine/day template
- zero-set exercises stay hidden from the logged-session detail surface
- set summaries and best-set summaries now share the same measurement-summary helpers
- stat values that contain multiple parts should render green-dot separators through the shared metric renderer

### Shared styling and component reuse that landed

- reusable floating-label field shell:
  - `repos/fawxzzy-fitness/src/components/ui/LabeledEditorField.tsx`
  - owns the border, focus state, and title cutout mask
  - used by the logged-session edit fields instead of ad hoc wrappers
- reusable field-control class exported from the same file:
  - `labeledEditorFieldControlClassName`
- set cards across logged-session edit and non-edit now share the same shell treatment:
  - `SET_CARD_SHELL_CLASS_NAME` in `src/app/history/[sessionId]/LogAuditClient.tsx`
- delete actions for exercise and set rows are aligned to the same shared bottom-action danger pattern instead of one-off red buttons
- compact history detail exercise cards now place the sets count on the same trailing rail as the chevron instead of inside the title row

### Header and compact-row lessons that should carry forward

- if a compact history header centers the title, the title node itself must be structured for centered layout; toggling `align=\"center\"` alone is not enough
- header descender clipping was caused by `leading-[1]`; raising the line-height fixed the bottom clipping on letters like `g`
- compact right-rail metadata should be treated as part of the trailing cluster when it visually belongs with the chevron

### Add-exercise screen convergence lessons

- current-session add-exercise and edit-day add-exercise should keep sharing the same layout path
- the configure-goal dock can hold:
  - shared preview summary
  - shared horizontal measurement rail
  - shared bottom action composition
- only the measurement lane should visually clip or hint horizontal overflow; the dock itself should stay width-contained
- the exercise list body should own the remaining screen height rather than being sized by a fixed visible-card count

### Screenshot and runtime debugging lessons added after more passes

- if direct Playwright fails because bundled Chromium is missing, use `channel: 'msedge'` in the isolated automation session
- if screenshots suddenly show blank body text or a Next dev error overlay, verify the live route itself before assuming the UI patch failed
- a successful restart can still lie if the old `:3000` process never died; confirm the listener PID actually changed before trusting a recapture
- if the dev server reports:
  - `Cannot find module './1682.js'`
  - or static chunk 404s under `/_next/static/chunks/...`
  treat it as the same stale `.next` runtime failure and run the one-server recovery path again

### Main files that now carry the current truth

- `repos/fawxzzy-fitness/src/app/history/[sessionId]/LogAuditClient.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistoryDetailExerciseCard.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistorySessionCard.tsx`
- `repos/fawxzzy-fitness/src/components/history/HistoryShared.tsx`
- `repos/fawxzzy-fitness/src/components/ui/LabeledEditorField.tsx`
- `repos/fawxzzy-fitness/src/components/ui/MetricItem.tsx`
- `repos/fawxzzy-fitness/src/components/ui/workout-entry/LoggedSetSummaryRow.tsx`
- `repos/fawxzzy-fitness/src/components/session/SessionExerciseBlock.tsx`
- `repos/fawxzzy-fitness/src/components/ExercisePicker.tsx`

### Operational note for future Codex threads

- if a later thread continues this UI lane, start by reading this handoff plus `docs/PLAYBOOK_NOTES.md`
- prefer updating the shared primitive or shared row component first before tweaking a local call site
- if the user says a screenshot does not reflect the requested edit, suspect one of:
  - stale chat image path reuse
  - stale `.next` runtime
  - the right component branch was not the one actually rendering the screen
