# ADR: Capability-Driven Installable Web App Pattern

- Status: Accepted for future ATLAS app guidance
- Date: 2026-04-21

## Context

Future ATLAS apps will want an "Install App" experience, but browsers do not expose a single universal installation API.

- MDN and web.dev both document that installability starts with PWA prerequisites such as a manifest, secure delivery, and install identity.
- MDN marks `beforeinstallprompt` as Limited availability, and MDN's trigger guide warns that the custom-prompt flow is non-standard and Chromium-based.
- web.dev documents that `beforeinstallprompt` is only fired after install criteria are met, and also documents cases where it cannot fire.
- Installed state is separate again: MDN and web.dev both document using display mode and install events to detect installed contexts and remove install promotion.

Without a stack rule, app teams are likely to ship an always-visible Install button that is broken, misleading, or dead on unsupported browsers.

## Decision

ATLAS will treat install UX as a capability-driven progressive enhancement pattern.

- Build installability first.
- Render a direct custom Install CTA only when install-prompt capability has been confirmed for the current runtime.
- Hide or replace the CTA when the app is already installed or already running in installed display mode.
- When prompt capability is absent but manual installation is still available, show truthful manual guidance instead of fake direct install behavior.
- Keep the implementation framework-neutral so React, Vue, Svelte, plain web, and native-wrapper web apps can reuse the same contract.

## Consequences

- Install UX becomes more trustworthy because the app only offers direct install when the runtime can actually honor it.
- App teams must invest in installed-state detection and fallback guidance, not only in a button.
- Documentation and shared abstractions can be reused across apps, while still allowing app-specific copy and timing.
- QA must validate both supported prompt flows and fallback/manual flows.

## Tradeoffs

- This pattern is more complex than a permanently visible Install button.
- Analytics must distinguish prompt-capable sessions from manual-guidance sessions.
- Manual fallback guidance is extra product work, especially for iOS and other prompt-limited environments.
- Because browser behavior changes over time, teams must periodically re-verify support assumptions against MDN and web.dev.

## Rejected Alternatives

### Always show a universal Install button

Rejected because it turns install into a product promise the browser may not support. This creates dead UI on unsupported browsers and teaches users not to trust the CTA.

### Treat installability as equivalent to prompt availability

Rejected because an app can be installable while the browser still does not expose `beforeinstallprompt` in the current runtime.

### Depend on one framework-specific hook or component contract

Rejected because the ATLAS asset is meant to span future apps and frameworks. The reusable unit should be a state and event contract, not a framework binding.

### Hide all install guidance unless direct prompt exists

Rejected because some platforms allow manual installation without exposing a programmatic prompt. In those cases the correct fallback is manual guidance, not silence.

## Why We Treat Install as Capability-Driven Rather Than Always-On UI

- Installability is a prerequisite, not a guarantee of a prompt.
- Browser-provided install UI is browser- and platform-dependent.
- `beforeinstallprompt` is non-universal.
- Installed state must suppress promotion to avoid redundant or contradictory UI.
- Manual install paths can still be valid when prompt APIs are absent.

The correct product model is therefore capability first, CTA second, fallback third.

## Primary References

- [MDN: Making PWAs installable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- [MDN: Trigger installation from your PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt)
- [MDN: Installing and uninstalling web apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Installing)
- [MDN: Window.beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event)
- [MDN: Window.appinstalled](https://developer.mozilla.org/en-US/docs/Web/API/Window/appinstalled_event)
- [web.dev: Installation prompt](https://web.dev/learn/pwa/installation-prompt/)
- [web.dev: Detection](https://web.dev/learn/pwa/detection/)
- [web.dev: What does it take to be installable?](https://web.dev/articles/install-criteria)

## Summary

- What was learned: direct install prompting is runtime capability, not a universal entitlement of every PWA.
- What future apps should reuse: the decision to gate CTA rendering on prompt capability and suppress promotion in installed contexts.
- What must still be app-specific: the install moment, the wording, and the manual guidance content.
- What should later become a shared module or package: common capability detection, installed-context detection, and event emission semantics.
