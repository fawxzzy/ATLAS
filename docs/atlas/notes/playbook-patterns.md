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

## Additional Pattern: Rapid Localhost Iteration Loop

### Rule

Keep a persistent local runtime alive and optimize for minimal patches plus immediate preview.

### Pattern

Use two-speed validation. Check the affected screen every iteration; run broader screenshot sweeps only at checkpoints.

### Failure Mode

Running a full screenshot pass after every micro-change destroys iteration speed and creates low-signal work.

### Summary

- What was learned: rapid iteration stays fast only when validation stays proportional to the scope of the patch.
- What future apps should reuse: the affected-screen-first loop for localhost, HMR, live reload, and Fast Refresh workflows.
- What must still be app-specific: the screen inventory source of truth, route access path, auth state, and exact screenshot tooling.
- What should later become a shared module or package: a reusable screen-inventory contract plus lightweight affected-screen screenshot adapters for web and mobile repos that already support them.

## Additional Pattern: Named Session Bootstraps

### Rule

Named AI session modes must resolve to canonical Atlas docs, not ad hoc interpretation.

### Pattern

Separate knowledge docs from execution bootstrap prompts, then bind both through a lightweight alias registry.

### Failure Mode

A workflow doc with no named invocation contract is hard to reuse consistently across sessions and repos.

### Summary

- What was learned: reusable workflows need a stable invocation layer or they degrade back into prompt folklore.
- What future apps should reuse: one named mode, one workflow doc, one prompt doc, and one alias registry entry per stable operating pattern.
- What must still be app-specific: repo resolution details, local runtime assumptions, and the exact validation output shape that each repo needs.
- What should later become a shared module or package: a small Atlas-owned session-mode registry contract plus deterministic repo-resolution helpers.
