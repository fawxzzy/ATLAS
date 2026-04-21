# PWA Install Readiness Checklist

Use this checklist before adding install promotion to any ATLAS app.

## PWA Foundation

- [ ] A web app manifest is present.
- [ ] The manifest is linked from every HTML page the app can be installed from.
- [ ] Install naming has been reviewed, including `name` and `short_name` where applicable.
- [ ] `start_url` has been reviewed for the intended installed entry experience.
- [ ] Display mode has been reviewed for installed behavior.
- [ ] Icons are present and reviewed, including install-quality icons for supported platforms.
- [ ] Chromium install-promotion requirements have been checked, including icons in 192px and 512px sizes where needed.
- [ ] HTTPS is confirmed for production, with localhost-only exceptions limited to development.

## Installed Experience

- [ ] Installed-state detection has been reviewed using display mode and any supported install signals.
- [ ] The app hides or replaces install promotion when already running installed.
- [ ] The app's installed shell, navigation, and window expectations have been reviewed.
- [ ] Service worker behavior has been reviewed.
- [ ] Offline capability expectations have been reviewed, even where they are not a hard install requirement.

## Custom CTA Gating

- [ ] The custom Install CTA is hidden by default.
- [ ] The CTA is shown only after install-prompt capability has actually been exposed.
- [ ] The implementation does not assume `beforeinstallprompt` exists on all browsers.
- [ ] The implementation treats `prompt()` as one-shot for a retained event.
- [ ] The CTA is cleared after acceptance, dismissal, or capability loss for the current deferred event.

## Fallback Guidance

- [ ] Manual fallback instructions have been reviewed for browsers that support manual installation without exposing prompt APIs.
- [ ] The UI does not pretend a direct install API exists when it does not.
- [ ] Manual instructions are suppressed when the app is already running installed.
- [ ] Platform wording has been reviewed for accuracy.

## Analytics

- [ ] Analytics hooks exist for CTA exposure, CTA click, prompt shown, prompt accepted, prompt dismissed, install detected, and manual help shown.
- [ ] Installed-context detection is logged so teams can measure how often promotion is correctly suppressed.
- [ ] Analytics names align with the shared ATLAS event vocabulary.

## Verification Matrix

- [ ] Chromium desktop has been tested for capability-gated CTA, prompt, and installed-state suppression.
- [ ] Chromium Android has been tested for capability-gated CTA, prompt, and install completion behavior.
- [ ] At least one browser without `beforeinstallprompt` support has been tested for manual fallback behavior.
- [ ] Already-installed app context has been tested.
- [ ] Standalone display mode has been tested.
- [ ] Repeat visit behavior after dismissal has been tested.

## Primary References

- [MDN: Making PWAs installable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)
- [MDN: Trigger installation from your PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt)
- [MDN: Create a standalone app](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Create_a_standalone_app)
- [web.dev: Installation prompt](https://web.dev/learn/pwa/installation-prompt/)
- [web.dev: Detection](https://web.dev/learn/pwa/detection/)
- [web.dev: Web app manifest](https://web.dev/learn/pwa/web-app-manifest/)
- [web.dev: What does it take to be installable?](https://web.dev/articles/install-criteria)

## Summary

- What was learned: shipping install UX safely requires readiness across manifest, icons, security, installed-state handling, and fallback guidance.
- What future apps should reuse: this checklist as a preflight gate before adding install promotion.
- What must still be app-specific: the exact manual instructions, installed UX review, and chosen engagement timing.
- What should later become a shared module or package: reusable verification helpers for capability gating, installed-state checks, and analytics hooks.
