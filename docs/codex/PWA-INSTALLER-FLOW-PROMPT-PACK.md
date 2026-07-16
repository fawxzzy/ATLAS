# PWA Installer Flow Prompt Pack

This document packages the Atlas-level Codex prompts for the cross-repo PWA installer and access flow work.

Use this when the operator wants copy-paste prompts that can be run lane-by-lane without assuming the target repos have already been inspected.

Atlas repo ids used here follow `stack.yaml` and `docs/registry/STACK-REPO-INVENTORY.json`:

- `fitness` -> `repos/fawxzzy-fitness`
- `trove` -> `repos/trove`

`trove` is the stable logical ID for the FawxzzyWeb launcher app in this prompt pack.

## Purpose

Provide a single orchestrator prompt plus bounded worker prompts for:

- repo discovery and lane planning
- shared platform and install detection
- Fitness app gating
- FawxzzyWeb launcher handoff
- screenshot and QA coverage
- Playbook extraction after implementation exists

## Scope

This is a stack-level coordination artifact under `docs/codex/`.

It does not claim that the target repos are mounted, healthy, or ready.

Each prompt is discovery-first and must inspect the target repo before editing.

## ATLAS workflow response contract

For ATLAS workflow use, every Codex-originated response produced from this prompt pack should begin with:

```text
CODEX-MSG-ID: CODEX-YYYY-MM-DD-###
```

If the exact ordinal is uncertain after a restart, emit a fresh unique suffix and keep the `CODEX-YYYY-MM-DD-` prefix.

Treat the origin ID as provenance metadata only. It does not replace receipts, SHAs, validation snapshots, or authority boundaries.

Canonical receipt:

- `docs/ops/MESSAGE-ORIGIN-ID-WORKFLOW-RULE-2026-06-09.md`

## Execution order

Run these in order:

1. master orchestrator prompt
2. Wave 1 only if a real shared package already exists or both apps clearly share code
3. Wave 2A in `fitness`
4. Wave 2B in `trove`
5. Wave 3 after both app lanes land
6. Playbook extraction after the implementation is real

## Hard constraints

Paste this block into every worker prompt.

```md
Hard constraints
- Do not invent repo structure; discover it first.
- Do not change unrelated routes, auth architecture, or styling systems.
- Do not label cross-origin navigation as "Install".
- Do not use localStorage or sessionStorage as the source of truth for installed state.
- Do not bypass iOS gating with query params in production.
- Do not block manifest, service worker, icons, auth callbacks, health routes, or public/legal/install help routes.
- If a required shared package does not already exist, prefer a local implementation with an extractable API over creating new cross-repo coupling.
- Keep browser install dismissal state session-scoped only.
- Use runtime standalone detection as the source of truth for installed access on iOS.
- Use "Share, then Add to Home Screen" wording unless the app already standardizes more specific Apple copy.
- Begin every Codex-originated ATLAS workflow response with `CODEX-MSG-ID: CODEX-YYYY-MM-DD-###`.
```

## Master orchestrator prompt

Paste this first at Atlas level.

```md
Objective
Map the Atlas-level repos and docs involved in the PWA installer flow, then produce an implementation plan and worker split before any repo code is changed.

Context
We are implementing a platform-specific PWA installer and access flow across multiple apps, starting with:
- `fitness` -> `repos/fawxzzy-fitness`
- `trove` -> `repos/trove`

FawxzzyWeb is the launcher and bio-link app. Fitness is the target app.

Desired product flow
1. FawxzzyWeb is commonly opened from TikTok or other social bio links.
2. If an iOS user opens a target app in an in-app browser, show a forced "Open in Safari" gate.
3. That gate must include:
   - direct explanation
   - canonical app URL
   - copy-to-clipboard button
   - simple manual steps
4. If an iOS user is in Safari but has not launched from the Home Screen, show a forced "Add to Home Screen" gate.
5. Once the app is launched from the iOS Home Screen or standalone mode, allow normal app access and login.
6. For Android and other non-iOS platforms, do not hard-lock access. Show a native install button only when the current app and browser expose `beforeinstallprompt`.
7. FawxzzyWeb must route users into each target app's own install or open flow. Do not attempt to trigger a PWA install prompt for a different origin from FawxzzyWeb.

Platform rules
- Do not attempt to force-open Safari.
- Do not attempt to force iOS Add to Home Screen.
- Treat "installed" as runtime standalone state, not storage state.
- Use Safari instruction copy that is resilient to iOS wording changes.
- Prefer a canonical public install landing route such as `/install` if the app already has one or can add one safely.

Tasks
1. Confirm whether `fitness` and `trove` are present, mounted, and editable.
2. Identify any shared package, shared UI library, or shared platform utility already used by both apps.
3. Identify frameworks and routing:
   - Next.js, React, Vite, Remix, other
   - App Router or Pages Router if Next.js
   - manifest and service worker setup
   - auth and login boundaries
4. Determine whether Fitness and FawxzzyWeb are same-origin or different-origin.
5. Decide where shared platform detection should live:
   - preferred: existing shared package
   - fallback: local utility in Fitness first with an extractable API
6. Produce a worker split with exact ownership and no overlapping write set.
7. Produce a screenshot and manual QA plan.

Required inspection targets
- package.json files
- app or router layout files
- manifest files
- service worker or PWA config
- auth and login route boundaries
- shared packages
- docs or playbook notes relevant to install flow

Verification constraints
- Do not make broad unrelated changes.
- Do not rewrite routing architecture.
- Confirm repo-local lint, typecheck, test, and build commands.
- Confirm how screenshots would be generated if implementation proceeds.

Documentation output
Recommend a repo-local doc target such as `docs/install-flow.md` and a manual QA doc such as `docs/manual-install-qa.md` if those lanes do not already exist.

Deliverable
Return:
1. repo and app map
2. same-origin or different-origin finding
3. exact worker lanes to run next
4. files or file groups each worker should modify
5. blockers or missing prerequisites
6. whether Wave 1 is justified or should be skipped
```

## Wave 1 prompt

Run this only if the orchestrator finds a real shared package or clearly shared code surface.

```md
Objective
Create a reusable PWA install and platform detection module that can power Fitness and FawxzzyWeb without coupling to app-specific UI.

Paste the shared hard-constraints block here before proceeding.

Implementation plan
1. Add a small platform and install utility module with framework-agnostic functions.
2. Export a normalized install context object.
3. Add typed support for `beforeinstallprompt` because it is not fully standardized in the TypeScript DOM API.
4. Add a clipboard helper for copying canonical install URLs.
5. Add tests for iOS, Android, standalone, Safari, in-app browser, and unsupported browser cases.
6. Avoid changing app screens in this worker.

Required API
- `getInstallContext(options)`
  Returns:
  - `platform`: `"ios" | "android" | "desktop" | "unknown"`
  - `browserKind`: `"safari" | "chrome" | "edge" | "firefox" | "inApp" | "unknown"`
  - `isIOS`
  - `isAndroid`
  - `isInAppBrowser`
  - `isSafari`
  - `isStandalone`
  - `isBrowserTab`
  - `canUseNativeInstallPrompt`
  - `shouldShowIOSOpenInSafariGate`
  - `shouldShowIOSAddToHomeScreenGate`
  - `shouldAllowAppAccess`
- `createPWAInstallController()`
  Handles:
  - listening for `beforeinstallprompt`
  - storing the deferred prompt
  - exposing `canPromptInstall`
  - `promptInstall()`
  - handling `appinstalled`
  - clearing prompt after use
- `copyInstallUrl(url)`
  Uses `navigator.clipboard` when available and provides a safe fallback.

Detection rules
1. iOS detection must cover modern iPadOS Safari cases where the platform appears Mac-like but `maxTouchPoints` indicates touch iPad.
2. Standalone detection must use:
   - `window.matchMedia("(display-mode: standalone)")`
   - `window.matchMedia("(display-mode: fullscreen)")` if appropriate
   - `navigator.standalone === true` for iOS Safari
3. In-app browser detection should be heuristic and documented.
   Include common tokens:
   - TikTok
   - musical_ly
   - Instagram
   - FBAN
   - FBAV
   - Messenger
   - Twitter/X
   - Line
   - LinkedInApp
   - Pinterest
   - Snapchat
   - Discord
   - WhatsApp
   - Telegram
   - MicroMessenger
4. Safari detection must avoid misclassifying CriOS, FxiOS, EdgiOS, and OPiOS as Safari.
5. Production behavior must not rely on query params or storage to pretend the app is installed.
6. Optional test-only overrides are allowed only outside production, for example:
   - `?installContext=ios-inapp`
   - `?installContext=ios-safari`
   - `?installContext=ios-standalone`
   - `?installContext=android`
   - `?installContext=desktop`

Files to modify
- shared platform or utility package files if present
- otherwise stop and report that Wave 1 should be skipped in favor of a local utility in Wave 2A
- tests near the utility
- local docs for detection limitations if the repo already has a docs lane

Verification
- run unit tests
- run typecheck
- run lint
- report exact commands used

Documentation
Update or create a repo-local doc such as `docs/install-platform-detection.md` with:
- detection limitations
- known in-app browser tokens
- why iOS uses a guided flow
- why non-iOS install depends on `beforeinstallprompt`

Deliverable
A PR-sized change containing only the shared installer and platform module, tests, and docs. Include screenshots only if a visual demo page already exists.
```

## Wave 2A prompt

Run this in `fitness` only.

```md
Objective
Implement the Fitness app access and install flow:
- iOS in-app browser: forced "Open in Safari" gate
- iOS Safari browser, not standalone: forced "Add to Home Screen" gate
- iOS standalone or Home Screen: normal app access and login
- Android and non-iOS: no hard lock; show native install button only when supported

Paste the shared hard-constraints block here before proceeding.

Implementation plan
1. Locate the Fitness app root layout, app shell, and auth boundary.
2. Add an `InstallGate` component that wraps only user-facing app routes.
3. Do not block:
   - manifest
   - service worker
   - static assets
   - health checks
   - auth callback routes if blocking would break login
   - public, legal, help, or install routes
4. Use the shared install and platform module if it already exists.
5. Otherwise implement a local utility with the same extractable API.
6. Add two iOS gate screens:
   - `IOSOpenInSafariGate`
   - `IOSAddToHomeScreenGate`
7. Add a non-iOS PWA install button or banner only when the current app can actually prompt install.
8. Add test-only context overrides for screenshots outside production only.
9. Preserve existing app architecture, styling system, auth flow, and routing conventions.

Behavior matrix
1. iOS + known in-app browser + not standalone:
   - block app access
   - show an "Open in Safari" gate
   - show the canonical Fitness URL from config or env, not a tracking-heavy current URL
   - show copy-to-clipboard
   - explain: "Copy this link, open Safari, paste it, then continue."
2. iOS + Safari browser + not standalone:
   - block app access
   - show an "Add to Home Screen" gate
   - instruct: Share, then Add to Home Screen, then open the app from the Home Screen
   - include copy URL as a fallback
3. iOS + standalone or Home Screen:
   - allow normal app access and login
4. Android or non-iOS + `beforeinstallprompt` available:
   - allow normal app access
   - show an "Install app" button or banner
   - clicking the button calls `promptInstall()`
   - hide the button after accepted install or `appinstalled`
   - if dismissed, do not spam; respect dismissal for the current session only
5. Android or non-iOS + `beforeinstallprompt` unavailable:
   - allow normal app access
   - do not show fake native install UI

Manifest and PWA readiness
Verify the app has:
- valid manifest
- name and short_name
- icons at installable sizes
- `display: standalone`
- `start_url`
- existing theme and background colors if the app already defines them
- a service worker if the app's installability depends on one

Do not overhaul the PWA setup unless the current implementation is clearly incomplete and required for installability.

Suggested component structure
- `InstallGate`
- `IOSOpenInSafariGate`
- `IOSAddToHomeScreenGate`
- `InstallAppButton`
- `usePWAInstallPrompt`
- `installContext` utility

Verification
1. run lint
2. run typecheck
3. run tests
4. run build
5. generate screenshots for:
   - iOS in-app browser gate
   - iOS Safari Add to Home Screen gate
   - iOS standalone allowed state
   - Android or non-iOS install button visible with mocked `beforeinstallprompt`
   - Android or non-iOS normal access when the prompt is unavailable
6. report exact commands used
7. list any manual QA steps Codex cannot verify

Documentation
Update a repo-local doc such as `docs/install-flow.md` with:
- Fitness-specific route behavior
- iOS gate screenshots
- Android install behavior
- test-only override instructions
- manual QA checklist

Deliverable
A PR-sized Fitness implementation with no FawxzzyWeb changes.
```

## Wave 2B prompt

Run this in `trove` only.

```md
Objective
Update FawxzzyWeb so its launcher buttons route users into the correct platform-specific install or open flow, especially from TikTok and other social in-app browsers.

Core rule
FawxzzyWeb must not attempt to install a different-origin PWA directly. If a target app is on a different origin, FawxzzyWeb opens the target app's install route and lets that app own `beforeinstallprompt` and iOS gating.

Paste the shared hard-constraints block here before proceeding.

Implementation plan
1. Locate the FawxzzyWeb launcher page and the app card or button rendering path.
2. Add or update an app registry or config with:
   - app id
   - display name
   - canonical URL
   - install URL
   - open URL
   - same-origin or different-origin classification
   - platform install behavior
3. Add platform-aware button labels:
   - iOS: `Open`
   - Android or non-iOS same-origin installable app: `Install`
   - Android or non-iOS different-origin target app: `Open installer`
   - fallback: `Open`
4. If FawxzzyWeb itself is opened inside an iOS in-app browser, prefer a clear "copy link and open in Safari" experience before sending the user deeper into the flow.
5. Preserve current FawxzzyWeb design and navigation architecture.

Button behavior details
- Do not label a button `Install` if it only navigates to another origin.
- Use `Install` only when the current page can actually trigger a native PWA install prompt.
- Use `Open` or `Open installer` when routing to the target app.
- Keep copy short and user-friendly.

Target handoff behavior
- iOS in-app browser:
  - either show FawxzzyWeb's own copy-link and open-in-Safari gate for the target install URL
  - or navigate to the target app's public install route where that app handles the gate
- iOS Safari:
  - open the target app's public install route
- iOS standalone:
  - open the target app normally
- Android or non-iOS:
  - open the target app's install route unless the current page can truly install the same-origin target app

Suggested data shape
Use the repo's existing config style if present. Otherwise something like:

{
  id: "fitness",
  name: "Fitness",
  canonicalUrl: "https://example.com",
  installUrl: "https://example.com/install",
  openUrl: "https://example.com",
  supportsPWA: true
}

Verification
1. run lint
2. run typecheck
3. run tests
4. run build
5. generate screenshots for:
   - FawxzzyWeb in an iOS in-app browser
   - FawxzzyWeb in iOS Safari
   - FawxzzyWeb on Android or non-iOS
   - Fitness card and button labels in each context
6. verify there are no route loops between FawxzzyWeb and Fitness
7. verify copy-to-clipboard behavior where present

Documentation
Update a repo-local doc such as `docs/install-flow.md` with:
- FawxzzyWeb-to-Fitness handoff
- same-origin versus different-origin rule
- TikTok and social bio-link behavior
- manual QA steps

Deliverable
A PR-sized FawxzzyWeb implementation with no Fitness changes.
```

## Wave 3 prompt

Run this after Waves 2A and 2B land.

```md
Objective
Add verification coverage and screenshot artifacts for the full installer and access flow across Fitness and FawxzzyWeb.

Paste the shared hard-constraints block here before proceeding.

Implementation plan
1. Locate the existing Playwright, Cypress, or browser test setup in each repo.
2. Prefer Playwright if available.
3. Add test-only install context overrides if not already present.
4. Add screenshot coverage for each platform state.
5. For Android or non-iOS native install behavior, verify app logic with a mocked `beforeinstallprompt` event. Do not claim this proves the real OS install prompt works.
6. Add a manual QA checklist for real-device validation.

Required screenshots
Fitness:
1. iOS in-app browser gate
2. iOS Safari Add to Home Screen gate
3. iOS standalone or Home Screen allowed state
4. Android or non-iOS install button visible
5. Android or non-iOS normal access when native prompt is unavailable

FawxzzyWeb:
1. iOS in-app browser launcher behavior
2. iOS Safari launcher behavior
3. Android or non-iOS launcher behavior
4. Fitness card or button handoff

Testing approach
- use mobile viewport presets
- use realistic user agents:
  - iPhone Safari
  - iPhone TikTok or similar in-app browser
  - Android Chrome
  - desktop Chrome
- mock display mode and standalone state where automation cannot truly install to the Home Screen
- mock `beforeinstallprompt` for Android button behavior
- keep mocks test-only and impossible to enable accidentally in production

Manual QA checklist
Create or update a repo-local `docs/manual-install-qa.md` with:

iOS:
- open FawxzzyWeb from a TikTok bio or another in-app browser
- confirm the Safari and copy gate
- copy the link
- open Safari
- paste the link
- confirm Add to Home Screen instructions
- add to Home Screen
- launch from the Home Screen
- confirm normal login or app access

Android:
- open Fitness in Chrome on Android
- confirm the install button appears only when the browser marks the app installable
- tap install
- confirm the browser install prompt appears
- install
- launch the installed app
- confirm normal access

Desktop fallback:
- open the app in desktop Chrome or Edge
- confirm install affordance only if the browser exposes one
- confirm no iOS gate appears

Verification
1. run screenshot tests
2. save screenshots in the repo's existing artifact convention
3. run lint, typecheck, and build
4. report:
   - commands run
   - screenshots generated
   - known limitations
   - manual device checks still required

Deliverable
A PR-sized QA and screenshot coverage lane for both apps.
```

## Playbook extraction prompt

Run this only after the implementation exists and the behavior is verified.

```md
Objective
Extract the reusable installer-flow pattern into Playbook notes so future apps can reuse it without relearning the browser and platform constraints.

Context
This is a documentation lane, not an implementation lane.

Tasks
1. Locate the Playbook repo and the appropriate doctrine or pattern note location.
2. Add or update a note for PWA installer gating.
3. Keep the note implementation-derived rather than speculative.

Required sections
- Rule
  A PWA install button may only trigger the native browser install prompt for the current installable app and origin after `beforeinstallprompt` has fired. Launchers should route users to the target app's install route instead of pretending they can install another app directly.
- Pattern
  Use a three-stage flow:
  1. iOS in-app browser: hard gate with "Open in Safari" and copy link
  2. iOS Safari browser: hard gate with Add to Home Screen instructions
  3. iOS standalone or Home Screen: allow normal access
  4. Android or non-iOS: allow access and progressively show native install UI only when available
- Failure Mode
  Do not store `installed=true` in storage as the access source of truth.
- Failure Mode
  User-agent detection for in-app browsers is heuristic and should stay isolated, tested, documented, and easy to update.
- Failure Mode
  Do not label cross-origin navigation as `Install`.
- Verification
  Document screenshot and manual QA expectations for iOS in-app browser, iOS Safari, iOS standalone, Android Chrome install, and desktop fallback.

Deliverable
A concise Playbook entry plus a short docs-summary bullet list suitable for release notes.
```

## Notes

- `beforeinstallprompt` remains browser-controlled and non-standard. A mocked test can verify app logic but not the real system modal.
- iOS Add to Home Screen is guided only. It cannot be forced by the app.
- If `fitness` is still not a clean mounted repo when implementation begins, the orchestrator should stop after discovery and report the blocker instead of drafting fake file edits.
