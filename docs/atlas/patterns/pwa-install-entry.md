# PWA Install Entry Pattern

## Overview

This pattern defines how future ATLAS web apps should expose "Install App" UX without overstating what the browser can do. The core rule is that installation is a capability, not a promise: an app must first be installable as a PWA, the browser may or may not expose install UI, and a custom in-app Install button is only appropriate when the runtime has actually exposed install-prompt capability.

## When to use

- Use this pattern when an app is already shipping or planning a real PWA surface.
- Use this pattern when the app has a manifest, installable identity, and a reviewed installed experience.
- Use this pattern when the product wants a custom in-app Install CTA as progressive enhancement on supported browsers.
- Use this pattern when the team is willing to provide manual install guidance on platforms where a direct prompt is unavailable.

## When not to use

- Do not use this pattern if the app is not intended to be installable as a PWA.
- Do not use this pattern if the app lacks a manifest, install identity, or reviewed installed display mode.
- Do not use this pattern if the team cannot maintain browser-specific fallback guidance.
- Do not use this pattern to promise one-click install on every browser or device.

## Installability Prerequisites

An app must be installable as a PWA before any custom install CTA is considered.

- Manifest: include a web app manifest and link it from every installable HTML page. MDN and web.dev both treat the manifest as foundational for installability.
- Install identity: ensure the manifest includes install-facing fields such as `name` or `short_name`, `start_url`, `display`, and icons. web.dev documents Chromium install-promotion criteria that include `name` or `short_name`, `start_url`, `display`, and icons including 192px and 512px sizes.
- Icons: provide real app icons, not placeholders. MDN recommends multiple icon sizes and maskable support for better OS integration.
- Secure context: serve the app over HTTPS in production. MDN states installability requires `https`, `localhost`, or `127.0.0.1`.
- Installed UX readiness: review the app's display mode and installed-window behavior before adding promotion. Installed and browser contexts are not the same surface.
- Service worker and offline expectations: MDN notes service workers are not universally required for installability, but they are commonly used to provide offline experience. ATLAS should therefore treat service worker and offline behavior as a readiness review item even when it is not a hard install gate in every browser.

## Browser Behavior Model

Treat these as separate concerns:

- Installable app: the app meets technical installability prerequisites.
- Browser-provided install UI: the browser may promote installation through its own address-bar icon, overflow menu entry, or similar surface.
- Custom in-app install CTA: the app may add its own Install button only when the runtime exposes install-prompt capability.

Important distinctions:

- `beforeinstallprompt` is not a universal browser feature. MDN marks it as Limited availability, and MDN's trigger guide calls it non-standard and currently Chromium-based.
- web.dev documents that the app must still pass install criteria before the browser fires `beforeinstallprompt`.
- The event will not fire when the app is already installed, when the app does not meet install criteria, or when the device/runtime cannot install the app.
- MDN documents that this custom-prompt technique is not supported on iOS.
- Browser install UI varies by browser and platform even when installability exists.

## Progressive Enhancement Strategy

The progressive enhancement order is fixed:

1. Build an installable PWA foundation.
2. Wait for the browser to expose install-prompt capability.
3. Render an in-app Install CTA only after capability is confirmed and the app is not already running in installed mode.
4. On click, call the retained prompt once.
5. Remove or replace the CTA after install, after dismissal, or when installed state is detected.

Operational rules:

- Hide the custom Install CTA by default.
- Reveal it only after `beforeinstallprompt` has fired and been retained.
- Treat `prompt()` as one-shot for a given deferred event.
- Hide or replace the CTA when `appinstalled` fires on supported Chromium browsers.
- Also hide or replace the CTA when runtime detection shows the app is already running in installed display mode, such as `standalone`.

## Fallback Strategy

When there is no usable prompt API, the app must not fake one-click install.

- If install is manually possible but `beforeinstallprompt` is unavailable, show manual guidance instead of a direct Install button.
- Render manual instructions only in browser mode, not when already running installed.
- Keep manual instructions platform-specific and truthful.
- On iOS and iPadOS, web.dev documents that Chrome and Edge do not expose `beforeinstallprompt`; manual installation goes through share-menu flows instead of a direct API.
- MDN separately documents that on iOS and iPadOS 16.4 and later, installation is available from the Share menu in supporting browsers, which reinforces the pattern rule that prompt capability and installability must be treated separately.

## UX Guidelines

- Default label: `Install app`.
- Only show the CTA after both conditions are true: install-prompt capability exists, and the app is not already installed.
- Do not render a permanent disabled Install button on unsupported platforms.
- Prefer surfacing the CTA at a meaningful engagement point rather than immediately on first paint.
- If the user dismisses the prompt, remove the CTA for the current deferred event and rely on a later browser re-exposure before offering the direct prompt again.
- If only manual guidance is available, label it as help or instructions rather than as a direct install action.
- Hide or replace install promotion when the app is already installed or running in a standalone display mode.

## Analytics Recommendations

Use a consistent event set across apps:

| Event | When to fire | Why it matters |
| --- | --- | --- |
| `install_cta_exposed` | When a capability-gated custom CTA becomes visible | Measures real prompt eligibility, not theoretical installability |
| `install_cta_clicked` | When the user clicks the custom CTA | Measures CTA engagement |
| `install_prompt_shown` | Immediately before or after invoking `prompt()` | Measures prompt usage volume |
| `install_prompt_accepted` | When the prompt result is accepted | Measures prompt conversion |
| `install_prompt_dismissed` | When the prompt result is dismissed | Measures friction or mistimed prompts |
| `app_installed` | When `appinstalled` fires or installed state is otherwise confirmed | Measures completed install outcomes |
| `manual_install_help_shown` | When manual fallback guidance is opened | Measures unsupported-capability demand |
| `already_installed_detected` | When installed display mode or equivalent installed context is detected | Prevents double-promotion and helps validate gating |

## Future Implementation Notes

- Keep the shared logic framework-agnostic.
- Put capability detection, installed-state detection, and telemetry vocabulary in a shared package when multiple apps need the same behavior.
- Keep copy, engagement heuristics, manual instruction content, and design treatment app-local.
- Treat browser support tables as living reference material and re-check MDN and web.dev before operationalizing the pattern in a production app.

## Primary References

- [MDN: Trigger installation from your PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt)
- [MDN: Making PWAs installable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- [MDN: Installing and uninstalling web apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Installing)
- [MDN: Window.beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event)
- [MDN: Window.appinstalled](https://developer.mozilla.org/en-US/docs/Web/API/Window/appinstalled_event)
- [MDN: Create a standalone app](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Create_a_standalone_app)
- [MDN: Define your app icons](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Define_app_icons)
- [web.dev: Installation prompt](https://web.dev/learn/pwa/installation-prompt/)
- [web.dev: Detection](https://web.dev/learn/pwa/detection/)
- [web.dev: Web app manifest](https://web.dev/learn/pwa/web-app-manifest/)
- [web.dev: What does it take to be installable?](https://web.dev/articles/install-criteria)

## Summary

- What was learned: installability, browser promotion, and custom CTA support are different layers and must not be conflated.
- What future apps should reuse: capability-gated CTA behavior, installed-state hiding, manual fallback handling, and the canonical telemetry vocabulary.
- What must still be app-specific: install copy, engagement timing, manual instruction content, and platform support priorities.
- What should later become a shared module or package: prompt availability state, installed-state detection, CTA lifecycle handling, and analytics event emission helpers.
