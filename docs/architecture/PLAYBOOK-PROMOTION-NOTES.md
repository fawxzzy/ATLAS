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

Release risk
- The main risk is not the semantic-lane code itself.
- The main risk is stale or invalid live-capture state:
  - wrong `:3000` owner
  - stale auth session
  - screenshot from the wrong route or state

Next gate before any production discussion
1. pass `npm run test:app-theme`
2. pass `npm run build`
3. refresh protected-route screenshot proof in a Codex-owned browser
4. confirm preview from the current workspace source
