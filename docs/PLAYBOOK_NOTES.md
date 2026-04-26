# Playbook Notes

## 2026-04-25 - Launcher routes, target app installs

- Rule: a launcher routes users to the target app's canonical install route; the target app owns installability, iOS gates, and standalone access truth.
- Rule: a native PWA install button may only exist for the current origin after `beforeinstallprompt` has fired.
- Pattern: use a split platform flow.
  1. iOS in-app browser: hard gate with `Open in Safari` and copy link.
  2. iOS Safari browser tab: hard gate with `Share, then Add to Home Screen`.
  3. iOS standalone/Home Screen: allow normal access.
  4. Android and other non-iOS browsers: allow access and show native install UI only when the browser exposes it.
- Failure Mode: do not treat `localStorage` or `sessionStorage` as installed truth.
- Failure Mode: do not label cross-origin navigation as `Install`.
- Failure Mode: do not wrap the entire app shell when browser auth and recovery routes must remain usable in-browser.
- Failure Mode: browser automation can prove app logic and mocked install states, but real iOS Add to Home Screen and real Android native install prompts still need manual device QA.
- Release-summary bullets:
  - Added launcher-to-target-app installer routing doctrine for cross-origin PWAs.
  - Added the iOS in-app browser, Safari, and standalone access-gate pattern.
  - Added the rule that native install CTAs are current-origin only and capability-gated.
  - Added runtime standalone detection as the installed-state source of truth.
  - Added manual-device QA as a required final step for real install flows.

## 2026-04-23 - Fitness auth must not own install acquisition

- Rule: app auth flow must not own install acquisition UX when install is handled externally.
- Pattern: auth/recovery routes should keep one shared shell with inline status and error messages instead of branching into screen-per-state variants.
- Failure Mode: install-first route branching and standalone recovery error screens create extra state surfaces, stale capture-map truth, and mobile UI drift for flows that should stay message-level.

## 2026-04-23 - Fitness release lanes require manual _stack deploys and reusable QA auth

- Type: Guardrail
- Summary: Fitness deploy and QA work must use `_stack` deploy entrypoints, keep Vercel Git auto-deploy creation disabled, and verify auth-aware local flows with one permanent Supabase QA user instead of random signup users.
- Suggested Playbook File: docs/GUARDRAILS/fitness-auth-deploy-qa-lane.md
- Rationale: Prevents repeated auth/deploy chaos where throwaway users accumulate, local browser and server Supabase env drift apart, Git-triggered Vercel deploys silently reappear, or deploys run from the wrong repo boundary.
- Evidence: repos/_stack/ops/Test-FitnessDeployLink.ps1, repos/_stack/ops/Test-FitnessDoctor.ps1, repos/fawxzzy-fitness/scripts/qa/fitness-qa-user.mjs, repos/fawxzzy-fitness/scripts/qa/fitness-local-feedback.mjs
- Status: Proposed

## Deploy identity guards

- Production deploy guards should validate the configured live hosting identity for the current lane, not a guessed future owner or namespace.
- For Vercel-backed repos, keep the expected scope and project in checked-in operator config and allow explicit environment overrides for one-off validation.
- Treat visible team-label cleanup and namespace changes as separate lanes. Namespace changes can alter future generated hosting URLs and should not be bundled into an unrelated production deploy.
- Hosting identity checks must validate immutable team/project IDs, not only mutable slugs or display names.
- Use connector-confirmed project identity as source of truth, then mirror that identity into operator deploy guards and repo-local `.vercel/project.json` metadata.
- Failure Mode: A team rename makes slug-only checks lie, which looks like a wrong-owner failure even when the linked Vercel project is correct.
- If Vercel sees the correct team and project but a fresh pushed SHA creates no deployment object, classify it as a Git integration ingestion failure before diagnosing app code or retrying production deploys from the CLI.
- After connector repair, prefer one fresh Git-triggered branch deployment as the proof path; only resume production shipping after Vercel creates and runs that branch deployment from Git.
- Failure Mode: Repeated CLI production retries can mask the real issue when Git-connected preview creation is disabled or dead, which makes an ingestion outage look like an app or build failure.
- Failure Mode: A mounted app folder under `C:\ATLAS` inherits the parent repo boundary and poisons Git recovery until the app is recloned as a real standalone repo.
- Failure Mode: Windows prebuilt deploy fallback can fail on symlink packaging; do not diagnose app code from that signal alone.
