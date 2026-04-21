# Playbook Patterns

## Rule

Never render a universal Install button. Render install UI only when install capability is confirmed for the current runtime.

## Pattern

Treat web app installation as progressive enhancement: installable PWA foundation first, custom CTA second, manual guidance fallback third.

## Failure Mode

Shipping a visible Install button without capability gating causes broken UX on unsupported browsers and teaches users not to trust the CTA.

## Primary References

- [MDN: Trigger installation from your PWA](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt)
- [MDN: Window.beforeinstallprompt](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeinstallprompt_event)
- [web.dev: Installation prompt](https://web.dev/learn/pwa/installation-prompt/)

## Summary

- What was learned: install UI must follow runtime capability, not product wishful thinking.
- What future apps should reuse: the rule, pattern, and failure-mode shorthand in reviews and planning.
- What must still be app-specific: exact UI treatment and platform-specific help content.
- What should later become a shared module or package: a standard install-promotion controller that enforces this rule automatically.
