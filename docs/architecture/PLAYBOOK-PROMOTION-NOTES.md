# Pass 2.5 Promotion Notes

Current lane
- Main work: App Theme V1.1 semantic-lane coverage plus visual validation.
- Preview deploys may proceed after local verification.
- Production remains intentionally gated.

What shipped locally
- The App Theme harness moved beyond a minimal primary/surface/radius proof.
- Semantic lanes now exist for:
  - secondary action
  - accent / divider
  - success / complete
  - selection / active
  - loader / scan
  - warning
- Today rest-day header wording was cleaned up.
- Session, edit-day, add-exercise, and history surfaces were rewired toward shared semantic lanes instead of route-local green/yellow accents.
- Fresh screenshot-backed local proof exists for the protected representative route suite under:
  - `tmp/captures/fitness/visual-operator/theme/2026-04-29`
- Separate closeout evidence exists for loader and settings-panel-open proof under:
  - `tmp/captures/fitness/app-theme-v1_1-closeout/2026-04-29`
- Final proof preview evidence now exists under:
  - `tmp/captures/fitness/app-theme-v1_1-final-proof/2026-04-29-preview`

Why this matters
- Theme settings are no longer just a feature.
- Theme settings are the proof harness for Atlas/Codex visual control over the app.

Promotion rules
- Promote the harness and the semantic-lane contract.
- Do not promote a full theme product claim from this pass.
- Do not reopen production from this lane until the protected representative route suite is freshly captured in a Codex-owned browser.

Browser rule
- Live UI work must run in a Codex-owned isolated browser profile.
- User browsers are not an approved operator surface.

Preview posture
- The canonical Vercel project lane is `fawxzzy-fitness`.
- Preview may be used for smoke checks after local verification.
- Production must remain untouched during this pass.
- Protected/history proof is now local-evidence-backed instead of assumed.
- The final proof preview pass confirmed `/login` and `/install` on the current READY preview, but did not produce protected preview proof because isolated `/settings` redirected to `/login`.

Release risk
- The main risk is not the semantic-lane code itself.
- The main risk is stale or invalid live-capture state:
  - wrong `:3000` owner
  - stale auth session
  - screenshot from the wrong route or state
- Secondary remaining risk:
  - settings-panel-open proof still depends on the closeout set
  - loader/scan proof still depends on the closeout set
  - rest-day header wording is source-verified but not freshly captured from a live rest-day state in the current operator profile
  - the local `:3000` lane can stall on `/login` and `/settings`, which blocks trustworthy refresh captures even while build output remains green

Next gate before any production discussion
1. pass `npm run test:app-theme`
2. pass `npm run build`
3. review the refreshed protected-route screenshot proof in a Codex-owned browser
4. confirm preview from the current workspace source
5. keep production gated unless the remaining evidence gaps are explicitly waived
