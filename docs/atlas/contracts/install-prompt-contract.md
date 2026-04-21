# Install Prompt Contract

## Purpose

This document defines the framework-neutral contract for future shared implementation of install promotion. It is a pattern interface, not production code.

## Product Rules

- Show a direct Install button only when prompt capability is available.
- Hide or replace the direct Install button when the app is already installed or already running in installed display mode.
- Provide manual instructions when installation is manually available but no prompt API exists.
- Do not promise one-click install on every browser or device.
- Keep the contract independent from any specific frontend framework.

## Core Concepts

- Availability state: whether the runtime currently exposes a direct install-prompt capability.
- Installed state: whether the app is already installed or already running in an installed display mode.
- Manual-instructions availability: whether the product can offer truthful manual install guidance for the current runtime.
- Outcome events: normalized events emitted as the install CTA is exposed, clicked, accepted, dismissed, or replaced by installed/manual states.

## Canonical Interface

Illustrative only:

```ts
type InstallAvailabilityState =
  | "not-installable"
  | "prompt-available"
  | "prompt-dismissed"
  | "manual-only";

type InstalledState =
  | "not-installed"
  | "installed"
  | "running-installed";

type InstallOutcome =
  | "accepted"
  | "dismissed"
  | "unavailable";

interface InstallPromptContract {
  availabilityState: InstallAvailabilityState;
  installedState: InstalledState;
  manualInstructionsAvailable: boolean;
  canTriggerInstall: boolean;

  triggerInstall(): Promise<InstallOutcome>;
  dismissInstallCTA(reason: "user-dismissed" | "accepted" | "installed" | "capability-lost"): void;
  getManualInstallInstructions(): InstallInstructionSet | null;
}

interface InstallInstructionSet {
  platformKey: string;
  title: string;
  steps: string[];
}
```

## State Machine

The shared implementation should model these states explicitly.

| State | CTA shown | Button label | Fallback copy | Telemetry event(s) |
| --- | --- | --- | --- | --- |
| `not-installable` | No direct CTA | None | Optional silent state or app-specific explanation | None by default |
| `prompt-available` | Yes | `Install app` | None | `install_cta_exposed` |
| `prompt-dismissed` | Usually no direct CTA until capability reappears | None or app-specific reminder | Optional "Install later from browser UI" guidance | `install_prompt_dismissed` |
| `accepted` or `installed` | No direct CTA | None | Optional "App installed" confirmation | `install_prompt_accepted`, `app_installed` |
| `already running installed` | No direct CTA | None | None | `already_installed_detected` |
| `manual-only` | No direct prompt CTA | `How to install` or similar help label if guidance is shown | Platform/browser-specific manual steps | `manual_install_help_shown` |

## Trigger Semantics

- `triggerInstall()` must no-op safely when `canTriggerInstall` is false.
- `triggerInstall()` must only call the retained prompt once for the current capability exposure.
- `triggerInstall()` should emit `install_cta_clicked` before invoking the browser prompt.
- When the prompt is actually shown, emit `install_prompt_shown`.
- Resolve `accepted` or `dismissed` based on the browser-reported outcome when available.
- If the runtime loses capability or no deferred prompt exists, resolve `unavailable`.

## Installed-State Detection

The contract should support installed-state detection through:

- display-mode checks such as `standalone`, `minimal-ui`, `fullscreen`, or other installed presentation modes relevant to the app's manifest.
- the `appinstalled` event where supported.
- optional app-specific signals if a team has an equivalent installed-context detector.

Direct prompt capability and installed-state detection must remain separate because an app can be installable without exposing prompt capability, and an installed app should suppress promotion even if the browser still exposes other install surfaces in a separate browser context.

## Analytics Contract

Use these canonical event names:

| Event | Fire when | Reason |
| --- | --- | --- |
| `install_cta_exposed` | A direct custom CTA becomes visible | Measures prompt-capable exposure |
| `install_cta_clicked` | User clicks the direct CTA | Measures CTA intent |
| `install_prompt_shown` | The retained prompt is invoked | Measures prompt activation |
| `install_prompt_accepted` | Browser prompt returns accepted | Measures direct conversion |
| `install_prompt_dismissed` | Browser prompt returns dismissed | Measures rejection or mistimed prompting |
| `app_installed` | Install completion is signaled, for example through `appinstalled` | Measures completed install |
| `manual_install_help_shown` | Manual instructions are displayed | Measures demand where direct prompt is absent |
| `already_installed_detected` | Installed or running-installed context is detected | Validates suppression logic |

## Verification Matrix

Minimum expected verification:

- Chromium desktop: CTA hidden by default, shown only after prompt capability, removed after install or dismissal.
- Chromium Android: CTA hidden by default, shown only after prompt capability, verify prompt acceptance path and installed result handling.
- Browser without `beforeinstallprompt`: no fake direct Install button; manual guidance only when truthful.
- Already-installed context: install promotion suppressed.
- Standalone display mode: install promotion suppressed.
- Repeat visit after dismissal: direct CTA only returns if the browser re-exposes capability.

## Shared vs App-Local Responsibilities

Suitable for a shared module:

- Prompt capability state.
- Installed-state detection helpers.
- CTA lifecycle state machine.
- Canonical analytics event emission.

Must remain app-local:

- Copy.
- Visual treatment.
- Engagement timing heuristics.
- Manual instruction wording and screenshots.
- Product decision on whether install promotion appears in a given journey.

## Primary References

- [MDN: Trigger installation from your PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt)
- [MDN: Window.beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event)
- [MDN: Window.appinstalled](https://developer.mozilla.org/en-US/docs/Web/API/Window/appinstalled_event)
- [MDN: Create a standalone app](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Create_a_standalone_app)
- [web.dev: Installation prompt](https://web.dev/learn/pwa/installation-prompt/)
- [web.dev: Detection](https://web.dev/learn/pwa/detection/)

## Summary

- What was learned: the reusable abstraction is a state machine and telemetry contract, not a universal button implementation.
- What future apps should reuse: the state vocabulary, trigger semantics, installed-state suppression, and canonical event names.
- What must still be app-specific: copy, UI placement, fallback instruction content, and product timing heuristics.
- What should later become a shared module or package: the capability detector, installed-state detector, and event-emitting controller that implements this contract.
